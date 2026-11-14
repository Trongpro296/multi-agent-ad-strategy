"""Prepare publication-only recovery from validated artifacts; never execute it."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime import sdk
from utils.ad_publication import verify_sources,validate_content,safe
from utils.workspace_paths import validate_path_component
import yaml


def build_publication_recovery(template,workspace,source_session):
    workspace=Path(workspace).resolve();man=verify_sources(workspace);bundle=validate_content(workspace)
    names=['review/review_manifest.json','artifacts/qa_report.json','artifacts/publication_content.json']
    names+=['artifacts/'+n for n in man['files']]
    names+=['review/'+man['plan_version']+'/'+n for n in man['files']]
    archive={}
    for name in names:
        path=safe(workspace,name);data=path.read_bytes()
        archive[name]={'base64':base64.b64encode(data).decode('ascii'),'sha256':hashlib.sha256(data).hexdigest()}
    encoded=base64.b64encode(json.dumps(archive).encode()).decode('ascii')
    script='''import base64,hashlib,json,os
from pathlib import Path
files=json.loads(base64.b64decode(%r).decode())
root=Path(os.environ['MAC_CODE_WORKSPACE']).resolve()
targets=[]
for name,record in files.items():
    rel=Path(name);target=root/rel
    if rel.is_absolute() or '..' in rel.parts or rel.parts[0] not in ('artifacts','review') or not target.resolve().is_relative_to(root) or target.is_symlink():raise ValueError('Unsafe restore path')
    data=base64.b64decode(record['base64'],validate=True)
    if hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('Restore data hash mismatch')
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=record['sha256']:raise ValueError('Refusing different existing restore file')
    targets.append((target,data))
for target,data in targets:
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():target.write_bytes(data)
    if hashlib.sha256(target.read_bytes()).hexdigest()!=files[target.relative_to(root).as_posix()]['sha256']:raise ValueError('Restored hash mismatch')
brief=json.loads((root/'artifacts/campaign_brief.json').read_text(encoding='utf-8-sig'))
manifest=json.loads((root/'review/review_manifest.json').read_text(encoding='utf-8-sig'))
print('Plan and public copy restored unchanged. Renew HUMAN: APPROVE once to authorize finalization; no planning/research/editor agents will run.')
print('plan_version='+manifest['plan_version'])
print(json.dumps(brief,ensure_ascii=False))
print('AD_PUBLICATION_RECOVERY_READY')
''' % encoded
    doc=copy.deepcopy(template);graph=doc['graph'];keep={'Client_Review','Review_Router','Publication_QA','Banner_Producer','Delivery_Packager','Build_Script','Build_Files','Delivery','Blocked_Output','Invalid_Review_Notice'}
    graph['nodes']=[n for n in graph['nodes'] if n['id'] in keep]
    graph['nodes'] += [{'id':'Recovery_Publication_Source','type':'literal','config':{'role':'user','content':'```python\n'+script+'\n```'}},
                       {'id':'Recovery_Publication_Restore','type':'python','config':{'timeout_seconds':60,'env':{'PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1'}}}]
    graph['edges']=[e for e in graph['edges'] if e['from'] in keep and e['to'] in keep]
    def proc(name):return {'type':'function','config':{'name':name}}
    graph['edges'] += [{'from':'Recovery_Publication_Source','to':'Recovery_Publication_Restore'},
                       {'from':'Recovery_Publication_Restore','to':'Client_Review','condition':{'type':'keyword','config':{'any':['AD_PUBLICATION_RECOVERY_READY'],'none':['[[EXEC_FAIL]]']}},'process':proc('ad_agency_bootstrap')},
                       {'from':'Recovery_Publication_Restore','to':'Blocked_Output','condition':{'type':'keyword','config':{'any':['[[EXEC_FAIL]]']}}},
                       {'from':'Review_Router','to':'Publication_QA','condition':{'type':'keyword','config':{'any':['[[REVIEW_APPROVE]]']}},'process':proc('ad_publication_resume_qa_input')},
                       {'from':'Review_Router','to':'Blocked_Output','condition':{'type':'keyword','config':{'any':['[[REVIEW_REVISE]]']}},'process':proc('ad_checked_payload')}]
    graph['start']=['Recovery_Publication_Source'];graph['id']='publication_recovery_'+hashlib.sha256(source_session.encode()).hexdigest()[:10]
    graph['description']='Khôi phục phần xuất bản '+source_session+': giữ nguyên kế hoạch và copy, chỉ chạy Publication_QA, ảnh và đóng gói sau HUMAN: APPROVE.'
    metadata={'source_session':source_session,'plan_version':man['plan_version'],'bundle_sha256':archive['artifacts/publication_content.json']['sha256'],
              'restored_files':{n:r['sha256'] for n,r in archive.items()},'pending_agents':['Publication_QA','Delivery_Packager'],
              'notice':'Prepared offline; no model/image call, no fake approval. New session requires one HUMAN: APPROVE.'}
    return doc,metadata


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--session',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    sid=validate_path_component(args.session,field='session')
    if not sid.startswith('session_'):sid='session_'+sid
    output=Path(args.output).resolve()
    if not output.is_relative_to((ROOT/'yaml_instance').resolve()) or output.suffix!='.yaml':raise ValueError('Output must be a YAML under yaml_instance')
    meta=output.with_suffix('.recovery.json')
    if output.exists() or meta.exists():raise FileExistsError('Use a new output filename')
    doc,info=build_publication_recovery(yaml.safe_load((ROOT/'yaml_instance/ad_agency_v2.yaml').read_text(encoding='utf-8')),ROOT/'WareHouse'/sid/'code_workspace',sid)
    from check.check import check_config
    error=check_config(doc)
    if error:raise ValueError('Invalid recovery graph: '+str(error))
    output.write_text(yaml.safe_dump(doc,allow_unicode=True,sort_keys=False,width=120),encoding='utf-8');meta.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Prepared:',output.name);print('Preserved files:',len(info['restored_files']));print('Pending agents:',', '.join(info['pending_agents']));print('No model or image request; no workflow executed. Original session unchanged.')


if __name__=='__main__':main()
