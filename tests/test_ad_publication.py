"""Final publication contracts, actual asset approval and exports; offline only."""
import copy
import json
from pathlib import Path
from unittest.mock import Mock
import pytest

from runtime import sdk
from entity.messages import Message,MessageRole
from functions.function_calling.file import save_file
from functions.edge_processor.ad_agency_contracts import _validate_result
from functions.edge_processor.ad_publication import ad_publication_release,ad_publication_build,ad_publication_start
from utils.attachments import AttachmentStore
from utils.ad_publication import validate_content,prepare_review,approve_from_plan,export_publication,read,sha,PublicationWriteValidationError,validate_publication_qa,PUBLIC_CHECKS
from utils.ad_banner import produce_banners
from test_ad_agency_audit import fixture_files,run_gate,qa_fixture,definitions,FILES
from test_ad_banner_node import image_response


def public_bundle_fixture(root,version):
    ref=[{'file':'creative_brief.md','location':'campaign concept'}]
    brief=read(root/'artifacts/campaign_brief.json')
    bundle={'schema_version':'1.0','plan_version':version,'brand_name':'Ban Công Xanh',
            'posts':[{'id':'P01','channel':'Facebook','content':'Bạn cần chăm cây ban công? Bắt đầu bằng một bức ảnh.','cta':'Nhắn tin để trao đổi phạm vi.','hashtags':['#BanCongXanh'],'banner_id':'BN01','source_refs':ref}],
            'video_scripts':[{'id':'V01','title':'Gửi ảnh ban công','duration_seconds':10,'scenes':[{'start':0,'end':10,'visual':'Minh họa người tưới cây trong ban công.','voiceover':'Gửi ảnh để trao đổi nhu cầu.','on_screen_text':'Chăm cây ban công','audio':'Nhạc nền có quyền sử dụng.'}],'source_refs':ref}],
            'banners':[{'id':'BN01','headline':'Chăm cây bắt đầu từ một bức ảnh','cta':'Nhắn tin để trao đổi phạm vi','visual_brief':'Minh họa thao tác chăm cây trên ban công căn hộ, dụng cụ nhỏ và cây chậu.','source_refs':ref},
                       {'id':'BN02','headline':'Ban công xanh, chăm sóc đúng nhu cầu','cta':'Gửi ảnh cây và khu vực','visual_brief':'Minh họa cây chậu ở ban công căn hộ, nhân vật kiểm tra lá cây.','source_refs':ref}],
            'calendar':[{'date':brief['start_date'],'channel':'Facebook','content_id':i,'owner':'Content'} for i in ('P01','V01')]}
    return bundle



def public_qa_fixture(root,version):
    return {'schema_version':'1.0','plan_version':version,'bundle_sha256':sha(Path(root)/'artifacts/publication_content.json'),
            'verdict':'PASS','checks':[{'id':key,'status':'PASS','reason':'Offline fixture: copy aligned with source and limits.',
            'source_refs':[{'file':'creative_brief.md','location':'campaign concept'}]} for key in sorted(PUBLIC_CHECKS)],'findings':[]}


def setup_bundle(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);fixture_files(tmp_path);run_gate(tmp_path)
    man=read(tmp_path/'review/review_manifest.json')
    (tmp_path/'artifacts/qa_report.json').write_text(json.dumps(qa_fixture(man['plan_version'])),encoding='utf-8')
    bundle=public_bundle_fixture(tmp_path,man['plan_version'])
    ctx={'python_workspace_root':tmp_path,'graph_directory':tmp_path.parent,'attachment_store':AttachmentStore(tmp_path/'attachments'),'ad_publication_write_validation':True}
    save_file('artifacts/publication_content.json',json.dumps(bundle,ensure_ascii=False),_context=ctx)
    monkeypatch.setenv('AD_PUBLICATION_REQUIRED','1');monkeypatch.setenv('AD_BANNER_ENABLED','1')
    monkeypatch.setenv('AD_BANNER_BASE_URL','http://127.0.0.1:1/v1');monkeypatch.setenv('AD_BANNER_API_KEY','offline')
    monkeypatch.setenv('AD_BANNER_COUNT','2');monkeypatch.setenv('AD_BANNER_REQUEST_LIMIT','2')
    (tmp_path/'artifacts/publication_qa.json').write_text(json.dumps(public_qa_fixture(tmp_path,man['plan_version'])),encoding='utf-8')
    ad_publication_start('[[REVIEW_APPROVE]]',ctx)
    return bundle,ctx


