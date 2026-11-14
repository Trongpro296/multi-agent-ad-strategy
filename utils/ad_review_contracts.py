"""Versioned measurement/QA contracts, embedded into standalone advertising scripts."""


def experiment_issues(artifacts):
    import csv
    import datetime
    import json
    import pathlib
    import re
    from decimal import Decimal, InvalidOperation

    root = pathlib.Path(artifacts)
    problems = []
    required = ('test_type', 'sample_unit', 'sample_basis', 'data_source',
                'business_kpi', 'decision_supported', 'decision_not_supported',
                'decision_owner', 'prerequisites', 'missing_data_rule', 'start', 'end')
    try:
        with (root / 'experiment_plan.csv').open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f, strict=True)
            if not set(required).issubset(reader.fieldnames or []):
                return ['experiment_plan.csv: missing measurement v2 columns; regenerate using the current contract']
            rows = list(reader)
        brief = json.loads((root / 'campaign_brief.json').read_text(encoding='utf-8-sig'))
        campaign_start = datetime.date.fromisoformat(brief['start_date'])
        campaign_end = datetime.date.fromisoformat(brief['end_date'])
    except (OSError, ValueError, KeyError, TypeError, csv.Error):
        return ['experiment_plan.csv: cannot read experiment dates/columns and campaign range']
    seen = set()
    for line, row in enumerate(rows, 2):
        prefix = 'experiment_plan.csv row %d: ' % line
        for field in required:
            if not str(row.get(field) or '').strip():
                problems.append(prefix + 'missing ' + field)
        identifier = str(row.get('test_id') or '').strip()
        if not identifier or identifier in seen:
            problems.append(prefix + 'test_id must be nonempty and unique')
        seen.add(identifier)
        if row.get('test_type') not in ('TECHNICAL_CHECK', 'CREATIVE_EXPLORATION', 'BUSINESS_EVALUATION'):
            problems.append(prefix + 'invalid test_type')
        if str(row.get('variant_a') or '').strip() == str(row.get('variant_b') or '').strip():
            problems.append(prefix + 'variants must describe different treatments')
        try:
            dates = [str(row.get(key) or '') for key in ('start', 'end')]
            if not all(re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) for value in dates):
                raise ValueError('ISO dates required')
            start, end = map(datetime.date.fromisoformat, dates)
            duration = Decimal(str(row.get('duration_days')))
            if not duration.is_finite() or start > end or duration != (end - start).days + 1:
                raise ValueError('duration mismatch')
            if start < campaign_start or end > campaign_end:
                raise ValueError('outside campaign')
        except (ValueError, InvalidOperation):
            problems.append(prefix + 'start/end must be inside campaign and match duration_days inclusively')
    return problems


