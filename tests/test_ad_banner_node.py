"""Banner node API contract, bounded requests and delivery integrity; offline only."""
import base64
import hashlib
import io
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock

import httpx
from PIL import Image
import pytest
import yaml

from runtime import sdk
from entity.configs import Node
from entity.messages import Message, MessageRole
from functions.edge_processor.ad_banners import ad_banner_script, ad_banner_result, ad_banner_fallback
from runtime.node.executor.base import ExecutionContext
from runtime.node.executor.python_executor import PythonNodeExecutor
from test_ad_agency_audit import FILES, fixture_files, run_gate, definitions, qa_fixture
from utils.ad_banner import produce_banners, attach_banner_assets

ROOT=Path(__file__).resolve().parents[1]


def prepared(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    fixture_files(tmp_path)
    assert run_gate(tmp_path,FILES[0]).rstrip().endswith('[[PLAN_OK]]')
    man=json.loads((tmp_path/'review/review_manifest.json').read_text())
    monkeypatch.setenv('AD_BANNER_ENABLED','1')
    monkeypatch.setenv('AD_BANNER_MODEL','ag/gemini-3.1-flash-image')
    monkeypatch.setenv('AD_BANNER_BASE_URL','http://127.0.0.1:20128/v1')
    monkeypatch.setenv('AD_BANNER_API_KEY','DO_NOT_LOG_THIS_KEY')
    monkeypatch.setenv('AD_BANNER_COUNT','2')
    monkeypatch.setenv('AD_BANNER_REQUEST_LIMIT','2')
    return man


def image_response():
    data=io.BytesIO();Image.new('RGB',(1024,1024),'#dbeafe').save(data,format='PNG')
    return httpx.Response(200,json={'data':[{'b64_json':base64.b64encode(data.getvalue()).decode()}]})


def test_two_images_saved_as_real_png_and_no_repeated_paid_calls(tmp_path,monkeypatch):
    man=prepared(tmp_path,monkeypatch);client=Mock();client.post.side_effect=lambda *a,**k:image_response()
    result=produce_banners(tmp_path,client=client)
    assert result['status']=='CREATED' and len(result['assets'])==2 and client.post.call_count==2
    for call in client.post.call_args_list:
        assert call.args[0]=='http://127.0.0.1:20128/v1/images/generations'
        assert call.kwargs['json']['model']=='ag/gemini-3.1-flash-image'
        assert call.kwargs['json']['response_format']=='b64_json' and call.kwargs['json']['n']==1
    for asset in result['assets']:
        p=tmp_path/'artifacts'/asset['path']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==asset['sha256']
        assert asset['status']=='DRAFT' and asset['visual_review']=='PENDING'
        with Image.open(p) as img:assert img.format=='PNG' and img.size==(1024,1024)
    assert produce_banners(tmp_path,client=client)==result and client.post.call_count==2
    assert 'DO_NOT_LOG_THIS_KEY' not in (tmp_path/'internal/banner_manifest.json').read_text()
    assert json.loads((tmp_path/'internal/banner_request_ledger.json').read_text())['requests_reserved']==2


def test_disabled_does_not_create_client_or_images(tmp_path,monkeypatch):
    man=prepared(tmp_path,monkeypatch);monkeypatch.setenv('AD_BANNER_ENABLED','0')
    client=Mock();result=produce_banners(tmp_path,client=client)
    assert result['status']=='DISABLED' and not result['assets'];client.post.assert_not_called()
    out=tmp_path/'export';out.mkdir()
    assert attach_banner_assets(tmp_path,out,man['plan_version'])==[]


@pytest.mark.parametrize('failure',['http','url_only','invalid_base64','not_image','too_many'])
def test_bad_responses_never_create_success_manifest_or_repeat_requests(tmp_path,monkeypatch,failure):
    prepared(tmp_path,monkeypatch);client=Mock()
    responses={'http':httpx.Response(429,json={'error':'sensitive upstream details'}),
        'url_only':httpx.Response(200,json={'data':[{'url':'https://example.com/not-downloaded.png'}]}),
        'invalid_base64':httpx.Response(200,json={'data':[{'b64_json':'!invalid!'}]}),
        'not_image':httpx.Response(200,json={'data':[{'b64_json':base64.b64encode(b'not an image').decode()}]}),
        'too_many':httpx.Response(200,json={'data':[{},{}]})}
    client.post.return_value=responses[failure]
    with pytest.raises(Exception):produce_banners(tmp_path,client=client)
    assert client.post.call_count==1
    assert json.loads((tmp_path/'internal/banner_manifest.json').read_text())['status']=='IN_PROGRESS'
    # Only one request remains, insufficient for a whole two-banner set.
    with pytest.raises(ValueError,match='budget exhausted'):produce_banners(tmp_path,client=client)
    assert client.post.call_count==1


def test_partial_success_is_not_repeated_after_explicit_budget_increase(tmp_path,monkeypatch):
    prepared(tmp_path,monkeypatch);client=Mock()
    client.post.side_effect=[image_response(),httpx.Response(503,json={'error':'busy'})]
    with pytest.raises(ValueError,match='HTTP 503'):produce_banners(tmp_path,client=client)
    partial=json.loads((tmp_path/'internal/banner_manifest.json').read_text())
    assert partial['status']=='IN_PROGRESS' and len(partial['assets'])==1
    before=(tmp_path/'artifacts'/partial['assets'][0]['path']).read_bytes()
    monkeypatch.setenv('AD_BANNER_REQUEST_LIMIT','3')
    client.post.side_effect=lambda *a,**k:image_response()
    complete=produce_banners(tmp_path,client=client)
    assert complete['status']=='CREATED' and client.post.call_count==3
    assert (tmp_path/'artifacts'/partial['assets'][0]['path']).read_bytes()==before


def test_changed_creative_or_cached_image_refuses_generation(tmp_path,monkeypatch):
    prepared(tmp_path,monkeypatch);client=Mock()
    (tmp_path/'artifacts/creative_brief.md').write_text('changed')
    with pytest.raises(ValueError,match='changed since review'):produce_banners(tmp_path,client=client)
    client.post.assert_not_called()


@pytest.mark.parametrize('corruption',['hash','version','approval','path'])
def test_build_rejects_tampered_or_falsely_approved_assets(tmp_path,monkeypatch,corruption):
    man=prepared(tmp_path,monkeypatch);client=Mock();client.post.side_effect=lambda *a,**k:image_response()
    result=produce_banners(tmp_path,client=client)
    path=tmp_path/'internal/banner_manifest.json'
    if corruption=='hash':(tmp_path/'artifacts'/result['assets'][0]['path']).write_bytes(b'corruption')
    if corruption=='version':result['plan_version']='different'
    if corruption=='approval':result['assets'][0]['status']='APPROVED_FOR_PUBLISH'
    if corruption=='path':result['assets'][0]['path']='../escape.png'
    path.write_text(json.dumps(result),encoding='utf-8')
    out=tmp_path/'export';out.mkdir()
    with pytest.raises(ValueError):attach_banner_assets(tmp_path,out,man['plan_version'])


@pytest.mark.parametrize('filename',FILES)
def test_real_build_copies_draft_banners_and_hashes_them(tmp_path,monkeypatch,filename):
    man=prepared(tmp_path,monkeypatch);client=Mock();client.post.side_effect=lambda *a,**k:image_response()
    result=produce_banners(tmp_path,client=client)
    (tmp_path/'artifacts/qa_report.json').write_text(json.dumps(qa_fixture(man['plan_version'])))
    build=definitions(filename,'Build_Script');approved,hashes,errors=build['verify']();assert not errors
    build['build'](approved,hashes)
    output=tmp_path/'output';manifest=json.loads((output/'manifest.json').read_text())
    assert len([p for p in output.rglob('*') if p.is_file()])==29
    assert len(manifest['generated_files'])==8
    for item in manifest['generated_files']:
        assert hashlib.sha256((output/item['name']).read_bytes()).hexdigest()==item['sha256']
    assets=json.loads((output/'asset_manifest.json').read_text())
    assert assets['assets'][0]['status']=='DRAFT' and assets['plan_version']==man['plan_version']


def test_python_node_executes_disabled_stage_from_checked_approval(tmp_path,monkeypatch):
    prepared(tmp_path,monkeypatch);monkeypatch.setenv('AD_BANNER_ENABLED','0')
    monkeypatch.setenv('MAC_ALLOW_UNSAFE_CODE_EXECUTION','1')
    code=ad_banner_script('HUMAN: APPROVE\n[[REVIEW_APPROVE]]',{})
    assert code and ad_banner_script('HUMAN: REVISE\n[[REVIEW_REVISE]]',{}) is None
    graph=yaml.safe_load((ROOT/'yaml_instance/ad_agency_v2.yaml').read_text(encoding='utf-8'))['graph']
    config=next(n for n in graph['nodes'] if n['id']=='Banner_Producer')
    config['config']['env']['AD_PUBLICATION_REQUIRED']='0'  # Legacy script fixture; publication subprocess tested separately.
    node=Node.from_dict(config,path='offline.banner')
    context=ExecutionContext(tool_manager=None,function_manager=None,log_manager=MagicMock(),global_state={'python_workspace_root':tmp_path})
    messages=PythonNodeExecutor(context).execute(node,[Message(role=MessageRole.USER,content=code)])
    text=messages[0].text_content()
    assert ad_banner_result(text,{})==text.strip() and ad_banner_fallback(text,{}) is None
    assert json.loads(text.strip().rsplit('\n',1)[0])['status']=='DISABLED'


@pytest.mark.parametrize('text',['', '[[EXEC_FAIL]]\n[[BANNER_READY]]', '{}\n[[BANNER_READY]]',
                               '{"status":"CREATED","assets":[]}\n[[BANNER_READY]]'])
def test_bad_banner_handoff_routes_to_blocked(text):
    assert ad_banner_result(text,{}) is None
    assert ad_banner_fallback(text,{}).startswith('[[EXEC_FAIL]]')