def images(tmp_path):
    client=Mock();client.post.side_effect=lambda *a,**k:image_response()
    result=produce_banners(tmp_path,client=client)
    assert client.post.call_count==2
    assert all(a['copy_mode']=='PUBLIC_REVIEW' and '[GIẢ THUYẾT]' not in a['headline'] for a in result['assets'])
    assert 'visual_brief' in client.post.call_args.kwargs['json']['prompt']
    return result


@pytest.mark.parametrize('fault',['label','placeholder','stale','unknown_banner','bad_time','out_of_range'])
def test_public_copy_rejects_internal_text_and_invalid_contract(tmp_path,monkeypatch,fault):
    bundle,ctx=setup_bundle(tmp_path,monkeypatch);bad=copy.deepcopy(bundle)
    if fault=='label':bad['posts'][0]['content']='[GIẢ THUYẾT] Chăm cây tốt hơn'
    elif fault=='placeholder':bad['banners'][0]['headline']='TODO điền thương hiệu'
    elif fault=='stale':bad['plan_version']='stale'
    elif fault=='unknown_banner':bad['posts'][0]['banner_id']='MISSING'
    elif fault=='bad_time':bad['video_scripts'][0]['scenes'][0]['start']=1
    else:bad['calendar'][0]['date']='2000-01-01'
    before=(tmp_path/'artifacts/publication_content.json').read_bytes()
    with pytest.raises(PublicationWriteValidationError):save_file('artifacts/publication_content.json',json.dumps(bad),_context=ctx)
    assert (tmp_path/'artifacts/publication_content.json').read_bytes()==before
    with pytest.raises(Exception,match='Unresolved publication'):_validate_result('Publication_Editor',Message(role=MessageRole.ASSISTANT,content='done'),ctx)


def test_complete_publication_flow_and_build_no_internal_labels_in_publish(tmp_path,monkeypatch):
    bundle,ctx=setup_bundle(tmp_path,monkeypatch)
    assert ad_publication_start('[[REVIEW_APPROVE]]',ctx)
    _validate_result('Publication_Editor',Message(role=MessageRole.ASSISTANT,content='done'),ctx)
    result=images(tmp_path)
    # The single HUMAN plan approval already recorded by start authorizes the
    # derived outputs. There is no second Human node or PUBLISH command.
    released=ad_publication_release(json.dumps(result)+'\n[[BANNER_READY]]',ctx)
    review=read(tmp_path/'internal/publication_review.json')
    assert review['release_id'] in released
    assert read(tmp_path/'internal/publication_approval.json')['approval_mode']=='PLAN_AUTHORIZATION'
    code=ad_publication_build('```python\nprint("build")\n```',ctx)
    assert ctx['ad_publication_approval_sha256'] in code
    monkeypatch.setenv('AD_PUBLICATION_APPROVAL_SHA256',ctx['ad_publication_approval_sha256'])
    space=definitions(FILES[0],'Build_Script');man,hashes,problems=space['verify']();assert not problems
    space['build'](man,hashes)
    out=tmp_path/'output'
    assert (out/'publish/posts/P01.txt').is_file() and (out/'publish/banners/BN01.png').is_file()
    assert (out/'production/video_scripts/V01.md').is_file()
    assert (out/'internal/advertising_strategy.md').is_file() and (out/'internal/qa_report.json').is_file()
    assert not (out/'qa_report.json').exists()
    pub=read(out/'internal/publication_manifest.json');assert pub['status']=='APPROVED_FOR_PUBLICATION'
    for name,d in pub['files'].items():assert sha(out/name)==d
    for path in (out/'publish').rglob('*.txt'):
        text=path.read_text(encoding='utf-8');assert '[GIẢ THUYẾT]' not in text and 'artifacts/' not in text
    exported=read(out/'manifest.json')
    for row in exported['delivered_files']+exported['generated_files']:assert sha(out/row['name'])==row['sha256']


