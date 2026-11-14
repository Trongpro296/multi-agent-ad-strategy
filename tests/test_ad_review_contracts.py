"""Measurement v2 and planning-vs-launch readiness, with real local validators."""
import copy
import json

import pytest

from entity.messages import Message, MessageRole
from functions.edge_processor.ad_agency_contracts import _validate_result
from functions.edge_processor.ad_agency_routes import ad_qa_route, ad_qa_fallback
from test_ad_agency_audit import FILES, definitions, fixture_files, run_gate, write_csv, qa_fixture
from utils.ad_review_contracts import experiment_issues, qa_report_issues
from utils.exceptions import WorkflowExecutionError


REVIEW_FILES={'campaign_brief.json','sources.csv','strategy_ids.json','media_plan.csv',
              'experiment_plan.csv','measurement_plan.md','advertising_strategy_draft.md','creative_brief.md'}


@pytest.mark.parametrize('case', ['legacy','stale','missing_summary','missing_criteria','duplicate_criterion',
    'unreviewed_pass','invalid_ref','unhashable_ref','pending_ready','missing_conditions','duplicate_condition',
    'missing_verification','missing_assumptions','bad_assumption','unresolved_issue','blocked_condition_ready'])
def test_qa_rejects_incomplete_or_contradictory_pass(case):
    qa=qa_fixture('version1')
    if case=='legacy':qa={'verdict':'PASS','plan_version':'version1','issues':[],'plan_gate_status':'OK'}
    elif case=='stale':qa['plan_version']='old'
    elif case=='missing_summary':qa['review_summary']=''
    elif case=='missing_criteria':qa['criteria_results'].pop()
    elif case=='duplicate_criterion':qa['criteria_results'][0]=copy.deepcopy(qa['criteria_results'][1])
    elif case=='unreviewed_pass':qa['criteria_results'][0]['status']='NOT_REVIEWED'
    elif case=='invalid_ref':qa['criteria_results'][0]['evidence_refs'][0]['file']='internal/assembly_notes.md'
    elif case=='unhashable_ref':qa['criteria_results'][0]['evidence_refs'][0]['file']=[]
    elif case=='pending_ready':qa['implementation_readiness']['status']='READY'
    elif case=='missing_conditions':qa['prelaunch_conditions']=[]
    elif case=='duplicate_condition':qa['prelaunch_conditions'][0]=copy.deepcopy(qa['prelaunch_conditions'][1])
    elif case=='missing_verification':qa['prelaunch_conditions'][0]['verification']=''
    elif case=='missing_assumptions':qa.pop('open_assumptions')
    elif case=='bad_assumption':qa['open_assumptions']=[{'description':'Unknown demand'}]
    elif case=='unresolved_issue':qa['issues']=[{'id':'QA1','description':'Unresolved'}]
    elif case=='blocked_condition_ready':
        qa['prelaunch_conditions'][0]['status']='BLOCKED';qa['implementation_readiness']['status']='READY'
    assert qa_report_issues(qa,'version1',REVIEW_FILES)


@pytest.mark.parametrize('filename',FILES)
@pytest.mark.parametrize('readiness',['CONDITIONAL','READY','NOT_READY'])
def test_planning_pass_packages_readiness_without_claiming_launch(tmp_path,monkeypatch,filename,readiness):
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path)
    assert run_gate(tmp_path,filename).rstrip().endswith('[[PLAN_OK]]')
    review=json.loads((tmp_path/'review/review_manifest.json').read_text())
    qa=qa_fixture(review['plan_version'])
    if readiness=='READY':
        for condition in qa['prelaunch_conditions']:
            condition.update(status='VERIFIED',verification='Offline fixture represents a supplied verification record, not a real deployment.')
    elif readiness=='NOT_READY':qa['prelaunch_conditions'][0]['status']='BLOCKED'
    qa['implementation_readiness']={'status':readiness,'reason':'Fixture condition status; packaging is not ad execution.'}
    (tmp_path/'artifacts/qa_report.json').write_text(json.dumps(qa))
    _validate_result('Strategy_QA',Message(role=MessageRole.ASSISTANT,content='QA: PASS'),{'python_workspace_root':tmp_path})
    script=definitions(filename,'Build_Script');man,hashes,problems=script['verify']()
    assert not problems
    listing=script['build'](man,hashes)
    assert len(listing)==26
    manifest=json.loads((tmp_path/'output/manifest.json').read_text())
    assert manifest['qa_verdict']=='PASS' and manifest['qa_schema_version']=='2.0'
    assert manifest['implementation_readiness']['status']==readiness
    assert manifest['prelaunch_conditions']==qa['prelaunch_conditions']


