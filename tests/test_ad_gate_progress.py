"""Regression for https false positives, early sources and no-progress loops."""
import csv
import io
import json
from datetime import date,timedelta
import pytest
from utils.ad_delivery_policy import delivery_issues,source_issues_csv
from functions.edge_processor.ad_agency_routes import ad_plan_classify,ad_plan_fallback,ad_checked_payload
from functions.function_calling.file import save_file
from utils.ad_csv import CSVWriteValidationError
from test_ad_csv_write_repair import state
from test_ad_agency_audit import fixture_files,run_gate,FILES


@pytest.mark.parametrize('text',[
    'Nguồn https://www.logitech.com/vi-vn/shop/p/m240-silent-bluetooth-mouse và https://support.logi.com/hc/en-ca/articles/example .',
    '[Hãng](https://www.logitech.com/vi-vn/shop/p/m240-silent-bluetooth-mouse)',
    'http://example.com/C:/public/path',
])
def test_real_web_urls_are_not_local_windows_paths(tmp_path,text):
    (tmp_path/'advertising_strategy_draft.md').write_text('# Kế hoạch\n'+text,encoding='utf-8')
    assert not any(f['code']=='INTERNAL_REFERENCE' for f in delivery_issues(tmp_path))


@pytest.mark.parametrize('path',[r'C:\Users\Admin\file.md','D:/Project/chatdev/file.md','artifacts/media_plan.csv','code_workspace/file.md','advertising_strategy_draft.md','(https://example.com)(D:/private/file.md)'])
def test_actual_internal_paths_are_still_blocked_with_location(tmp_path,path):
    (tmp_path/'advertising_strategy_draft.md').write_text('# Kế hoạch\n'+path,encoding='utf-8')
    findings=[f for f in delivery_issues(tmp_path) if f['code']=='INTERNAL_REFERENCE']
    assert findings and 'line 2' in findings[0]['message']


def source_csv(url,accessed):
    output=io.StringIO(newline='');w=csv.writer(output);w.writerow(['id','claim','source_url','access_date','scope','evidence_type'])
    w.writerow(['SRC-005','Observed source',url,accessed,'market_research.md','external']);return output.getvalue()


@pytest.mark.parametrize('fault',['scheme','future','bad_date'])
def test_sources_rejected_at_write_without_changing_existing_file(tmp_path,fault):
    ctx=state(tmp_path)
    save_file('artifacts/sources.csv',source_csv('https://example.com','2026-01-01'),_context=ctx)
    path=tmp_path/'artifacts/sources.csv';before=path.read_bytes()
    text=source_csv('example.com' if fault=='scheme' else 'https://example.com','2999-01-01' if fault=='future' else 'not-a-date' if fault=='bad_date' else '2026-01-01')
    with pytest.raises(CSVWriteValidationError,match='EXTERNAL_SOURCE|SOURCE_DATE'):
        save_file('artifacts/sources.csv',text,_context=ctx)
    assert path.read_bytes()==before


def test_source_date_is_compared_to_explicit_local_day_without_fabrication():
    text=source_csv('https://example.com','2026-11-20').encode()
    assert any(f['code']=='SOURCE_DATE_FUTURE' for f in source_issues_csv(text,date(2026,11,15)))
    assert not source_issues_csv(text,date(2026,11,20))


@pytest.mark.parametrize('filename',FILES)
def test_gate_sends_sources_to_error_not_assembler_rework(tmp_path,monkeypatch,filename):
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path)
    (tmp_path/'artifacts/sources.csv').write_text(source_csv('thegioididong.com/example','2999-01-01'),encoding='utf-8')
    out=run_gate(tmp_path,filename)
    assert out.rstrip().endswith('[[PLAN_ERROR]]') and 'Evidence_Digest' in out and 'SOURCE_DATE_FUTURE' in out
    assert not (tmp_path/'review/review_manifest.json').exists()


