"""Prepare a self-contained recovery YAML from saved artifacts, without model calls.

Example: uv run python tools/prepare_ad_recovery.py --session session_960ee949-d325-41ba-bf2d-7fedfb34760c
The command only prepares a new workflow. It never launches it or changes the source session.
"""
import argparse
import base64
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime import sdk
from entity.messages import Message,MessageRole
from functions.edge_processor.ad_agency_contracts import _OUTPUTS,_validate_result
from utils.workspace_paths import validate_path_component
from utils.exceptions import WorkflowExecutionError
from utils.execution_markers import EXEC_FAILURE
import yaml

ALWAYS_REVIEW={'Plan_Assembler','Strategy_QA','Delivery_Packager'}


def restore_script(archive):
    encoded=base64.b64encode(json.dumps(archive,ensure_ascii=False).encode('utf-8')).decode('ascii')
    # All source material is encoded data, not interpolated executable Python or YAML variables.
    return '''import base64, hashlib, json, os
from pathlib import Path
archive=json.loads(base64.b64decode(%r).decode('utf-8'))
root=Path(os.environ['MAC_CODE_WORKSPACE']).resolve()
targets=[]
for name,record in archive['files'].items():
    if Path(name).name!=name or name in ('.','..'):
        raise ValueError('Invalid recovery filename')
    target=root/'artifacts'/name
    if not target.resolve().is_relative_to(root) or target.is_symlink():
        raise ValueError('Unsafe recovery target')
    data=base64.b64decode(record['base64'],validate=True)
    if hashlib.sha256(data).hexdigest()!=record['sha256']:
        raise ValueError('Recovery payload hash mismatch: '+name)
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=record['sha256']:
        raise ValueError('Refusing to overwrite different existing artifact: '+name)
    targets.append((target,data))
for target,data in targets:
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():target.write_bytes(data)
    if hashlib.sha256(target.read_bytes()).hexdigest()!=archive['files'][target.name]['sha256']:
        raise ValueError('Recovery destination hash mismatch')
print('AD_RECOVERY_READY')
print(archive['original_request'])
''' % encoded


def normalize_missing_estimates(data):
    """Translate only the observed explicit unknown marker; never infer numbers."""
    reader=csv.DictReader(io.StringIO(data.decode('utf-8-sig')),strict=True)
    fields=list(reader.fieldnames or [])
    required={'scenario','channel','budget_amount','metric','metric_value','formula','assumption'}
    if not required.issubset(fields) or len(fields)!=len(set(fields)):
        raise ValueError('Cannot normalize invalid budget scenario headers')
    rows=list(reader)
    changes=[]
    for index,row in enumerate(rows,2):
        if None in row or any(v is None for v in row.values()):
            raise ValueError('Cannot normalize malformed budget scenario rows')
        raw=row['metric_value'].strip()
        if raw!='[SUY LUẬN] Thiếu dữ liệu':continue
        status=row.get('estimate_status','').strip()
        if status not in ('','NOT_ESTIMATED'):
            raise ValueError('Conflicting estimate_status in source row')
        row['metric_value']=''
        row['estimate_status']='NOT_ESTIMATED'
        row['assumption']=(row['assumption'].strip()+' | Giá trị gốc: '+raw).lstrip(' |')
        changes.append({'row':index,'original_metric_value':raw,'estimate_status':'NOT_ESTIMATED'})
    if not changes:return data,[]
    if 'estimate_status' not in fields:fields.append('estimate_status')
    for row in rows:row.setdefault('estimate_status','ESTIMATED')
    output=io.StringIO(newline='')
    writer=csv.DictWriter(output,fieldnames=fields)
    writer.writeheader();writer.writerows(rows)
    return output.getvalue().encode('utf-8-sig'),changes