def test_schema_invalid_report_stops_before_human_and_build(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path);run_gate(tmp_path)
    review=json.loads((tmp_path/'review/review_manifest.json').read_text())
    legacy={'verdict':'PASS','plan_version':review['plan_version'],'plan_gate_status':'OK','issues':[]}
    (tmp_path/'artifacts/qa_report.json').write_text(json.dumps(legacy))
    with pytest.raises(WorkflowExecutionError,match='QA v2 contract'):
        _validate_result('Strategy_QA',Message(role=MessageRole.ASSISTANT,content='QA: PASS'),{'python_workspace_root':tmp_path})
    assert definitions(FILES[0],'Build_Script')['verify']()[2]
    assert not (tmp_path/'output').exists()


@pytest.mark.parametrize('verdict',['REVISE','BLOCKED'])
def test_explicit_nonpassing_review_routes_consistently(tmp_path,monkeypatch,verdict):
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path);run_gate(tmp_path)
    review=json.loads((tmp_path/'review/review_manifest.json').read_text())
    qa=qa_fixture(review['plan_version']);qa['verdict']=verdict
    qa['criteria_results'][0]['status']='FAIL'
    qa['issues']=[{'id':'QA1','severity':'high','area':'brief','description':'Fixture mismatch','fix':'Resolve the source issue',
                   'owner':'Plan_Assembler','evidence_refs':[{'file':'campaign_brief.json','location':'fixture goal'}]}]
    qa['implementation_readiness']={'status':'NOT_READY','reason':'Planning issue must be resolved.'}
    (tmp_path/'artifacts/qa_report.json').write_text(json.dumps(qa))
    message=Message(role=MessageRole.ASSISTANT,content='QA: '+verdict)
    _validate_result('Strategy_QA',message,{'python_workspace_root':tmp_path})
    routed=ad_qa_route(message.text_content(),{})
    if verdict=='BLOCKED':
        assert routed.endswith('[[QA_INVALID]]') and ad_qa_fallback(routed,{}) is not None
    else:assert routed.endswith('[[QA_REVISE]]') and ad_qa_fallback(routed,{}) is None


@pytest.mark.parametrize('filename',FILES)
@pytest.mark.parametrize('case',['type','unit','basis','source','decision','owner','missing_rule','dates','duration','outside','duplicate','same_variant','legacy_header'])
def test_gate_rejects_unactionable_or_inconsistent_experiment(tmp_path,monkeypatch,filename,case):
    monkeypatch.chdir(tmp_path);rows=fixture_files(tmp_path)['experiment_plan.csv'];row=rows[0]
    if case=='type':row['test_type']='A/B'
    elif case=='unit':row['sample_unit']=''
    elif case=='basis':row['sample_basis']=''
    elif case=='source':row['data_source']=''
    elif case=='decision':row['decision_not_supported']=''
    elif case=='owner':row['decision_owner']=''
    elif case=='missing_rule':row['missing_data_rule']=''
    elif case=='dates':row['start']='20260101'
    elif case=='duration':row['duration_days']=6
    elif case=='outside':row.update(start='2026-02-01',end='2026-02-07')
    elif case=='duplicate':rows.append(dict(row))
    elif case=='same_variant':row['variant_b']=row['variant_a']
    write_csv(tmp_path,'experiment_plan.csv',rows)
    if case=='legacy_header':
        (tmp_path/'artifacts/experiment_plan.csv').write_text('test_id,hypothesis,variant_a,variant_b,primary_metric,min_sample,duration_days,decision_rule\nT1,test,A,B,CTR,30,7,observe\n')
    result=run_gate(tmp_path,filename)
    assert result.rstrip().endswith('[[PLAN_ISSUES]]') and 'experiment_plan.csv' in result
    assert not (tmp_path/'review/review_manifest.json').exists()


def test_copied_qa_is_rechecked_against_manifest_before_packaging(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path);run_gate(tmp_path)
    man=json.loads((tmp_path/'review/review_manifest.json').read_text());qa=qa_fixture(man['plan_version'])
    file=tmp_path/'artifacts/qa_report.json';file.write_text(json.dumps(qa))
    script=definitions(FILES[0],'Build_Script');approved,hashes,problems=script['verify']();assert not problems
    qa['implementation_readiness']['status']='READY';file.write_text(json.dumps(qa))
    with pytest.raises(ValueError,match='Copied QA report'):
        script['build'](approved,hashes)
    assert not (tmp_path/'output').exists()


