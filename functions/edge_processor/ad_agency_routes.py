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
