"""Pre-write CSV checks and bounded same-Agent repair, without network calls."""
import csv
import io
import json
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, Mock

import pytest

from runtime import sdk
from entity.configs import Node
from entity.messages import Message, MessageRole
from functions.function_calling.file import save_file
from functions.edge_processor.ad_agency_contracts import _validate_result
from runtime.node.agent.providers.openai_provider import OpenAIProvider
from runtime.node.agent.tool.tool_manager import ToolManager
from runtime.node.executor.agent_executor import AgentNodeExecutor
from runtime.node.executor.base import ExecutionContext
from utils.ad_csv import CSV_COLUMNS, CSVWriteValidationError
from utils.attachments import AttachmentStore
from utils.exceptions import WorkflowExecutionError


HEADER = 'scenario,channel,budget_amount,metric,metric_value,formula,assumption,estimate_status\n'
BAD = HEADER + 'baseline,Facebook,1500000,Messages,,,,,NOT_ESTIMATED\n'
GOOD = HEADER + 'baseline,Facebook,1500000,Messages,,,No baseline,NOT_ESTIMATED\n'


def state(root):
    return {'python_workspace_root': root, 'graph_directory': root.parent,
            'attachment_store': AttachmentStore(root/'attachments'), 'ad_csv_write_validation': True}


def save(ctx, content, name='budget_scenarios.csv', **kwargs):
    return save_file('artifacts/'+name, content, encoding='utf-8-sig', _context=ctx, **kwargs)


def test_bad_write_keeps_existing_bytes_and_blocks_stale_success(tmp_path):
    ctx = state(tmp_path)
    save(ctx, GOOD)
    path = tmp_path/'artifacts/budget_scenarios.csv'
    before = path.read_bytes()
    with pytest.raises(CSVWriteValidationError, match='expected 8 cells, received 9'):
        save(ctx, BAD)
    assert path.read_bytes() == before
    assert 'artifacts/budget_scenarios.csv' in ctx['ad_csv_write_errors']
    with pytest.raises(WorkflowExecutionError, match='unresolved CSV write rejection'):
        _validate_result('Media_Planner', Message(role=MessageRole.ASSISTANT, content='done'), ctx)
    save(ctx, GOOD)
    assert not ctx['ad_csv_write_errors']


@pytest.mark.parametrize('name', CSV_COLUMNS)
def test_all_six_contract_csvs_share_prewrite_schema(tmp_path, name):
    ctx = state(tmp_path)
    buf = io.StringIO(newline='')
    writer = csv.writer(buf)
    writer.writerow(CSV_COLUMNS[name])
    writer.writerow(['dữ liệu, có dấu phẩy\nvà xuống dòng'] * len(CSV_COLUMNS[name]))
    save(ctx, buf.getvalue(), name)
    assert (tmp_path/'artifacts'/name).exists()


@pytest.mark.parametrize('content', [HEADER, 'wrong,header\na,b\n', HEADER+'a,b\n',
                                   HEADER+'"unterminated\n', HEADER.replace('scenario,', 'channel,')+'a,b\n'])
def test_bad_new_file_is_not_created(tmp_path, content):
    with pytest.raises(CSVWriteValidationError):
        save(state(tmp_path), content)
    assert not (tmp_path/'artifacts/budget_scenarios.csv').exists()


def test_append_checks_entire_candidate_and_preserves_previous_file(tmp_path):
    ctx = state(tmp_path)
    save(ctx, GOOD)
    before = (tmp_path/'artifacts/budget_scenarios.csv').read_bytes()
    with pytest.raises(CSVWriteValidationError):
        save(ctx, 'bad,two\n', mode='append')
    assert (tmp_path/'artifacts/budget_scenarios.csv').read_bytes() == before
    save(ctx, GOOD.splitlines(keepends=True)[1], mode='append')
    assert not ctx['ad_csv_write_errors']
    assert len(list(csv.reader(io.StringIO((tmp_path/'artifacts/budget_scenarios.csv').read_text(encoding='utf-8-sig'))))) == 3


