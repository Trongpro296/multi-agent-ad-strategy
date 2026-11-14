---
name: ad-tracking-readiness
description: Kiểm tra mức sẵn sàng đo lường từ quảng cáo tới lead/đơn hàng khi Performance hoặc QA cần xác định điều kiện trước launch; không tự triển khai tracking.
---

# Mức sẵn sàng tracking

Dùng cho Performance_Analyst và Strategy_QA. Đánh giá điều kiện đo lường cho đúng KPI của brief; không coi một kế hoạch tracking là hệ thống đã cài hoặc đã hoạt động.

## Đi theo một luồng chuyển đổi

Đọc brief, funnel, measurement_plan và dữ liệu kiểm tra được cung cấp. Theo dấu từ kênh → link/điểm đến → hành động → lead/đơn → kết quả xác nhận. Với mỗi bước, xác định event/ghi nhận, nguồn dữ liệu, người phụ trách, định danh liên kết và phần có thể bị mất dấu.

Phân biệt các mức: đã kiểm chứng bằng bằng chứng hiện hành; được người dùng khai báo; chưa có; chưa kiểm chứng; không áp dụng. Không suy trạng thái 'đã cài' từ việc có website, tên pixel, tài khoản analytics hoặc một ảnh dashboard. Nếu có tool kiểm thử được phép thì ghi hành động, thời điểm và kết quả thực; nếu không, đưa bước kiểm thử cho người thực thi.

## Những điều phải đối chiếu

- Conversion có định nghĩa rõ và phân biệt inquiry/lead đủ điều kiện/đơn xác nhận/thanh toán/hủy; event không bị dùng lẫn.
- Quy ước UTM nhất quán giữa kênh, campaign và nội dung, với quy tắc giữ/ghi nhận nguồn tới lead hoặc đơn. Không đưa PII hay khóa bí mật vào URL hoặc báo cáo.
- ID giao dịch/lead và quy tắc khử trùng phù hợp. Không cộng báo cáo nền tảng và CRM như hai tập chuyển đổi độc lập khi có thể trùng người/đơn.
- Timestamp, múi giờ, currency, cửa sổ quy gán và độ trễ báo cáo nhất quán; nêu khác biệt thay vì ép hai nguồn bằng nhau.
- Event thử có thể phân biệt với production; phép thử không được tạo đơn thanh toán thật hoặc làm nhiễu báo cáo nếu chưa được cho phép.

Nếu doanh nghiệp dùng Messenger/điện thoại/bán tại quầy, đề xuất sổ ghi nhận hoặc CRM tối giản có mã nguồn, lead ID, trạng thái và giá trị; nêu giới hạn quy gán. Không ép website/pixel khi brief không có hạ tầng đó.

## Điều kiện trước triển khai

Phân loại mỗi thiếu sót theo ảnh hưởng tới KPI chính. Thiếu đo KPI chính cần điều kiện xử lý hoặc phương án đo thủ công được chấp thuận trước khi khuyên launch; thiếu một chỉ số phụ không tự động chặn toàn chiến dịch.

Bàn giao checklist: bước funnel, KPI/event, dữ liệu cần, trạng thái và bằng chứng, lỗi/giới hạn, người sửa, kiểm thử chấp nhận. Ghi vào measurement_plan hoặc qa_report theo quyền node; không tự thêm file, sửa website/tài khoản, bật tag hoặc phát verdict ngoài hợp đồng workflow.


## Báo cáo đúng vai trò và mức sẵn sàng
Performance_Analyst ghi hiện trạng tracking, nguồn dữ liệu, owner và phép kiểm cần thực hiện trong measurement_plan.md; không tự ghi QA hoặc handoff_notes.md. Strategy_QA dùng QA schema 2.0 để tách chất lượng kế hoạch khỏi mức sẵn sàng triển khai. Kiểm riêng TRACKING, ASSETS, ACCOUNT_SETUP, OFFER_CLAIMS, OPERATIONS; VERIFIED cần bằng chứng thực tế, PENDING cần việc và người xác nhận, không áp dụng phải có lý do. PASS không đồng nghĩa READY. Chưa có kiểm chứng thì giữ điều kiện mở, không tự coi tracking/asset đã được tạo hoặc chiến dịch đã chạy.

## Độ dài và tái sử dụng đầu vào
Viết phần nghiệp vụ của vai trò, dẫn file/claim ID thay chép lại brief. Chat tóm tắt file, kết luận và giới hạn; giữ quyết định cuối nếu có. Đọc lại sau ghi, không lặp load khi nguồn chưa đổi. Mốc độ dài trong nhiệm vụ là tham khảo, không cắt schema hoặc bằng chứng để đủ số từ.
