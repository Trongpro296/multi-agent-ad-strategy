"""Advertising workflow contracts. Runs locally; never calls a model or tool."""
import csv
import json
from pathlib import Path
import unicodedata
import datetime
import re
import hashlib
from decimal import Decimal
from importlib.util import find_spec

from utils.exceptions import WorkflowExecutionError
from utils.code_execution import require_unsafe_code_execution
from utils.ad_review_contracts import qa_report_issues
from utils.ad_csv import CSV_COLUMNS as _COLUMNS

_OUTPUTS = {
    'Director_Brief': ('campaign_brief.json',),
    'Market_Researcher': ('market_research.md',),
    'Competitor_Analyst': ('competitor_analysis.md',),
    'Customer_Insight': ('audience_segments.json', 'customer_journey.md'),
    'Evidence_Digest': ('evidence_digest.md', 'sources.csv'),
    'Brand_Strategist': ('brand_positioning.md',),
    'Director_Strategy': ('campaign_strategy.md', 'strategy_ids.json'),
    'Media_Planner': ('media_plan.csv', 'budget_scenarios.csv'),
    'Creative_Director': ('creative_brief.md', 'creative_matrix.csv'),
    'Performance_Analyst': ('measurement_plan.md', 'experiment_plan.csv'),
    'Plan_Assembler': ('advertising_strategy_draft.md', 'execution_calendar.csv'),
    'Strategy_QA': ('qa_report.json',),
    'Delivery_Packager': ('handoff_notes.md',),
}
def _validate_result(node_id, message, state):
    if node_id == 'Publication_QA':
        from utils.ad_publication import validate_publication_qa,verify_sources
        if state.get('ad_publication_write_errors'):raise WorkflowExecutionError('Unresolved publication QA write rejection',node_id=node_id)
        verify_sources(state['python_workspace_root'])
        report=validate_publication_qa(state['python_workspace_root'])
        message.content='Public content QA: '+report['verdict']+'\n'+json.dumps(report,ensure_ascii=False)
        return
    if node_id == 'Publication_Editor':
        from utils.ad_publication import validate_content,verify_sources
        if state.get('ad_publication_write_errors'):raise WorkflowExecutionError('Unresolved publication content write rejection',node_id=node_id)
        verify_sources(state['python_workspace_root'])
        bundle=validate_content(state['python_workspace_root'])
        message.content='Final public copy prepared for Human review; plan_version='+bundle['plan_version']
        return
    names = _OUTPUTS.get(node_id)
    if not names:
        return
    # Brief clarification is a valid intermediate outcome, not a file handoff.
    if node_id == 'Director_Brief':
        from functions.edge_processor.ad_agency_routes import ad_brief_route
        routed = ad_brief_route(message.text_content(), {})
        if routed.endswith('[[BRIEF_NEED_INFO]]'):
            return
    workspace = Path(state['python_workspace_root']).resolve()
    problems = []
    pending = state.get('ad_csv_write_errors', {})
    for name in names:
        if 'artifacts/' + name in pending:
            problems.append('unresolved CSV write rejection: ' + name)
        path = workspace / 'artifacts' / name
        if not path.resolve().is_relative_to(workspace) or not path.is_file():
            problems.append('missing/unsafe artifacts/' + name)
            continue
        try:
            text = path.read_text(encoding='utf-8-sig')
            if not text.strip():
                problems.append('empty artifacts/' + name)
            elif name.endswith('.json'):
                value = json.loads(text)
                if not isinstance(value, (dict, list)) or not value:
                    problems.append('empty/invalid JSON ' + name)
            elif name.endswith('.csv'):
                with path.open(encoding='utf-8-sig', newline='') as f:
                    reader = csv.DictReader(f, strict=True)
                    header = reader.fieldnames or []
                    if len(set(header)) != len(header) or not set(_COLUMNS[name]).issubset(header):
                        problems.append('CSV columns invalid ' + name)
                    rows = list(reader)
                    if not rows:
                        problems.append('CSV has a header but no data rows: ' + name)
                    elif any(None in row or any(value is None for value in row.values()) for row in rows):
                        problems.append('CSV row width does not match the header: ' + name)
        except (ValueError, OSError, csv.Error) as exc:
            problems.append(name + ': ' + type(exc).__name__)
    if problems:
        raise WorkflowExecutionError('Artifact contract failed for '+node_id+': '+'; '.join(problems), node_id=node_id)
    if node_id == 'Evidence_Digest':
        from utils.ad_delivery_policy import source_issues_csv
        findings=source_issues_csv((workspace/'artifacts/sources.csv').read_bytes())
        if findings:raise WorkflowExecutionError('Evidence source contract failed: '+'; '.join(f['message'] for f in findings),node_id=node_id)
    if node_id == 'Director_Brief':
        brief = json.loads((workspace/'artifacts/campaign_brief.json').read_text(encoding='utf-8-sig'))
        try:
            budget = brief['budget']
            amount = str(budget['ad_spend']).strip()
            if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', amount) or not Decimal(amount).is_finite() or not str(budget['currency']).strip():
                raise ValueError('budget')
            dates = [brief[k] for k in ('start_date','end_date')]
            if not all(isinstance(d,str) and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',d) for d in dates):
                raise ValueError('dates')
            start,end = map(datetime.date.fromisoformat,dates)
            if start>end: raise ValueError('date range')
        except (KeyError,TypeError,ValueError):
            raise WorkflowExecutionError('Brief READY requires valid budget.ad_spend, currency and campaign dates; ask BRIEF: NEED_INFO instead',node_id=node_id)
    if node_id == 'Strategy_QA':
        if state.get('ad_qa_write_errors'):
            raise WorkflowExecutionError('Unresolved QA report write rejection; correct qa_report.json before finishing',node_id=node_id)
        qa = json.loads((workspace/'artifacts/qa_report.json').read_text(encoding='utf-8-sig'))
        manifest = json.loads((workspace/'review/review_manifest.json').read_text(encoding='utf-8-sig'))
        report_problems = qa_report_issues(qa,manifest.get('plan_version'),manifest.get('files',{}))
        if report_problems:
            raise WorkflowExecutionError('QA v2 contract failed: '+'; '.join(report_problems),node_id=node_id)
        review_files = manifest.get('files')
        if not isinstance(review_files, dict) or not review_files:
            raise WorkflowExecutionError('QA snapshot verification failed: missing file hashes',node_id=node_id)
        for name, expected in review_files.items():
            path = workspace/'artifacts'/name
            if (Path(name).name != name or path.is_symlink() or
                    not path.resolve().is_relative_to(workspace/'artifacts') or
                    not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
                raise WorkflowExecutionError('QA snapshot verification failed: changed/missing/unsafe file '+name,node_id=node_id)
        # The validated report is authoritative. Never route using model prose.
        # JSON encoding keeps quoted examples on one line; neutralize reserved
        # markers in diagnostic text before adding the sole canonical decision.
        from functions.edge_processor.ad_agency_routes import _clean
        from utils.execution_markers import EXEC_FAILURE_MARKERS
        payload = _clean(json.dumps(qa, ensure_ascii=False))
        for marker in EXEC_FAILURE_MARKERS:
            payload = payload.replace(marker, 'execution failure (quoted in QA report)')
        message.content = payload + '\nQA: ' + qa['verdict']
    if not message.text_content().strip():
        if node_id in ('Director_Brief','Strategy_QA'):
            raise WorkflowExecutionError('Missing final routing decision for '+node_id, node_id=node_id)
        message.content = 'Verified saved files:\n' + '\n'.join('artifacts/'+n for n in names)
    # Only validated artifacts may be referenced instead of pasted verbatim in
    # a downstream prompt. Hashes prevent eliding a file that has since changed.
    state.setdefault('ad_artifact_receipts', {})[node_id] = {
        name: hashlib.sha256((workspace/'artifacts'/name).read_bytes()).hexdigest() for name in names
    }


def ad_agency_bootstrap(data, context):
    """Install local result checks and enforce the request's explicit no-web constraint."""
    require_unsafe_code_execution('Advertising Plan_Gate/Build_Files')
    missing = [name for name in ('openpyxl', 'pptx') if find_spec(name) is None]
    if missing:
        raise WorkflowExecutionError('Missing local build dependencies: '+', '.join(missing))
    context['node_result_validator'] = _validate_result
    context['ad_context_policy'] = 'file_first_v1'
    # One extra provider attempt per failed turn, inside the configured total
    # retry budget. Never rerun the node or replay completed tools.
    context['ad_malformed_retry_limit'] = 1
    context['ad_csv_write_validation'] = True
    context['ad_qa_write_validation'] = True
    context['ad_publication_write_validation'] = True
    run_date=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date().isoformat()
    context['agent_request_constraints'] = (data or '')+'\nTRUSTED_RUNTIME_DATE (Asia/Ho_Chi_Minh): '+run_date+'. This is the run-start date, not proof of a web access. Record actual access evidence; never use a future campaign date as access_date.'
    context.pop('ad_plan_last_issues',None)
    normalized = ' '.join(unicodedata.normalize('NFC', data or '').casefold().split())
    no_web = any(term in normalized for term in (
        'không tìm web', 'không dùng web', 'không tìm kiếm web', 'không tìm kiếm trên web',
        'không truy cập web', 'no web', 'do not browse', 'without web',
    ))
    context['disabled_tool_names'] = ['web_search','read_webpage_content'] if no_web else []
    return data
