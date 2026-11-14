"""Deterministic delivery checks; semantic claim review remains QA's responsibility.

The single self-contained function is embedded in the advertising Python nodes so
they also run from an isolated session cwd, without importing the project package.
"""



def source_issues_csv(data, today=None):
    """Source shape/provenance checks only; never invent access evidence."""
    import csv
    import datetime
    import io
    import re
    from urllib.parse import urlsplit
    if today is None:
        today=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date()
    findings=[]
    def issue(code,message):findings.append({'file':'sources.csv','code':code,'message':message})
    try:
        reader=csv.DictReader(io.StringIO(data.decode('utf-8-sig'),newline=''),strict=True)
        rows=list(reader);seen=set()
        for line,row in enumerate(rows,2):
            if None in row or any(value is None for value in row.values()):
                issue('SOURCE_FORMAT','Malformed source row %d.' % line);continue
            source_id=str(row.get('id') or '').strip()
            if not source_id:issue('SOURCE_ID','Source id is required at row %d.' % line)
            elif source_id in seen:issue('DUPLICATE_SOURCE','Duplicate evidence ID at row %d: %s' % (line,source_id))
            seen.add(source_id)
            if str(row.get('evidence_type') or '').strip()!='external':continue
            raw_url=str(row.get('source_url') or '').strip()
            try:
                url=urlsplit(raw_url)
                valid_url=url.scheme in ('http','https') and bool(url.hostname) and url.username is None and not any(c.isspace() for c in raw_url)
                url.port
            except ValueError:valid_url=False
            if not valid_url:
                issue('EXTERNAL_SOURCE','Row %d (%s): source_url must be an absolute http:// or https:// URL actually accessed; received %r.' % (line,source_id,raw_url))
            raw_date=str(row.get('access_date') or '').strip()
            try:
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',raw_date):raise ValueError('ISO date required')
                accessed=datetime.date.fromisoformat(raw_date)
            except ValueError:
                issue('SOURCE_DATE','Row %d (%s): actual access_date must be YYYY-MM-DD; received %r.' % (line,source_id,raw_date));continue
            if accessed>today:
                issue('SOURCE_DATE_FUTURE','Row %d (%s): access_date %s is after current date %s (Asia/Ho_Chi_Minh). Use evidence of the actual access; do not invent a replacement date.' % (line,source_id,accessed,today))
    except (OSError,ValueError,csv.Error,UnicodeError):
        issue('SOURCE_FORMAT','Cannot validate evidence provenance: invalid UTF-8/CSV/source URL.')
    return findings


def delivery_issues(artifacts, include_handoff=False):
    import csv
    import datetime
    import json
    import pathlib
    import re
    from urllib.parse import unquote, urlsplit

    root = pathlib.Path(artifacts)
    names = {
        'campaign_brief.json', 'market_research.md', 'competitor_analysis.md',
        'audience_segments.json', 'customer_journey.md', 'evidence_digest.md',
        'sources.csv', 'brand_positioning.md', 'campaign_strategy.md',
        'strategy_ids.json', 'media_plan.csv', 'budget_scenarios.csv',
        'creative_brief.md', 'creative_matrix.csv', 'measurement_plan.md',
        'experiment_plan.csv', 'advertising_strategy.md', 'execution_calendar.csv',
        'qa_report.json', 'handoff_notes.md', 'manifest.json',
        'Campaign_Plan.xlsx', 'Campaign_Presentation.pptx',
        'visit_log_template.csv', 'daily_report_template.csv', 'prelaunch_checklist.csv',
    }
    findings = []
    if include_handoff:
        manifest_path = root.parent / 'internal' / 'banner_manifest.json'
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
            if manifest.get('status') == 'CREATED':
                names.add('asset_manifest.json')
                for asset in manifest.get('assets', []):
                    rel = pathlib.PurePosixPath(asset.get('path', ''))
                    if (not rel.is_absolute() and '..' not in rel.parts and rel.parts
                            and rel.parts[0] == 'banners' and rel.suffix == '.png'):
                        names.add(str(rel))
        except (OSError, ValueError, TypeError, AttributeError):
            pass  # Build independently checks manifest integrity before copying.

    def issue(file, code, message):
        findings.append({'file': file, 'code': code, 'message': message})

    def reference(file, target):
        target = unquote(target.strip()).split('#', 1)[0].split('?', 1)[0]
        if not target or target.startswith(('http://', 'https://', 'mailto:')):
            return
        if target not in names:
            issue(file, 'DELIVERY_REFERENCE', 'Use an existing delivery filename, not an internal/unknown path: ' + target)

    files = ['advertising_strategy_draft.md']
    if include_handoff:
        files.append('handoff_notes.md')
    for file in files:
        path = root / file
        if not path.is_file():
            continue  # The Gate/Build already handles mandatory missing files.
        text = path.read_text(encoding='utf-8-sig')
        heading = next((line for line in text.splitlines() if line.strip()), '')
        if re.search(r'bản nháp|\bdraft\b|\brework\b|chờ\s+(?:gate|qa|strategy_qa)', heading, re.I):
            issue(file, 'DELIVERY_TITLE', 'Use a neutral client title; review status belongs in handoff/manifest.')
        if file == 'advertising_strategy_draft.md':
            if re.search(r'^\s*#{1,6}\s+(?:Bàn giao nhận được|Nhật ký (?:rework|thay đổi))\s*$', text, re.I | re.M) or re.search(r'^\s*FILE ĐÃ ĐỔI\s*:', text, re.I | re.M):
                issue(file, 'INTERNAL_NOTES', 'Move handoff receipts and rework history to internal/assembly_notes.md.')
        # Ignore real web URLs, while preserving positions for useful errors.
        local_text=re.sub(r'https?://[^\s<>"`\[\]()\\]+',lambda m:' '*len(m.group()),text,flags=re.I)
        local_match=re.search(r'artifacts[/\\]|code_workspace[/\\]|advertising_strategy_draft\.md|(?<![A-Za-z0-9_])[A-Za-z]:[/\\]', local_text)
        if local_match:
            issue(file, 'INTERNAL_REFERENCE', 'Client documents must refer to delivered filenames, not workspace/draft paths; line %d, matched %r.' % (text.count('\n',0,local_match.start())+1,local_match.group()))
        for target in re.findall(r'\[[^\]\n]*\]\(<?([^\s)>]+)>?(?:\s+"[^"]*")?\)', text):
            reference(file, target)
        for target in re.findall(r'`([^`\n]+\.(?:md|csv|json|xlsx|pptx))`', text):
            reference(file, target)

    sources = root / 'sources.csv'
    if sources.is_file():
        try:findings.extend(source_issues_csv(sources.read_bytes()))
        except OSError:issue('sources.csv','SOURCE_FORMAT','Cannot read sources.csv')
    return findings
