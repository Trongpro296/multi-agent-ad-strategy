"""Readable derived exports and conservative prompt compaction, entirely offline."""
import csv
import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from openpyxl import load_workbook
from pptx import Presentation

from runtime import sdk
from entity.configs import Node
from entity.messages import Message, MessageRole, ToolCallPayload, MessageBlock, MessageBlockType
from runtime.node.executor.agent_executor import AgentNodeExecutor
from runtime.node.executor.base import ExecutionContext
from test_ad_agency_audit import FILES, definitions, fixture_files, qa_fixture, run_gate
from tools.compare_ad_runs import compare_runs
from utils.ad_context import optimize_ad_inputs
from utils.token_tracker import TokenTracker, TokenUsage


def export_fixture(root, monkeypatch, filename=FILES[0], plan=None):
    monkeypatch.chdir(root);fixture_files(root)
    if plan:(root/'artifacts/advertising_strategy_draft.md').write_text(plan,encoding='utf-8')
    assert run_gate(root,filename).rstrip().endswith('[[PLAN_OK]]')
    man=json.loads((root/'review/review_manifest.json').read_text());qa=qa_fixture(man['plan_version'])
    (root/'artifacts/qa_report.json').write_text(json.dumps(qa))
    build=definitions(filename,'Build_Script');approved,hashes,problems=build['verify']();assert not problems
    build['build'](approved,hashes)
    return root/'output',qa


@pytest.mark.parametrize('filename',FILES)
def test_styled_workbook_and_blank_operating_templates(tmp_path,monkeypatch,filename):
    out,qa=export_fixture(tmp_path,monkeypatch,filename)
    wb=load_workbook(out/'Campaign_Plan.xlsx')
    assert len(wb.sheetnames)==10 and wb.sheetnames[0]=='Overview'
    for ws in wb:
        assert ws.freeze_panes=='A2' and ws.auto_filter.ref and ws['A1'].font.bold
        assert ws['A1'].fill.fgColor.rgb=='0017324D'
    assert wb['Media_Plan']['G2'].value==100 and wb['Media_Plan']['G2'].data_type=='n'
    assert wb['Media_Plan']['F2'].value==100 and '%' in wb['Media_Plan']['F2'].number_format
    assert wb['Media_Plan']['I2'].number_format=='yyyy-mm-dd'
    assert wb['Experiments']['F2'].value==30
    assert wb['Overview']['B4'].value=='CONDITIONAL'
    for name in ('visit_log_template.csv','daily_report_template.csv'):
        assert (out/name).read_bytes().startswith(b'\xef\xbb\xbf')
        with (out/name).open(encoding='utf-8-sig',newline='') as stream:
            reader=csv.DictReader(stream);assert reader.fieldnames and list(reader)==[]
    with (out/'prelaunch_checklist.csv').open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
    assert len(rows)==5 and {r['status'] for r in rows}=={'PENDING'}
    assert len(wb['Visit_Log'].data_validations.dataValidation)==1
    assert len(list(out.iterdir()))==26
    manifest=json.loads((out/'manifest.json').read_text())
    assert len(manifest['generated_files'])==5 and len(manifest['operating_templates'])==3
    for record in manifest['delivered_files']+manifest['generated_files']:
        assert hashlib.sha256((out/record['name']).read_bytes()).hexdigest()==record['sha256']


def test_presentation_native_tables_and_pagination_preserve_end_of_long_content(tmp_path,monkeypatch):
    paragraph=' '.join('Nội dung tiếng Việt số '+str(i) for i in range(350))+' LAST_SENTENCE_KEPT'
    long_cell=' '.join('Mô tả chi tiết '+str(i) for i in range(100))+' LAST_TABLE_CELL_KEPT'
    plan='# Kế hoạch Mây\n\n## Quyết định\n'+paragraph+'\n\n## Ngân sách\n| Kênh | Nội dung |\n|---|---|\n| Facebook | '+long_cell+' |\n'
    out,_=export_fixture(tmp_path,monkeypatch,plan=plan)
    prs=Presentation(out/'Campaign_Presentation.pptx')
    texts=[];tables=0
    for slide in prs.slides:
        for shape in slide.shapes:
            assert shape.left>=0 and shape.top>=0 and shape.left+shape.width<=prs.slide_width+1 and shape.top+shape.height<=prs.slide_height+1
            if shape.has_text_frame:texts.append(shape.text)
            if shape.has_table:
                tables+=1;texts.extend(c.text for row in shape.table.rows for c in row.cells)
    combined=' '.join(texts)
    assert 'LAST_SENTENCE_KEPT' in combined and 'LAST_TABLE_CELL_KEPT' in combined
    assert '|---|' not in combined and tables>1 and len(prs.slides)>4
    assert 'CONDITIONAL' in combined