def test_other_workflows_and_blank_operating_templates_are_unaffected(tmp_path):
    ctx = state(tmp_path)
    save(ctx, 'date,count\n', 'visit_log_template.csv')
    ctx.pop('ad_csv_write_validation')
    save(ctx, BAD)
    assert (tmp_path/'artifacts/budget_scenarios.csv').exists()


@pytest.mark.parametrize('outcome', ['repair', 'two_corrections', 'exhaust', 'ignore'])
def test_real_agent_repairs_in_same_tool_loop_or_stops_at_limit(tmp_path, monkeypatch, outcome):
    ctx = state(tmp_path)
    ctx['node_result_validator'] = _validate_result
    node = Node.from_dict({'id': 'Media_Planner', 'type': 'agent', 'config': {
        'name': 'offline', 'provider': 'openai', 'api_key': 'offline', 'params': {'protocol': 'chat'},
        'retry': {'enabled': False},
        'tooling': [{'type': 'function', 'config': {'tools': [{'name': 'save_file'}]}}]}}, path='offline.node')
    media = ','.join(CSV_COLUMNS['media_plan.csv'])+'\nFacebook,primary,messages,S1,O1,100,1500000,VND,2026-12-01,2026-12-07,inbox,test\n'
    save(ctx, media, 'media_plan.csv')
    if outcome == 'ignore':
        save(ctx, GOOD)  # A valid old file must not mask a rejected new handoff.
    requests = []
    def response(calls=(), text=''):
        return NS(usage=None, choices=[NS(finish_reason='tool_calls' if calls else 'stop', message=NS(
            content=text, tool_calls=[NS(id='t'+str(len(requests)), function=NS(name='save_file',
                arguments=json.dumps({'path':'artifacts/budget_scenarios.csv','content':content,'encoding':'utf-8-sig'})))
                for content in calls]))])
    def create(**payload):
        requests.append(payload)
        step = len(requests)
        if step == 1:
            return response([BAD])
        errors = [m['content'] for m in payload['messages'] if m['role']=='tool']
        assert any('expected 8 cells, received 9' in text for text in errors)
        if outcome == 'ignore':
            return response(text='Everything saved')
        if outcome == 'exhaust':
            return response([BAD])
        success_step = 3 if outcome == 'two_corrections' else 2
        if step < success_step:
            return response([BAD])
        if step == success_step:
            assert not (tmp_path/'artifacts/budget_scenarios.csv').exists()
            return response([GOOD])
        assert step == success_step+1
        return response(text='Both CSVs saved and checked')
    client = Mock()
    client.chat.completions.create.side_effect = create
    client.responses.create.side_effect = AssertionError('No Responses/network fallback')
    monkeypatch.setattr(OpenAIProvider, 'create_client', lambda self: client)
    run = AgentNodeExecutor(ExecutionContext(tool_manager=ToolManager(),function_manager=None,
        log_manager=MagicMock(),global_state=ctx))
    if outcome in ('exhaust', 'ignore'):
        pattern = 'CSV repair limit' if outcome=='exhaust' else 'unresolved CSV write rejection'
        with pytest.raises(WorkflowExecutionError, match=pattern):
            run.execute(node,[Message(role=MessageRole.USER,content='offline repair')])
        assert len(requests) == (3 if outcome=='exhaust' else 2)
    else:
        assert run.execute(node,[Message(role=MessageRole.USER,content='offline repair')])
        assert len(requests) == (4 if outcome=='two_corrections' else 3)
        assert not ctx['ad_csv_write_errors']
        assert (tmp_path/'artifacts/budget_scenarios.csv').read_text(encoding='utf-8-sig') == GOOD
    assert (tmp_path/'artifacts/media_plan.csv').read_text(encoding='utf-8-sig') == media