@pytest.mark.parametrize('tamper',['copy','banner','approval','review','plan'])
def test_publication_fails_closed_on_post_review_changes(tmp_path,monkeypatch,tamper):
    _,ctx=setup_bundle(tmp_path,monkeypatch);images(tmp_path);review=prepare_review(tmp_path)
    seal=approve_from_plan(tmp_path,ctx['ad_publication_authorization'])
    if tamper=='copy':(tmp_path/review['preview_files'][0]).write_text('Changed')
    elif tamper=='banner':(tmp_path/'artifacts'/review['banner_assets'][0]['path']).write_bytes(b'Changed')
    elif tamper=='approval':(tmp_path/'internal/publication_approval.json').write_text('{}')
    elif tamper=='review':(tmp_path/'internal/publication_review.json').write_text('{}')
    else:(tmp_path/'artifacts/campaign_brief.json').write_text('{}')
    out=tmp_path/'export';out.mkdir()
    with pytest.raises((ValueError,KeyError)):export_publication(tmp_path,out,review['plan_version'],seal)
    assert not (out/'publish').exists()


def test_missing_trusted_human_seal_cannot_be_forged_by_file_write(tmp_path,monkeypatch):
    setup_bundle(tmp_path,monkeypatch)
    with pytest.raises(Exception,match='Missing trusted Human'):ad_publication_build('```python\npass\n```',{'python_workspace_root':tmp_path})


def test_disabled_images_are_explicit_and_never_fabricated(tmp_path,monkeypatch):
    _,ctx=setup_bundle(tmp_path,monkeypatch);monkeypatch.setenv('AD_BANNER_ENABLED','0');client=Mock()
    result=produce_banners(tmp_path,client=client);client.post.assert_not_called()
    review=prepare_review(tmp_path);assert review['images_enabled'] is False
    seal=approve_from_plan(tmp_path,ctx['ad_publication_authorization'])
    out=tmp_path/'export';out.mkdir();export_publication(tmp_path,out,review['plan_version'],seal)
    assert not (out/'publish/banners').exists()
    assert read(out/'internal/publication_manifest.json')['images_enabled'] is False


def test_actual_publication_banner_subprocess_disabled_without_paid_calls(tmp_path,monkeypatch):
    import yaml
    from unittest.mock import MagicMock
    from entity.configs import Node
    from runtime.node.executor.base import ExecutionContext
    from runtime.node.executor.python_executor import PythonNodeExecutor
    from functions.edge_processor.ad_publication import ad_publication_banner_script
    bundle,ctx=setup_bundle(tmp_path,monkeypatch);monkeypatch.setenv('AD_BANNER_ENABLED','0');monkeypatch.setenv('MAC_ALLOW_UNSAFE_CODE_EXECUTION','1')
    ad_publication_start('[[REVIEW_APPROVE]]',ctx)
    code=ad_publication_banner_script('saved',ctx)
    from test_ad_agency_audit import ROOT
    graph=yaml.safe_load((ROOT/'yaml_instance/ad_agency_v2.yaml').read_text(encoding='utf-8'))['graph']
    config=next(n for n in graph['nodes'] if n['id']=='Banner_Producer')
    node=Node.from_dict(config,path='offline.publication.banner')
    result=PythonNodeExecutor(ExecutionContext(tool_manager=None,function_manager=None,log_manager=MagicMock(),global_state=ctx)).execute(node,[Message(role=MessageRole.USER,content=code)])
    assert result[0].text_content().strip().endswith('[[BANNER_READY]]')
    review=prepare_review(tmp_path);assert not review['images_enabled']


