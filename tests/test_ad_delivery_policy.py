"""Client delivery checks exercised through the real Gate and Build, offline."""
import csv
import io
import json

import pytest

from test_ad_agency_audit import FILES, definitions, fixture_files, run_gate, qa_fixture
from utils.ad_delivery_policy import delivery_issues


@pytest.mark.parametrize('filename', FILES)
@pytest.mark.parametrize('bad_text,code', [
    ('# Kế hoạch Mây — bản nháp rework chờ Gate/Strategy_QA\n', 'DELIVERY_TITLE'),
    ('# Kế hoạch Mây\n\n## Bàn giao nhận được\nMedia: ĐÃ NHẬN', 'INTERNAL_NOTES'),
    ('# Kế hoạch Mây\n\n### Nhật ký rework\nFILE ĐÃ ĐỔI: media_plan.csv', 'INTERNAL_NOTES'),
    ('# Kế hoạch Mây\nĐọc `artifacts/media_plan.csv`.', 'INTERNAL_REFERENCE'),
    ('# Kế hoạch Mây\nĐọc `advertising_strategy_draft.md`.', 'INTERNAL_REFERENCE'),
    ('# Kế hoạch Mây\n[Tracking](missing_tracker.csv)', 'DELIVERY_REFERENCE'),
])
def test_gate_reworks_bad_delivery_without_snapshot_or_source_mutation(tmp_path, monkeypatch, filename, bad_text, code):
    monkeypatch.chdir(tmp_path)
    fixture_files(tmp_path)
    path=tmp_path/'artifacts/advertising_strategy_draft.md'
    path.write_text(bad_text,encoding='utf-8')
    before=path.read_bytes()
    output=run_gate(tmp_path,filename)
    assert output.rstrip().endswith('[[PLAN_ISSUES]]') and code in output
    assert not (tmp_path/'review/review_manifest.json').exists()
    assert path.read_bytes()==before


@pytest.mark.parametrize('filename', FILES)
def test_clean_plan_allows_internal_history_outside_delivery(tmp_path, monkeypatch, filename):
    monkeypatch.chdir(tmp_path)
    fixture_files(tmp_path)
    (tmp_path/'internal').mkdir()
    (tmp_path/'internal/assembly_notes.md').write_text('## Bàn giao nhận được\nFILE ĐÃ ĐỔI: media_plan.csv\n',encoding='utf-8')
    plan='# Kế hoạch Mây\n\n## Tóm tắt điều hành\nGiả thuyết chưa xác minh; cần kiểm tra thực địa.\n[Media](media_plan.csv) và `advertising_strategy.md`.\n'
    path=tmp_path/'artifacts/advertising_strategy_draft.md'
    path.write_text(plan,encoding='utf-8')
    assert run_gate(tmp_path,filename).rstrip().endswith('[[PLAN_OK]]')
    manifest=json.loads((tmp_path/'review/review_manifest.json').read_text())
    assert 'internal/assembly_notes.md' not in manifest['files']
    assert (tmp_path/'review'/manifest['plan_version']/'advertising_strategy_draft.md').read_bytes()==path.read_bytes()


@pytest.mark.parametrize('filename', FILES)
def test_build_rejects_old_handoff_reference_then_delivers_clean_unmodified_sources(tmp_path, monkeypatch, filename):
    monkeypatch.chdir(tmp_path)
    fixture_files(tmp_path)
    assert run_gate(tmp_path,filename).rstrip().endswith('[[PLAN_OK]]')
    manifest=json.loads((tmp_path/'review/review_manifest.json').read_text())
    (tmp_path/'artifacts/qa_report.json').write_text(json.dumps(qa_fixture(manifest['plan_version'])))
    notes=tmp_path/'artifacts/handoff_notes.md'
    notes.write_text('# Bàn giao\nĐọc artifacts/advertising_strategy_draft.md',encoding='utf-8')
    build=definitions(filename,'Build_Script')
    _,_,problems=build['verify']()
    assert any('INTERNAL_REFERENCE' in problem for problem in problems)
    assert not (tmp_path/'output').exists()
    notes.write_text('# Bàn giao\nĐọc [Kế hoạch](advertising_strategy.md) và `media_plan.csv`.\nKế hoạch đã duyệt; tracking cần chuẩn bị.',encoding='utf-8')
    man,hashes,problems=build['verify']()
    assert not problems
    names=build['build'](man,hashes)
    assert len(names)==26 and 'assembly_notes.md' not in names
    assert (tmp_path/'output/advertising_strategy.md').read_bytes()==(tmp_path/'review'/man['plan_version']/'advertising_strategy_draft.md').read_bytes()
    assert (tmp_path/'output/handoff_notes.md').read_bytes()==notes.read_bytes()


@pytest.mark.parametrize('status,url,date,code', [
    ('external','','2026-11-13','EXTERNAL_SOURCE'),
    ('external','https://example.test/source','','SOURCE_DATE'),
    ('external','https://example.test/source','2026-02-30','SOURCE_DATE'),
    ('external','not-a-url','2026-11-13','EXTERNAL_SOURCE'),
    ('external','https://example.test/source','2026-11-13',None),
    ('hypothesis','','',None),
    ('document','','',None),
])
def test_provenance_checks_structure_without_fabricating_or_certifying_claims(tmp_path,status,url,date,code):
    path=tmp_path/'sources.csv'
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['id','claim','source_url','access_date','scope','evidence_type'])
        writer.writerow(['E1','Claim requiring semantic review',url,date,'Brief giả định; chưa xác minh thực địa',status])
    before=path.read_bytes()
    result=delivery_issues(tmp_path)
    assert bool(result)==bool(code)
    if code:assert result[0]['code']==code
    assert path.read_bytes()==before


def test_duplicate_source_ids_are_ambiguous_even_if_urls_are_valid(tmp_path):
    (tmp_path/'sources.csv').write_text('id,claim,source_url,access_date,scope,evidence_type\nE1,One,,,brief,document\nE1,Two,,,brief,document\n')
    assert any(x['code']=='DUPLICATE_SOURCE' for x in delivery_issues(tmp_path))


@pytest.mark.parametrize('filename', FILES)
def test_preflight_detects_stale_embedded_policy_before_launch(filename):
    from pathlib import Path
    import yaml
    from tools.preflight_ad_agency import check_delivery_policy
    graph=yaml.safe_load((Path(__file__).resolve().parents[1]/'yaml_instance'/filename).read_text(encoding='utf-8'))['graph']
    check_delivery_policy(graph)
    node=next(n for n in graph['nodes'] if n['id']=='Build_Script')
    node['config']['content']=node['config']['content'].replace("return findings", "return []",1)
    with pytest.raises(ValueError,match='out of sync'):
        check_delivery_policy(graph)
