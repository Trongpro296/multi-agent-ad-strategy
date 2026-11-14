"""Publication copy contracts and hash-bound human release; no network calls."""
import csv
import hashlib
import io
import json
import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()[:16]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def safe(root,rel):
    root=Path(root).resolve();rel=Path(rel)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts:
        raise ValueError('Unsafe publication path')
    target=root/rel
    if any(p.is_symlink() for p in (target,*target.parents) if p!=root.parent) or not target.resolve().is_relative_to(root):
        raise ValueError('Unsafe publication path')
    return target


class PublicationWriteValidationError(ValueError):
    label='Publication'
    def __init__(self,path,detail):
        self.path=path
        super().__init__('Publication content rejected before writing: '+detail+'. File unchanged. Correct the public copy; do not invent verification.')


def validate_content(root,data=None):
    root=Path(root)
    bundle=json.loads(data.decode('utf-8-sig')) if data is not None else read(root/'artifacts/publication_content.json')
    man=read(root/'review/review_manifest.json');brief=read(root/'artifacts/campaign_brief.json')
    if not isinstance(bundle,dict) or bundle.get('schema_version')!='1.0' or bundle.get('plan_version')!=man['plan_version']:
        raise ValueError('Publication schema_version=1.0 and current plan_version required')
    forbidden=re.compile(r'\[(?:GIẢ THUYẾT|SUY LUẬN|TÀI LIỆU)\]|\[\[|\{\{|artifacts/|code_workspace/|advertising_strategy_draft|CHƯA DUYỆT|BẢN NHÁP|\bTODO\b|\bTBD\b|<[^>]+>',re.I)
    def text(v,label,limit=12000):
        if not isinstance(v,str) or not v.strip() or len(v)>limit or forbidden.search(v):
            raise ValueError(label+': nonempty final text required; no internal labels, placeholders or workspace paths')
    def refs(item):
        values=item.get('source_refs')
        if not isinstance(values,list) or not values:raise ValueError('source_refs required for every public item')
        for ref in values:
            if not isinstance(ref,dict) or ref.get('file') not in man['files'] or not isinstance(ref.get('location'),str) or not ref['location'].strip():
                raise ValueError('Invalid source_refs file/location')
    def identifier(value):
        if not isinstance(value,str) or not re.fullmatch(r'[A-Z][A-Z0-9_-]{1,30}',value):raise ValueError('Public item id must be ASCII uppercase identifier')
    text(bundle.get('brand_name'),'brand_name',80)
    ids=set();posts=bundle.get('posts');videos=bundle.get('video_scripts');banners=bundle.get('banners')
    for name,items,minimum,maximum in [('posts',posts,1,20),('video_scripts',videos,1,6),('banners',banners,1,4)]:
        if not isinstance(items,list) or not minimum<=len(items)<=maximum:raise ValueError(name+': invalid count')
        for item in items:
            if not isinstance(item,dict):raise ValueError(name+': object required')
            identifier(item.get('id'))
            if item['id'] in ids:raise ValueError('Duplicate public item id')
            ids.add(item['id']);refs(item)
    banner_ids={b['id'] for b in banners}
    for b in banners:
        text(b.get('headline'),'headline',180);text(b.get('cta'),'banner CTA',120);text(b.get('visual_brief'),'visual_brief',2200)
    for p in posts:
        for field in ('channel','content','cta'):text(p.get(field),'post '+field)
        if not isinstance(p.get('hashtags'),list) or len(p['hashtags'])>15:raise ValueError('hashtags list required, max 15')
        for tag in p['hashtags']:text(tag,'hashtag',80)
        if p.get('banner_id') is not None and p['banner_id'] not in banner_ids:raise ValueError('Unknown banner_id')
    for video in videos:
        text(video.get('title'),'video title',180)
        duration=video.get('duration_seconds');scenes=video.get('scenes')
        if type(duration) not in (int,float) or not 5<=duration<=180 or not isinstance(scenes,list) or not scenes:raise ValueError('Invalid video duration/scenes')
        cursor=0
        for scene in scenes:
            if not isinstance(scene,dict) or type(scene.get('start')) not in (int,float) or type(scene.get('end')) not in (int,float) or scene['start']!=cursor or not cursor<scene['end']<=duration:raise ValueError('Video scenes must cover contiguous duration')
            for key in ('visual','voiceover','on_screen_text','audio'):text(scene.get(key),'scene '+key)
            cursor=scene['end']
        if cursor!=duration:raise ValueError('Video scenes must end at duration_seconds')
    calendar=bundle.get('calendar');covered=set()
    if not isinstance(calendar,list) or not calendar:raise ValueError('Nonempty publication calendar required')
    for item in calendar:
        if not isinstance(item,dict) or item.get('content_id') not in ids:raise ValueError('Unknown calendar content_id')
        if not isinstance(item.get('date'),str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',item['date']):raise ValueError('Calendar date must be YYYY-MM-DD')
        when=date.fromisoformat(item['date'])
        if not date.fromisoformat(brief['start_date'])<=when<=date.fromisoformat(brief['end_date']):raise ValueError('Publication calendar outside campaign')
        text(item.get('channel'),'calendar channel',100);text(item.get('owner'),'calendar owner',150);covered.add(item['content_id'])
    if not ({p['id'] for p in posts}|{v['id'] for v in videos}).issubset(covered):raise ValueError('Every post/script needs a calendar entry')
    # Contracts check structure and traceability; plan authorization delegates
    # production, and never fabricates evidence for unsupported claims.
    return bundle


PUBLIC_CHECKS={'FACTS','OFFERS_CLAIMS','COPY_COMPLETENESS','CTA_CONSISTENCY','SCHEDULE','VIDEO_SCRIPT','VISUAL_BRIEFS','RIGHTS_PROVENANCE'}



def publication_qa_template(root):
    """Exact shape/identity only; deliberately incomplete until actual review."""
    root=Path(root);bundle=validate_content(root)
    return {'schema_version':'1.0','plan_version':bundle['plan_version'],
            'bundle_sha256':sha(root/'artifacts/publication_content.json'),'verdict':'BLOCKED',
            'checks':[{'id':key,'status':'FAIL','reason':'','source_refs':[]} for key in sorted(PUBLIC_CHECKS)],
            'findings':[]}


def validate_publication_qa(root,data=None):
    root=Path(root);report=json.loads(data.decode('utf-8-sig')) if data is not None else read(root/'artifacts/publication_qa.json')
    bundle=validate_content(root);man=read(root/'review/review_manifest.json')
    if not isinstance(report,dict) or report.get('schema_version')!='1.0' or report.get('plan_version')!=bundle['plan_version'] or report.get('bundle_sha256')!=sha(root/'artifacts/publication_content.json'):
        raise ValueError('Publication QA schema/version/content hash mismatch')
    aliases=[key for key in ('criteria_results','issues') if key in report]
    if aliases:
        raise ValueError('Wrong report fields '+', '.join(aliases)+': use checks (not criteria_results), findings (not issues); this is Publication_QA, not Strategy_QA')
    checks=report.get('checks');findings=report.get('findings')
    if not isinstance(checks,list):
        raise ValueError('Missing/wrong checks: expected a list of 8 objects using keys id,status,reason,source_refs. Required IDs: '+', '.join(sorted(PUBLIC_CHECKS)))
    if any(not isinstance(c,dict) for c in checks):raise ValueError('checks must contain objects, not strings')
    ids=[c.get('id') for c in checks]
    invalid=[str(x) for x in ids if not isinstance(x,str) or x not in PUBLIC_CHECKS]
    missing=sorted(PUBLIC_CHECKS-{x for x in ids if isinstance(x,str)})
    duplicate=sorted({x for x in ids if isinstance(x,str) and ids.count(x)>1})
    if len(ids)!=8 or invalid or missing or duplicate:
        raise ValueError('Invalid checks IDs: missing='+str(missing)+'; unknown='+str(invalid)+'; duplicate='+str(duplicate)+
                         '. Keep the exact template IDs; use id, not criterion_id. Required IDs: '+', '.join(sorted(PUBLIC_CHECKS)))
    for check in checks:
        if check.get('status') not in ('PASS','FAIL') or not isinstance(check.get('reason'),str) or not check['reason'].strip():raise ValueError('Public QA check needs status and reason')
        refs=check.get('source_refs')
        if not isinstance(refs,list) or not refs:raise ValueError('Public QA source references required')
        for ref in refs:
            if not isinstance(ref,dict) or ref.get('file') not in man['files'] or not isinstance(ref.get('location'),str) or not ref['location'].strip():raise ValueError('Public QA invalid source reference')
    if not isinstance(findings,list) or any(not isinstance(f,str) or not f.strip() for f in findings):raise ValueError('Public QA findings must be a list of specific nonempty findings')
    verdict=report.get('verdict')
    if verdict=='PASS':
        if findings or any(c['status']!='PASS' for c in checks):raise ValueError('Public QA PASS requires all checks PASS and no findings')
    elif verdict=='BLOCKED':
        if not findings or all(c['status']=='PASS' for c in checks):raise ValueError('Public QA BLOCKED requires findings and a failed check')
    else:raise ValueError('Public QA verdict must be PASS or BLOCKED')
    return report


def verify_sources(root):
    root=Path(root);man=read(root/'review/review_manifest.json');files=man.get('files',{})
    if not files:raise ValueError('Missing reviewed plan files')
    for name,expected in files.items():
        if Path(name).name!=name or sha(safe(root,'artifacts/'+name))!=expected or sha(safe(root,'review/'+man['plan_version']+'/'+name))!=expected:
            raise ValueError('Plan source changed since QA: '+name)
    qa=read(root/'artifacts/qa_report.json')
    from utils.ad_review_contracts import qa_report_issues
    if qa_report_issues(qa,man['plan_version'],files) or qa.get('verdict')!='PASS':raise ValueError('Current valid QA PASS required')
    return man


def prepare_review(root):
    root=Path(root);man=verify_sources(root);bundle=validate_content(root)
    qa=validate_publication_qa(root)
    if qa['verdict']!='PASS':raise ValueError('Public content QA has not passed')
    banners=read(root/'internal/banner_manifest.json')
    if banners.get('plan_version')!=man['plan_version'] or banners.get('status') not in ('CREATED','DISABLED'):raise ValueError('Incomplete banner stage')
    assets=banners.get('assets',[])
    if banners['status']=='CREATED' and {b['id'] for b in bundle['banners']}!={a.get('id') for a in assets}:raise ValueError('Missing required banner variants')
    preview=root/'artifacts/publication_preview';preview.mkdir(parents=True,exist_ok=True)
    paths=[]
    def put(name,content):
        target=safe(root,'artifacts/publication_preview/'+name);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(content,encoding='utf-8');paths.append(target.relative_to(root).as_posix())
    for post in bundle['posts']:
        put('posts/'+post['id']+'.txt',post['content'].strip()+'\n\n'+post['cta'].strip()+('\n\n'+' '.join(post['hashtags']) if post['hashtags'] else '')+'\n')
    for video in bundle['video_scripts']:
        lines=['# '+video['title'],'',str(video['duration_seconds'])+' giây','']
        for scene in video['scenes']:
            lines+=['## '+str(scene['start'])+'–'+str(scene['end'])+' giây','Cảnh quay: '+scene['visual'],'Lời thoại: '+scene['voiceover'],'Chữ hiển thị: '+scene['on_screen_text'],'Âm thanh: '+scene['audio'],'']
        put('video_scripts/'+video['id']+'.md','\n'.join(lines))
    output=io.StringIO(newline='');writer=csv.DictWriter(output,fieldnames=['date','channel','content_id','owner']);writer.writeheader();writer.writerows(bundle['calendar'])
    put('content_calendar.csv','\ufeff'+output.getvalue())
    for asset in assets:
        expected=next((b for b in bundle['banners'] if b['id']==asset.get('id')),None)
        if not expected or asset.get('headline')!=expected['headline'] or asset.get('cta')!=expected['cta']:
            raise ValueError('Generated banner text does not match final public copy')
        source=safe(root,'artifacts/'+asset['path'])
        from PIL import Image
        if source.stat().st_size>16*1024*1024:raise ValueError('Banner exceeds size limit')
        with Image.open(source) as image:
            if image.format!='PNG' or image.size!=(1024,1024):raise ValueError('Invalid final banner format/dimensions')
            image.verify()
        if sha(source)!=asset.get('sha256') or asset.get('copy_mode')!='PUBLIC_REVIEW':raise ValueError('Banner hash/copy mode mismatch')
    tracked=['artifacts/'+name for name in man['files']]+['artifacts/qa_report.json','artifacts/publication_content.json','artifacts/publication_qa.json','internal/banner_manifest.json']+paths+['artifacts/'+a['path'] for a in assets]
    files={path:sha(safe(root,path)) for path in tracked}
    review={'schema_version':'1.0','plan_version':man['plan_version'],'files':files,'preview_files':paths,'banner_assets':assets,'images_enabled':banners['status']=='CREATED'}
    review['release_id']=digest(review)
    write(root/'internal/publication_review.json',review)
    return review


def verify_review(root,review):
    if not isinstance(review,dict) or review.get('release_id')!=digest({k:v for k,v in review.items() if k!='release_id'}):raise ValueError('Publication review identity mismatch')
    if not review.get('files'):raise ValueError('Empty publication review')
    for path,expected in review['files'].items():
        if sha(safe(root,path))!=expected:raise ValueError('Publication file changed after preview: '+path)
    verify_sources(root)


def approve_from_plan(root,authorization):
    root=Path(root);review=read(root/'internal/publication_review.json')
    verify_review(root,review)
    if not isinstance(authorization,dict) or authorization.get('plan_version')!=review['plan_version'] or authorization.get('mode')!='PLAN_AND_DERIVED_OUTPUTS':
        raise ValueError('Missing Human plan authorization for final outputs')
    man=read(root/'review/review_manifest.json')
    if authorization.get('plan_files')!=man['files'] or authorization.get('qa_sha256')!=sha(root/'artifacts/qa_report.json'):
        raise ValueError('Plan or QA differs from Human authorization')
    if not authorization.get('authorized_at'):
        raise ValueError('Missing authorization time')
    approval={'status':'APPROVED','approval_mode':'PLAN_AUTHORIZATION','release_id':review['release_id'],
              'plan_authorized_at':authorization['authorized_at'],
              'review_sha256':sha(root/'internal/publication_review.json'),
              'approved_at':datetime.now(timezone.utc).isoformat(),
              'confirmation':'Human approved the plan and delegated final copy/image production. Assets were sealed automatically under that authorization; no separate visual-review claim, posting or ad spend.'}
    write(root/'internal/publication_approval.json',approval)
    return sha(root/'internal/publication_approval.json')


def export_publication(root,destination,plan_version,approval_sha256):
    root=Path(root);dest=Path(destination);path=root/'internal/publication_approval.json'
    raw_approval=path.read_bytes()
    if not approval_sha256 or hashlib.sha256(raw_approval).hexdigest()!=approval_sha256:raise ValueError('Missing or changed human publication approval seal')
    approval=json.loads(raw_approval.decode('utf-8-sig'));review=read(root/'internal/publication_review.json');verify_review(root,review)
    if approval.get('status')!='APPROVED' or approval.get('release_id')!=review['release_id'] or approval.get('review_sha256')!=sha(root/'internal/publication_review.json') or review['plan_version']!=plan_version:raise ValueError('Publication approval/version mismatch')
    files=[]
    for source_name in review['preview_files']:
        relative=Path(source_name).relative_to('artifacts/publication_preview')
        target_name=('production/' if relative.parts[0]=='video_scripts' else 'publish/')+relative.as_posix()
        target=safe(dest,target_name);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(safe(root,source_name),target)
        if sha(target)!=review['files'][source_name]:raise ValueError('Public copy changed while exporting')
        files.append(target_name)
    for asset in review['banner_assets']:
        name='publish/banners/'+asset['id']+'.png';target=safe(dest,name);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(safe(root,'artifacts/'+asset['path']),target)
        if sha(target)!=review['files']['artifacts/'+asset['path']]:raise ValueError('Banner changed while exporting')
        files.append(name)
    verify_review(root,review)
    for rel,expected in [('artifacts/publication_content.json',review['files']['artifacts/publication_content.json']),
                         ('artifacts/publication_qa.json',review['files']['artifacts/publication_qa.json']),
                         ('internal/publication_review.json',approval['review_sha256']),
                         ('internal/publication_approval.json',approval_sha256)]:
        name='internal/'+Path(rel).name;target=safe(dest,name);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(safe(root,rel),target)
        if sha(target)!=expected:raise ValueError('Publication metadata changed while exporting')
        files.append(name)
    manifest={'schema_version':'1.0','status':'APPROVED_FOR_PUBLICATION','release_id':review['release_id'],'plan_version':plan_version,'approved_at':approval['approved_at'],'approval_mode':approval.get('approval_mode'),'images_enabled':review['images_enabled'],'files':{name:sha(safe(dest,name)) for name in files},'ai_generated_assets':[a['id'] for a in review['banner_assets']],'notice':'Video files are production scripts only. No automatic posting, media buying or operational readiness certification.'}
    write(dest/'internal/publication_manifest.json',manifest);files.append('internal/publication_manifest.json')
    return files


def finalize_delivery(root,destination,plan_version,approval_sha256):
    root=Path(root);dest=Path(destination)
    files=export_publication(root,dest,plan_version,approval_sha256)
    # Keep legacy planning/research files for audit, outside the publish folder.
    internal=dest/'internal';internal.mkdir(exist_ok=True)
    for path in list(dest.iterdir()):
        if path.name in ('publish','production','internal'):continue
        target=internal/path.name
        if target.exists():raise ValueError('Duplicate internal export path')
        shutil.move(str(path),str(target))
    (dest/'README.md').write_text('BỘ BÀN GIAO CUỐI THEO KẾ HOẠCH ĐÃ DUYỆT\n\n- publish/posts/: nội dung bài đăng hoàn chỉnh.\n- publish/banners/: banner hoàn chỉnh theo ủy quyền kế hoạch (nếu bật tạo ảnh).\n- publish/content_calendar.csv: lịch và mã nội dung.\n- production/video_scripts/: kịch bản để sản xuất, không phải video đã quay.\n- internal/: nghiên cứu, kế hoạch, QA, điều kiện vận hành và nguồn gốc ảnh.\n\nDuyệt nội dung không tự bật quảng cáo hoặc xác nhận các điều kiện vận hành đã hoàn tất.\n',encoding='utf-8')
    return sorted(p.relative_to(dest).as_posix() for p in dest.rglob('*') if p.is_file())