def test_no_final_release_without_matching_plan_authorization(tmp_path,monkeypatch):
    _,ctx=setup_bundle(tmp_path,monkeypatch);result=images(tmp_path)
    ctx.pop('ad_publication_authorization')
    with pytest.raises(ValueError,match='Missing Human plan authorization'):
        ad_publication_release(json.dumps(result)+'\n[[BANNER_READY]]',ctx)
    assert not (tmp_path/'internal/publication_approval.json').exists()


def test_main_and_auto_have_only_one_human_approval_for_publication():
    import yaml
    from test_ad_agency_audit import ROOT
    for filename in FILES:
        graph=yaml.safe_load((ROOT/'yaml_instance'/filename).read_text(encoding='utf-8'))['graph']
        nodes={n['id']:n for n in graph['nodes']}
        assert 'Publication_Review' not in nodes and nodes['Client_Review']['type']=='human'
        assert any(e['from']=='Banner_Producer' and e['to']=='Delivery_Packager' and e['process']['config']['name']=='ad_publication_release' for e in graph['edges'])


def test_copy_change_during_export_is_not_silently_approved(tmp_path,monkeypatch):
    import shutil
    _,ctx=setup_bundle(tmp_path,monkeypatch);images(tmp_path);review=prepare_review(tmp_path)
    seal=approve_from_plan(tmp_path,ctx['ad_publication_authorization'])
    source=tmp_path/review['preview_files'][0];copyfile=shutil.copyfile
    def changed_copy(src,dst,*args,**kwargs):
        if Path(src)==source:source.write_text('Changed during copying')
        return copyfile(src,dst,*args,**kwargs)
    monkeypatch.setattr(shutil,'copyfile',changed_copy)
    out=tmp_path/'export';out.mkdir()
    with pytest.raises(ValueError,match='changed while exporting'):
        export_publication(tmp_path,out,review['plan_version'],seal)


def test_publication_qa_rejects_stale_content_and_blocks_image_generation(tmp_path,monkeypatch):
    from functions.edge_processor.ad_publication import ad_publication_qa_to_banner,ad_publication_qa_blocked,ad_publication_qa_input
    bundle,ctx=setup_bundle(tmp_path,monkeypatch)
    assert sha(tmp_path/'artifacts/publication_content.json') in ad_publication_qa_input('saved',ctx)
    report=public_qa_fixture(tmp_path,bundle['plan_version']);report['verdict']='BLOCKED';report['checks'][0]['status']='FAIL';report['findings']=['Remove unsupported price claim']
    save_file('artifacts/publication_qa.json',json.dumps(report),_context=ctx)
    assert ad_publication_qa_to_banner('audit complete',ctx) is None
    assert 'unsupported price' in ad_publication_qa_blocked('audit complete',ctx)
    report['bundle_sha256']='stale'
    with pytest.raises(PublicationWriteValidationError,match='content hash mismatch'):
        save_file('artifacts/publication_qa.json',json.dumps(report),_context=ctx)
    assert not (tmp_path/'internal/banner_manifest.json').exists()


