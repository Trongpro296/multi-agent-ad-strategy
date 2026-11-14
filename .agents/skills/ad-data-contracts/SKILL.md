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


ĐỒNG BỘ THỬ NGHIỆM V2:
Đọc experiment_plan.csv và measurement_plan.md hiện hành; giữ lịch, tiền, variant, concept, metric và điều kiện sẵn sàng nhất quán với Media/Creative/calendar. Chưa có hợp đồng từ nhánh Performance thì ghi dependency còn thiếu, không tạo một phép thử khác mâu thuẫn. Rework phải giữ đủ 20 cột experiment theo schema mới; không tự điền dữ liệu nền hoặc xác nhận tracking để vượt Gate.

## Độ dài và tái sử dụng đầu vào
Viết phần nghiệp vụ của vai trò, dẫn file/claim ID thay chép lại brief. Chat tóm tắt file, kết luận và giới hạn; giữ quyết định cuối nếu có. Đọc lại sau ghi, không lặp load khi nguồn chưa đổi. Mốc độ dài trong nhiệm vụ là tham khảo, không cắt schema hoặc bằng chứng để đủ số từ.

## Truyền bảng CSV qua save_file
Chỉ khi vai trò được giao xuất CSV: content của save_file có thể là chuỗi JSON gồm columns (tên cột theo schema) và rows (mảng object có đúng các key cột). Ưu tiên cách này để Python tự quote nội dung có dấu phẩy, dấu ngoặc kép hoặc xuống dòng và lưu UTF-8 BOM. Không bỏ dấu tiếng Việt để sửa số cột. Không dùng cấu trúc này cho qa_report.json hoặc publication JSON. Không tự thay dữ liệu thiếu bằng 0 hoặc cắt/ghép ô.

## URL và ngày nguồn
Nguồn external phải có URL tuyệt đối http/https và access_date thực tế YYYY-MM-DD, không trong tương lai. Dùng URL và dấu thời gian thực tế của lần truy cập; ngày chiến dịch hoặc TRUSTED_RUNTIME_DATE chỉ là thông tin thời gian, không chứng minh đã mở trang. Không tự thêm ngày, đổi loại nguồn hoặc xóa dòng để né kiểm tra. Nếu chỉ có tài liệu bàn giao, ghi đúng xuất xứ và phạm vi, không biến thành lần truy cập web mới. sources.csv được kiểm trước ghi và trước bàn giao; lỗi nguồn không gửi Assembler sửa thuyết minh lặp lại.
