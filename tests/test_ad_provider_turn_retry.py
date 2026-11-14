"""Offline malformed-response recovery must never replay completed file tools."""
import json
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, Mock

import pytest

from runtime import sdk
from entity.configs import Node
from entity.configs.node.agent import AgentRetryConfig
from entity.messages import Message, MessageRole
from functions.edge_processor.ad_agency_contracts import _validate_result
from runtime.node.agent.providers.openai_provider import OpenAIProvider
from runtime.node.agent.providers.response import ModelResponse, ProviderResponseError
from runtime.node.agent.tool.tool_manager import ToolManager
from runtime.node.executor.agent_executor import AgentNodeExecutor
from runtime.node.executor.base import ExecutionContext
from utils.attachments import AttachmentStore


def executor(state):
    return AgentNodeExecutor(ExecutionContext(tool_manager=ToolManager(), function_manager=None,
                                             log_manager=MagicMock(), global_state=state))


def policy(**overrides):
    values = dict(path='offline.retry', enabled=True, max_attempts=2, min_wait_seconds=0,
                  max_wait_seconds=0, non_retry_exception_types=['ProviderResponseError'])
    values.update(overrides)
    return AgentRetryConfig(**values)


def test_advertising_malformed_response_retries_once_within_total_budget():
    run = executor({'ad_malformed_retry_limit': 1})
    ok = ModelResponse(Message(role=MessageRole.ASSISTANT, content='done'))
    call = Mock(side_effect=[ProviderResponseError('malformed_function_call'), ok])
    assert run._execute_with_retry(NS(id='Evidence_Digest'), policy(), call) is ok
    assert call.call_count == 2


@pytest.mark.parametrize('budget', [2, 5])
def test_repeated_malformed_response_stops_after_two_calls_even_with_larger_budget(budget):
    call = Mock(side_effect=ProviderResponseError('malformed_function_call'))
    with pytest.raises(ProviderResponseError):
        executor({'ad_malformed_retry_limit': 1})._execute_with_retry(NS(id='offline'), policy(max_attempts=budget), call)
    assert call.call_count == 2


@pytest.mark.parametrize('settings,state', [({'enabled': False}, {'ad_malformed_retry_limit': 1}),
                                         ({'max_attempts': 1}, {'ad_malformed_retry_limit': 1}),
                                         ({}, {})])
def test_disabled_single_attempt_and_unrelated_workflows_do_not_retry(settings, state):
    call = Mock(side_effect=ProviderResponseError('malformed_function_call'))
    with pytest.raises(ProviderResponseError):
        executor(state)._execute_with_retry(NS(id='offline'), policy(**settings), call)
    assert call.call_count == 1


@pytest.mark.parametrize('reason', ['invalid_tool_arguments', 'invalid_tool_call', 'response_format_mismatch',
                                  'empty_response', 'length', 'content_filter'])
def test_other_provider_errors_keep_nonretry_policy(reason):
    call = Mock(side_effect=ProviderResponseError(reason))
    with pytest.raises(ProviderResponseError):
        executor({'ad_malformed_retry_limit': 1})._execute_with_retry(NS(id='offline'), policy(), call)
    assert call.call_count == 1


def test_real_tool_loop_keeps_first_file_and_discards_failed_response_calls(tmp_path, monkeypatch):
    state = {'ad_malformed_retry_limit': 1, 'python_workspace_root': tmp_path,
             'graph_directory': tmp_path.parent, 'attachment_store': AttachmentStore(tmp_path/'attachments'),
             'node_result_validator': _validate_result}
    node = Node.from_dict({'id': 'Evidence_Digest', 'type': 'agent', 'config': {
        'name': 'offline', 'provider': 'openai', 'api_key': 'offline', 'params': {'protocol': 'chat'},
        'retry': {'enabled': True, 'max_attempts': 2, 'min_wait_seconds': 0, 'max_wait_seconds': 0,
                  'non_retry_exception_types': ['ProviderResponseError']},
        'tooling': [{'type': 'function', 'config': {'tools': [{'name': 'save_file'}]}}]}}, path='offline.node')
    first = '# Bằng chứng\nChưa có nguồn ngoài.\n'
    second = 'id,claim,source_url,access_date,scope,evidence_type\nS1,Chưa xác minh,,,brief,hypothesis\n'
    requests = []
    def reply(reason, calls=(), text=''):
        return NS(id='offline-response', model='offline', usage=None, choices=[NS(finish_reason=reason,
            message=NS(content=text, tool_calls=[NS(id='t'+str(len(requests)), function=NS(
                name='save_file', arguments=json.dumps(args, ensure_ascii=False))) for args in calls]))])
    def create(**payload):
        requests.append(payload)
        if len(requests) == 1:
            return reply('tool_calls', [{'path': 'artifacts/evidence_digest.md', 'content': first, 'mode': 'append'}])
        if len(requests) == 2:
            # Even a supplied call in a failed response must never execute.
            return reply('malformed_function_call', [{'path': 'artifacts/evidence_digest.md', 'content': 'CORRUPTION', 'mode': 'append'}])
        if len(requests) == 3:
            assert requests[1] == requests[2]  # Same complete history, no fabricated tool result.
            assert (tmp_path/'artifacts/evidence_digest.md').read_text(encoding='utf-8') == first
            return reply('tool_calls', [{'path': 'artifacts/sources.csv', 'content': second, 'encoding': 'utf-8-sig'}])
        assert len(requests) == 4
        return reply('stop', text='Đã lưu hai file; dữ kiện chưa được xác minh ngoài.')
    client = Mock()
    client.chat.completions.create.side_effect = create
    client.responses.create.side_effect = AssertionError('No Responses fallback')
    monkeypatch.setattr(OpenAIProvider, 'create_client', lambda self: client)
    result = executor(state).execute(node, [Message(role=MessageRole.USER, content='Offline file test')])
    assert result and len(requests) == 4
    assert (tmp_path/'artifacts/evidence_digest.md').read_text(encoding='utf-8') == first
    assert (tmp_path/'artifacts/sources.csv').read_text(encoding='utf-8-sig') == second
    diagnostics = list((tmp_path/'diagnostics').glob('*.json'))
    assert len(diagnostics) == 1
    assert json.loads(diagnostics[0].read_text())['finish_reason'] == 'malformed_function_call'
    client.responses.create.assert_not_called()
