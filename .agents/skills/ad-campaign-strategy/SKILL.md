---
name: ad-campaign-strategy
description: Chọn chiến lược quảng cáo, mục tiêu đo lường, phân khúc, offer và funnel
  nhất quán để các planner triển khai.
---

# ad-campaign-strategy

## Từ phân tích sang lựa chọn
Đọc brief, evidence, định vị và phân khúc. Chọn một hướng ưu tiên phù hợp mục tiêu, tiền quảng cáo, công suất phục vụ, tài sản và tracking; nêu hướng thay thế cùng điều kiện chuyển. Đừng biến mọi kênh/nhóm khách hàng thành ưu tiên ngang nhau.

Chuỗi lập luận phải nối: mục tiêu kinh doanh → hành vi chuyển đổi → phân khúc → vấn đề/lợi ích → offer → thông điệp → điểm đến → KPI. Nêu điểm nghẽn funnel và bằng chứng đỡ cho lựa chọn. Không đặt KPI doanh thu/ROAS số cụ thể nếu thiếu giá trị đơn, biên lợi nhuận, tracking hoặc cơ sở giả định được phép.

## Registry ID cho ba planner
strategy_ids.json dùng cấu trúc: goal{goal_id,statement,primary_kpi}; segments[{segment_id,name,priority}]; offers[{offer_id,description}]; funnel[]; alternatives[]; validation_conditions[]. ID phân khúc phải kế thừa audience_segments.json, không dựng nhóm mới bằng cách đổi nhãn. Offer phải đúng brief; ID G1/S1/O1... là tham chiếu dùng xuyên suốt, không đổi giữa hai file.

Nêu rõ giả định nào có thể làm chiến lược thất bại và cách kiểm chứng trước khi chi nhiều hơn. Thiếu thông tin trọng yếu thì chỉ ra thiếu, không lấp bằng dự báo vô căn cứ. Mục tiêu kiểm thử không biến thành cam kết kết quả thật.

campaign_strategy.md diễn giải hướng chọn/không chọn, funnel, KPI, vai trò các kênh, điều kiện triển khai, phương án thay thế và rủi ro. Lưu cả strategy_ids.json và load lại để kiểm ID; bàn giao cùng một chiến lược cho Media, Creative và Performance.

## File phải lưu

- `artifacts/campaign_strategy.md`
- `artifacts/strategy_ids.json`

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không gửi cả bộ file dài vào chat; tóm tắt việc đã làm, giới hạn và đường dẫn, trừ khi node yêu cầu hiển thị đầy đủ.
