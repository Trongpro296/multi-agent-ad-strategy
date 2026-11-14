---
name: ad-plan-assembly-rework
description: Tổng hợp kế hoạch quảng cáo và sửa đúng artifacts theo phản hồi Gate/QA/Human
  mà vẫn giữ brief và phiên bản hiện hành.
---

# ad-plan-assembly-rework

## Tổng hợp có đối chiếu
Load brief, Strategy, Evidence và ba bàn giao Media/Creative/Performance. Ghi tình trạng ĐÃ NHẬN/THIẾU/KHÔNG HỢP LỆ trong internal/assembly_notes.md, không đưa vào bản kế hoạch khách hàng. Không dựng lại nguồn nghiên cứu còn thiếu chỉ để qua Gate.

Đối chiếu chuỗi goal/segment/offer/concept với kênh, chi tiêu, CTA/điểm đến và KPI. Giải quyết mâu thuẫn dựa trên brief và căn cứ; ghi quyết định, không chỉ nối nguyên văn các báo cáo. Lịch triển khai cần thời gian sản xuất, cấu hình tracking và review trước launch, người phụ trách, deliverable và phụ thuộc. Chỉ đặt ngày trong campaign; không tự kéo dài chiến dịch.

advertising_strategy_draft.md dùng các mục ##: Tóm tắt điều hành; Thị trường và đối thủ; Khách hàng; Định vị; Chiến lược; Kênh và ngân sách; Sáng tạo; Đo lường và thử nghiệm; Lịch triển khai; Rủi ro; Giả định và vấn đề còn mở; Phụ lục nguồn.

## Khi được yêu cầu sửa
Đọc file hiện hành trước khi sửa: message Planner cũ không phải bản đúng sau các vòng rework. Gắn lỗi → file/cột → cách sửa → tác động tới phần thuyết minh. Lỗi CSV/phân bổ cần sửa chính CSV bằng save_file, rồi cập nhật draft; không chỉ viết rằng đã sửa trong chat.

Có thể sửa bảng triển khai và lịch để đáp ứng phản hồi nhưng không đổi sản phẩm, mục tiêu, ad_spend hoặc dữ kiện nguồn. Không sửa qa_report, manifest hoặc snapshot review. Nếu yêu cầu làm đổi brief ở mức lớn, ghi CẦN LẬP LẠI TỪ BRIEF trong ghi chú và nêu giới hạn ở phần vấn đề còn mở, không lách bằng số liệu mới.

Ghi FILE ĐÃ ĐỔI và lý do từng file vào internal/assembly_notes.md. Load lại các file đã sửa; không tự tuyên bố PLAN: OK/QA: PASS hoặc phát token nội bộ. Chỉ Gate/QA/Controller quyết định đi tiếp.

## File phải lưu

- `artifacts/advertising_strategy_draft.md`
- `artifacts/execution_calendar.csv`

`execution_calendar.csv` giữ nguyên thứ tự header:

```csv
week,start,end,channel,activity,owner,deliverable
```

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không dán lại toàn bộ file vào Chat; tóm tắt việc đã làm, giới hạn và đường dẫn, giữ câu hỏi/issue và dòng trạng thái cuối nếu có. Node sau đọc file thật bằng load_file.


TIÊU CHUẨN BẢN KẾ HOẠCH SẠCH:
- File làm việc vẫn là artifacts/advertising_strategy_draft.md nhưng tiêu đề phải trung tính, ví dụ “Kế hoạch quảng cáo — <thương hiệu>”. Không ghi bản nháp, rework, chờ Gate/QA hoặc tự ghi đã duyệt trong tiêu đề. Không dự đoán kết quả Gate/QA/Human.
- Tóm tắt điều hành 5–8 ý: mục tiêu, đối tượng, lựa chọn chiến lược, tiền, lịch, điều kiện trước launch và người quyết định. Giữ các mục nghiệp vụ đã quy định; không đưa nhật ký workflow lên đầu tài liệu khách hàng.
- Tình trạng nhận Media/Creative/Performance/Evidence, FILE ĐÃ ĐỔI, lý do sửa và lỗi QA được ghi trong internal/assembly_notes.md và tóm tắt chat. Đây là ghi chú vận hành, không phải nguồn bằng chứng hoặc file bàn giao, không tự cấp phiên bản.
- Khi sửa một quyết định, lập bảng tác động file → đoạn/cột → cách sửa trong ghi chú nội bộ; đọc lại toàn bộ tài liệu liên quan. Có thể sửa bảng triển khai và thuyết minh chiến lược/sáng tạo/đo lường theo phản hồi trong phạm vi brief. Không viết lại brief, market_research.md, competitor_analysis.md, audience_segments.json, customer_journey.md, evidence_digest.md hoặc sources.csv để che lỗi nguồn; không sửa QA/manifest/snapshot.
- Nếu claim nguồn chưa được hỗ trợ, bỏ nó khỏi kết luận sử dụng và ghi giới hạn trong Giả định/vấn đề còn mở. Đồng thời báo rõ file nguồn chưa khắc phục trong ghi chú; không nói đã đồng bộ toàn bộ bộ hồ sơ. Nếu cần thay dữ kiện nguồn hoặc lập lại brief, yêu cầu dừng để chủ nguồn xử lý; không bịa căn cứ.


ĐỒNG BỘ THỬ NGHIỆM V2:
Đọc experiment_plan.csv và measurement_plan.md hiện hành; giữ lịch, tiền, variant, concept, metric và điều kiện sẵn sàng nhất quán với Media/Creative/calendar. Chưa có hợp đồng từ nhánh Performance thì ghi dependency còn thiếu, không tạo một phép thử khác mâu thuẫn. Rework phải giữ đủ 20 cột experiment theo schema mới; không tự điền dữ liệu nền hoặc xác nhận tracking để vượt Gate.

## Độ dài và tái sử dụng đầu vào
Viết phần nghiệp vụ của vai trò, dẫn file/claim ID thay chép lại brief. Chat tóm tắt file, kết luận và giới hạn; giữ quyết định cuối nếu có. Đọc lại sau ghi, không lặp load khi nguồn chưa đổi. Mốc độ dài trong nhiệm vụ là tham khảo, không cắt schema hoặc bằng chứng để đủ số từ.

## Truyền bảng CSV qua save_file
Chỉ khi vai trò được giao xuất CSV: content của save_file có thể là chuỗi JSON gồm columns (tên cột theo schema) và rows (mảng object có đúng các key cột). Ưu tiên cách này để Python tự quote nội dung có dấu phẩy, dấu ngoặc kép hoặc xuống dòng và lưu UTF-8 BOM. Không bỏ dấu tiếng Việt để sửa số cột. Không dùng cấu trúc này cho qa_report.json hoặc publication JSON. Không tự thay dữ liệu thiếu bằng 0 hoặc cắt/ghép ô.
