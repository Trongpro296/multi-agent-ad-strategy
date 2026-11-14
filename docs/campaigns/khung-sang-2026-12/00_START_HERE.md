# Khung Sáng — dự án thử nghiệm thương mại mới

Chuẩn bị ngày 2026-11-14. Đề bài: ra mắt dịch vụ chụp ảnh sản phẩm cho shop online tại TP.HCM.

Khung Sáng là tên làm việc của một phương án kinh doanh mới, chưa phải studio được xác nhận đang hoạt động. Những lựa chọn về sản phẩm/giá/tiền/lịch do người chuẩn bị đề xuất theo ủy quyền; không phải bằng chứng đã có khách hoặc khả năng cung cấp dịch vụ.

| Hạng mục | Phương án |
|---|---|
| Dịch vụ | 10 SKU sản phẩm nhỏ, 20 ảnh hoàn thiện, nền đơn giản |
| Giá để lập phương án | 1500000 VND/gói, phải kiểm giá vốn/phạm vi/thuế/phí trước công bố |
| Khách ưu tiên | Shop bán phụ kiện/gia dụng nhỏ tại TP.HCM, cần ảnh đăng bán |
| Kênh | Facebook, tiếp nhận qua Messenger; trang và tài khoản chưa xác minh |
| Mục tiêu | Yêu cầu báo giá đủ điều kiện, theo dõi đến booking và bàn giao thật |
| Thời gian | 2026-12-01 đến 2026-12-14, 14 ngày, Asia/Saigon |
| Tiền | 4000000 VND: 2800000 quảng cáo + 1200000 nội dung, khác 0 |
| Trạng thái | Lập kế hoạch được, chưa được đăng/chạy hoặc nhận lịch khách thật |

## Bắt đầu trên giao diện

1. Mở `ad_agency_v2.yaml` sau khi backend đã nạp các bản sửa gần nhất. Tải lại frontend nếu chưa thấy khung nhập mới.
2. Add files: đính kèm `01_BRIEF_AND_SOURCES.md`; chờ thẻ file chuyển Ready. Không cần đính kèm chính file prompt.
3. Copy toàn bộ `02_RUN_PROMPT.txt` vào ô nhập rồi Launch. Prompt có đủ dữ liệu chính để dùng cả khi không đính kèm.
4. Nếu Brief hỏi, trả lời bằng hồ sơ này; điều chưa xác minh giữ là điều kiện mở, không khai nhân sự/tài sản đã có.
5. Đến Client_Review: kiểm đúng plan_version và QA. Chưa đồng ý thì HUMAN: REVISE kèm góp ý; chỉ khi chấp nhận kế hoạch mới dùng đúng dòng HUMAN: APPROVE.
6. Khi bật AD_BANNER_ENABLED=1, sau duyệt kế hoạch node ảnh có thể gửi tối đa 2 request qua 9Router, có thể phát sinh phí/quota. Ảnh AI là minh họa DRAFT, không phải portfolio thật của studio.

Không cần tự chạy lại toàn bộ nếu một bước lỗi: giữ session ID, đọc diagnostic và cân nhắc recovery. Bộ file này là đầu vào; chưa có workflow/model nào được chạy thay bạn.