@pytest.mark.parametrize('fault',['plan_schema','invented_ids','criterion_key'])
def test_observed_publication_qa_schema_errors_return_exact_repair_template(tmp_path,monkeypatch,fault):
    from utils.ad_publication import publication_qa_template
    _,ctx=setup_bundle(tmp_path,monkeypatch);good=read(tmp_path/'artifacts/publication_qa.json');bad=copy.deepcopy(good)
    if fault=='plan_schema':
        bad['criteria_results']=bad.pop('checks');bad['issues']=bad.pop('findings')
    elif fault=='invented_ids':
        for check,name in zip(bad['checks'],['CLAIM_CHECK','PRICE_CHECK','OFFER_CHECK','CTA_CHECK','COMPLETENESS_CHECK','CALENDAR_CHECK','SCRIPT_CHECK','VISUAL_BRIEF_CHECK']):check['id']=name
    else:
        for check in bad['checks']:check['criterion_id']=check.pop('id')
    before=(tmp_path/'artifacts/publication_qa.json').read_bytes()
    with pytest.raises(PublicationWriteValidationError) as error:
        save_file('artifacts/publication_qa.json',json.dumps(bad),_context=ctx)
    detail=str(error.value)
    assert all(key in detail for key in PUBLIC_CHECKS)
    assert 'checks' in detail and 'source_refs' in detail and good['bundle_sha256'] in detail
    assert (tmp_path/'artifacts/publication_qa.json').read_bytes()==before
    template=publication_qa_template(tmp_path)
    assert {c['id'] for c in template['checks']}==PUBLIC_CHECKS
    with pytest.raises(ValueError):validate_publication_qa(tmp_path,json.dumps(template).encode())


def test_publication_qa_has_a_dedicated_skill_without_plan_schema():
    import yaml
    from test_ad_agency_audit import ROOT
    for filename in FILES:
        graph=yaml.safe_load((ROOT/'yaml_instance'/filename).read_text(encoding='utf-8'))['graph']
        qa=next(n for n in graph['nodes'] if n['id']=='Publication_QA')
        assert qa['config']['skills']['allow']==['ad-publication-quality-review']


def test_real_publication_qa_agent_can_repair_observed_schema_from_tool_error(tmp_path,monkeypatch):
    from types import SimpleNamespace as NS
    from unittest.mock import MagicMock
    from entity.configs import Node
    from runtime.node.agent.providers.openai_provider import OpenAIProvider
    from runtime.node.agent.tool.tool_manager import ToolManager
    from runtime.node.executor.agent_executor import AgentNodeExecutor
    from runtime.node.executor.base import ExecutionContext
    _,ctx=setup_bundle(tmp_path,monkeypatch);ctx['node_result_validator']=_validate_result
    good=read(tmp_path/'artifacts/publication_qa.json');bad=copy.deepcopy(good);bad['criteria_results']=bad.pop('checks');bad['issues']=bad.pop('findings')
    node=Node.from_dict({'id':'Publication_QA','type':'agent','config':{'name':'offline','provider':'openai','api_key':'offline',
        'params':{'protocol':'chat'},'retry':{'enabled':False},'tooling':[{'type':'function','config':{'tools':[{'name':'save_file'}]}}]}},path='offline.publication.qa')
    requests=[]
    def create(**payload):
        requests.append(payload);step=len(requests)
        if step==2:
            errors=[str(m.get('content')) for m in payload['messages'] if m['role']=='tool']
            assert any('criteria_results' in text and 'FACTS' in text and good['bundle_sha256'] in text for text in errors)
        calls=[] if step==3 else [NS(id='pqa'+str(step),function=NS(name='save_file',arguments=json.dumps({'path':'artifacts/publication_qa.json','content':json.dumps(bad if step==1 else good)})))]
        return NS(usage=None,choices=[NS(finish_reason='stop' if step==3 else 'tool_calls',message=NS(content='done' if step==3 else '',tool_calls=calls))])
    client=Mock();client.chat.completions.create.side_effect=create;client.responses.create.side_effect=AssertionError('No live requests')
    monkeypatch.setattr(OpenAIProvider,'create_client',lambda self:client)
    result=AgentNodeExecutor(ExecutionContext(tool_manager=ToolManager(),function_manager=None,log_manager=MagicMock(),global_state=ctx)).execute(node,[Message(role=MessageRole.USER,content='audit')])
    assert len(requests)==3 and not ctx['ad_publication_write_errors'] and 'Public content QA: PASS' in result[0].text_content()
