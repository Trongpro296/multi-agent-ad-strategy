"""Publication-only recovery preserves source bytes and never calls upstream Agents."""
import hashlib
import json
from pathlib import Path
import pytest
import yaml
from runtime import sdk
from entity.messages import Message,MessageRole
from runtime.node.executor.agent_executor import AgentNodeExecutor
from runtime.node.executor.human_executor import HumanNodeExecutor
from tools.prepare_publication_recovery import build_publication_recovery
from test_ad_publication import setup_bundle,public_qa_fixture
from test_ad_agency_audit import ROOT
from test_ad_agency_routes import VARIABLES


def test_publication_only_recovery_skips_planning_and_editor(tmp_path,monkeypatch):
    source=tmp_path/'source';source.mkdir();bundle,_=setup_bundle(source,monkeypatch)
    before={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
    doc,meta=build_publication_recovery(yaml.safe_load((ROOT/'yaml_instance/ad_agency_v2.yaml').read_text(encoding='utf-8')),source,'offline_publication')
    path=tmp_path/'recovery.yaml';path.write_text(yaml.safe_dump(doc,allow_unicode=True),encoding='utf-8')
    assert meta['pending_agents']==['Publication_QA','Delivery_Packager'] and len(meta['restored_files'])==39
    executed=[]
    def fake_agent(executor,node,messages):
        executed.append(node.id);root=Path(executor.context.global_state['python_workspace_root'])
        if node.id=='Publication_QA':
            template='\n'.join(m.text_content() for m in messages)
            assert 'checks' in template and 'FACTS' in template
            (root/'artifacts/publication_qa.json').write_text(json.dumps(public_qa_fixture(root,bundle['plan_version'])),encoding='utf-8')
        elif node.id=='Delivery_Packager':(root/'artifacts/handoff_notes.md').write_text('Offline publication recovery only',encoding='utf-8')
        else:raise AssertionError('Upstream agent must not run: '+node.id)
        return [Message(role=MessageRole.ASSISTANT,content='saved')]
    monkeypatch.setenv('MAC_ALLOW_UNSAFE_CODE_EXECUTION','1');monkeypatch.setenv('AD_BANNER_ENABLED','0')
    monkeypatch.setattr(AgentNodeExecutor,'execute',fake_agent)
    humans=[]
    def human(executor,node,messages):
        humans.append(node.id);return [Message(role=MessageRole.USER,content='HUMAN: APPROVE')]
    monkeypatch.setattr(HumanNodeExecutor,'execute',human);monkeypatch.setattr(sdk,'OUTPUT_ROOT',tmp_path/'runs')
    result=sdk.run_workflow(path,task_prompt='Resume final QA',variables=VARIABLES,session_name='session_publication_recovery_test')
    assert executed==['Publication_QA','Delivery_Packager'] and humans==['Client_Review']
    root=result.meta_info.output_dir/'code_workspace'
    assert (root/'output/publish/posts/P01.txt').is_file()
    assert before=={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}


def test_publication_recovery_rejects_changed_plan(tmp_path,monkeypatch):
    setup_bundle(tmp_path,monkeypatch);(tmp_path/'artifacts/media_plan.csv').write_text('changed')
    with pytest.raises(ValueError,match='Plan source changed'):
        build_publication_recovery(yaml.safe_load((ROOT/'yaml_instance/ad_agency_v2.yaml').read_text(encoding='utf-8')),tmp_path,'changed')
