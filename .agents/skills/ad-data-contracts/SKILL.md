---
name: ad-data-contracts
description: Chuẩn hóa hoặc sửa CSV/JSON quảng cáo, định dạng số và quan hệ ID khi tạo bảng Media, Performance hoặc rework; không thay thế Gate bằng code.
---

# Hợp đồng dữ liệu quảng cáo

Áp dụng khi node cần tạo/sửa dữ liệu máy đọc, nhất là Media_Planner, Performance_Analyst và Plan_Assembler. Giữ vai trò, danh sách file được phép ghi và dòng quyết định của System Prompt; skill này không mở rộng quyền sửa file.

## Xác định hợp đồng trước khi sửa

Đọc file hiện hành, schema trong nhiệm vụ và lỗi Gate nếu có. Phân biệt lỗi biểu diễn, lỗi số học, lỗi tham chiếu và thiếu dữ liệu nguồn. Khi làm với bộ ad_agency_v2, xem [references/current-schema.md](references/current-schema.md) để lấy header và ví dụ; nếu nhiệm vụ dùng schema mới, đối chiếu với schema thực thay vì ép về mẫu cũ.

Chỉ dùng load_file/list_directory/save_file đã được node cấp. Không tự cài package hoặc gọi execute_code nếu công cụ đó không có. Chỉ nói đã chạy validator/build khi có kết quả công cụ tương ứng.

## Sửa biểu diễn mà không đổi ý nghĩa

- CSV dùng encoding utf-8-sig để Excel đọc tiếng Việt, một header, thứ tự cột đúng hợp đồng; quote ô có dấu phẩy, dấu nháy hoặc xuống dòng. Không nhét code fence hoặc lời giải thích ngoài bảng vào file.
- Số máy đọc dùng dấu chấm thập phân, không đơn vị, dấu phân cách hàng nghìn hoặc %. Không đoán 1,200 có nghĩa 1200 hay 1.2; kiểm nguồn/đơn vị, hỏi hoặc báo thiếu khi không xác định được. Không loại ký tự rồi âm thầm đổi giá trị.
- Với budget_scenarios.csv, chỉ để metric_value trống khi estimate_status=NOT_ESTIMATED và assumption nêu rõ dữ liệu thiếu. ESTIMATED vẫn cần số hữu hạn không âm, formula và assumption. Không coi NOT_ESTIMATED là dự báo bằng 0 hoặc kết quả đã chứng minh.
- Phân biệt budget_pct=25 trong bảng với tỷ lệ 0.25 khi tính công thức. Không tự nhân/chia 100 nếu chưa biết đơn vị. Không dùng 0 thay cho unknown hoặc mẫu số bằng 0.
- JSON phải hợp lệ, có đúng kiểu object/mảng; dùng number cho tiền và số lượng, không phải chuỗi chứa đơn vị. Không có NaN/Infinity, comment, dấu phẩy cuối hoặc tên khóa trùng.
- Ngày phải là ngày thật dạng YYYY-MM-DD, đúng thời gian campaign. min_sample/duration_days là số nguyên dương; diễn giải cỡ mẫu để trong decision_rule.

## Quan hệ và dữ liệu lặp

Kiểm segment_id/offer_id với strategy_ids.json; không tự đổi tên ID để qua kiểm tra, không xóa dòng có ID lạ nếu chưa hiểu tác động. Không tạo offer/nhóm khách hàng mới trong lúc sửa định dạng.

media_plan cộng tiền theo các dòng phân bổ thực tế. Với budget_scenarios, cùng (scenario, channel) có thể lặp ngân sách qua nhiều metric: chỉ tính chi tiêu một lần cho cặp đó, nhưng mọi giá trị lặp phải bằng nhau; (scenario, channel, metric) phải duy nhất. Không deduplicate mù để che mâu thuẫn.

## Bàn giao

Sửa đúng file/cột được giao, cập nhật thuyết minh liên quan nếu node có quyền. Giữ nguyên brief, manifest và snapshot. Lưu rồi load lại từng file đã đổi; ghi lỗi gốc, cách sửa, file đổi và kiểm tra còn thiếu trong phần bàn giao hiện có. Không tự thêm file báo cáo hoặc cột mới khi workflow chưa cho phép; quyết định PLAN/QA vẫn do node có thẩm quyền phát.
