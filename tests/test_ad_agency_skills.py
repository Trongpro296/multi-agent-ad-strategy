"""Exercise real skill loading and file tools with a mocked model, fully offline."""
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest
import yaml

from runtime import sdk
from check.check import load_config
from entity.configs import Node
from entity.configs.node.agent import AgentConfig
from entity.messages import Message, MessageRole, ToolCallPayload
from functions.edge_processor.ad_agency_contracts import ad_agency_bootstrap
from runtime.node.agent import ModelResponse, ProviderRegistry
from runtime.node.agent.skills import AgentSkillManager
from runtime.node.agent.tool.tool_manager import ToolManager
from runtime.node.executor.agent_executor import AgentNodeExecutor
from runtime.node.executor.base import ExecutionContext
from utils.attachments import AttachmentStore
from utils.function_manager import FunctionManager, FUNCTION_CALLING_DIR

ROOT=Path(__file__).resolve().parents[1]
FILES=('ad_agency_v2.yaml','ad_agency_v2_auto.yaml')
VARIABLES=dict(BASE_URL='http://127.0.0.1:1/v1',API_KEY='offline',MODEL_STRONG='offline',MODEL_CHEAP='offline',MODEL_REVIEW='offline')
MAIN=yaml.safe_load((ROOT/'yaml_instance'/FILES[0]).read_text(encoding='utf-8'))['graph']
AGENTS=[node['id'] for node in MAIN['nodes'] if node['type']=='agent']


@pytest.mark.parametrize('filename',FILES)
@pytest.mark.parametrize('node_id',AGENTS)
def test_skill_isolation_activation_and_existing_tools(filename,node_id):
    design=load_config(ROOT/'yaml_instance'/filename,vars_override=VARIABLES)
    node=next(node for node in design.graph.nodes if node.id==node_id)
    config=node.as_config(AgentConfig)
    assert config.skills.enabled and config.skills.allow
    manager=AgentSkillManager(allow=config.skills.allow)
    assert {skill.name for skill in manager.discover()}==set(config.skills.allow)
    for name in config.skills.allow:
        active=manager.activate_skill(name)
        assert manager.active_skill().name==name
        assert active['allowed_tools']==[]  # Existing Tooling remains in force, not narrowed accidentally.
    assert not manager.discovery_warnings()
    with pytest.raises(ValueError):manager.activate_skill('python-scratchpad')
    specs=ToolManager().get_tool_specs(config.tooling)
    external={spec.name for spec in specs}
    assert {'load_file','save_file','list_directory'}<=external
    assert {spec.name for spec in manager.build_tool_specs()}=={'activate_skill','read_skill_file'}
    assert not external & {'activate_skill','read_skill_file'}


def test_executor_activates_skill_and_saves_both_evidence_files(tmp_path,monkeypatch):
    monkeypatch.setenv('MAC_ALLOW_UNSAFE_CODE_EXECUTION','1')
    workspace=tmp_path/'code_workspace';workspace.mkdir()
    state={'python_workspace_root':workspace,'graph_directory':tmp_path,'attachment_store':AttachmentStore(workspace/'attachments')}
    ad_agency_bootstrap('Kiểm thử giả định, không tìm web',state)
    raw=next(node for node in MAIN['nodes'] if node['id']=='Evidence_Digest')
    node=Node.from_dict(raw,path='test.node')
    skill=node.as_config(AgentConfig).skills.allow[0]
    digest='# Bằng chứng\nChỉ có giả thuyết, không truy cập web.\n'
    sources='id,claim,source_url,access_date,scope,evidence_type\nH1,Giới hạn dữ liệu,,,kiểm thử,hypothesis\n'
    def batch(items):
        calls=[ToolCallPayload(id='call_'+str(i),function_name=name,arguments=json.dumps(args,ensure_ascii=False)) for i,(name,args) in enumerate(items)]
        return ModelResponse(Message(role=MessageRole.ASSISTANT,content='',tool_calls=calls),finish_reason='tool_calls')
    provider=Mock()
    provider.call_model.side_effect=[
        batch([('activate_skill',{'skill_name':skill})]),
        batch([('save_file',{'path':'artifacts/evidence_digest.md','content':digest}),('save_file',{'path':'artifacts/sources.csv','content':sources,'encoding':'utf-8-sig'})]),
        batch([('load_file',{'path_or_id':'artifacts/evidence_digest.md'}),('load_file',{'path_or_id':'artifacts/sources.csv'})]),
        ModelResponse(Message(role=MessageRole.ASSISTANT,content='Đã lưu hai file. Giới hạn: dữ liệu giả định.')),
    ]
    monkeypatch.setattr(ProviderRegistry,'get_provider',lambda _:Mock(return_value=provider))
    context=ExecutionContext(tool_manager=ToolManager(),function_manager=FunctionManager(FUNCTION_CALLING_DIR),log_manager=MagicMock(),global_state=state)
    result=AgentNodeExecutor(context).execute(node,[Message(role=MessageRole.USER,content='test')])
    assert (workspace/'artifacts/evidence_digest.md').read_text(encoding='utf-8')==digest
    assert (workspace/'artifacts/sources.csv').read_text(encoding='utf-8-sig')==sources
    assert (workspace/'artifacts/sources.csv').read_bytes().startswith(b'\xef\xbb\xbf')
    assert provider.call_model.call_count==4 and result[0].text_content()
    conversation=provider.call_model.call_args.kwargs['conversation']
    assert any(m.metadata.get('skill_activation') and m.metadata.get('skill_name')==skill for m in conversation)
    bound={spec.name for spec in provider.call_model.call_args.kwargs['tool_specs']}
    assert {'activate_skill','save_file','load_file'}<=bound
    assert 'web_search' not in bound and 'read_webpage_content' not in bound
