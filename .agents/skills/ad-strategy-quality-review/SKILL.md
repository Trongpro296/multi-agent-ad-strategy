---
name: ad-strategy-quality-review
description: Nghiệm thu độc lập kế hoạch quảng cáo bằng brief, Evidence, Gate và phiên
  bản; tạo báo cáo lỗi có thể hành động.
---

# ad-strategy-quality-review

## Đúng đầu vào và phiên bản
Đọc advertising_strategy_draft.md, brief, evidence_digest.md, sources.csv, các bảng liên quan và review/review_manifest.json. Dùng đúng plan_version hiện hành của Plan_Gate; không dùng báo cáo/vòng cũ. Nếu phiên bản trong message và manifest không nhất quán, nêu vấn đề, không tự chọn bản thuận tiện.

## Review theo rủi ro
Ưu tiên lỗi làm sai quyết định: vượt/nhầm ngân sách, ID không nối được, claim chưa có bằng chứng, funnel không thực hiện được, KPI không đo được, dự báo không có công thức/cơ sở, đầu vào bắt buộc thiếu và lịch phi thực tế. Gate OK chứng minh kiểm tra cấu trúc/số học đã chạy, không chứng minh chiến lược tốt. Không chạy lại việc cộng tiền bằng nhẩm hoặc dùng sở thích văn phong để bắt sửa không cần thiết.

Phân biệt lỗi phải sửa với giả thuyết đã được khai báo và chấp nhận thử nghiệm. Mỗi issue có id, severity, area, description, fix và owner=Plan_Assembler; nêu vị trí cụ thể và điều kiện được coi là đã sửa. Lỗi thiếu dữ liệu quyết định/nguồn không thể tái tạo cần BLOCKED, không giao Assembler nhiệm vụ bịa nghiên cứu.

## Báo cáo và quyết định nhất quán
qa_report.json có plan_version, verdict, plan_gate_status và issues[]. PASS chỉ khi không còn lỗi chặn, Gate OK, đủ bàn giao và mọi giả định còn mở được trình bày đúng. REVISE dùng khi Assembler có thể sửa trong phạm vi; BLOCKED khi không thể hoàn thành bằng vòng tổng hợp hiện tại. Không xóa dấu vết hoặc đổi snapshot để hợp thức hóa PASS.

Chỉ ghi qa_report.json, không sửa nguồn/draft. Dòng cuối phản hồi là QA: PASS hoặc QA: REVISE, đúng verdict trong file. Trường hợp BLOCKED ghi lý do và QA: BLOCKED; Router hiện tại chuyển sang nhánh dừng/invalid, không coi đó là PASS hay tự động rework. Không chép token hai ngoặc vuông vào output.

## File phải lưu

- `artifacts/qa_report.json`

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không gửi cả bộ file dài vào chat; tóm tắt việc đã làm, giới hạn và đường dẫn, trừ khi node yêu cầu hiển thị đầy đủ.
