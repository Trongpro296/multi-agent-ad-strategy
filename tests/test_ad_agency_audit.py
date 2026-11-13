"""Offline regression for actual campaign failures. No model or web calls."""
import contextlib
import csv
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock

import httpx
import openai
import pytest
import yaml

from runtime import sdk  # Initialize runtime before importing config/registries.
from entity.configs import Node
from entity.configs.node.agent import AgentConfig
from entity.configs.node.python_runner import PythonRunnerConfig
from entity.messages import Message, MessageRole, ToolCallPayload
from entity.tool_spec import ToolSpec
from functions.edge_processor.ad_agency_contracts import _COLUMNS, _OUTPUTS, _validate_result, ad_agency_bootstrap
from runtime.node.agent import ModelResponse, ProviderRegistry
from runtime.node.agent.providers.openai_provider import OpenAIProvider
from runtime.node.agent.providers.gemini_provider import GeminiProvider
from runtime.node.agent.providers.response import ProviderResponseError, validate_tool_calls
from runtime.node.executor.agent_executor import AgentNodeExecutor
from runtime.node.executor.base import ExecutionContext
from runtime.node.executor.python_executor import PythonNodeExecutor
from utils.exceptions import WorkflowExecutionError, SecurityError

ROOT = Path(__file__).resolve().parents[1]
FILES = ('ad_agency_v2.yaml', 'ad_agency_v2_auto.yaml')


def script(filename, node_id):
    nodes = yaml.safe_load((ROOT/'yaml_instance'/filename).read_text(encoding='utf-8'))['graph']['nodes']
    code = next(n['config']['content'] for n in nodes if n['id']==node_id)
    return code.split('\n',1)[1].rsplit('```',1)[0]


def definitions(filename, node_id):
    space = {}
    exec(compile(script(filename,node_id).rsplit('\ntry:\n',1)[0],node_id,'exec'),space)
    return space


def write_csv(root, name, rows):
    with (root/'artifacts'/name).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=_COLUMNS[name]); writer.writeheader(); writer.writerows(rows)


def fixture_files(root):
    (root/'artifacts').mkdir(exist_ok=True)
    for name in {name for names in _OUTPUTS.values() for name in names}:
        (root/'artifacts'/name).write_text('# Kiểm thử tiếng Việt\n\n## Kế hoạch\nNgân sách và đo lường.\n',encoding='utf-8')
    documents = {
        'campaign_brief.json': {'budget':{'ad_spend':100,'currency':'VND'},'start_date':'2026-01-01','end_date':'2026-01-31'},
        'strategy_ids.json': {'segments':[{'segment_id':'S1'}],'offers':[{'offer_id':'O1'}]},
        'audience_segments.json': {'segments':[{'segment_id':'S1'}]},
    }
    for name,obj in documents.items():
        (root/'artifacts'/name).write_text(json.dumps(obj,ensure_ascii=False),encoding='utf-8-sig')
    rows = {
        'media_plan.csv':[dict(channel='Facebook',role='acquisition',objective='leads',segment_id='S1',offer_id='O1',budget_pct=100,budget_amount=100,currency='VND',start='2026-01-01',end='2026-01-31',landing_page='N/A',assumption='hypothesis')],
        'budget_scenarios.csv':[dict(scenario='thận trọng',channel='Facebook',budget_amount=100,metric='leads',metric_value=5,formula='100/20',assumption='hypothesis'),dict(scenario='thận trọng',channel='Facebook',budget_amount=100,metric='CPA',metric_value=20,formula='100/5',assumption='hypothesis')],
        'creative_matrix.csv':[dict(concept_id='C1',segment_id='S1',insight='test',hook='hook',benefit='benefit',proof='hypothesis',cta='contact',format='image',asset_requirement='image',test_variant='A')],
        'experiment_plan.csv':[dict(test_id='T1',hypothesis='test',variant_a='A',variant_b='B',primary_metric='CTR',min_sample=30,duration_days=7,decision_rule='hypothesis')],
        'execution_calendar.csv':[dict(week=1,start='2026-01-01',end='2026-01-07',channel='Facebook',activity='launch',owner='team',deliverable='ads')],
        'sources.csv':[dict(id='H1',claim='Giả thuyết để kiểm thử',source_url='',access_date='',scope='test',evidence_type='hypothesis')],
    }
    for name,value in rows.items(): write_csv(root,name,value)
    return rows


def run_gate(root, filename=FILES[0]):
    space=definitions(filename,'Plan_Gate_Script'); output=io.StringIO()
    with contextlib.redirect_stdout(output): space['main']()
    return output.getvalue()


