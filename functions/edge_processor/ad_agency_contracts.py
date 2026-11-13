"""Advertising workflow contracts. Runs locally; never calls a model or tool."""
import csv
import json
from pathlib import Path
import unicodedata
import datetime
import re
from decimal import Decimal
from importlib.util import find_spec

from utils.exceptions import WorkflowExecutionError
from utils.code_execution import require_unsafe_code_execution

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
_COLUMNS = {
    'sources.csv': ('id','claim','source_url','access_date','scope','evidence_type'),
    'media_plan.csv': ('channel','role','objective','segment_id','offer_id','budget_pct','budget_amount','currency','start','end','landing_page','assumption'),
    'budget_scenarios.csv': ('scenario','channel','budget_amount','metric','metric_value','formula','assumption'),
    'creative_matrix.csv': ('concept_id','segment_id','insight','hook','benefit','proof','cta','format','asset_requirement','test_variant'),
    'experiment_plan.csv': ('test_id','hypothesis','variant_a','variant_b','primary_metric','min_sample','duration_days','decision_rule'),
    'execution_calendar.csv': ('week','start','end','channel','activity','owner','deliverable'),
}


def _validate_result(node_id, message, state):
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
    for name in names:
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
        from functions.edge_processor.ad_agency_routes import ad_qa_route
        qa = json.loads((workspace/'artifacts/qa_report.json').read_text(encoding='utf-8-sig'))
        manifest = json.loads((workspace/'review/review_manifest.json').read_text(encoding='utf-8-sig'))
        routed = ad_qa_route(message.text_content(), {})
        verdict = qa.get('verdict') if isinstance(qa,dict) else None
        if verdict not in ('PASS','REVISE') or not routed.endswith('[[QA_'+str(verdict)+']]') or qa.get('plan_version')!=manifest.get('plan_version') or qa.get('plan_gate_status')!='OK' or not isinstance(qa.get('issues'),list):
            raise WorkflowExecutionError('QA report/decision/version mismatch; refusing stale or inconsistent approval',node_id=node_id)
    if not message.text_content().strip():
        if node_id in ('Director_Brief','Strategy_QA'):
            raise WorkflowExecutionError('Missing final routing decision for '+node_id, node_id=node_id)
        message.content = 'Verified saved files:\n' + '\n'.join('artifacts/'+n for n in names)


def ad_agency_bootstrap(data, context):
    """Install local result checks and enforce the request's explicit no-web constraint."""
    require_unsafe_code_execution('Advertising Plan_Gate/Build_Files')
    missing = [name for name in ('openpyxl', 'pptx') if find_spec(name) is None]
    if missing:
        raise WorkflowExecutionError('Missing local build dependencies: '+', '.join(missing))
    context['node_result_validator'] = _validate_result
    context['agent_request_constraints'] = data or ''
    normalized = ' '.join(unicodedata.normalize('NFC', data or '').casefold().split())
    no_web = any(term in normalized for term in (
        'không tìm web', 'không dùng web', 'không tìm kiếm web', 'không tìm kiếm trên web',
        'không truy cập web', 'no web', 'do not browse', 'without web',
    ))
    context['disabled_tool_names'] = ['web_search','read_webpage_content'] if no_web else []
    return data
