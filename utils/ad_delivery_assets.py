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
        textbox(s, .65, .35, 12, 1.1, title, 24, navy, True)
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
            header_lines = [wrap(plain(header[i]), width - .16, 13) for i in indexes]
            header_height = max(.5, max(map(len, header_lines)) * .24 + .16)
            if header_height > 1.5:
                # Unusually verbose headers remain readable in a dedicated text page.
                text_pages(title + ' — tên cột', [plain(header[i]) for i in indexes])
                displayed = [str(i + 1) for i in indexes]
                header_height = .5
            else:
                displayed = ['\n'.join(lines) for lines in header_lines]
            chunks = []
            for row in body:
                cells = [wrap(plain(row[i] if i < len(row) else ''), width - .16, 13) for i in indexes]
                for offset in range(0, max(map(len, cells)), 10):
                    values = ['\n'.join(cell[offset:offset + 10]) for cell in cells]
                    height = max(.44, max(len(cell[offset:offset + 10]) for cell in cells) * .24 + .16)
                    chunks.append((values, height))
            while chunks:
                selected, height = [], header_height
                while chunks and height + chunks[0][1] <= 5.15:
                    values, row_height = chunks.pop(0)
                    selected.append((values, row_height)); height += row_height
                s = slide(title)
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
                            paragraph.font.name, paragraph.font.size = font_name, Pt(13)
                            paragraph.font.bold = rindex == 0
                            paragraph.font.color.rgb = RGBColor.from_string('FFFFFF' if rindex == 0 else navy)
                            paragraph.line_spacing = Pt(16)

    md = (root / 'advertising_strategy.md').read_text(encoding='utf-8-sig')
    lines = md.splitlines()
    title = plain(next((line.lstrip('# ').strip() for line in lines if line.strip()), 'Kế hoạch quảng cáo'))
    cover = slide('Chiến lược quảng cáo')
    title_lines = wrap(title, 11.7, 28)
    if len(title_lines) <= 5:
        textbox(cover, .8, 2.1, 11.7, 2.7, '\n'.join(title_lines), 28, navy, True)
    else:
        textbox(cover, .8, 2.1, 11.7, 1, 'Bộ kế hoạch và điều kiện triển khai', 28, navy, True)
        text_pages('Tên kế hoạch', [title])
    textbox(cover, .8, 5.5, 11.7, .8, 'QA: ' + qa['verdict'] + '\nChỉ trình bày kế hoạch; chưa xác nhận chiến dịch đã chạy.', 18, teal)
    text_pages('Kết luận và điều kiện trước launch', [qa['review_summary'], qa['implementation_readiness']['reason']] +
               [item['condition_id'] + ' — ' + item['status'] + ': ' + item['description'] + ' | ' + item['owner'] + ' | ' + item['verification'] for item in qa['prelaunch_conditions']])
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