def qa_report_issues(report, plan_version, review_files):
    """Validate structure and decision consistency; never certify semantic truth."""
    if not isinstance(report, dict):
        return ['QA v2 report must be an object']
    problems = []
    if report.get('schema_version') != '2.0':
        problems.append('QA schema_version must be 2.0; a legacy PASS is not sufficient')
    if report.get('plan_version') != plan_version or report.get('plan_gate_status') != 'OK':
        problems.append('QA must match the current plan_version and successful Gate')
    verdict = report.get('verdict')
    if verdict not in ('PASS', 'REVISE', 'BLOCKED'):
        problems.append('invalid QA verdict')
    allowed_files = set(review_files)

    def text(value):
        return isinstance(value, str) and bool(value.strip())

    def references(value, location):
        if not isinstance(value, list) or not value:
            problems.append(location + ': evidence_refs must identify reviewed files/locations')
            return
        for ref in value:
            if not isinstance(ref, dict) or not text(ref.get('file')) or ref['file'] not in allowed_files or not text(ref.get('location')):
                problems.append(location + ': invalid evidence file/location; file must be a filename in review_manifest.files (not the manifest itself), and location must be nonempty')

    criteria_ids = {'BRIEF_ALIGNMENT', 'EVIDENCE', 'CROSS_FILE_CONSISTENCY', 'BUDGET',
                    'EXPERIMENTS', 'MEASUREMENT', 'DELIVERY', 'IMPLEMENTATION_CONDITIONS'}
    criteria = report.get('criteria_results')
    if not isinstance(criteria, list) or not all(isinstance(row, dict) for row in criteria):
        problems.append('criteria_results must contain the eight review criteria')
        criteria = []
    ids = [row.get('criterion_id') for row in criteria]
    if len(ids) != len(criteria_ids) or any(not isinstance(key, str) for key in ids) or set(str(key) for key in ids) != criteria_ids:
        problems.append('criteria_results must contain each required criterion exactly once')
    for row in criteria:
        status = row.get('status')
        if status not in ('PASS', 'FAIL', 'NOT_REVIEWED') or not text(row.get('rationale')):
            problems.append('criterion requires valid status and rationale')
        if status != 'NOT_REVIEWED':
            references(row.get('evidence_refs'), 'criterion ' + str(row.get('criterion_id')))
        if verdict == 'PASS' and status != 'PASS':
            problems.append('QA PASS requires every criterion to pass')

    issues = report.get('issues')
    if not isinstance(issues, list):
        problems.append('issues must be a list')
        issues = []
    if verdict == 'PASS' and issues:
        problems.append('QA PASS cannot contain unresolved issues')
    if verdict in ('REVISE', 'BLOCKED') and (not issues or not any(row.get('status') != 'PASS' for row in criteria)):
        problems.append('REVISE/BLOCKED needs actionable issues and a non-passing criterion')
    issue_ids = set()
    for row in issues:
        if not isinstance(row, dict):
            problems.append('issue must be an object')
            continue
        identifier = row.get('id')
        if not text(identifier) or str(identifier) in issue_ids:
            problems.append('issue IDs must be nonempty and unique')
        issue_ids.add(str(identifier))
        if row.get('severity') not in ('high', 'medium', 'low'):
            problems.append('issue '+str(identifier)+': invalid severity '+repr(row.get('severity'))+'; use high, medium or low (lowercase)')
        missing = [k for k in ('area', 'description', 'fix', 'owner') if not text(row.get(k))]
        if missing:
            problems.append('issue '+str(identifier)+': missing/nonempty text required: '+', '.join(missing))
        references(row.get('evidence_refs'), 'issue ' + str(identifier))

    assumptions = report.get('open_assumptions')
    if not isinstance(assumptions, list):
        problems.append('open_assumptions must be a list, including when empty')
        assumptions = []
    assumption_ids = set()
    for row in assumptions:
        if not isinstance(row, dict) or not all(text(row.get(k)) for k in ('id', 'description', 'impact', 'owner')):
            problems.append('open assumption must identify id, description, impact and owner')
            continue
        if row['id'] in assumption_ids:
            problems.append('open assumption IDs must be unique')
        assumption_ids.add(row['id'])
        references(row.get('evidence_refs'), 'assumption ' + row['id'])

    condition_ids = {'TRACKING', 'ASSETS', 'ACCOUNT_SETUP', 'OFFER_CLAIMS', 'OPERATIONS'}
    conditions = report.get('prelaunch_conditions')
    if not isinstance(conditions, list) or not all(isinstance(row, dict) for row in conditions):
        problems.append('prelaunch_conditions must contain the five readiness checks')
        conditions = []
    ids = [row.get('condition_id') for row in conditions]
    if len(ids) != len(condition_ids) or any(not isinstance(key, str) for key in ids) or set(str(key) for key in ids) != condition_ids:
        problems.append('prelaunch_conditions must contain each required check exactly once')
    statuses = []
    for row in conditions:
        status = row.get('status')
        statuses.append(status)
        if status not in ('PENDING', 'VERIFIED', 'BLOCKED', 'NOT_APPLICABLE') or not all(text(row.get(k)) for k in ('description', 'owner', 'verification')):
            problems.append('prelaunch condition needs status, description, owner and verification basis/action')
        references(row.get('evidence_refs'), 'condition ' + str(row.get('condition_id')))
    expected = 'NOT_READY' if verdict != 'PASS' or 'BLOCKED' in statuses else 'CONDITIONAL' if 'PENDING' in statuses else 'READY'
    readiness = report.get('implementation_readiness')
    if not isinstance(readiness, dict) or readiness.get('status') != expected or not text(readiness.get('reason')):
        problems.append('implementation_readiness must match verdict/conditions: ' + expected)
    if not text(report.get('review_summary')):
        problems.append('review_summary must explain the conclusion and material limits')
    return problems


class QAWriteValidationError(ValueError):
    def __init__(self, path, detail):
        self.path = path
        super().__init__('QA report rejected before writing '+path+': '+detail+
                         '. File unchanged. Correct the report and call save_file again; do not change the verdict merely to pass validation.')


def validate_qa_write(workspace, data):
    import json
    from pathlib import Path
    path = 'artifacts/qa_report.json'
    try:
        report = json.loads(data.decode('utf-8-sig'))
        manifest = json.loads((Path(workspace)/'review/review_manifest.json').read_text(encoding='utf-8-sig'))
        if not isinstance(manifest, dict) or not isinstance(manifest.get('files'), dict) or not manifest['files']:
            raise ValueError('missing/nonempty review_manifest.files required')
        problems = qa_report_issues(report, manifest.get('plan_version'), manifest['files'])
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise QAWriteValidationError(path, 'invalid JSON/report/current review manifest: '+str(exc)) from exc
    if problems:
        raise QAWriteValidationError(path, '; '.join(problems))
