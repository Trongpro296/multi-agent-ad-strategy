"""Deterministic, standalone export for the existing Python workflow runtime."""


def build_delivery_assets(folder, qa, plan_version):
    import csv
    import datetime
    import json
    import math
    import pathlib
    import re
    import textwrap
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Inches, Pt
    from PIL import ImageFont

    root = pathlib.Path(folder)
    templates = {
        'visit_log_template.csv': ['date', 'time', 'visit_id', 'unit', 'people_count', 'receipt_refs', 'asked_status',
                                   'response_status', 'source_raw', 'source_category', 'campaign_code', 'campaign_relation',
                                   'recorder', 'missing_flag', 'duplicate_flag', 'notes'],
        'daily_report_template.csv': ['date', 'unit', 'observed_total', 'asked', 'not_asked', 'answered', 'campaign_related',
                                      'paid_self_reported', 'code_observed', 'facebook_paid_unknown', 'missing', 'duplicates',
                                      'ad_spend', 'currency', 'data_status', 'notes'],
        'prelaunch_checklist.csv': ['condition_id', 'description', 'status', 'owner', 'verification', 'evidence_refs'],
    }
    checklist = [{**item, 'evidence_refs': '; '.join(ref['file'] + ': ' + ref['location'] for ref in item['evidence_refs'])}
                 for item in qa['prelaunch_conditions']]
    for filename, header in templates.items():
        with (root / filename).open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=header)
            writer.writeheader()
            if filename == 'prelaunch_checklist.csv':
                writer.writerows({key: row.get(key, '') for key in header} for row in checklist)

    wb = load_workbook(root / 'Campaign_Plan.xlsx')
    overview = wb.create_sheet('Overview', 0)
    overview.append(['Hướng dẫn bộ kế hoạch', 'Giá trị / cách sử dụng'])
    brief = json.loads((root / 'campaign_brief.json').read_text(encoding='utf-8-sig'))
    for row in [
        ['Phiên bản', plan_version], ['QA kế hoạch', qa['verdict']],
        ['Sẵn sàng triển khai', qa['implementation_readiness']['status']],
        ['Giải thích mức sẵn sàng', qa['implementation_readiness']['reason']],
        ['Thời gian', str(brief.get('start_date', '')) + ' đến ' + str(brief.get('end_date', ''))],
        ['Tiền quảng cáo đã duyệt', brief.get('budget', {}).get('ad_spend')],
        ['Tiền sản xuất riêng', brief.get('budget', {}).get('production')],
        ['Tiền khác/dự phòng riêng', brief.get('budget', {}).get('other')],
        ['Đơn vị tiền', brief.get('budget', {}).get('currency', '')],
        ['Đọc trước', 'handoff_notes.md → advertising_strategy.md → các bảng và kế hoạch đo lường.'],
        ['Dự báo', 'Ô trống cùng NOT_ESTIMATED nghĩa là chưa đủ dữ liệu; không phải kết quả bằng 0.'],
        ['Biểu mẫu vận hành', 'Visit_Log và Daily_Report là mẫu trống, không phải dữ liệu đã thu. Không có số khách/hiệu quả giả.'],
        ['Chốt đơn vị', 'Chọn đúng đơn vị trong measurement_plan.md (người/lượt nhóm/lead/đơn); không tự chuyển đổi hoặc cộng trùng.'],
        ['Visit_Log', 'Ghi date + visit_id để khử trùng. Không thu tên/số điện thoại. Nếu campaign không đo lượt ghé, cần điều chỉnh biểu mẫu theo KPI trước sử dụng.'],
        ['Daily_Report', 'Các nhóm nguồn có thể giao nhau; không cộng paid_self_reported và code_observed thành tổng mới. Không điền 0 cho dữ liệu chưa biết.'],
        ['Checklist', 'Giữ nguyên trạng thái QA. VERIFIED là khai báo có căn cứ được QA xem xét; xuất file không tự thực hiện kiểm tra thực địa.'],
        ['Bản sao nhập liệu', 'Tạo bản sao workbook/CSV để nhập actuals; giữ bộ bàn giao gốc và manifest làm mốc đối chiếu.'],
        ['Giới hạn', 'QA PASS và bàn giao tài liệu không phải lệnh khởi chạy quảng cáo hoặc cam kết hiệu quả.'],
    ]:
        overview.append(row)
    for sheet, filename in [('Visit_Log', 'visit_log_template.csv'), ('Daily_Report', 'daily_report_template.csv'),
                            ('Prelaunch_Checklist', 'prelaunch_checklist.csv')]:
        ws = wb.create_sheet(sheet)
        with (root / filename).open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.reader(stream):
                ws.append(row)
        if sheet != 'Prelaunch_Checklist':
            for _ in range(20):
                ws.append([None] * len(templates[filename]))
    navy, teal, pale, gray = '17324D', '087F8C', 'E8F5F3', 'DEE5EC'
    for ws in wb:
        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = ws.dimensions
        ws.sheet_view.showGridLines = False
        headers = [str(cell.value or '') for cell in ws[1]]
        for index, header in enumerate(headers, 1):
            values = [str(ws.cell(row, index).value or '') for row in range(1, min(ws.max_row, 150) + 1)]
            width = 52 if header in ('assumption', 'decision_rule', 'verification', 'notes', 'description', 'sample_basis',
                                    'decision_supported', 'decision_not_supported', 'missing_data_rule') else min(36, max(16, max(map(len, values), default=16) + 2))
            ws.column_dimensions[get_column_letter(index)].width = width
        if ws.title == 'Overview':
            ws.column_dimensions['A'].width, ws.column_dimensions['B'].width = 29, 95
        for row in ws:
            lines = 1
            for cell in row:
                cell.font = Font(name='Calibri', size=11, color=navy)
                cell.alignment = Alignment(vertical='top', wrap_text=True)
                cell.border = Border(bottom=Side(style='hair', color=gray))
                value = cell.value
                if isinstance(value, str):
                    # LLM/source strings stay strings, including formula-looking text.
                    cell.data_type = 's'
                    width = ws.column_dimensions[cell.column_letter].width or 16
                    lines = max(lines, sum(max(1, math.ceil(len(part) / max(8, width - 2))) for part in value.split('\n')))
                    if row[0].row > 1 and headers[cell.column - 1] in ('start', 'end', 'date', 'access_date') and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                        cell.value = datetime.date.fromisoformat(value)
                        cell.number_format = 'yyyy-mm-dd'
                elif isinstance(value, (int, float)):
                    key = headers[cell.column - 1]
                    currency = str(brief.get('budget', {}).get('currency', '')).upper()
                    cell.number_format = '#,##0.########' if key == 'metric_value' else '#,##0.##'
                    if key == 'budget_pct':
                        cell.number_format = '0.##"%"'  # 25 means 25%, not 0.25.
                    elif key in ('budget_amount', 'ad_spend') and re.fullmatch(r'[A-Z]{3}', currency):
                        cell.number_format = '#,##0.## "' + currency + '"'
                if row[0].row > 1:
                    cell.fill = PatternFill('solid', fgColor='F4F8FB' if row[0].row % 2 == 0 else 'FFFFFF')
            ws.row_dimensions[row[0].row].height = min(320, max(25, lines * 15 + 7))
        for cell in ws[1]:
            cell.fill = PatternFill('solid', fgColor=navy)
            cell.font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
        ws.row_dimensions[1].height = 34
        ws.print_options.horizontalCentered = True
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.orientation = 'landscape'
        ws.page_setup.paperSize = ws.PAPERSIZE_A3
        ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
        ws.print_title_rows = '1:1'
    for cell in overview[4]:
        cell.fill = PatternFill('solid', fgColor='FFF1CC' if qa['implementation_readiness']['status'] != 'READY' else pale)
    for name, column, choices in [('Prelaunch_Checklist', 'C', 'PENDING,VERIFIED,BLOCKED,NOT_APPLICABLE'),
                                   ('Visit_Log', 'G', 'ASKED,NOT_ASKED'), ('Daily_Report', 'O', 'COMPLETE,PARTIAL,MISSING')]:
        validation = DataValidation(type='list', formula1='"' + choices + '"', allow_blank=True)
        validation.errorTitle, validation.error = 'Giá trị chưa hợp lệ', 'Chọn trạng thái trong danh sách.'
        validation.showErrorMessage = True
        wb[name].add_data_validation(validation)
        validation.add(column + '2:' + column + '1000')
    wb.save(root / 'Campaign_Plan.xlsx')

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    font_name = 'Arial'
    presentation_main = True
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
    from PIL import Image
    import hashlib
    import os

    def wrap(value, inches, points):
        candidates = ['C:/Windows/Fonts/arial.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
                      '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'DejaVuSans.ttf']
        font = None
        for candidate in candidates:
            try:
                font = ImageFont.truetype(candidate, round(points * 96 / 72))
                break
            except OSError:
                continue
        if font is None:
            return textwrap.wrap(value, max(10, int(inches * 72 / points)), break_long_words=True, break_on_hyphens=False) or ['']
        limit = inches * 96 * .94
        result, line = [], ''
        for word in value.split():
            proposed = (line + ' ' + word).strip()
            if font.getlength(proposed) <= limit:
                line = proposed
                continue
            if line:
                result.append(line); line = ''
            while font.getlength(word) > limit:
                count = 1
                while count < len(word) and font.getlength(word[:count + 1]) <= limit:
                    count += 1
                result.append(word[:count]); word = word[count:]
            line = word
        if line: result.append(line)
        return result or ['']

    def plain(value):
        value = re.sub(r'\[([^]]+)\]\(([^)]+)\)', r'\1 (\2)', value)
        return value.replace('**', '').replace('`', '').strip()

    def textbox(slide, x, y, w, h, text, size=18, color=navy, bold=False):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        frame = box.text_frame
        frame.word_wrap = True
        frame.margin_left = frame.margin_right = 0
        frame.margin_top = frame.margin_bottom = 0
        p = frame.paragraphs[0]
        p.text = text
        p.font.name, p.font.size, p.font.bold = font_name, Pt(size), bold
        p.font.color.rgb = RGBColor.from_string(color)
        p.line_spacing = Pt(size * 1.25)
        return box

    def slide(title):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = RGBColor(255, 255, 255)
        title_lines = wrap(title, 12, 30)
        textbox(s, .65, .35, 12, 1.1, '\n'.join(title_lines) if len(title_lines) <= 2 else 'Chi tiết kế hoạch', 30, navy, True)
        if len(title_lines) > 2:
            s.notes_slide.notes_text_frame.text = title
        textbox(s, .65, 7.06, 12, .25, 'Phiên bản ' + str(plan_version) + '  •  ' + qa['implementation_readiness']['status'] + '  •  ' + str(len(prs.slides)), 10, teal)
        return s

    def text_pages(title, paragraphs):
        # Explicit wrapping and pagination preserve all words; no character slicing.
        page, used = None, 0
        for paragraph in paragraphs:
            cleaned = plain(re.sub(r'^\s*(?:[-*+]\s+|#{1,6}\s+)', '', paragraph))
            if not cleaned:
                continue
            lines = wrap(cleaned, 11.8, 17)
            while lines:
                if page is None or used >= 15:
                    page, used = slide(title), 0
                take = min(len(lines), 15 - used)
                block, lines = lines[:take], lines[take:]
                textbox(page, .75, 1.55 + used * .31, 11.8, take * .31 + .1, '\n'.join(block), 17)
                used += take + 1

    def table_pages(title, rows):
        if not rows:
            return
        header, body = rows[0], rows[1:]
        count = len(header)
        # Wide tables repeat their identifying first column across column panels.
        groups = [list(range(count))] if count <= 6 else [[0] + list(range(start, min(start + 5, count))) for start in range(1, count, 5)]
        for indexes in groups:
            width = 11.8 / len(indexes)
            size = 17 if presentation_main else 13
            line_height = size * 1.25 / 72 + .02
            header_lines = [wrap(plain(header[i]), width - .16, size) for i in indexes]
            header_height = max(.5, max(map(len, header_lines)) * line_height + .16)
            if header_height > 1.5:
                # Unusually verbose headers remain readable in a dedicated text page.
                text_pages(title + ' — tên cột', [plain(header[i]) for i in indexes])
                displayed = [str(i + 1) for i in indexes]
                header_height = .5
            else:
                displayed = ['\n'.join(lines) for lines in header_lines]
            chunks = []
            for row in body:
                cells = [wrap(plain(row[i] if i < len(row) else ''), width - .16, size) for i in indexes]
                for offset in range(0, max(map(len, cells)), 10):
                    values = ['\n'.join(cell[offset:offset + 10]) for cell in cells]
                    height = max(.44, max(len(cell[offset:offset + 10]) for cell in cells) * line_height + .16)
                    chunks.append((values, height))
            while chunks:
                selected, height = [], header_height
                while chunks and height + chunks[0][1] <= 5.15:
                    values, row_height = chunks.pop(0)
                    selected.append((values, row_height)); height += row_height
                s = slide(title)
                notes(s, 'media_plan.csv; execution_calendar.csv; qa_report.json' if presentation_main else 'advertising_strategy.md', '\n'.join(' | '.join(row) for row in rows))
                table = s.shapes.add_table(len(selected) + 1, len(indexes), Inches(.75), Inches(1.55), Inches(11.8), Inches(height)).table
                table.rows[0].height = Inches(header_height)
                for rindex, (values, row_height) in enumerate([(displayed, header_height)] + selected):
                    table.rows[rindex].height = Inches(row_height)
                    for cindex, value in enumerate(values):
                        cell = table.cell(rindex, cindex)
                        cell.text = value
                        cell.margin_left = cell.margin_right = Inches(.08)
                        cell.margin_top = cell.margin_bottom = Inches(.04)
                        cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor.from_string(navy if rindex == 0 else ('F0F5F8' if rindex % 2 else 'FFFFFF'))
                        for paragraph in cell.text_frame.paragraphs:
                            paragraph.font.name, paragraph.font.size = font_name, Pt(size)
                            paragraph.font.bold = rindex == 0
                            paragraph.font.color.rgb = RGBColor.from_string('FFFFFF' if rindex == 0 else navy)
                            paragraph.line_spacing = Pt(size * 1.25)

    def notes(page, source, detail=''):
        page.notes_slide.notes_text_frame.text = 'Nguồn: ' + source + '\n' + detail

    def read_text(name):
        path = root / name
        return path.read_text(encoding='utf-8-sig') if path.exists() else ''

    def read_rows(name):
        path = root / name
        if not path.exists():
            return []
        with path.open(encoding='utf-8-sig', newline='') as stream:
            return list(csv.DictReader(stream))

    def display(value):
        if value is None or value == '':
            return 'Chưa có thông tin'
        if isinstance(value, dict):
            labels = {'name': 'Nhóm khách hàng', 'description': 'Đặc điểm', 'segment_id': 'Mã phân khúc', 'segments': 'Phân khúc'}
            return '\n'.join(labels.get(str(k), str(k)) + ': ' + display(v) for k, v in value.items())
        if isinstance(value, list):
            return '; '.join(display(v) for v in value)
        return plain(str(value))

    def excerpt(value, limit=7, width=11.8, size=20):
        # Select complete sentences, never slice a claim or remove its qualifier.
        paragraphs = re.split(r'\n+|(?<=[.!?;])\s+', display(value))
        selected, used = [], 0
        for paragraph in paragraphs:
            paragraph = plain(re.sub(r'^\s*(?:[-*+]\s+|#{1,6}\s+)', '', paragraph))
            if not paragraph or paragraph.startswith('|'):
                continue
            height = len(wrap(paragraph, width, size))
            if used + height > limit:
                if selected:
                    break
                continue
            selected.append(paragraph)
            used += height + 1
            if len(selected) == 3:
                break
        return '\n\n'.join(selected) if selected else 'Xem nội dung đầy đủ trong phụ lục và hồ sơ nguồn.'

    def narrative(title, value, source):
        page = slide(title)
        textbox(page, .75, 1.65, 11.8, 4.7, excerpt(value), 20)
        notes(page, source, display(value))
        return page

    def file_section(name, keywords=()):
        text = read_text(name)
        sections = re.split(r'(?m)^#{1,3}\s+', text)
        for section in sections:
            heading = section.split('\n', 1)[0].casefold()
            if any(key.casefold() in heading for key in keywords):
                return section
        return text

    # Optional creative assets must belong to the sealed publication for this plan.
    publication, banner_assets = None, []
    workspace = root.resolve().parent
    if os.environ.get('AD_PUBLICATION_REQUIRED') == '1':
        from utils.ad_publication import read, safe, sha, verify_review
        seal = os.environ.get('AD_PUBLICATION_APPROVAL_SHA256')
        approval_path = workspace / 'internal/publication_approval.json'
        if not seal or sha(approval_path) != seal:
            raise ValueError('PPTX requires the trusted publication approval seal')
        approval = read(approval_path)
        review = read(workspace / 'internal/publication_review.json')
        verify_review(workspace, review)
        if (review['plan_version'] != plan_version or approval.get('status') != 'APPROVED'
                or approval.get('release_id') != review['release_id']
                or approval.get('review_sha256') != sha(workspace / 'internal/publication_review.json')):
            raise ValueError('PPTX publication version/approval mismatch')
        publication = read(workspace / 'artifacts/publication_content.json')
        banner_assets = review.get('banner_assets', [])
        if publication['plan_version'] != plan_version:
            raise ValueError('PPTX public copy version mismatch')

    md = read_text('advertising_strategy.md')
    lines = md.splitlines()
    title = plain(next((line.lstrip('# ').strip() for line in lines if line.strip()), 'Kế hoạch quảng cáo'))
    brand = display((publication or {}).get('brand_name') or brief.get('brand_name') or brief.get('brand') or 'Kế hoạch chiến dịch')
    cover = slide('Kế hoạch chiến dịch')
    cover.background.fill.fore_color.rgb = RGBColor.from_string(navy)
    for shape in cover.shapes:
        if shape.has_text_frame:
            for paragraph in shape.text_frame.paragraphs:
                paragraph.font.color.rgb = RGBColor.from_string('FFFFFF')
    textbox(cover, .8, 1.9, 11.7, 1.0, excerpt(brand, 2, 11.7, 38), 38, 'FFFFFF', True)
    textbox(cover, .8, 3.3, 11.7, 1.9, excerpt(title, 4, 11.7, 24), 24, 'FFFFFF')
    period = str(brief.get('start_date', '')) + ' — ' + str(brief.get('end_date', ''))
    textbox(cover, .8, 5.65, 11.7, .7, period, 20, 'A6DDD7')
    notes(cover, 'campaign_brief.json; advertising_strategy.md', title)

    narrative('Quyết định chính', qa['review_summary'], 'qa_report.json / review_summary')
    narrative('Mục tiêu và phạm vi',
              'Mục tiêu: ' + display(brief.get('goal', brief.get('objective'))) + '\n'
              + 'Sản phẩm: ' + display(brief.get('product')) + '\n'
              + 'Thị trường: ' + display(brief.get('market', brief.get('region'))), 'campaign_brief.json')
    audience_path = root / 'audience_segments.json'
    audience = json.loads(audience_path.read_text(encoding='utf-8-sig')) if audience_path.exists() else brief.get('audience')
    narrative('Khách hàng ưu tiên', audience, 'audience_segments.json; campaign_brief.json')
    narrative('Bối cảnh và bằng chứng', file_section('advertising_strategy.md', ('thị trường', 'đối thủ')), 'advertising_strategy.md; evidence_digest.md; sources.csv')
    narrative('Định vị và thông điệp', file_section('advertising_strategy.md', ('định vị',)), 'advertising_strategy.md; brand_positioning.md')
    narrative('Chiến lược và hành trình chuyển đổi',
              file_section('advertising_strategy.md', ('chiến lược', 'hành trình', 'funnel')),
              'advertising_strategy.md; campaign_strategy.md; customer_journey.md')

    budget = brief.get('budget', {})
    currency = str(budget.get('currency') or '')
    labels = {'ad_spend': 'Quảng cáo', 'production': 'Sản xuất', 'other': 'Khoản khác'}
    known = [(label, budget[key]) for key, label in labels.items()
             if type(budget.get(key)) in (int, float) and math.isfinite(budget[key]) and budget[key] >= 0]
    budget_page = slide('Phân bổ ngân sách' + (' (' + currency + ')' if currency else ''))
    if known and any(amount > 0 for _, amount in known):
        data = CategoryChartData()
        data.categories = [label for label, _ in known]
        data.add_series('Ngân sách', [amount for _, amount in known])
        chart = budget_page.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(.8), Inches(1.6),
                                             Inches(11.5), Inches(3.9), data).chart
        chart.has_legend = False
        chart.category_axis.tick_labels.font.size = Pt(18)
        chart.value_axis.tick_labels.font.size = Pt(14)
        chart.value_axis.tick_labels.number_format = '#,##0'
        plot = chart.plots[0]
        plot.has_data_labels = True
        plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
        plot.data_labels.font.size = Pt(16)
        plot.data_labels.number_format = '#,##0'
        series = chart.series[0]
        series.format.fill.solid()
        series.format.fill.fore_color.rgb = RGBColor.from_string(teal)
        missing = [label for key, label in labels.items() if key not in budget or budget[key] is None]
        caption = 'Chỉ thể hiện các khoản có số liệu trong brief. Không phải kết quả chi tiêu thực tế.'
        if missing:
            caption += '\nChưa có số liệu: ' + ', '.join(missing) + '.'
        textbox(budget_page, .8, 5.85, 11.7, .9, caption, 17)
    else:
        textbox(budget_page, .8, 1.7, 11.7, 2, 'Chưa đủ số liệu ngân sách để vẽ biểu đồ. Xem brief và bảng Media.', 22)
    notes(budget_page, 'campaign_brief.json / budget', json.dumps(budget, ensure_ascii=False))

    media = read_rows('media_plan.csv')
    channel_groups = {}
    for row in media:
        channel_groups.setdefault((row.get('channel', ''), row.get('currency', '')), []).append(row)
    channel_rows = []
    for (channel, unit), items in channel_groups.items():
        amounts = []
        for item in items:
            try:
                amount = float(item['budget_amount'])
                if not math.isfinite(amount) or amount < 0:
                    raise ValueError('Invalid media budget for PPTX')
                amounts.append(amount)
            except (KeyError, ValueError):
                amounts = []
                break
        total = format(sum(amounts), ',.2f').rstrip('0').rstrip('.') + ' ' + unit if amounts else 'Chưa đủ số liệu'
        objectives = list(dict.fromkeys(r.get('objective', '') for r in items if r.get('objective')))
        dates = [r.get('start', '') for r in items] + [r.get('end', '') for r in items]
        channel_rows.append([channel, '\n'.join(objectives), total, min(dates) + ' → ' + max(dates)])
    table_pages('Kế hoạch kênh', [['Kênh', 'Mục tiêu', 'Ngân sách', 'Thời gian']] + channel_rows)
    narrative('Ý tưởng sáng tạo', file_section('advertising_strategy.md', ('sáng tạo', 'creative')), 'advertising_strategy.md; creative_brief.md; creative_matrix.csv')
    if publication:
        for asset in banner_assets:
            rel = 'artifacts/' + asset['path']
            path = safe(workspace, rel)
            if hashlib.sha256(path.read_bytes()).hexdigest() != review['files'].get(rel):
                raise ValueError('PPTX banner hash mismatch')
            item = next((b for b in publication['banners'] if b['id'] == asset['id']), None)
            if item is None:
                raise ValueError('PPTX banner has no approved public brief')
            page = slide('Banner ' + asset['id'])
            with Image.open(path) as image:
                width, height = image.size
            scale = min(5.0 / width, 5.0 / height)
            page.shapes.add_picture(str(path), Inches(.8 + (5.0 - width * scale) / 2),
                                   Inches(1.55 + (5.0 - height * scale) / 2),
                                   width=Inches(width * scale), height=Inches(height * scale))
            copy = item['headline'] + '\n\n' + item['cta']
            textbox(page, 6.25, 1.8, 6.1, 4.3, excerpt(copy, 9, 6.1, 22), 22)
            notes(page, 'publication_content.json / ' + item['id'],
                  copy + '\nMinh họa AI; nguồn và hash trong publication_manifest.json. Không xác nhận đã được người dùng duyệt thị giác riêng.')
        for post in publication['posts'][:2]:
            narrative('Bài đăng ' + post['id'], post['content'] + '\n' + post['cta'],
                      'publication_content.json / posts / ' + post['id'])
        for video in publication['video_scripts'][:2]:
            narrative('Kịch bản: ' + video['id'], video['title'] + '\n' + '\n'.join(
                str(scene['start']) + '–' + str(scene['end']) + 's: ' + scene['visual']
                for scene in video['scenes']), 'publication_content.json / video_scripts / ' + video['id'])

    calendar = read_rows('execution_calendar.csv')
    weeks = {}
    for row in calendar:
        weeks.setdefault(row.get('week') or row.get('start', ''), []).append(row)
    week_rows = []
    for week, items in weeks.items():
        starts = [r.get('start', '') for r in items if r.get('start')]
        ends = [r.get('end', '') for r in items if r.get('end')]
        period = (min(starts) if starts else '') + ' → ' + (max(ends) if ends else '')
        channels = ', '.join(dict.fromkeys(r.get('channel', '') for r in items))
        owners = ', '.join(dict.fromkeys(r.get('owner', '') for r in items))
        week_rows.append([period, channels, str(len(items)) + ' hoạt động', owners])
    table_pages('Lịch triển khai theo giai đoạn', [['Thời gian', 'Kênh', 'Khối lượng', 'Phụ trách']] + week_rows)
    narrative('Đo lường và quy tắc quyết định',
              file_section('advertising_strategy.md', ('đo lường', 'thử nghiệm', 'KPI')),
              'advertising_strategy.md; measurement_plan.md; experiment_plan.csv')
    narrative('Điều kiện triển khai', qa['implementation_readiness']['reason'],
              'qa_report.json / implementation_readiness')
    table_pages('Việc cần hoàn tất trước triển khai', [['Điều kiện', 'Trạng thái', 'Người phụ trách']] +
                [[c['condition_id'], c['status'], c['owner']] for c in qa['prelaunch_conditions']])

    divider = slide('Phụ lục · Kế hoạch đầy đủ')
    textbox(divider, .8, 2.2, 11.7, 2.5,
            'Nội dung chi tiết, bảng và các giới hạn của kế hoạch được giữ nguyên ở các trang tiếp theo.\n\n'
            'Bảng số liệu đầy đủ nằm trong Campaign_Plan.xlsx; nguồn và trạng thái triển khai nằm trong hồ sơ nội bộ.', 24)
    notes(divider, 'advertising_strategy.md; Campaign_Plan.xlsx')

    presentation_main = False
    section, paragraphs, index = 'Tổng quan', [], 1
    def flush():
        if paragraphs:
            text_pages(section, paragraphs)
            paragraphs.clear()
    while index < len(lines):
        line = lines[index]
        if line.startswith('## '):
            flush(); section = plain(line[3:]); index += 1; continue
        if line.strip().startswith('|') and index + 1 < len(lines) and re.fullmatch(r'\s*\|?[\s:|\-]+\|?\s*', lines[index + 1]):
            flush()
            rows = [[plain(cell) for cell in line.strip().strip('|').split('|')]]
            index += 2
            while index < len(lines) and lines[index].strip().startswith('|'):
                rows.append([plain(cell) for cell in lines[index].strip().strip('|').split('|')]); index += 1
            if len(rows) > 1: table_pages(section, rows)
            else: text_pages(section, [' | '.join(rows[0])])
            continue
        if line.strip() and not line.strip().startswith(chr(96) * 3):
            paragraphs.append(line)
        index += 1
    flush()
    prs.save(root / 'Campaign_Presentation.pptx')
    return ['Campaign_Plan.xlsx', 'Campaign_Presentation.pptx'] + list(templates)
