"""Advertising workflow payload checks; no network, file writes or model calls."""

import re
from utils.execution_markers import EXEC_FAILURE, has_execution_failure as _has_exec_failure


_TOKENS = tuple(
    f"[[{family}_{state}]]"
    for family, states in (
        ("BRIEF", ("READY", "NEED_INFO", "INVALID")),
        ("QA", ("PASS", "REVISE", "INVALID")),
        ("PLAN", ("OK", "ISSUES", "ERROR")),
        ("BUILD", ("OK", "BLOCKED", "ERROR")),
        ("REVIEW", ("APPROVE", "REVISE", "INVALID")),
    )
    for state in states
)
_FAILURE = EXEC_FAILURE


def _clean(text):
    for token in _TOKENS:
        text = text.replace(token, token.replace("[[", "[ [").replace("]]", "] ]"))
    return text


def _route(data, family, states):
    text = data or ""
    result = "INVALID"
    if not any(token in text for token in _TOKENS) and not _has_exec_failure(text):
        options = "|".join(re.escape(state) for state in states)
        status = rf"{family}: (?P<status>{options})"
        # Bold must be paired. The optional period is outside the bold span.
        line_re = re.compile(rf"[ \t]*(?P<bold>\*\*)?{status}(?(bold)\*\*)\.?[ \t]*")
        fence_char, fence_length = None, 0
        matches = []
        lines = text.replace("\r\n", "\n").split("\n")
        nonblank = [i for i, line in enumerate(lines) if line.strip(" \t\r")]
        for index, line in enumerate(lines):
            stripped = line.lstrip(" \t")
            fence = re.match(r"(`{3,}|~{3,})(.*)$", stripped)
            if fence_char is not None:
                if fence and fence.group(1)[0] == fence_char and len(fence.group(1)) >= fence_length and not fence.group(2).strip():
                    fence_char, fence_length = None, 0
                continue
            if fence:
                fence_char, fence_length = fence.group(1)[0], len(fence.group(1))
                continue
            match = line_re.fullmatch(line)
            if match:
                matches.append((index, match.group("status")))
        if len(matches) == 1 and nonblank and matches[0][0] == nonblank[-1] and fence_char is None:
            result = matches[0][1]
    return _clean(text) + f"\n[[{family}_{result}]]"


def ad_brief_route(data, _context):
    """Preserve current brief/questions and append one validated brief token."""
    return _route(data, "BRIEF", ("READY", "NEED_INFO"))


def ad_qa_route(data, _context):
    """Preserve current QA report and append one validated QA token."""
    return _route(data, "QA", ("PASS", "REVISE"))


def ad_review_route(data, _context):
    """Validate the exact Human command, preserving its feedback for rework."""
    text = data or ""
    command = text.strip()
    result = "INVALID"
    if "[[" not in text and not _has_exec_failure(text):
        if command == "HUMAN: APPROVE":
            result = "APPROVE"
        elif command.startswith("HUMAN: REVISE"):
            feedback = command[len("HUMAN: REVISE"):]
            # Preserve the former word-boundary and nonempty-feedback rules.
            word = lambda char: char.isalnum() or char == "_"
            if feedback and not word(feedback[0]) and any(word(c) for c in feedback):
                result = "REVISE"
    return _clean(text) + f"\n[[REVIEW_{result}]]"


def _fallback(data, family, states):
    text = data or ""
    found = [token for token in _TOKENS for _ in range(text.count(token))]
    valid = {f"[[{family}_{state}]]" for state in states}
    if len(found) == 1 and found[0] in valid and not _has_exec_failure(text) and text.rstrip().endswith(found[0]):
        return None  # Engine drops this payload BEFORE setting the edge trigger.
    return _clean(text) + f"\nRouting rejected: invalid {family} output."


def ad_brief_fallback(data, _context):
    """Drop only recognized READY/NEED_INFO output; forward failures to Blocked."""
    return _fallback(data, "BRIEF", ("READY", "NEED_INFO"))


