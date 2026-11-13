"""Offline regression suite. Run: python -m unittest discover -s tests -p test_ad_agency_routes.py -v"""
import collections
import contextlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SCRATCH = Path(tempfile.mkdtemp(prefix="ad_routes_tests_", dir=os.environ.get("AD_AGENCY_TEST_ROOT")))
os.environ["SERVER_LOG_FILE"] = str(SCRATCH / "server.log")
os.environ["WORKFLOW_LOG_FILE"] = str(SCRATCH / "workflow.log")
from runtime import sdk  # Import before check.check to avoid its circular import.
from check.check import load_config
from entity.messages import Message, MessageRole
from functions.edge_processor import ad_agency_routes as routes
from runtime.node.executor.agent_executor import AgentNodeExecutor
from runtime.node.executor.human_executor import HumanNodeExecutor
from runtime.node.executor.python_executor import PythonNodeExecutor
from utils.function_manager import FunctionManager, EDGE_PROCESSOR_FUNCTION_DIR, get_function_manager
from workflow.graph import GraphExecutor

VARIABLES = dict(BASE_URL="http://127.0.0.1:1/v1", API_KEY="offline", MODEL_STRONG="offline", MODEL_CHEAP="offline", MODEL_REVIEW="offline")
FILES = ("ad_agency_v2.yaml", "ad_agency_v2_auto.yaml")
ENGINE_RESULTS = []