@pytest.mark.parametrize('filename', FILES)
def test_gate_utf8_repeated_metrics_and_build_real_files(tmp_path, monkeypatch, filename):
    monkeypatch.chdir(tmp_path); fixture_files(tmp_path)
    assert run_gate(tmp_path,filename).rstrip().endswith('[[PLAN_OK]]')
    man=json.loads((tmp_path/'review/review_manifest.json').read_text())
    (tmp_path/'artifacts/qa_report.json').write_text(json.dumps({'verdict':'PASS','plan_version':man['plan_version']}),encoding='utf-8')
    space=definitions(filename,'Build_Script'); approved,hashes,problems=space['verify']()
    assert not problems
    names=space['build'](approved,hashes)
    assert len(names)==23 and {'Campaign_Plan.xlsx','Campaign_Presentation.pptx','manifest.json'} <= set(names)
    from openpyxl import load_workbook
    from pptx import Presentation
    wb=load_workbook(tmp_path/'output/Campaign_Plan.xlsx')
    assert wb['Budget_Scenarios']['A2'].value=='thận trọng'
    assert wb['Experiments']['F2'].value==30
    assert wb['Experiments']['F2'].data_type=='n'
    assert len(Presentation(tmp_path/'output/Campaign_Presentation.pptx').slides)==2
    for n,digest in hashes.items():
        target='advertising_strategy.md' if n=='advertising_strategy_draft.md' else n
        assert space['sha'](tmp_path/'output'/target)==digest


@pytest.mark.parametrize('case', ['negative','nan','comma','percent','empty_table','missing_id','bad_date','over_cap','zero_cap','duplicate_metric','conflicting_budget','bad_sample','missing_file','duplicate_columns','short_row'])
def test_gate_rejects_invalid_data(tmp_path,monkeypatch,case):
    monkeypatch.chdir(tmp_path); rows=fixture_files(tmp_path)
    if case in ('negative','nan','comma','percent','over_cap'):
        rows['media_plan.csv'][0]['budget_amount']={'negative':'-1','nan':'NaN','comma':'0,5','percent':'12,5%','over_cap':'100.01'}[case]
    if case=='zero_cap':
        p=tmp_path/'artifacts/campaign_brief.json';b=json.loads(p.read_text(encoding='utf-8-sig'));b['budget']['ad_spend']=0;p.write_text(json.dumps(b))
    if case=='empty_table': rows['media_plan.csv']=[]
    if case=='missing_id': rows['media_plan.csv'][0]['segment_id']=''
    if case=='bad_date': rows['media_plan.csv'][0]['start']='20260101'
    if case=='duplicate_metric': rows['budget_scenarios.csv'].append(rows['budget_scenarios.csv'][0].copy())
    if case=='conflicting_budget': rows['budget_scenarios.csv'][1]['budget_amount']=99
    if case=='bad_sample': rows['experiment_plan.csv'][0]['min_sample']='NaN'
    for name,value in rows.items(): write_csv(tmp_path,name,value)
    if case=='missing_file': (tmp_path/'artifacts/evidence_digest.md').unlink()
    if case=='duplicate_columns': (tmp_path/'artifacts/media_plan.csv').write_text('channel,channel\nFB,FB\n')
    if case=='short_row':
        with (tmp_path/'artifacts/media_plan.csv').open('a',encoding='utf-8') as f:f.write('FB\n')
    assert not run_gate(tmp_path).rstrip().endswith('[[PLAN_OK]]')
    assert not (tmp_path/'review/review_manifest.json').exists()


@pytest.mark.parametrize('target',['source','snapshot','qa_version','qa_fail','missing_note'])
def test_build_blocks_changes_after_review(tmp_path,monkeypatch,target):
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path);run_gate(tmp_path)
    man=json.loads((tmp_path/'review/review_manifest.json').read_text());qa={'verdict':'PASS','plan_version':man['plan_version']}
    if target=='qa_version': qa['plan_version']='stale'
    if target=='qa_fail': qa['verdict']='REVISE'
    (tmp_path/'artifacts/qa_report.json').write_text(json.dumps(qa))
    if target=='source': (tmp_path/'artifacts/evidence_digest.md').write_text('changed')
    if target=='snapshot': (tmp_path/'review'/man['plan_version']/'evidence_digest.md').write_text('changed')
    if target=='missing_note': (tmp_path/'artifacts/handoff_notes.md').unlink()
    assert definitions(FILES[0],'Build_Script')['verify']()[2]
    assert not (tmp_path/'output').exists()


