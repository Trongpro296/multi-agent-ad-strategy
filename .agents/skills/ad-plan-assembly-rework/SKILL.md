---
name: ad-plan-assembly-rework
description: Tổng hợp kế hoạch quảng cáo và sửa đúng artifacts theo phản hồi Gate/QA/Human
  mà vẫn giữ brief và phiên bản hiện hành.
---

# ad-plan-assembly-rework

## Tổng hợp có đối chiếu
Load brief, Strategy, Evidence và ba bàn giao Media/Creative/Performance. Ghi tình trạng ĐÃ NHẬN/THIẾU/KHÔNG HỢP LỆ cho từng phần bắt buộc ở đầu bản nháp. Không dựng lại nguồn nghiên cứu còn thiếu chỉ để qua Gate.

Đối chiếu chuỗi goal/segment/offer/concept với kênh, chi tiêu, CTA/điểm đến và KPI. Giải quyết mâu thuẫn dựa trên brief và căn cứ; ghi quyết định, không chỉ nối nguyên văn các báo cáo. Lịch triển khai cần thời gian sản xuất, cấu hình tracking và review trước launch, người phụ trách, deliverable và phụ thuộc. Chỉ đặt ngày trong campaign; không tự kéo dài chiến dịch.

advertising_strategy_draft.md dùng các mục ##: Tóm tắt điều hành; Thị trường và đối thủ; Khách hàng; Định vị; Chiến lược; Kênh và ngân sách; Sáng tạo; Đo lường và thử nghiệm; Lịch triển khai; Rủi ro; Giả định và vấn đề còn mở; Phụ lục nguồn.

## Khi được yêu cầu sửa
Đọc file hiện hành trước khi sửa: message Planner cũ không phải bản đúng sau các vòng rework. Gắn lỗi → file/cột → cách sửa → tác động tới phần thuyết minh. Lỗi CSV/phân bổ cần sửa chính CSV bằng save_file, rồi cập nhật draft; không chỉ viết rằng đã sửa trong chat.

Có thể sửa bảng triển khai và lịch để đáp ứng phản hồi nhưng không đổi sản phẩm, mục tiêu, ad_spend hoặc dữ kiện nguồn. Không sửa qa_report, manifest hoặc snapshot review. Nếu yêu cầu làm đổi brief ở mức lớn, ghi CẦN LẬP LẠI TỪ BRIEF, không lách bằng số liệu mới.

Đầu bản nháp ghi FILE ĐÃ ĐỔI và lý do từng file. Load lại các file đã sửa; không tự tuyên bố PLAN: OK/QA: PASS hoặc phát token nội bộ. Chỉ Gate/QA/Controller quyết định đi tiếp.

## File phải lưu

- `artifacts/advertising_strategy_draft.md`
- `artifacts/execution_calendar.csv`

`execution_calendar.csv` giữ nguyên thứ tự header:

```csv
week,start,end,channel,activity,owner,deliverable
```

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không gửi cả bộ file dài vào chat; tóm tắt việc đã làm, giới hạn và đường dẫn, trừ khi node yêu cầu hiển thị đầy đủ.