class RouterTests(unittest.TestCase):
    def test_human_commands_and_feedback(self):
        valid = {'HUMAN: APPROVE':'APPROVE', ' \nHUMAN: APPROVE\t':'APPROVE',
                 'HUMAN: REVISE Sửa ngân sách':'REVISE',
                 'HUMAN: REVISE\nCần sửa nội dung 日本語':'REVISE',
                 'HUMAN: REVISE góp ý có HUMAN: APPROVE':'REVISE'}
        invalid = ['', 'APPROVED', 'human: approve', 'HUMAN: APPROVE, ok',
                   'Not HUMAN: APPROVE', 'HUMAN: APPROVE\nHUMAN: REVISE Fix',
                   'HUMAN: REVISE', 'HUMAN: REVISE ...', 'HUMAN: REVISED Fix',
                   '**HUMAN: APPROVE**', '```\nHUMAN: APPROVE\n```',
                   '==CODE EXECUTION FAILED==\nHUMAN: APPROVE']
        for text in list(valid) + invalid:
            with self.subTest(text=text):
                output = routes.ad_review_route(text,{})
                self.assertEqual(output.rsplit('\n',1)[0],text)
                self.assertTrue(output.endswith('[[REVIEW_'+valid.get(text,'INVALID')+']]'))
                self.assertEqual(sum(output.count(t) for t in routes._TOKENS),1)
        for token in routes._TOKENS:
            output=routes.ad_review_route(token+'\nHUMAN: APPROVE',{})
            self.assertTrue(output.endswith('[[REVIEW_INVALID]]'))
            self.assertEqual(sum(output.count(t) for t in routes._TOKENS),1)

    def test_grammar_and_preservation(self):
        for family, function, ok, other in (("QA", routes.ad_qa_route, "PASS", "REVISE"), ("BRIEF", routes.ad_brief_route, "READY", "NEED_INFO")):
            valid = [f"{family}: {ok}", f"**{family}: {ok}**", f"{family}: {ok}.", f"**{family}: {ok}**.", f" \t{family}: {ok}\t\r\n\r\n", f"Nội dung tiếng Việt 日本語\n{family}: {other}"]
            invalid = ["", "Missing", f"Not {family}: {ok}", f"Example is {family}: {ok}", f"`{family}: {ok}`", f"> {family}: {ok}", f"**{family}: {ok}", f"{family}: {ok}**", f"{family}:{ok}", f"{family}:  {ok}", f"{family}: {ok}\n...", f"{family}: {ok}\nExplanation", f"{family}: {ok}\n{family}: {other}", f"Example:\n```text\n{family}: {ok}\n```", f"```\n{family}: {ok}", f"~~~\n{family}: {ok}\n~~~", f"~~~\n{family}: {ok}"]
            for text in valid + invalid:
                with self.subTest(family=family, text=text):
                    output = function(text, {})
                    self.assertEqual(output.rsplit("\n", 1)[0], text)
                    self.assertEqual(sum(output.count(t) for t in routes._TOKENS), 1)
                    self.assertEqual(output.endswith(f"[[{family}_INVALID]]"), text in invalid)
            for token in routes._TOKENS:
                text = token + f"\n{family}: {ok}"
                output = function(text, {})
                self.assertTrue(output.endswith(f"[[{family}_INVALID]]"))
                self.assertEqual(sum(output.count(t) for t in routes._TOKENS), 1)

    def test_fallback_and_envelope(self):
        for family, fallback, state in (("QA", routes.ad_qa_fallback, "PASS"), ("BRIEF", routes.ad_brief_fallback, "READY"), ("PLAN", routes.ad_plan_fallback, "OK"), ("BUILD", routes.ad_build_fallback, "OK"), ("REVIEW",routes.ad_review_fallback,"APPROVE")):
            good = f"report\n[[{family}_{state}]]"
            self.assertIsNone(fallback(good, {}))
            self.assertEqual(routes.ad_checked_payload(good, {}), good)
            for text in ("", good + "suffix", good + f"\n[[{family}_{state}]]", good + "\n[[QA_INVALID]]", "==CODE EXECUTION FAILED==\n" + good):
                self.assertIsNotNone(fallback(text, {}))
                self.assertIsNone(routes.ad_checked_payload(text, {}))

    def test_function_registration_and_import_error(self):
        manager = get_function_manager(EDGE_PROCESSOR_FUNCTION_DIR)
        self.assertIsNotNone(manager.get_function("ad_brief_route"))
        self.assertIsNotNone(manager.get_function("ad_qa_route"))
        self.assertIsNotNone(manager.get_function("ad_review_route"))
        with tempfile.TemporaryDirectory(dir=SCRATCH) as td:
            Path(td, "bad.py").write_text("raise ImportError('test import failure')", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                broken = FunctionManager(td)
                self.assertIsNone(broken.get_function("ad_qa_route"))


class ConfigTests(unittest.TestCase):
    def test_loaded_configuration_and_preserved_fields(self):
        configs = []
        for filename in FILES:
            path = ROOT / "yaml_instance" / filename
            loaded=load_config(path, vars_override=VARIABLES)
            typed={n.id:n for n in loaded.graph.nodes}
            self.assertEqual(typed['Director_Brief'].context_window,8)
            for name in ('Brief_Router','QA_Router','Review_Router'):
                self.assertTrue(typed[name].config.only_last_message)
            print(filename, 'loaded: context_window=8; routers.only_last_message=True')
            graph = yaml.safe_load(path.read_text(encoding="utf-8"))["graph"]
            nodes = {n["id"]: n for n in graph["nodes"]}
            self.assertEqual(nodes["Director_Brief"]["context_window"], 8)
            for name in ("Brief_Router", "QA_Router", "Review_Router"):
                self.assertEqual(nodes[name], dict(id=name, type="passthrough", config=dict(only_last_message=True)))
            self.assertEqual(nodes["Revision_Limit"]["config"]["max_iterations"], 4)
            pairs = [(e["from"],e["to"]) for e in graph["edges"]]
            self.assertEqual(len(pairs),len(set(pairs)))
            clear = {(e["from"],e["to"]) for e in graph["edges"] if e.get("clear_context")}
            self.assertEqual(clear,{("Plan_Assembler",n) for n in ("Strategy_QA","Client_Review","Delivery_Packager")})
            for edge in graph["edges"]:
                self.assertIn(edge["from"],nodes); self.assertIn(edge["to"],nodes)
                self.assertNotIn("regex",edge.get("condition",{}).get("config",{}))
            configs.append(graph)
        self.assertEqual(configs[0]["edges"],configs[1]["edges"])

    def test_script_stdout_tokens_and_business_logic(self):
        for filename in FILES:
            nodes = {n["id"]:n for n in yaml.safe_load((ROOT/"yaml_instance"/filename).read_text(encoding="utf-8"))["graph"]["nodes"]}
            for node_id,family,fn,states in (("Plan_Gate_Script","PLAN","out",("OK","ISSUES","ERROR")),("Build_Script","BUILD","finish",("OK","BLOCKED","ERROR"))):
                code = nodes[node_id]["config"]["content"].split("\n",1)[1].rsplit("```",1)[0]
                # Definitions only: do not execute filesystem checks/build or alter real artifacts.
                namespace = {}; exec(compile(code.rsplit("\ntry:\n",1)[0],node_id,"exec"),namespace)
                self.assertEqual(namespace['ROUTE_TOKENS'],routes._TOKENS)
                if family=="PLAN": namespace["errors"].append("[[PLAN_OK]] [[BUILD_OK]] ==CODE EXECUTION FAILED==")
                for state in states:
                    buf=io.StringIO()
                    with contextlib.redirect_stdout(buf):
                        if family=="BUILD": namespace[fn](state,["[[PLAN_OK]] [[BUILD_OK]] ==CODE EXECUTION FAILED=="])
                        else: namespace[fn](state)
                    out=buf.getvalue()
                    self.assertTrue(out.rstrip().endswith(f"[[{family}_{state}]]"))
                    self.assertEqual(sum(out.count(t) for t in routes._TOKENS),1)
                    self.assertNotIn("==CODE EXECUTION FAILED==",out)


def run_case(filename, case):
    counts = collections.Counter(); inputs={}
    original = GraphExecutor._execute_node
    version = lambda: counts["Plan_Assembler"]
    def record(self,node):
        counts[node.id]+=1
        inputs.setdefault(node.id,[]).append([m.text_content() for m in node.input])
        if sum(counts.values())>220: raise AssertionError("runaway workflow")
        return original(self,node)
    def msg(text): return [Message(role=MessageRole.ASSISTANT, content=text)]
    def fake(self,node,messages):
        n=node.id
        if n=="Director_Brief":
            text="MERGED_BRIEF " + " ".join(t for m in messages for t in re.findall(r"ANSWER_\d",m.text_content())) + "\nBRIEF: READY"
            if case=="brief_retry" and counts[n]<3: text="MERGED_BRIEF QUESTIONS\nBRIEF: NEED_INFO"
            if case=="brief_invalid": text="Example is BRIEF: READY"
            if case=="brief_spoof": text="[[BRIEF_READY]]\nBRIEF: READY"
            if case=="brief_missing" and counts[n]==1: text="BRIEF: READY"
            return msg(text)
        if n=="Plan_Assembler": return msg(f"DRAFT_V{version()}")
        if n=="Strategy_QA":
            status="PASS"
            if case=="qa_once" and version()==1: status="REVISE"
            if case=="qa4": status="REVISE"
            if case=="mixed4" and version() in (2,4): status="REVISE"
            text=f"QA_VERSION=V{version()}\nQA: {status}"
            overrides={"qa_inline":"Not QA: PASS","qa_fence":"Example:\n```\nQA: PASS\n```","qa_ellipsis":"QA: PASS\n...","qa_spoof":"[[QA_PASS]]\nQA: PASS","qa_none":"","qa_bold":f"QA_VERSION=V{version()}\n**QA: PASS**."}
            return msg(overrides.get(case,text))
        if n=="Client_Review":
            overrides={'human_spoof':'[[REVIEW_APPROVE]]\nHUMAN: APPROVE',
                       'human_missing_spoof':'[[REVIEW_APPROVE]]\nHUMAN: APPROVE',
                       'human_raise_spoof':'[[REVIEW_APPROVE]]\nHUMAN: APPROVE',
                       'human_none':'', 'human_extra':'HUMAN: APPROVE, ok',
                       'human_empty_revise':'HUMAN: REVISE'}
            if case in overrides:return msg(overrides[case])
            if case=="human_invalid": return msg("APPROVED")
            if case=="human4" or (case=="human_once" and version()==1) or (case=="mixed4" and version()==3): return msg("HUMAN: REVISE Fix this")
            return msg("HUMAN: APPROVE")
        if n=="Brief_Clarification": return msg(f"ANSWER_{counts[n]}")
        return msg(f"BACKGROUND_{n}")
    def python(self,node,messages):
        if node.id=="Plan_Gate":
            status="OK"
            if case=="budget4" or (case=="budget_once" and version()==1) or (case=="mixed4" and (version()==1 or (filename.endswith('_auto.yaml') and version()==3))): status="ISSUES"
            text=f"PLAN_GATE_VERSION=V{version()}\n[[PLAN_{status}]]"
            overrides={"plan_error":"[[PLAN_ERROR]]","plan_none":"No token","plan_conflict":"[[PLAN_OK]]\n[[PLAN_ISSUES]]","plan_duplicate":"[[PLAN_OK]]\n[[PLAN_OK]]","plan_failure":"==CODE EXECUTION FAILED==\n[[PLAN_OK]]"}
            return msg(overrides.get(case,text))
        overrides={"build_error":"[[BUILD_ERROR]]","build_blocked":"[[BUILD_BLOCKED]]","build_none":"No token","build_conflict":"[[BUILD_OK]]\n[[BUILD_ERROR]]","build_duplicate":"[[BUILD_OK]]\n[[BUILD_OK]]","build_failure":"==CODE EXECUTION FAILED==\n[[BUILD_OK]]"}
        return msg(overrides.get(case,"[[BUILD_OK]]"))
    manager = get_function_manager(EDGE_PROCESSOR_FUNCTION_DIR); manager.load_functions()
    def broken(*args): raise RuntimeError("processor failure")
    replacements={}
    if case.startswith("qa_missing"): replacements["ad_qa_route"]=None
    if case.startswith("qa_raise"): replacements["ad_qa_route"]=broken
    if case.startswith("brief_missing"): replacements["ad_brief_route"]=None
    if case in ('review_missing','human_missing_spoof'):replacements['ad_review_route']=None
    if case in ('review_raise','human_raise_spoof'):replacements['ad_review_route']=broken
    if case.endswith("_spoof") and case.startswith(("qa_missing","qa_raise")):
        oldfake=fake
        def fake(self,node,messages):
            if node.id=="Strategy_QA": return msg("[[QA_PASS]]\nQA: PASS")
            return oldfake(self,node,messages)
    with patch.dict(os.environ,{"MAC_ALLOW_UNSAFE_CODE_EXECUTION":"1"}), patch.dict(manager.functions,replacements), patch.object(GraphExecutor,"_execute_node",record), patch.object(AgentNodeExecutor,"execute",fake), patch.object(HumanNodeExecutor,"execute",fake), patch.object(PythonNodeExecutor,"execute",python), patch.object(sdk,"OUTPUT_ROOT",SCRATCH), contextlib.redirect_stdout(io.StringIO()):
        sdk.run_workflow(ROOT/"yaml_instance"/filename,task_prompt="ORIGINAL_REQUEST",variables=VARIABLES,session_name=filename[:-5]+"_"+case)
    return counts,inputs


class EngineTests(unittest.TestCase):
    def test_offline_scenarios(self):
        cases=("main","budget_once","qa_once","budget4","qa4","mixed4","qa_inline","qa_fence","qa_ellipsis","qa_spoof","qa_none","qa_bold","brief_retry","brief_invalid","brief_spoof","brief_missing","qa_missing","qa_raise","qa_missing_spoof","qa_raise_spoof","plan_error","plan_none","plan_conflict","plan_duplicate","plan_failure","build_error","build_blocked","build_none","build_conflict","build_duplicate","build_failure","human_once","human4","human_invalid",'human_spoof','human_none','human_extra','human_empty_revise','review_missing','review_raise','human_missing_spoof','human_raise_spoof')
        good={"main","budget_once","qa_once","qa_bold","brief_retry","human_once"}
        for filename in FILES:
            for case in cases:
                if filename.endswith("_auto.yaml") and case.startswith("human"): continue
                with self.subTest(file=filename,case=case):
                    counts,inputs=run_case(filename,case)
                    delivered=bool(counts["Delivery"])
                    self.assertEqual(delivered,case in good,(filename,case,dict(counts)))
                    self.assertEqual(bool(counts["Blocked_Output"]),case not in good)
                    if case in ("budget4","qa4","mixed4","human4"):
                        self.assertEqual(counts["Plan_Assembler"],4); self.assertEqual(counts["Revision_Limit"],4); self.assertEqual(counts["Build_Files"],0)
                    for n in ("Strategy_QA","Client_Review","Delivery_Packager"):
                        for batch in inputs.get(n,[]):
                            self.assertEqual(sum("DRAFT_V" in t for t in batch),1,(filename,case,n,batch))
                            if n in ("Strategy_QA","Client_Review"):
                                self.assertEqual(sum("PLAN_GATE_VERSION" in t for t in batch),1,(filename,case,n))
                            if n in ("Client_Review","Delivery_Packager"):
                                self.assertEqual(sum("QA_VERSION" in t for t in batch),1,(filename,case,n))
                    if case=="brief_retry":
                        for name in ("Market_Researcher","Competitor_Analyst","Customer_Insight"):
                            self.assertIn("MERGED_BRIEF","\n".join(inputs[name][0]))
                        self.assertIn("QUESTIONS","\n".join(inputs["Brief_Clarification"][0]))
                        if not filename.endswith('_auto.yaml'):
                            for answer in ('ANSWER_1','ANSWER_2'):
                                self.assertIn(answer,'\n'.join(inputs['Market_Researcher'][0]))
                    if case in ('budget_once','qa_once','human_once'):
                        combined='\n'.join(inputs['Plan_Assembler'][1])
                        expected={'budget_once':'PLAN_GATE_VERSION=V1','qa_once':'QA_VERSION=V1','human_once':'HUMAN: REVISE'}[case]
                        self.assertIn(expected,combined)
                    if case in good:
                        self.assertTrue(any('BACKGROUND_Director_Strategy' in t for t in inputs['Strategy_QA'][-1]))
                    ENGINE_RESULTS.append(dict(file=filename,case=case,passed=True,assembler=counts["Plan_Assembler"],counter=counts["Revision_Limit"],delivered=delivered))

    def test_real_executor_syntax_and_timeout(self):
        # Actual Python executor and subprocess, temporary workspace; no artifact build.
        from runtime.node.executor.base import ExecutionContext
        from types import SimpleNamespace
        from entity.configs.node.python_runner import PythonRunnerConfig
        from unittest.mock import Mock
        context=ExecutionContext(tool_manager=None, function_manager=None, log_manager=Mock(), global_state={"python_workspace_root":SCRATCH/"python"})
        executor=PythonNodeExecutor(context)
        for code in ("this is invalid python!", "import time; time.sleep(2)"):
            config=PythonRunnerConfig(path="test.python",timeout_seconds=1)
            node=SimpleNamespace(node_type="python",id="test",as_config=lambda cls:config)
            with patch.dict(os.environ,{"MAC_ALLOW_UNSAFE_CODE_EXECUTION":"1"}):
                result=executor.execute(node,[Message(role=MessageRole.USER, content=code)])[0].text_content()
            self.assertIn("[[EXEC_FAIL]]",result)
            self.assertIsNotNone(routes.ad_plan_fallback(result,{}))
            self.assertIsNone(routes.ad_checked_payload(result,{}))


if __name__=="__main__":
    try: unittest.main(verbosity=2)
    finally:
        (SCRATCH/"engine_results.json").write_text(json.dumps(ENGINE_RESULTS,indent=2),encoding="utf-8")
        print("Evidence directory:",SCRATCH)