def test_artifact_contract_and_file_only_receipt(tmp_path):
    state={'python_workspace_root':tmp_path};fixture_files(tmp_path)
    message=Message(role=MessageRole.ASSISTANT,content='')
    _validate_result('Evidence_Digest',message,state)
    assert 'sources.csv' in message.text_content()
    (tmp_path/'artifacts/sources.csv').unlink()
    with pytest.raises(WorkflowExecutionError,match='sources.csv'): _validate_result('Evidence_Digest',message,state)
    with pytest.raises(WorkflowExecutionError,match='routing decision'):
        _validate_result('Director_Brief',Message(role=MessageRole.ASSISTANT,content=''),state)
    (tmp_path/'artifacts/campaign_brief.json').unlink()
    _validate_result('Director_Brief',Message(role=MessageRole.ASSISTANT,content='Questions\nBRIEF: NEED_INFO'),state)


def test_bootstrap_checks_execution_permission_before_model(monkeypatch):
    monkeypatch.setenv('MAC_ALLOW_UNSAFE_CODE_EXECUTION','0')
    state={}
    with pytest.raises(SecurityError):ad_agency_bootstrap('test',state)
    assert not state


def test_bootstrap_checks_build_dependencies_before_model(monkeypatch):
    monkeypatch.setenv('MAC_ALLOW_UNSAFE_CODE_EXECUTION','1')
    monkeypatch.setattr('functions.edge_processor.ad_agency_contracts.find_spec',lambda _:None)
    with pytest.raises(WorkflowExecutionError,match='dependencies'):ad_agency_bootstrap('test',{})


@pytest.mark.parametrize('case',['ok','stale','wrong_verdict','missing_issues','bad_gate'])
def test_qa_contract_before_human_or_packager(tmp_path,monkeypatch,case):
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path);run_gate(tmp_path)
    man=json.loads((tmp_path/'review/review_manifest.json').read_text())
    qa={'plan_version':man['plan_version'],'verdict':'PASS','plan_gate_status':'OK','issues':[]}
    if case=='stale':qa['plan_version']='old'
    if case=='wrong_verdict':qa['verdict']='REVISE'
    if case=='missing_issues':qa.pop('issues')
    if case=='bad_gate':qa['plan_gate_status']='ISSUES'
    (tmp_path/'artifacts/qa_report.json').write_text(json.dumps(qa))
    msg=Message(role=MessageRole.ASSISTANT,content='QA: PASS')
    if case=='ok':_validate_result('Strategy_QA',msg,{'python_workspace_root':tmp_path})
    else:
        with pytest.raises(WorkflowExecutionError,match='mismatch'):_validate_result('Strategy_QA',msg,{'python_workspace_root':tmp_path})


@pytest.mark.parametrize('case',['no_budget','comma_budget','bad_dates'])
def test_incomplete_brief_does_not_start_research(tmp_path,case):
    fixture_files(tmp_path);p=tmp_path/'artifacts/campaign_brief.json';brief=json.loads(p.read_text(encoding='utf-8-sig'))
    if case=='no_budget':brief.pop('budget')
    if case=='comma_budget':brief['budget']['ad_spend']='0,5'
    if case=='bad_dates':brief['end_date']='2026-02-30'
    p.write_text(json.dumps(brief))
    with pytest.raises(WorkflowExecutionError,match='Brief READY'):
        _validate_result('Director_Brief',Message(role=MessageRole.ASSISTANT,content='BRIEF: READY'),{'python_workspace_root':tmp_path})


def provider(protocol='chat'):
    return OpenAIProvider(AgentConfig(path='test.provider',base_url=None,name='offline',provider='openai',api_key='offline',params={'protocol':protocol}))


@pytest.mark.parametrize('reason',['malformed_function_call','length','content_filter',None])
def test_provider_does_not_silently_accept_failed_turn(reason):
    with pytest.raises(ProviderResponseError):
        provider()._deserialize_chat_response(NS(choices=[NS(finish_reason=reason,message=NS(content='',tool_calls=[]))]))


def test_provider_empty_wrong_shape_and_internal_parameters():
    p=provider()
    with pytest.raises(ProviderResponseError,match='missing_choices'):p._deserialize_chat_response(NS(choices=[]))
    with pytest.raises(ProviderResponseError,match='empty_response'):p._deserialize_chat_response(NS(choices=[NS(finish_reason='stop',message=NS(content='',tool_calls=[]))]))
    with pytest.raises(ProviderResponseError,match='response_format_mismatch'):p._deserialize_response(NS(object='chat.completion'))
    with pytest.raises(ProviderResponseError,match='incomplete'):p._deserialize_response(NS(object='response',status='incomplete'))
    for fn,first in ((p._build_chat_payload,[]),(p._build_request_payload,[])):
        payload=fn(first,None,{'protocol':'chat','tool_loop_limit':4,'temperature':0.1})
        assert 'protocol' not in payload and 'tool_loop_limit' not in payload