@pytest.mark.parametrize('outcome',['repair','exhaust','ignore'])
def test_real_qa_agent_repairs_report_or_stops_at_bounded_limit(tmp_path,monkeypatch,outcome):
    from test_ad_agency_audit import fixture_files,run_gate,qa_fixture
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path);run_gate(tmp_path)
    manifest=json.loads((tmp_path/'review/review_manifest.json').read_text())
    good=json.dumps(qa_fixture(manifest['plan_version']))
    bad=json.loads(good);bad['criteria_results'][0]['evidence_refs'][0]['file']='review/review_manifest.json'
    bad=json.dumps(bad)
    ctx=state(tmp_path);ctx.update(ad_qa_write_validation=True,node_result_validator=_validate_result)
    if outcome=='ignore':save_file('artifacts/qa_report.json',good,_context=ctx)
    node=Node.from_dict({'id':'Strategy_QA','type':'agent','config':{
        'name':'offline','provider':'openai','api_key':'offline','params':{'protocol':'chat'},
        'retry':{'enabled':False},'tooling':[{'type':'function','config':{'tools':[{'name':'save_file'}]}}]}},path='offline.qa')
    requests=[]
    def create(**payload):
        requests.append(payload);step=len(requests)
        if step>1:
            assert any('invalid evidence file/location' in str(m.get('content')) for m in payload['messages'] if m['role']=='tool')
        content=bad if step==1 or outcome=='exhaust' else good
        done=(outcome=='ignore' and step==2) or (outcome=='repair' and step==3)
        calls=[] if done else [NS(id='qa'+str(step),function=NS(name='save_file',arguments=json.dumps({'path':'artifacts/qa_report.json','content':content})))]
        return NS(usage=None,choices=[NS(finish_reason='stop' if done else 'tool_calls',message=NS(content='Saved' if done else '',tool_calls=calls))])
    client=Mock();client.chat.completions.create.side_effect=create
    client.responses.create.side_effect=AssertionError('No live API')
    monkeypatch.setattr(OpenAIProvider,'create_client',lambda self:client)
    executor=AgentNodeExecutor(ExecutionContext(tool_manager=ToolManager(),function_manager=None,log_manager=MagicMock(),global_state=ctx))
    if outcome=='repair':
        assert executor.execute(node,[Message(role=MessageRole.USER,content='offline QA')])[0].text_content().endswith('QA: PASS')
        assert len(requests)==3 and not ctx['ad_qa_write_errors']
    else:
        with pytest.raises(WorkflowExecutionError,match='QA report repair limit|Unresolved QA report write rejection'):
            executor.execute(node,[Message(role=MessageRole.USER,content='offline QA')])
        assert len(requests)==(3 if outcome=='exhaust' else 2)


def table_payload(assumption='Chưa có dữ liệu (past_ad_spend=null, data_status=NO_OBSERVED_HISTORY); cần kiểm chứng.'):
    columns=HEADER.strip().split(',')
    row=dict(zip(columns,['conservative','Facebook Feed',2800000,'impressions',None,None,assumption,'NOT_ESTIMATED']))
    return json.dumps({'columns':columns,'rows':[row]},ensure_ascii=False)


def test_structured_table_preserves_observed_comma_vietnamese_quotes_and_newlines(tmp_path):
    import codecs
    ctx=state(tmp_path);text='Chưa có dữ liệu (past_ad_spend=null, data_status=NO_OBSERVED_HISTORY); "không bịa".\nKiểm lại sau.'
    with pytest.raises(CSVWriteValidationError):save(ctx,BAD)
    save(ctx,table_payload(text))
    raw=(tmp_path/'artifacts/budget_scenarios.csv').read_bytes()
    assert raw.startswith(codecs.BOM_UTF8) and raw.count(codecs.BOM_UTF8)==1
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    assert rows[0]['assumption']==text and rows[0]['metric_value']=='' and rows[0]['formula']==''
    assert rows[0]['budget_amount']=='2800000' and rows[0]['estimate_status']=='NOT_ESTIMATED'
    assert not ctx['ad_csv_write_errors']