def messages_fixture(root):
    (root/'artifacts').mkdir()
    body='# Research\n'+'Verified stored text. '*100
    file=root/'artifacts/market_research.md';file.write_text(body)
    state={'python_workspace_root':root,'ad_context_policy':'file_first_v1',
           'ad_artifact_receipts':{'Market_Researcher':{'market_research.md':hashlib.sha256(file.read_bytes()).hexdigest()}}}
    msg=Message(role=MessageRole.ASSISTANT,content='Important limitation: no external evidence.\n```markdown\n'+body+'\n```\nDo not launch before approval.',metadata={'source':'Market_Researcher','version':'v1'})
    return state,msg,file


def test_compaction_replaces_only_verified_verbatim_body_and_keeps_warnings(tmp_path):
    state,msg,file=messages_fixture(tmp_path)
    original=msg.text_content()
    compact,stats=optimize_ad_inputs([msg,msg.clone()],state,'Brand_Strategist')
    assert len(compact)==1 and stats['duplicate_handoffs_removed']==1 and stats['verbatim_artifacts_replaced']==1
    assert stats['input_characters_after']<stats['input_characters_before']/2
    assert 'Important limitation' in compact[0].text_content() and 'Do not launch' in compact[0].text_content()
    assert 'artifacts/market_research.md' in compact[0].text_content() and msg.text_content()==original


@pytest.mark.parametrize('change',['file_changed','missing_file','policy_off','different_body','different_revision'])
def test_compaction_falls_back_without_hiding_changed_or_unknown_sources(tmp_path,change):
    state,msg,file=messages_fixture(tmp_path)
    if change=='file_changed':file.write_text('new source')
    elif change=='missing_file':file.unlink()
    elif change=='policy_off':state.pop('ad_context_policy')
    elif change=='different_body':msg=msg.with_content(msg.text_content().replace('Verified','Different'))
    if change=='different_revision':
        other=msg.clone();other.metadata['version']='v2'
        compact,stats=optimize_ad_inputs([msg,other],state,'Brand_Strategist')
        assert len(compact)==2
    else:
        compact,stats=optimize_ad_inputs([msg],state,'Brand_Strategist')
        assert compact[0].text_content()==msg.text_content()


def test_unreadable_file_keeps_original_handoff(tmp_path, monkeypatch):
    state, msg, file = messages_fixture(tmp_path)
    def denied(path):
        raise PermissionError('offline permission fixture')
    monkeypatch.setattr(Path, 'read_bytes', denied)
    compact, stats = optimize_ad_inputs([msg], state, 'Brand_Strategist')
    assert compact[0].text_content() == msg.text_content()
    assert stats['verbatim_artifacts_replaced'] == 0


def test_questions_decisions_and_tool_call_pairs_are_never_compacted(tmp_path):
    state,msg,file=messages_fixture(tmp_path)
    items=[Message(role=MessageRole.USER,content='HUMAN: REVISE Fix tracking',metadata={'source':'Client_Review'}),
           Message(role=MessageRole.ASSISTANT,content='BRIEF: NEED_INFO',metadata={'source':'Director_Brief'}),
           Message(role=MessageRole.ASSISTANT,content='QA: REVISE',metadata={'source':'Strategy_QA'}),
           Message(role=MessageRole.ASSISTANT,content='',tool_calls=[ToolCallPayload(id='t1',function_name='load_file',arguments='{}')],metadata={'source':'Market_Researcher'}),
           Message(role=MessageRole.TOOL,content=msg.text_content(),tool_call_id='t1',metadata={'source':'Market_Researcher'})]
    compact,stats=optimize_ad_inputs(items,state,'Plan_Assembler')
    assert [m.to_dict() for m in compact]==[m.to_dict() for m in items]
    assert not stats['duplicate_handoffs_removed'] and not stats['verbatim_artifacts_replaced']


def test_real_executor_records_character_metrics_separately_from_reported_tokens(tmp_path):
    state,msg,file=messages_fixture(tmp_path);tracker=TokenTracker('offline')
    context=ExecutionContext(tool_manager=None,function_manager=None,log_manager=MagicMock(),global_state=state,token_tracker=tracker)
    node=Node.from_dict({'id':'Brand_Strategist','type':'agent','config':{'provider':'openai','name':'offline','api_key':'offline','role':'Keep all original constraints.'}},path='offline')
    conversation=AgentNodeExecutor(context)._prepare_message_conversation(node,[msg],None)
    assert 'Keep all original constraints.' in conversation[0].text_content()
    tracker.record_usage('Brand_Strategist','offline',TokenUsage(input_tokens=100,output_tokens=20,total_tokens=120))
    data=tracker.get_token_usage()
    assert data['total_usage']['total_tokens']==120 and data['model_call_count']==1
    assert data['context_optimizations'][0]['verbatim_artifacts_replaced']==1


def test_run_comparison_handles_zero_baseline_and_does_not_claim_cost_savings():
    before={'total_usage':dict(input_tokens=0,output_tokens=0,total_tokens=0),'call_history':[],'model_usages':{}}
    after={'total_usage':dict(input_tokens=20,output_tokens=5,total_tokens=25),'call_history':[{}],'model_usages':{'other':{}}}
    result=compare_runs(before,after)
    assert result['totals']['total_tokens']['change_pct'] is None and result['models_changed']
    assert result['model_calls']=={'before':0,'after':1} and 'not a price estimate' in result['limits']
