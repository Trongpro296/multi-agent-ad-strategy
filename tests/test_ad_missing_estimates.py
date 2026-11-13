"""Offline regression for explicit unavailable forecasts and recovery provenance."""
import base64
import csv
import hashlib
import io
import json

import pytest

from test_ad_agency_audit import FILES, definitions, fixture_files, run_gate
from test_ad_malformed_recovery import prepare_source
from tools.prepare_ad_recovery import build_recovery, normalize_missing_estimates, restore_script


def write_scenarios(path, rows, status=True):
    fields=['scenario','channel','budget_amount','metric','metric_value','formula','assumption']
    if status:fields.append('estimate_status')
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)


@pytest.mark.parametrize('filename',FILES)
def test_unknown_forecast_survives_gate_snapshot_and_excel(tmp_path,monkeypatch,filename):
    monkeypatch.chdir(tmp_path)
    rows=fixture_files(tmp_path)['budget_scenarios.csv']
    rows[0].update(metric_value='',formula='',assumption='No historical conversion data',estimate_status='NOT_ESTIMATED')
    rows[1]['estimate_status']='ESTIMATED'
    write_scenarios(tmp_path/'artifacts/budget_scenarios.csv',rows)
    output=run_gate(tmp_path,filename)
    assert output.rstrip().endswith('[[PLAN_OK]]')
    assert 'unestimated_metrics' in output and 'No historical conversion data' in output
    manifest=json.loads((tmp_path/'review/review_manifest.json').read_text())
    (tmp_path/'artifacts/qa_report.json').write_text(json.dumps({'verdict':'PASS','plan_version':manifest['plan_version']}))
    script=definitions(filename,'Build_Script')
    approved,hashes,problems=script['verify']()
    assert not problems
    script['build'](approved,hashes)
    from openpyxl import load_workbook
    sheet=load_workbook(tmp_path/'output/Campaign_Plan.xlsx')['Budget_Scenarios']
    assert sheet['E2'].value is None and sheet['H2'].value=='NOT_ESTIMATED'
    assert sheet['E3'].value==20 and sheet['E3'].data_type=='n'
    assert (tmp_path/'output/budget_scenarios.csv').read_bytes()==(tmp_path/'artifacts/budget_scenarios.csv').read_bytes()


@pytest.mark.parametrize('filename',FILES)
@pytest.mark.parametrize('case', ['text_without_status','unknown_zero','unknown_text','missing_reason','estimated_blank','estimated_nan','estimated_no_formula','invalid_status','blank_status'])
def test_unknown_does_not_relax_numeric_or_evidence_contract(tmp_path,monkeypatch,filename,case):
    monkeypatch.chdir(tmp_path)
    rows=fixture_files(tmp_path)['budget_scenarios.csv']
    for row in rows:row['estimate_status']='ESTIMATED'
    target=rows[0]
    target.update(metric_value='',formula='',estimate_status='NOT_ESTIMATED')
    if case=='text_without_status':
        for row in rows:row.pop('estimate_status')
        target['metric_value']='[SUY LUẬN] Thiếu dữ liệu'
    elif case=='unknown_zero':target['metric_value']='0'
    elif case=='unknown_text':target['metric_value']='unknown'
    elif case=='missing_reason':target['assumption']=''
    elif case=='estimated_blank':target.update(estimate_status='ESTIMATED',formula='100/20')
    elif case=='estimated_nan':target.update(estimate_status='ESTIMATED',metric_value='NaN',formula='100/20')
    elif case=='estimated_no_formula':target.update(estimate_status='ESTIMATED',metric_value='5')
    elif case=='invalid_status':target['estimate_status']='unknown'
    elif case=='blank_status':target['estimate_status']=''
    write_scenarios(tmp_path/'artifacts/budget_scenarios.csv',rows,status=case!='text_without_status')
    assert run_gate(tmp_path,filename).rstrip().endswith('[[PLAN_ISSUES]]')
    assert not (tmp_path/'review/review_manifest.json').exists()


def test_recovery_normalization_is_opt_in_recorded_and_source_immutable(tmp_path,monkeypatch):
    source,log,template,_=prepare_source(tmp_path)
    path=source/'artifacts/budget_scenarios.csv'
    rows=list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8-sig'))))
    rows[0]['metric_value']='[SUY LUẬN] Thiếu dữ liệu'
    write_scenarios(path,rows,status=False)
    original=path.read_bytes()
    _,default=build_recovery(template,source,log,'offline_source')
    assert not default['transformations'] and default['files']==default['source_files']
    doc,manifest=build_recovery(template,source,log,'offline_source',normalize_estimates=True)
    assert path.read_bytes()==original
    assert manifest['source_files']['budget_scenarios.csv']==hashlib.sha256(original).hexdigest()
    assert manifest['files']['budget_scenarios.csv']!=manifest['source_files']['budget_scenarios.csv']
    assert manifest['transformations']['budget_scenarios.csv']==[{'row':2,'original_metric_value':'[SUY LUẬN] Thiếu dữ liệu','estimate_status':'NOT_ESTIMATED'}]
    restore=next(n for n in doc['graph']['nodes'] if n['id']=='Recovery_Source')['config']['content']
    destination=tmp_path/'destination';destination.mkdir()
    monkeypatch.setenv('MAC_CODE_WORKSPACE',str(destination))
    exec(restore.split('\n',1)[1].rsplit('```',1)[0],{})
    recovered=list(csv.DictReader((destination/'artifacts/budget_scenarios.csv').open(encoding='utf-8-sig')))
    assert recovered[0]['metric_value']=='' and recovered[0]['estimate_status']=='NOT_ESTIMATED'
    assert '[SUY LUẬN] Thiếu dữ liệu' in recovered[0]['assumption']
    assert recovered[1]['metric_value']=='20' and recovered[1]['estimate_status']=='ESTIMATED'
    for name,digest in manifest['files'].items():
        assert hashlib.sha256((destination/'artifacts'/name).read_bytes()).hexdigest()==digest
    assert path.read_bytes()==original


def test_normalizer_never_guesses_arbitrary_nonnumeric_or_decimal_values():
    original=b'scenario,channel,budget_amount,metric,metric_value,formula,assumption\r\nx,Facebook,100,CPA,"0,5",100/20,test\r\n'
    assert normalize_missing_estimates(original)==(original,[])