def test_structured_append_keeps_header_once_and_inserts_missing_line_ending(tmp_path):
    import codecs
    ctx=state(tmp_path);save(ctx,GOOD.rstrip('\n'))
    save(ctx,table_payload(),mode='append')
    raw=(tmp_path/'artifacts/budget_scenarios.csv').read_bytes()
    rows=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
    assert len(rows)==3 and all(len(row)==8 for row in rows)
    assert raw.count(codecs.BOM_UTF8)==1 and rows[2][-1]=='NOT_ESTIMATED'


@pytest.mark.parametrize('fault',['missing_key','extra_key','nested','bool','nonfinite','duplicate_json','wrong_append_header'])
def test_invalid_structured_table_preserves_old_file(tmp_path,fault):
    ctx=state(tmp_path);save(ctx,GOOD);before=(tmp_path/'artifacts/budget_scenarios.csv').read_bytes()
    table=json.loads(table_payload());mode='overwrite'
    if fault=='missing_key':table['rows'][0].pop('assumption')
    elif fault=='extra_key':table['rows'][0]['typo']='extra'
    elif fault=='nested':table['rows'][0]['assumption']={'bad':'nested'}
    elif fault=='bool':table['rows'][0]['budget_amount']=True
    elif fault=='nonfinite':table['rows'][0]['budget_amount']=float('nan')
    elif fault=='wrong_append_header':table['columns'].reverse();mode='append'
    content=json.dumps(table,ensure_ascii=False)
    if fault=='duplicate_json':content=content.replace('"rows":','"rows": [], "rows":',1)
    with pytest.raises(CSVWriteValidationError):save(ctx,content,mode=mode)
    assert (tmp_path/'artifacts/budget_scenarios.csv').read_bytes()==before


def test_structured_content_does_not_change_other_workflow_file_semantics(tmp_path):
    ctx=state(tmp_path);ctx.pop('ad_csv_write_validation');content=table_payload()
    save(ctx,content)
    assert (tmp_path/'artifacts/budget_scenarios.csv').read_text(encoding='utf-8-sig')==content


def test_real_agent_repairs_csv_using_structured_content_after_rejection(tmp_path,monkeypatch):
    ctx=state(tmp_path);ctx['node_result_validator']=_validate_result
    node=Node.from_dict({'id':'Media_Planner','type':'agent','config':{'name':'offline','provider':'openai','api_key':'offline','params':{'protocol':'chat'},'retry':{'enabled':False},'tooling':[{'type':'function','config':{'tools':[{'name':'save_file'}]}}]}},path='offline.structured.csv')
    media=','.join(CSV_COLUMNS['media_plan.csv'])+'\nFacebook,primary,messages,S1,O1,100,2800000,VND,2026-12-07,2026-12-20,inbox,test\n'
    save(ctx,media,'media_plan.csv');requests=[]
    def create(**payload):
        requests.append(payload);step=len(requests)
        if step==2:assert any('JSON string with columns' in str(m.get('content')) for m in payload['messages'] if m['role']=='tool')
        calls=[] if step==3 else [NS(id='csv'+str(step),function=NS(name='save_file',arguments=json.dumps({'path':'artifacts/budget_scenarios.csv','content':BAD if step==1 else table_payload()})))]
        return NS(usage=None,choices=[NS(finish_reason='stop' if step==3 else 'tool_calls',message=NS(content='saved' if step==3 else '',tool_calls=calls))])
    client=Mock();client.chat.completions.create.side_effect=create;client.responses.create.side_effect=AssertionError('No live API')
    monkeypatch.setattr(OpenAIProvider,'create_client',lambda self:client)
    executor=AgentNodeExecutor(ExecutionContext(tool_manager=ToolManager(),function_manager=None,log_manager=MagicMock(),global_state=ctx))
    assert executor.execute(node,[Message(role=MessageRole.USER,content='offline CSV repair')])
    assert len(requests)==3 and not ctx['ad_csv_write_errors']