def build_recovery(template,workspace,log_path,source_name,creative_model=None,normalize_estimates=False):
    template=copy.deepcopy(template)
    completed=set();request=None
    for line in Path(log_path).open(encoding='utf-8'):
        try:entry=json.loads(line)
        except ValueError:continue
        if entry.get('event_type')=='NODE_END':
            completed.add(entry.get('node_id'))
            if entry.get('node_id')=='Campaign_Input' and isinstance(entry.get('output'),str):
                request=entry['output']
    if not request:raise ValueError('Original Campaign_Input request is missing from the session log')
    workspace=Path(workspace).resolve();artifacts=workspace/'artifacts'
    review_names={n for node,names in _OUTPUTS.items() if node not in ('Strategy_QA','Delivery_Packager') for n in names}
    files={};source_hashes={};transformations={}
    for name in sorted(review_names):
        path=artifacts/name
        if not path.is_file():continue
        if path.is_symlink() or not path.resolve().is_relative_to(workspace):
            raise ValueError('Unsafe source artifact: '+name)
        data=path.read_bytes()
        if not data.strip():raise ValueError('Empty source artifact: '+name)
        data.decode('utf-8-sig')
        source_hashes[name]=hashlib.sha256(data).hexdigest()
        if name=='budget_scenarios.csv' and normalize_estimates:
            data,changes=normalize_missing_estimates(data)
            if changes:transformations[name]=changes
        files[name]={'base64':base64.b64encode(data).decode('ascii'),'sha256':hashlib.sha256(data).hexdigest()}
    if not files:raise ValueError('No source artifacts to recover')
    graph=template['graph'];cached=[];pending=[]
    for node in graph['nodes']:
        if node.get('type')!='agent':continue
        name=node['id']
        can_cache=False
        if name in completed and name not in ALWAYS_REVIEW and name in _OUTPUTS:
            message=Message(role=MessageRole.ASSISTANT,content='BRIEF: READY' if name=='Director_Brief' else 'Saved artifacts')
            try:
                _validate_result(name,message,{'python_workspace_root':workspace})
                can_cache=True
            except WorkflowExecutionError:
                # A historic success does not authorize skipping a missing or
                # invalid artifact. Its owning Agent must execute again.
                pass
        if can_cache:
            paths=', '.join('artifacts/'+n for n in _OUTPUTS[name])
            content='Khôi phục đầu ra đã có từ phiên trước: '+paths+'. Dùng load_file để đọc nội dung hiện hành khi cần.'
            if name=='Director_Brief':content+='\nBRIEF: READY'
            node['type']='literal';node['config']={'role':'assistant','content':content}
            cached.append(name)
        else:
            pending.append(name)
            if name=='Creative_Director' and creative_model:
                if node['config'].get('provider','').lower()!='openai':
                    raise ValueError('Creative model override requires an OpenAI-compatible provider')
                node['config']['name']=creative_model
                node['config'].setdefault('params',{})['protocol']='chat'
            if name=='Creative_Director' and 'creative_brief.md' in files and 'creative_matrix.csv' not in files:
                node['config']['role']+='''

KHÔI PHỤC PHIÊN DỞ: artifacts/creative_brief.md đã được ghi thành công ở phiên trước.
Đọc file đó cùng campaign_brief.json và strategy_ids.json; tạo phần còn thiếu creative_matrix.csv theo các concept/claim đã có.
Không viết lại creative_brief.md hoặc tạo chiến lược mới. Nếu có điểm mâu thuẫn, nêu rõ để QA xử lý thay vì tự sửa dữ kiện nguồn.
Chỉ dùng read_skill_file cho tên thật trong available_files; không đọc lại SKILL.md vừa kích hoạt.
Sau khi lưu CSV, load lại cả hai file để kiểm tra. Chat chỉ cần tóm tắt file và giới hạn, không chép toàn bộ nội dung.
'''
    archive={'source_session':source_name,'original_request':request,'files':files}
    ids={n['id'] for n in graph['nodes']}
    if ids & {'Recovery_Source','Recovery_Restore'}:raise ValueError('Template already contains recovery nodes')
    graph['nodes'] += [
        {'id':'Recovery_Source','type':'literal','config':{'role':'user','content':'```python\n'+restore_script(archive)+'\n```'}},
        {'id':'Recovery_Restore','type':'python','config':{'timeout_seconds':60,'env':{'PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1'}}},
    ]
    graph['edges'] += [
        {'from':'Recovery_Source','to':'Recovery_Restore'},
        {'from':'Recovery_Restore','to':'Campaign_Input','condition':{'type':'keyword','config':{'any':['AD_RECOVERY_READY'],'none':[EXEC_FAILURE]}}},
        {'from':'Recovery_Restore','to':'Blocked_Output','condition':{'type':'keyword','config':{'any':[EXEC_FAILURE]}}},
    ]
    graph['start']=['Recovery_Source']
    graph['id']='ad_recovery_'+hashlib.sha256(source_name.encode()).hexdigest()[:10]
    graph['description']='Khôi phục '+source_name+': dùng lại artifacts, chỉ chạy các Agent còn thiếu và nghiệm thu mới.'
    manifest={'source_session':source_name,'files':{n:r['sha256'] for n,r in files.items()},'cached_agents':cached,'pending_agents':pending,
              'source_files':source_hashes,'transformations':transformations,
              'creative_model_override':creative_model,
              'note':'Prepared offline; not a QA approval or proof of model reliability. Original session is unchanged.'}
    return template,manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session',required=True)
    parser.add_argument('--template',default='ad_agency_v2.yaml')
    parser.add_argument('--output',help='New .yaml path under yaml_instance; existing files are never overwritten')
    parser.add_argument('--creative-model',help='Optional explicit model override for Creative only in the generated recovery YAML')
    parser.add_argument('--normalize-missing-estimates',action='store_true',help='Translate the observed explicit unknown forecast text to blank + NOT_ESTIMATED in the recovery copy only')
    args=parser.parse_args()
    sid=validate_path_component(args.session,field='session')
    if not sid.startswith('session_'):sid='session_'+sid
    template_path=(ROOT/'yaml_instance'/args.template).resolve()
    if not template_path.is_relative_to((ROOT/'yaml_instance').resolve()):raise ValueError('Template must be under yaml_instance')
    source=ROOT/'WareHouse'/sid
    output=Path(args.output).resolve() if args.output else ROOT/'yaml_instance'/('ad_agency_recovery_'+sid[8:16]+'.yaml')
    if not output.is_relative_to((ROOT/'yaml_instance').resolve()):raise ValueError('Output must be under yaml_instance')
    manifest_path=output.with_suffix('.recovery.json')
    if output.exists() or manifest_path.exists():raise FileExistsError('Choose a new output filename')
    doc,manifest=build_recovery(yaml.safe_load(template_path.read_text(encoding='utf-8')),source/'code_workspace',ROOT/'logs'/(sid+'.log'),sid,args.creative_model,args.normalize_missing_estimates)
    # Schema/graph validation only; never execute the workflow during preparation.
    from check.check import check_config
    error=check_config(doc)
    if error:raise ValueError('Recovery graph validation failed: '+error)
    output.write_text(yaml.safe_dump(doc,allow_unicode=True,sort_keys=False,width=110),encoding='utf-8')
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Prepared:',output.name)
    print('Restored files:',len(manifest['files']),'cached agents:',', '.join(manifest['cached_agents']))
    print('Pending agents:',', '.join(manifest['pending_agents']))
    print('No model called and no workflow executed. Source session is unchanged.')


if __name__=='__main__':main()
