"""A successful load_file must deliver readable bytes to the actual Chat request."""
import json
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, Mock

import pytest
import httpx
from openai import OpenAI

from runtime import sdk
from entity.configs import Node
from entity.configs.node.agent import AgentConfig
from entity.messages import AttachmentRef,FunctionCallOutputEvent,Message,MessageBlock,MessageBlockType,MessageRole
from functions.edge_processor.ad_agency_contracts import _validate_result
from runtime.node.agent.providers.openai_provider import OpenAIProvider
from runtime.node.agent.tool.tool_manager import ToolManager
from runtime.node.executor.agent_executor import AgentNodeExecutor
from runtime.node.executor.base import ExecutionContext
from utils.attachments import AttachmentStore


def provider():
    return OpenAIProvider(AgentConfig(path='offline',name='offline',provider='openai',api_key='offline',base_url=None,params={'protocol':'chat'}))


@pytest.mark.parametrize('name,mime,text',[
    ('brief.md','text/markdown','# Nội dung creative thật\nKhông chỉ metadata.'),
    ('registry.json','application/json','{"segment_id":"S1","name":"Văn phòng"}'),
    ('table.csv','application/vnd.ms-excel','concept_id,segment_id\nC1,S1\n'),
])
def test_chat_tool_and_event_include_local_text_content(tmp_path,name,mime,text):
    path=tmp_path/name;path.write_text(text,encoding='utf-8-sig',newline='\n')
    block=MessageBlock(MessageBlockType.FILE,attachment=AttachmentRef(attachment_id='source',name=name,mime_type=mime,local_path=str(path)))
    p=provider()
    message=Message(role=MessageRole.TOOL,content=[block],tool_call_id='load1')
    serialized=p._build_chat_payload([message],None,{})['messages'][0]
    assert text in serialized['content'] and serialized['tool_call_id']=='load1'
    event=FunctionCallOutputEvent(call_id='load1',function_name='load_file',output_blocks=[block])
    assert text in p._serialize_function_call_output_event_for_chat(event)['content']


def test_chat_tool_file_content_respects_inline_limit(tmp_path):
    path=tmp_path/'large.md';path.write_text('A'*100,encoding='utf-8')
    block=MessageBlock(MessageBlockType.FILE,attachment=AttachmentRef(attachment_id='large',name='large.md',mime_type='text/markdown',local_path=str(path)))
    p=provider();p.text_inline_char_limit=20
    content=p._serialize_message_for_chat(Message(role=MessageRole.TOOL,content=[block],tool_call_id='load'))['content']
    assert 'A'*20 in content and 'A'*21 not in content and 'truncated' in content


def test_real_openai_sdk_http_json_contains_file_text_without_network(tmp_path):
    contents=[('brief.md','text/markdown','# Nội dung nguồn thật'),
              ('ids.json','application/json','{"segment_id":"S1"}'),
              ('rows.csv','application/vnd.ms-excel','concept_id,segment_id\nC1,S1\n')]
    messages=[]
    for i,(name,mime,text) in enumerate(contents):
        path=tmp_path/name;path.write_text(text,encoding='utf-8-sig',newline='\n')
        block=MessageBlock(MessageBlockType.FILE,attachment=AttachmentRef(attachment_id=str(i),name=name,mime_type=mime,local_path=str(path)))
        messages.append(Message(role=MessageRole.TOOL,tool_call_id='load'+str(i),content=[block]))
    seen=[]
    def handler(request):
        body=json.loads(request.content)
        assert request.url.path=='/v1/chat/completions'
        for i,(_,_,text) in enumerate(contents):assert text in body['messages'][i]['content']
        seen.append(body)
        return httpx.Response(200,json={'id':'offline','object':'chat.completion','created':1,'model':'offline',
            'choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':'received'}}]})
    # MockTransport invokes only this in-process handler, never the network.
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        with OpenAI(api_key='offline',base_url='http://offline.invalid/v1',http_client=http,max_retries=0) as client:
            response=provider().call_model(client,messages,[],protocol='chat')
    assert len(seen)==1 and response.message.text_content()=='received'


def test_real_executor_provider_and_file_tools_can_read_then_write_data_rows(tmp_path,monkeypatch):
    artifacts=tmp_path/'artifacts';artifacts.mkdir()
    brief='# SOURCE_CONCEPT: C1\nHOOK_FROM_REAL_FILE: Bánh cho giờ nghỉ\n'
    (artifacts/'creative_brief.md').write_text(brief,encoding='utf-8',newline='\n')
    (artifacts/'campaign_brief.json').write_text('{"product":"Bánh","budget":{"ad_spend":100}}',encoding='utf-8')
    (artifacts/'strategy_ids.json').write_text('{"segments":[{"segment_id":"S1"}],"offers":[{"offer_id":"O1"}]}',encoding='utf-8')
    csv='concept_id,segment_id,insight,hook,benefit,proof,cta,format,asset_requirement,test_variant\nC1,S1,Giờ nghỉ,Bánh cho giờ nghỉ,Chia sẻ,Giả thuyết,Nhắn tin,image,Ảnh thật,A\n'
    node=Node.from_dict({'id':'Creative_Director','type':'agent','config':{'name':'offline','provider':'openai','api_key':'offline','params':{'protocol':'chat'},'tooling':[{'type':'function','config':{'tools':[{'name':'load_file'},{'name':'save_file'}]}}]}},path='offline.node')
    client=Mock();steps=[]
    def answer(payload_calls=None,text=''):
        return NS(usage=None,choices=[NS(finish_reason='tool_calls' if payload_calls else 'stop',message=NS(content=text,tool_calls=[NS(id='call_'+str(len(steps))+'_'+str(i),function=NS(name=name,arguments=json.dumps(args,ensure_ascii=False))) for i,(name,args) in enumerate(payload_calls or [])]))])
    def create(**payload):
        steps.append(payload)
        if len(steps)==1:
            return answer([('load_file',{'path_or_id':'artifacts/'+name}) for name in ('creative_brief.md','campaign_brief.json','strategy_ids.json')])
        tool_text='\n'.join(m['content'] for m in payload['messages'] if m['role']=='tool')
        if len(steps)==2:
            # This checks the real SDK-bound serialization, not a mock provider
            # that can "know" file content without receiving it.
            assert brief in tool_text and '"segment_id":"S1"' in tool_text and '"ad_spend":100' in tool_text
            return answer([('save_file',{'path':'artifacts/creative_matrix.csv','content':csv,'encoding':'utf-8-sig'})])
        if len(steps)==3:return answer([('load_file',{'path_or_id':'artifacts/creative_matrix.csv'})])
        assert csv in tool_text
        return answer(text='Saved verified data rows')
    client.chat.completions.create.side_effect=create
    client.responses.create.side_effect=AssertionError('Unexpected Responses request')
    monkeypatch.setattr(OpenAIProvider,'create_client',lambda self:client)
    state={'python_workspace_root':tmp_path,'graph_directory':tmp_path.parent,'attachment_store':AttachmentStore(tmp_path/'attachments'),'node_result_validator':_validate_result}
    context=ExecutionContext(tool_manager=ToolManager(),function_manager=None,log_manager=MagicMock(),global_state=state)
    result=AgentNodeExecutor(context).execute(node,[Message(role=MessageRole.USER,content='Read existing files and finish matrix')])
    assert result and len(steps)==4
    assert (artifacts/'creative_matrix.csv').read_text(encoding='utf-8-sig')==csv
    client.responses.create.assert_not_called()
