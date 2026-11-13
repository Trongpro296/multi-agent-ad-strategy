"""Offline recovery: real restore/Python/Gates, mocked models and Human approval."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import yaml

from runtime import sdk
from entity.configs import Node
from entity.configs.node.agent import AgentConfig
from entity.messages import Message,MessageRole,ToolCallPayload
from runtime.node.agent.providers.openai_provider import OpenAIProvider
from runtime.node.agent.providers.response import ProviderResponseError
from runtime.node.agent.skills import AgentSkillManager
from runtime.node.executor.agent_executor import AgentNodeExecutor
from runtime.node.executor.base import ExecutionContext
from runtime.node.executor.human_executor import HumanNodeExecutor
from tools.prepare_ad_recovery import build_recovery,restore_script
from test_ad_agency_audit import fixture_files

ROOT=Path(__file__).resolve().parents[1]
VARIABLES=dict(BASE_URL='http://127.0.0.1:1/v1',API_KEY='offline',MODEL_STRONG='offline',MODEL_CHEAP='offline',MODEL_REVIEW='offline')
CACHED={'Director_Brief','Market_Researcher','Competitor_Analyst','Customer_Insight','Evidence_Digest','Brand_Strategist','Director_Strategy','Media_Planner','Performance_Analyst'}


def test_activation_has_real_file_manifest_and_single_copy_of_instructions():
    manager=AgentSkillManager(allow=['ad-media-planning'])
    result=manager.activate_skill('ad-media-planning')
    assert result['available_files']==['SKILL.md']
    with pytest.raises(ValueError,match='Available files'):
        manager.read_skill_file('ad-media-planning','references/example.md')
    node=Node.from_dict({'id':'Media_Planner','type':'agent','config':{'name':'offline','provider':'openai','api_key':'offline'}},path='offline.node')
    executor=AgentNodeExecutor(ExecutionContext(tool_manager=None,function_manager=None,log_manager=MagicMock()))
    call=ToolCallPayload(id='skill1',function_name='activate_skill',arguments=json.dumps({'skill_name':'ad-media-planning'}))
    messages,events=executor._execute_tool_batch(node,[call],manager.build_tool_specs(),manager)
    assert [m.role for m in messages]==[MessageRole.TOOL,MessageRole.SYSTEM]
    receipt=json.loads(messages[0].text_content())
    assert receipt['instructions_loaded'] and receipt['available_files']==['SKILL.md']
    assert 'instructions' not in receipt and 'path' not in receipt
    assert result['instructions'] in messages[1].text_content()
    assert result['instructions'] not in events[0].output_text


def test_malformed_response_diagnostic_without_another_model_call(tmp_path):
    config=AgentConfig(path='offline',base_url=None,name='offline',provider='openai',api_key='not-recorded')
    provider=OpenAIProvider(config)
    raw=SimpleNamespace(id='response1',model='offline',choices=[SimpleNamespace(finish_reason='malformed_function_call',message=SimpleNamespace(content='',tool_calls=[]))])
    with pytest.raises(ProviderResponseError) as caught:provider._deserialize_chat_response(raw)
    error=caught.value
    assert error.diagnostics['finish_reason']=='malformed_function_call' and error.diagnostics['tool_calls']==[]
    context=ExecutionContext(tool_manager=None,function_manager=None,log_manager=MagicMock(),global_state={'python_workspace_root':tmp_path})
    node=SimpleNamespace(id='Creative_Director',model_name='offline')
    rel=AgentNodeExecutor(context)._save_provider_diagnostic(node,[Message(role=MessageRole.USER,content='PRIVATE_INPUT_DO_NOT_COPY')],error)
    saved=(tmp_path/rel).read_text(encoding='utf-8')
    assert 'PRIVATE_INPUT_DO_NOT_COPY' not in saved and 'not-recorded' not in saved
    assert json.loads(saved)['request_summary'][0]['text_characters']==len('PRIVATE_INPUT_DO_NOT_COPY')


def prepare_source(tmp_path):
    source=tmp_path/'source';source.mkdir();fixture_files(source)
    originals={name:(source/'artifacts'/name).read_bytes() for name in ('creative_matrix.csv','advertising_strategy_draft.md','execution_calendar.csv')}
    for name in list(originals)+['qa_report.json','handoff_notes.md']:(source/'artifacts'/name).unlink()
    log=tmp_path/'source.log'
    entries=[{'event_type':'NODE_END','node_id':'Campaign_Input','output':'Original constraints: do not browse; offline test'}]
    entries += [{'event_type':'NODE_END','node_id':node,'output':'saved'} for node in CACHED]
    log.write_text('\n'.join(json.dumps(e) for e in entries),encoding='utf-8')
    template=yaml.safe_load((ROOT/'yaml_instance/ad_agency_v2.yaml').read_text(encoding='utf-8'))
    return source,log,template,originals


def test_recovery_uses_existing_fifteen_files_and_only_four_pending_agents(tmp_path,monkeypatch):
    source,log,template,originals=prepare_source(tmp_path)
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (source/'artifacts').iterdir()}
    untouched=copy.deepcopy(template)
    doc,manifest=build_recovery(template,source,log,'offline_source',creative_model='offline-recovery')
    assert template==untouched
    assert set(manifest['cached_agents'])==CACHED and len(manifest['files'])==15
    assert set(manifest['pending_agents'])=={'Creative_Director','Plan_Assembler','Strategy_QA','Delivery_Packager'}
    assert next(n for n in doc['graph']['nodes'] if n['id']=='Creative_Director')['config']['name']=='offline-recovery'
    path=tmp_path/'recovery.yaml';path.write_text(yaml.safe_dump(doc,allow_unicode=True),encoding='utf-8')
    executed=[]
    def fake_agent(executor,node,messages):
        executed.append(node.id)
        folder=Path(executor.context.global_state['python_workspace_root'])/'artifacts'
        if node.id=='Creative_Director':(folder/'creative_matrix.csv').write_bytes(originals['creative_matrix.csv'])
        elif node.id=='Plan_Assembler':
            for name in ('advertising_strategy_draft.md','execution_calendar.csv'):(folder/name).write_bytes(originals[name])
        elif node.id=='Strategy_QA':
            man=json.loads((folder.parent/'review/review_manifest.json').read_text())
            (folder/'qa_report.json').write_text(json.dumps({'verdict':'PASS','plan_version':man['plan_version'],'plan_gate_status':'OK','issues':[]}),encoding='utf-8')
            return [Message(role=MessageRole.ASSISTANT,content='QA: PASS')]
        elif node.id=='Delivery_Packager':(folder/'handoff_notes.md').write_text('OFFLINE FIXTURE ONLY',encoding='utf-8')
        else:raise AssertionError('Completed Agent must not call a model: '+node.id)
        return [Message(role=MessageRole.ASSISTANT,content='saved')]
    monkeypatch.setenv('MAC_ALLOW_UNSAFE_CODE_EXECUTION','1')
    monkeypatch.setattr(AgentNodeExecutor,'execute',fake_agent)
    monkeypatch.setattr(HumanNodeExecutor,'execute',lambda self,node,inputs:[Message(role=MessageRole.USER,content='HUMAN: APPROVE')])
    monkeypatch.setattr(sdk,'OUTPUT_ROOT',tmp_path/'runs')
    result=sdk.run_workflow(path,task_prompt='ignored recovery launch note',variables=VARIABLES,session_name='session_offline_recovery')
    assert set(executed)==set(manifest['pending_agents']) and len(executed)==4
    artifacts=result.meta_info.output_dir/'code_workspace/artifacts'
    for name,digest in before.items():assert hashlib.sha256((artifacts/name).read_bytes()).hexdigest()==digest
    assert (result.meta_info.output_dir/'code_workspace/output/Campaign_Plan.xlsx').is_file()
    assert {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (source/'artifacts').iterdir()}==before


def test_restore_refuses_to_overwrite_changed_file(tmp_path,monkeypatch):
    import base64
    original=b'original';archive={'original_request':'offline','files':{'file.md':{'base64':base64.b64encode(original).decode(),'sha256':hashlib.sha256(original).hexdigest()}}}
    (tmp_path/'artifacts').mkdir();target=tmp_path/'artifacts/file.md';target.write_bytes(b'changed')
    monkeypatch.setenv('MAC_CODE_WORKSPACE',str(tmp_path))
    with pytest.raises(ValueError,match='Refusing to overwrite'):exec(restore_script(archive),{})
    assert target.read_bytes()==b'changed'


def test_missing_file_is_not_cached_even_if_old_node_succeeded(tmp_path):
    source,log,template,_=prepare_source(tmp_path)
    (source/'artifacts/media_plan.csv').unlink()
    doc,manifest=build_recovery(template,source,log,'offline_source')
    assert 'Media_Planner' not in manifest['cached_agents']
    assert 'Media_Planner' in manifest['pending_agents']
    assert next(n for n in doc['graph']['nodes'] if n['id']=='Media_Planner')['type']=='agent'


def test_corrupt_restore_payload_is_rejected_before_writing(tmp_path,monkeypatch):
    import base64
    archive={'original_request':'offline','files':{'file.md':{'base64':base64.b64encode(b'changed').decode(),'sha256':hashlib.sha256(b'expected').hexdigest()}}}
    monkeypatch.setenv('MAC_CODE_WORKSPACE',str(tmp_path))
    with pytest.raises(ValueError,match='hash mismatch'):exec(restore_script(archive),{})
    assert not (tmp_path/'artifacts/file.md').exists()