def ad_qa_fallback(data, _context):
    """Drop only recognized PASS/REVISE output; forward failures to Blocked."""
    return _fallback(data, "QA", ("PASS", "REVISE"))


def ad_plan_fallback(data, _context):
    """Drop only recognized OK/ISSUES output; forward failures to Blocked."""
    return _fallback(data, "PLAN", ("OK", "ISSUES"))


def ad_build_fallback(data, _context):
    """Drop only recognized OK output; forward failures to Blocked."""
    return _fallback(data, "BUILD", ("OK",))


def ad_review_fallback(data, _context):
    """Forward invalid/missing review tokens to Invalid_Review_Notice."""
    return _fallback(data, "REVIEW", ("APPROVE", "REVISE"))


def ad_checked_payload(data, _context):
    """Drop malformed envelopes before a successful/rework edge can trigger."""
    for family, states in (("BRIEF", ("READY", "NEED_INFO")), ("QA", ("PASS", "REVISE")),
                           ("PLAN", ("OK", "ISSUES")), ("BUILD", ("OK",)),
                           ("REVIEW", ("APPROVE", "REVISE"))):
        if _fallback(data, family, states) is None:
            return data
    return None


def ad_plan_classify(data, context):
    """Run once per Gate output: classify ownership and detect no-progress."""
    import json
    text=str(data or '').replace('\r\n','\n').replace('\r','')
    def blocked(report,reason,owner):
        report=dict(report);report['status']='ERROR';report['repair_owner']=owner
        report['errors']=list(report.get('errors') or [])+[reason]
        context.pop('ad_plan_last_issues',None)
        payload=_clean(json.dumps(report,ensure_ascii=False))
        from utils.execution_markers import EXEC_FAILURE_MARKERS
        for marker in EXEC_FAILURE_MARKERS:payload=payload.replace(marker,'execution failure (diagnostic)')
        return payload+'\nPLAN: ERROR\n[[PLAN_ERROR]]'
    if _fallback(text,'PLAN',('OK','ISSUES','ERROR')) is not None:
        return blocked({},'Invalid Plan_Gate result envelope','workflow')
    try:
        body,separator,_=text.rpartition('\nPLAN: ')
        if not separator:raise ValueError('missing status line')
        report=json.loads(body);status=report['status']
        if status not in ('OK','ISSUES','ERROR') or not text.rstrip().endswith('[[PLAN_'+status+']]'):raise ValueError('status mismatch')
        if not isinstance(report.get('errors'),list) or not isinstance(report.get('issues'),list):raise ValueError('errors/issues must be lists')
    except (ValueError,KeyError,TypeError):return blocked({},'Invalid Plan_Gate JSON/status','workflow')
    if status=='OK' and (report['errors'] or report['issues']):return blocked(report,'Contradictory successful Gate result','workflow')
    if status=='ISSUES' and report['errors']:return blocked(report,'Gate errors cannot enter a repair loop','workflow')
    if status!='ISSUES':
        context.pop('ad_plan_last_issues',None)
        return data
    issues=report['issues']
    if not issues or any(not isinstance(issue,str) or not issue.strip() for issue in issues):return blocked(report,'Invalid empty/malformed repair issues','workflow')
    readonly=('campaign_brief.json','market_research.md','competitor_analysis.md','audience_segments.json','customer_journey.md','evidence_digest.md','sources.csv')
    source_issues=[issue for issue in issues if any(re.match(r'^'+re.escape(name)+r'(?:[\s:\[]|$)',issue.strip()) for name in readonly)]
    if source_issues:
        return blocked(report,'Source/brief verification is outside Plan_Assembler permissions. Route to source owner; do not repeat the assembly loop.','Evidence/Research/Brief owner')
    signature=tuple(sorted(set(' '.join(issue.split()) for issue in issues)))
    if context.get('ad_plan_last_issues')==signature:
        return blocked(report,'NO_PROGRESS: the same unresolved Gate issues remain after a repair. Stop repeated model calls and inspect the named files.','manual repair')
    context['ad_plan_last_issues']=signature
    return data