@pytest.mark.parametrize('filename',FILES)
def test_gate_allows_actual_session_url_pattern(tmp_path,monkeypatch,filename):
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path)
    (tmp_path/'artifacts/advertising_strategy_draft.md').write_text('# Kế hoạch\nNguồn https://www.logitech.com/vi-vn/shop/p/m240-silent-bluetooth-mouse và https://support.logi.com/hc/en-ca/articles/11654238591767-Specification-M240 .',encoding='utf-8')
    assert run_gate(tmp_path,filename).rstrip().endswith('[[PLAN_OK]]')


def envelope(status,issues=()):
    return json.dumps({'status':status,'errors':[],'issues':list(issues),'info':{}})+'\nPLAN: '+status+'\n[[PLAN_'+status+']]'


def test_same_gate_issues_stop_after_one_unsuccessful_repair():
    ctx={};message=envelope('ISSUES',['media_plan.csv: budget mismatch'])
    assert ad_plan_classify(message,ctx)==message
    blocked=ad_plan_classify(message,ctx)
    assert blocked.endswith('[[PLAN_ERROR]]') and 'NO_PROGRESS' in blocked
    assert ad_plan_fallback(blocked,{}) is not None
    assert ad_checked_payload(blocked,{}) is None


def test_source_issues_never_enter_assembler_loop_even_for_legacy_gate():
    message=envelope('ISSUES',['sources.csv [EXTERNAL_SOURCE]: missing scheme'])
    assert ad_plan_classify(message,{}).endswith('[[PLAN_ERROR]]')


def test_different_issues_or_a_successful_gate_reset_progress():
    ctx={};first=envelope('ISSUES',['media_plan.csv: budget mismatch']);second=envelope('ISSUES',['execution_calendar.csv: invalid week'])
    assert ad_plan_classify(first,ctx)==first and ad_plan_classify(second,ctx)==second
    assert ad_plan_classify(envelope('OK'),ctx).endswith('[[PLAN_OK]]')
    assert ad_plan_classify(second,ctx)==second


@pytest.mark.parametrize('data',['No JSON','{}\nPLAN: ISSUES\n[[PLAN_ISSUES]]'])
def test_invalid_gate_payload_fails_closed(data):
    assert ad_plan_classify(data,{}).endswith('[[PLAN_ERROR]]')


def test_real_graph_stops_identical_gate_errors_without_third_assembler(tmp_path,monkeypatch):
    import yaml
    from runtime import sdk
    from entity.messages import Message,MessageRole
    from runtime.node.executor.agent_executor import AgentNodeExecutor
    from runtime.node.executor.python_executor import PythonNodeExecutor
    from test_ad_agency_audit import ROOT
    from test_ad_agency_routes import VARIABLES
    doc=yaml.safe_load((ROOT/'yaml_instance/ad_agency_v2_auto.yaml').read_text(encoding='utf-8'))
    # Isolate assembly progress using literals for completed upstream agents.
    for node in doc['graph']['nodes']:
        if node['type']=='agent' and node['id']!='Plan_Assembler':
            content='BRIEF: READY' if node['id']=='Director_Brief' else 'cached source'
            node['type']='literal';node['config']={'role':'assistant','content':content}
        if node['id']=='Revision_Limit':node['config']['max_iterations']=4  # prove no-progress, not the counter, stops it
    path=tmp_path/'workflow.yaml';path.write_text(yaml.safe_dump(doc,allow_unicode=True),encoding='utf-8')
    calls=[]
    def agent(executor,node,messages):
        calls.append(node.id);return [Message(role=MessageRole.ASSISTANT,content='assembly completed')]
    def python(executor,node,messages):
        assert node.id=='Plan_Gate'
        return [Message(role=MessageRole.ASSISTANT,content=envelope('ISSUES',['media_plan.csv: unchanged budget mismatch']))]
    monkeypatch.setenv('MAC_ALLOW_UNSAFE_CODE_EXECUTION','1');monkeypatch.setattr(AgentNodeExecutor,'execute',agent);monkeypatch.setattr(PythonNodeExecutor,'execute',python)
    monkeypatch.setattr(sdk,'OUTPUT_ROOT',tmp_path/'runs')
    result=sdk.run_workflow(path,task_prompt='offline progress check',variables=VARIABLES,session_name='session_progress_test')
    assert calls==['Plan_Assembler','Plan_Assembler']
    assert result is not None