@pytest.mark.parametrize('chat', ['', 'QA: REVISE', 'QA: PASS\nExtra explanation', '[[QA_PASS]]\nQA: PASS', 'Example: QA: PASS'])
def test_qa_routes_from_valid_report_independent_of_chat(tmp_path,monkeypatch,chat):
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path);run_gate(tmp_path)
    review=json.loads((tmp_path/'review/review_manifest.json').read_text())
    qa=qa_fixture(review['plan_version'])
    (tmp_path/'artifacts/qa_report.json').write_text(json.dumps(qa))
    message=Message(role=MessageRole.ASSISTANT,content=chat)
    _validate_result('Strategy_QA',message,{'python_workspace_root':tmp_path})
    assert message.text_content().endswith('\nQA: PASS')
    assert ad_qa_route(message.text_content(),{}).endswith('[[QA_PASS]]')


@pytest.mark.parametrize('change',['modify','delete','empty_manifest'])
def test_qa_rejects_changed_snapshot_before_routing(tmp_path,monkeypatch,change):
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path);run_gate(tmp_path)
    path=tmp_path/'review/review_manifest.json';review=json.loads(path.read_text())
    (tmp_path/'artifacts/qa_report.json').write_text(json.dumps(qa_fixture(review['plan_version'])))
    if change=='modify':(tmp_path/'artifacts/media_plan.csv').write_text('changed')
    elif change=='delete':(tmp_path/'artifacts/media_plan.csv').unlink()
    else:
        review['files']={};path.write_text(json.dumps(review))
    with pytest.raises(WorkflowExecutionError,match='QA snapshot verification|QA v2 contract'):
        _validate_result('Strategy_QA',Message(role=MessageRole.ASSISTANT,content='QA: PASS'),{'python_workspace_root':tmp_path})


@pytest.mark.parametrize('fault',['severity','manifest_ref','missing_owner','bad_json'])
def test_qa_prewrite_rejection_preserves_old_report_and_requires_repair(tmp_path,monkeypatch,fault):
    from functions.function_calling.file import save_file
    from utils.attachments import AttachmentStore
    from utils.ad_review_contracts import QAWriteValidationError
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path);run_gate(tmp_path)
    review=json.loads((tmp_path/'review/review_manifest.json').read_text())
    qa=qa_fixture(review['plan_version'])
    ctx={'python_workspace_root':tmp_path,'graph_directory':tmp_path.parent,
         'attachment_store':AttachmentStore(tmp_path/'attachments'),'ad_qa_write_validation':True}
    save_file('artifacts/qa_report.json',json.dumps(qa),_context=ctx)
    target=tmp_path/'artifacts/qa_report.json';before=target.read_bytes()
    bad=copy.deepcopy(qa)
    if fault=='manifest_ref':bad['criteria_results'][0]['evidence_refs'][0]['file']='review/review_manifest.json'
    else:
        bad['verdict']='REVISE';bad['criteria_results'][0]['status']='FAIL'
        bad['implementation_readiness']={'status':'NOT_READY','reason':'Correction required'}
        bad['issues']=[{'id':'Q1','severity':'CRITICAL' if fault=='severity' else 'high','area':'delivery',
                       'description':'Mismatch','fix':'Correct the relevant source','owner':'Plan_Assembler',
                       'evidence_refs':[{'file':'media_plan.csv','location':'row 2'}]}]
        if fault=='missing_owner':bad['issues'][0].pop('owner')
    with pytest.raises(QAWriteValidationError):
        save_file('artifacts/qa_report.json','{' if fault=='bad_json' else json.dumps(bad),_context=ctx)
    assert target.read_bytes()==before
    with pytest.raises(WorkflowExecutionError,match='Unresolved QA report write rejection'):
        _validate_result('Strategy_QA',Message(role=MessageRole.ASSISTANT,content='done'),ctx)
    save_file('artifacts/qa_report.json',json.dumps(qa),_context=ctx)
    assert not ctx['ad_qa_write_errors']
    _validate_result('Strategy_QA',Message(role=MessageRole.ASSISTANT,content='done'),ctx)