@pytest.mark.parametrize('arguments',['not json','[]','null'])
def test_invalid_tool_batch_rejected_before_execution(arguments):
    with pytest.raises(ProviderResponseError):
        validate_tool_calls(Message(role=MessageRole.ASSISTANT,content='',tool_calls=[ToolCallPayload(id='one',function_name='save_file',arguments=arguments)]))


def test_provider_only_falls_back_for_unsupported_endpoint():
    client=Mock();p=provider('responses')
    client.responses.create.return_value=NS(object='chat.completion')
    with pytest.raises(ProviderResponseError):p.call_model(client,[],[])
    client.chat.completions.create.assert_not_called()
    for status in (404,429,500):
        client=Mock();error=openai.APIStatusError('test',response=httpx.Response(status,request=httpx.Request('POST','http://offline.invalid')),body={})
        client.responses.create.side_effect=error
        client.chat.completions.create.return_value=NS(usage=None,choices=[NS(finish_reason='stop',message=NS(content='done',tool_calls=[]))])
        if status==404: assert p.call_model(client,[],[]).message.text_content()=='done'
        else:
            with pytest.raises(openai.APIStatusError):p.call_model(client,[],[])
        assert client.chat.completions.create.call_count==int(status==404)


@pytest.mark.parametrize('reason',['MAX_TOKENS','MALFORMED_FUNCTION_CALL','SAFETY'])
def test_native_gemini_reports_failure_reason(reason):
    p=GeminiProvider(AgentConfig(path='test.provider',base_url=None,name='offline',provider='gemini',api_key='offline'))
    with pytest.raises(ProviderResponseError):p._deserialize_response(NS(candidates=[NS(finish_reason=reason,content=NS(parts=[]))]))


def test_native_gemini_can_save_two_files_in_one_batch():
    p=GeminiProvider(AgentConfig(path='test.provider',base_url=None,name='offline',provider='gemini',api_key='offline'))
    parts=[NS(function_call=NS(name='save_file',args={'path':name},id=None)) for name in ('evidence_digest.md','sources.csv')]
    message=p._deserialize_response(NS(candidates=[NS(finish_reason='STOP',content=NS(parts=parts))]))
    validate_tool_calls(message)
    assert len(message.tool_calls)==2 and message.tool_calls[0].id!=message.tool_calls[1].id


def test_real_executor_blocks_downstream_on_missing_artifact(tmp_path,monkeypatch):
    monkeypatch.setenv('MAC_ALLOW_UNSAFE_CODE_EXECUTION','1')
    fixture_files(tmp_path);(tmp_path/'artifacts/sources.csv').unlink()
    state={'python_workspace_root':tmp_path};ad_agency_bootstrap('test without web',state)
    tool_manager=Mock();tool_manager.get_tool_specs.return_value=[ToolSpec('web_search'),ToolSpec('save_file')]
    fake=Mock();fake.call_model.return_value=ModelResponse(Message(role=MessageRole.ASSISTANT,content='Done'))
    constructor=Mock(return_value=fake);monkeypatch.setattr(ProviderRegistry,'get_provider',lambda _:constructor)
    context=ExecutionContext(tool_manager=tool_manager,function_manager=Mock(),log_manager=Mock(),global_state=state)
    node=Node.from_dict({'id':'Evidence_Digest','type':'agent','config':{'name':'offline','provider':'openai','role':'test','api_key':'offline'}},path='test.node')
    with pytest.raises(WorkflowExecutionError,match='sources.csv'):AgentNodeExecutor(context).execute(node,[Message(role=MessageRole.USER,content='test')])
    assert fake.call_model.call_count==1
    assert [s.name for s in fake.call_model.call_args.kwargs['tool_specs']]==['save_file']
    assert 'without web' in fake.call_model.call_args.kwargs['conversation'][0].text_content()


def test_python_child_receives_environment_and_utf8(tmp_path,monkeypatch):
    monkeypatch.setenv('PYTHONIOENCODING','cp1252')
    config=PythonRunnerConfig(path='test.python',env={'AUDIT_SENTINEL':'present'})
    node=NS(id='utf8',node_type='python',as_config=lambda _:config)
    context=ExecutionContext(tool_manager=None,function_manager=None,log_manager=Mock(),global_state={'python_workspace_root':tmp_path})
    script_path=tmp_path/'check.py';script_path.write_text('import os\nprint("Ngân sách thận trọng")\nprint(os.environ["AUDIT_SENTINEL"])\nprint(os.environ["MAC_NODE_ID"])',encoding='utf-8')
    result=PythonNodeExecutor(context)._run_process(config,script_path,tmp_path,node)
    assert result.success and 'Ngân sách thận trọng' in result.stdout and 'present' in result.stdout and 'utf8' in result.stdout
