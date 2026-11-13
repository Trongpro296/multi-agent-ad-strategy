"""Every campaign agent must use its declared Chat protocol, with no live API."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from runtime import sdk
from check.check import load_config
from entity.configs.node.agent import AgentConfig
from entity.messages import Message, MessageRole
from runtime.node.agent.providers.openai_provider import OpenAIProvider

ROOT=Path(__file__).resolve().parents[1]
AGENTS=('Director_Brief','Market_Researcher','Competitor_Analyst','Customer_Insight',
        'Evidence_Digest','Brand_Strategist','Director_Strategy','Media_Planner',
        'Creative_Director','Performance_Analyst','Plan_Assembler','Strategy_QA','Delivery_Packager')
VARIABLES=dict(BASE_URL='http://127.0.0.1:1/v1',API_KEY='offline',MODEL_STRONG='offline',MODEL_CHEAP='offline',MODEL_REVIEW='offline')


@pytest.mark.parametrize('filename',('ad_agency_v2.yaml','ad_agency_v2_auto.yaml'))
@pytest.mark.parametrize('node_id',AGENTS)
def test_each_agent_uses_chat_without_responses_request(filename,node_id):
    design=load_config(ROOT/'yaml_instance'/filename,vars_override=VARIABLES)
    config=next(n for n in design.graph.nodes if n.id==node_id).as_config(AgentConfig)
    assert config.params.get('protocol')=='chat'
    provider=OpenAIProvider(config)
    client=Mock()
    client.responses.create.side_effect=AssertionError('Responses endpoint must not be called')
    client.chat.completions.create.return_value=SimpleNamespace(
        usage=None,choices=[SimpleNamespace(finish_reason='stop',message=SimpleNamespace(content='offline result',tool_calls=[]))],
    )
    response=provider.call_model(client,[Message(role=MessageRole.USER,content='offline')],[],**config.params)
    assert response.message.text_content()=='offline result'
    client.chat.completions.create.assert_called_once()
    client.responses.create.assert_not_called()
    assert 'protocol' not in client.chat.completions.create.call_args.kwargs
