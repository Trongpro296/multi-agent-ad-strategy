"""Short execution marker routing and compatibility with older saved graphs."""
import contextlib
import io
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from runtime import sdk
from entity.configs.edge.edge_condition import KeywordEdgeConditionConfig
from entity.configs.node.python_runner import PythonRunnerConfig
from entity.messages import Message,MessageRole
from functions.edge.conditions import code_pass,code_fail
from functions.edge_processor import ad_agency_routes as routes
from runtime.edge.conditions.base import ConditionFactoryContext
from runtime.edge.conditions.keyword_manager import KeywordEdgeConditionManager
from runtime.node.executor.base import ExecutionContext
from runtime.node.executor.python_executor import PythonNodeExecutor
from utils.execution_markers import EXEC_FAILURE,LEGACY_EXEC_FAILURE

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('configured',[EXEC_FAILURE,LEGACY_EXEC_FAILURE])
@pytest.mark.parametrize('received',[EXEC_FAILURE,LEGACY_EXEC_FAILURE])
@pytest.mark.parametrize('case_sensitive',[True,False])
def test_keyword_aliases_keep_metadata_short_and_route_old_and_new(configured,received,case_sensitive):
    context=ExecutionContext(tool_manager=None,function_manager=None,log_manager=Mock())
    config=KeywordEdgeConditionConfig.from_dict({'any':['[[PLAN_OK]]'],'none':[configured],'case_sensitive':case_sensitive},path='test')
    condition=KeywordEdgeConditionManager(config,ConditionFactoryContext(),context)
    assert condition.metadata['none']==[configured]
    assert not condition._evaluate(received+'\n[[PLAN_OK]]')
    if not case_sensitive:assert not condition._evaluate(received.lower()+'\n[[PLAN_OK]]')
    plain='Test cũ: FAIL, đã sửa và kiểm lại.\n[[PLAN_OK]]'
    assert condition._evaluate(plain)
    assert routes.ad_checked_payload(plain,{})==plain
    assert routes.ad_plan_fallback(plain,{}) is None


@pytest.mark.parametrize('marker',[EXEC_FAILURE,LEGACY_EXEC_FAILURE])
def test_functions_and_routers_reject_failure_even_with_success_token(marker):
    assert code_fail(marker) and not code_pass(marker)
    assert code_pass('FAIL is a report word, not an execution marker')
    for family,state,fallback in [('PLAN','OK',routes.ad_plan_fallback),('BUILD','OK',routes.ad_build_fallback),('QA','PASS',routes.ad_qa_fallback)]:
        text=marker+'\n[['+family+'_'+state+']]'
        assert routes.ad_checked_payload(text,{}) is None
        assert fallback(text,{}) is not None
    assert routes.ad_qa_route(marker+'\nQA: PASS',{}).endswith('[[QA_INVALID]]')


@pytest.mark.parametrize('filename',['ad_agency_v2.yaml','ad_agency_v2_auto.yaml','ad_agency_recovery_960ee949.yaml','ad_agency_recovery_960ee949_openai.yaml'])
def test_all_campaign_edges_are_short_and_script_diagnostics_escape_both(filename):
    graph=yaml.safe_load((ROOT/'yaml_instance'/filename).read_text(encoding='utf-8'))['graph']
    for edge in graph['edges']:
        condition=edge.get('condition') or {}
        if not isinstance(condition,dict):continue
        config=condition.get('config') or {}
        assert LEGACY_EXEC_FAILURE not in config.get('any',[])+config.get('none',[])
    nodes={n['id']:n for n in graph['nodes']}
    for name,fn,family in [('Plan_Gate_Script','out','PLAN'),('Build_Script','finish','BUILD')]:
        code=nodes[name]['config']['content'].split('\n',1)[1].rsplit('```',1)[0]
        namespace={};exec(compile(code.rsplit('\ntry:\n',1)[0],name,'exec'),namespace)
        text=EXEC_FAILURE+' '+LEGACY_EXEC_FAILURE+' [[PLAN_OK]]'
        if family=='PLAN':namespace['errors'].append(text)
        result=io.StringIO()
        with contextlib.redirect_stdout(result):
            if family=='PLAN':namespace[fn]('ERROR')
            else:namespace[fn]('ERROR',[text])
        assert EXEC_FAILURE not in result.getvalue() and LEGACY_EXEC_FAILURE not in result.getvalue()
        assert result.getvalue().rstrip().endswith('[['+family+'_ERROR]]')


def test_real_python_errors_emit_short_marker(tmp_path,monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setenv('MAC_ALLOW_UNSAFE_CODE_EXECUTION','1')
    context=ExecutionContext(tool_manager=None,function_manager=None,log_manager=Mock(),global_state={'python_workspace_root':tmp_path})
    config=PythonRunnerConfig(path='test')
    node=SimpleNamespace(id='Failure',node_type='python',as_config=lambda _:config)
    result=PythonNodeExecutor(context).execute(node,[Message(role=MessageRole.USER,content="raise RuntimeError('offline failure')")])[0]
    assert result.text_content().startswith(EXEC_FAILURE+'\n')
    assert LEGACY_EXEC_FAILURE not in result.text_content()


@pytest.mark.parametrize('configured',[EXEC_FAILURE,LEGACY_EXEC_FAILURE])
@pytest.mark.parametrize('payload',[EXEC_FAILURE+'\n[[PLAN_OK]]',LEGACY_EXEC_FAILURE+'\n[[PLAN_OK]]','Test cũ FAIL đã sửa\n[[PLAN_OK]]'])
def test_real_graph_selects_exactly_one_branch(tmp_path,monkeypatch,configured,payload):
    from workflow.graph import GraphExecutor
    doc={'version':'0.4.0','graph':{'id':'marker_test','start':['Source'],'end':['Success','Blocked'],
        'nodes':[{'id':name,'type':'literal','config':{'content':text}} for name,text in [('Source',payload),('Success','delivered'),('Blocked','blocked')]],
        'edges':[{'from':'Source','to':'Success','condition':{'type':'keyword','config':{'any':['[[PLAN_OK]]'],'none':[configured]}}},
                 {'from':'Source','to':'Blocked','process':{'type':'function','config':{'name':'ad_plan_fallback'}}}]}}
    path=tmp_path/'graph.yaml';path.write_text(yaml.safe_dump(doc),encoding='utf-8')
    monkeypatch.setattr(sdk,'OUTPUT_ROOT',tmp_path/'runs')
    original=GraphExecutor._execute_node;executed=[]
    def track(self,node):executed.append(node.id);return original(self,node)
    monkeypatch.setattr(GraphExecutor,'_execute_node',track)
    sdk.run_workflow(path,task_prompt='offline',session_name='session_marker_test')
    failed=payload.startswith((EXEC_FAILURE,LEGACY_EXEC_FAILURE))
    assert ('Blocked' in executed)==failed
    assert ('Success' in executed)==(not failed)
