"""Human plan approval authorizes final derived outputs; code seals exact files."""
import json
from pathlib import Path
from utils.ad_publication import prepare_review,approve_from_plan,read,verify_sources,validate_content,sha
from utils.exceptions import WorkflowExecutionError


def ad_publication_release(data,context):
    from functions.edge_processor.ad_banners import ad_banner_result
    if ad_banner_result(data,context) is None:return None
    root=Path(context['python_workspace_root']);review=prepare_review(root)
    context['ad_publication_approval_sha256']=approve_from_plan(root,context.get('ad_publication_authorization'))
    return 'Final publication release '+review['release_id']+' sealed under the prior HUMAN: APPROVE plan authorization. No second approval required. Write handoff notes only; do not modify approved files. Images '+('created.' if review['images_enabled'] else 'disabled: no banner files produced.')


def ad_publication_build(data,context):
    seal=context.get('ad_publication_approval_sha256')
    if not isinstance(seal,str) or len(seal)!=64:raise WorkflowExecutionError('Missing trusted Human publication approval')
    text=str(data or '')
    if not text.startswith('```python\n'):raise WorkflowExecutionError('Invalid Build script envelope')
    # Inject the trusted approval digest after the literal fence. Agent tools
    # cannot mint the in-memory digest by writing a fake approval JSON file.
    repo=str(Path(__file__).resolve().parents[2])
    return text.replace('```python\n','```python\nimport os, sys\nsys.path.insert(0, '+repr(repo)+')\nos.environ["AD_PUBLICATION_APPROVAL_SHA256"] = '+json.dumps(seal)+'\nos.environ["AD_PUBLICATION_REQUIRED"] = "1"\n',1)


def ad_publication_start(data,context):
    from functions.edge_processor.ad_agency_routes import ad_checked_payload
    checked=ad_checked_payload(data,context)
    if checked is None or not str(checked).endswith('[[REVIEW_APPROVE]]'):return None
    man=verify_sources(Path(context['python_workspace_root']))
    from datetime import datetime,timezone
    context['ad_publication_plan_version']=man['plan_version']
    context.pop('ad_publication_approval_sha256',None)
    context['ad_publication_authorization']={'mode':'PLAN_AND_DERIVED_OUTPUTS','plan_version':man['plan_version'],
        'plan_files':dict(man['files']),'qa_sha256':sha(Path(context['python_workspace_root'])/'artifacts/qa_report.json'),
        'authorized_at':datetime.now(timezone.utc).isoformat()}

    return 'Plan approved: '+man['plan_version']+'. Prepare final public content from the reviewed files; no new facts or operational claims. HUMAN: APPROVE also authorizes final copy and asset production under this plan; do not request a second approval.'


def ad_publication_banner_script(data,context):
    from functions.edge_processor.ad_banners import ad_banner_script
    root=Path(context['python_workspace_root']);bundle=validate_content(root)
    if bundle['plan_version']!=context.get('ad_publication_plan_version'):raise WorkflowExecutionError('Missing checked plan approval for publication')
    return 'import os\nos.environ["AD_PUBLICATION_REQUIRED"] = "1"\n'+ad_banner_script('[[REVIEW_APPROVE]]',context)


def ad_publication_qa_to_banner(data,context):
    from utils.ad_publication import validate_publication_qa
    report=validate_publication_qa(context['python_workspace_root'])
    if report['verdict']!='PASS':return None
    return ad_publication_banner_script(data,context)


def ad_publication_qa_blocked(data,context):
    from utils.ad_publication import validate_publication_qa
    report=validate_publication_qa(context['python_workspace_root'])
    if report['verdict']=='PASS':return None
    return 'Public content QA blocked final delivery: '+json.dumps(report['findings'],ensure_ascii=False)


def ad_publication_qa_input(data,context):
    from utils.ad_publication import publication_qa_template
    root=Path(context['python_workspace_root']);template=publication_qa_template(root)
    return ('Audit artifacts/publication_content.json and its actual sources. Save only artifacts/publication_qa.json. '
            'Keep the exact keys checks/findings and all eight id values below. Never use criteria_results, criterion_id or issues. '
            'Fill reason and source_refs for every check. PASS only if all checks pass and findings is empty; otherwise BLOCKED with specific findings. '
            'The template is intentionally incomplete: do not save it unchanged. No extra Human approval.\n'
            +json.dumps(template,ensure_ascii=False,indent=2))


def ad_publication_resume_qa_input(data,context):
    if ad_publication_start(data,context) is None:return None
    return ad_publication_qa_input(data,context)
