"""Regression for Claude's duplicate tool_result error after skill activation.

Exercises actual executor batch assembly and both OpenAI payload serializers;
no API client, network requests or workflow runs are required.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import httpx
import openai
import pytest

from runtime import sdk
from entity.configs import Node
from entity.configs.node.agent import AgentConfig, AgentRetryConfig
from entity.messages import FunctionCallOutputEvent, Message, MessageRole, ToolCallPayload
from runtime.node.agent import ModelResponse
from runtime.node.agent.providers.openai_provider import OpenAIProvider
from runtime.node.agent.skills import AgentSkillManager
from runtime.node.executor.agent_executor import AgentNodeExecutor
from runtime.node.executor.base import ExecutionContext


def executor():
    return AgentNodeExecutor(ExecutionContext(
        tool_manager=None, function_manager=None, log_manager=MagicMock(), global_state={},
    ))


def status_error(status):
    return openai.APIStatusError(
        'offline error', body={},
        response=httpx.Response(status, request=httpx.Request('POST', 'http://offline.invalid')),
    )


def policy(**extra):
    return AgentRetryConfig.from_dict({
        'enabled': True, 'max_attempts': 2, 'min_wait_seconds': 0, 'max_wait_seconds': 0,
        **extra,
    }, path='offline.retry')


CASES = [
    [('activate_skill', {'skill_name': 'ad-brief-planning'})],
    [('activate_skill', {'skill_name': 'ad-brief-planning'}),
     ('read_skill_file', {'skill_name': 'ad-brief-planning', 'relative_path': 'SKILL.md'})],
    [('activate_skill', {'skill_name': 'ad-brief-planning'}), ('unconfigured_tool', {})],
    [('activate_skill', {'skill_name': 'does-not-exist'}),
     ('activate_skill', {'skill_name': 'ad-brief-planning'})],
    [('activate_skill', {'skill_name': 'ad-brief-planning'}),
     ('activate_skill', {'skill_name': 'ad-budget-feasibility'})],
]


@pytest.mark.parametrize('items', CASES)
def test_complete_tool_batch_precedes_skill_followups_in_both_protocols(items):
    node = Node.from_dict({
        'id': 'offline', 'type': 'agent',
        'config': {'name': 'offline', 'provider': 'openai', 'api_key': 'offline'},
    }, path='offline.node')
    manager = AgentSkillManager(allow=['ad-brief-planning', 'ad-budget-feasibility'])
    calls = [ToolCallPayload(id='call_'+str(i), function_name=name, arguments=json.dumps(args))
             for i, (name, args) in enumerate(items)]
    expected = [call.id for call in calls]
    messages, events = executor()._execute_tool_batch(node, calls, manager.build_tool_specs(), manager)

    # Every call, including a failed one, has exactly one result. No instruction
    # may interrupt the batch: gateways require results adjacent to their calls.
    assert [m.tool_call_id for m in messages[:len(calls)]] == expected
    assert all(m.role is MessageRole.TOOL for m in messages[:len(calls)])
    followups = messages[len(calls):]
    assert followups and all(m.role is MessageRole.SYSTEM for m in followups)
    assert all(m.metadata.get('skill_activation') for m in followups)
    assert all(isinstance(event, FunctionCallOutputEvent) for event in events[:len(calls)])
    assert [event.call_id for event in events[:len(calls)]] == expected
    assert events[len(calls):] == followups

    provider = OpenAIProvider(node.as_config(AgentConfig))
    conversation = [Message(role=MessageRole.USER, content='offline'),
                    Message(role=MessageRole.ASSISTANT, content='', tool_calls=calls)] + messages
    chat = provider._build_chat_payload(conversation, None, {'protocol': 'chat'})['messages']
    assert [m.get('tool_call_id') for m in chat[2:2+len(calls)]] == expected
    assert all(m['role']=='tool' for m in chat[2:2+len(calls)])
    assert all(m['role']=='system' for m in chat[2+len(calls):])

    timeline = [{'type': 'function_call', 'call_id': call.id, 'name': call.function_name,
                 'arguments': call.arguments} for call in calls] + events
    response_input = provider._build_request_payload(timeline, None, {})['input']
    outputs = response_input[len(calls):2*len(calls)]
    assert [item['call_id'] for item in outputs] == expected
    assert all(item['type']=='function_call_output' for item in outputs)
    assert all(item['role']=='system' for item in response_input[2*len(calls):])


@pytest.mark.parametrize('status', [400, 401, 403, 404, 422])
def test_permanent_client_errors_do_not_retry_through_apierror_base_class(status):
    assert not policy().should_retry(status_error(status))


@pytest.mark.parametrize('status', [408, 409, 425, 429, 500, 502, 503, 504])
def test_transient_status_retries_are_preserved(status):
    assert policy().should_retry(status_error(status))


def test_explicit_status_and_nonretry_overrides_are_respected():
    assert policy(retry_on_status_codes=[400]).should_retry(status_error(400))
    assert not policy(non_retry_exception_types=['APIStatusError']).should_retry(status_error(429))
    assert not policy(enabled=False).should_retry(status_error(500))
    transport = openai.APIConnectionError(request=httpx.Request('POST', 'http://offline.invalid'))
    assert policy().should_retry(transport)
    wrapper = RuntimeError('rate limit text does not make a wrapped bad request transient')
    wrapper.__cause__ = status_error(400)
    assert not policy().should_retry(wrapper)


def test_bad_request_is_invoked_once_but_rate_limit_can_retry():
    node = SimpleNamespace(id='offline')
    fail = Mock(side_effect=status_error(400))
    with pytest.raises(openai.APIStatusError):
        executor()._execute_with_retry(node, policy(), fail)
    assert fail.call_count == 1
    response = ModelResponse(Message(role=MessageRole.ASSISTANT, content='done'))
    transient = Mock(side_effect=[status_error(429), response])
    assert executor()._execute_with_retry(node, policy(), transient) is response
    assert transient.call_count == 2
