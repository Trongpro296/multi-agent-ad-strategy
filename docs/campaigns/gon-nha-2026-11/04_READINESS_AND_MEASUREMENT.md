# Điều kiện và đo lường

## 1. Trạng thái trước triển khai

Người dùng là chủ dự án/người duyệt kế hoạch. Các vai trò dưới đây mới là phân công cần có, chưa có người nhận việc thực tế.

| ID | Việc cần làm | Vai trò cần phân công | Trạng thái | Bằng chứng cần có |
|---|---|---|---|---|
| TRACKING | Sổ lead/booking, mã chiến dịch GN2611, phân loại nguồn và thử luồng | Người vận hành + người đối soát | PENDING | Lần thử tin nhắn/lead mẫu được ghi và loại khỏi báo cáo thật |
| ASSETS | Ảnh dịch vụ thật, quyền sử dụng, nội dung cuối, tên thương hiệu | Người nội dung + chủ dự án | PENDING | File gốc, đồng ý sử dụng và duyệt nội dung |
| ACCOUNT_SETUP | Trang, tài khoản, quyền truy cập, thanh toán và giới hạn chi tiêu | Người quản trị tài khoản | PENDING | Kiểm thực tế trong tài khoản, không gửi khóa/mật khẩu vào Agent |
| OFFER_CLAIMS | Chi phí, giá/phụ phí, phạm vi, đổi/hủy và claim | Chủ dự án + người điều phối dịch vụ | PENDING | Bảng chi phí và chính sách được chấp nhận |
| OPERATIONS | Người làm, vùng, lịch ca, người trực, dụng cụ và xử lý sự cố | Người điều phối dịch vụ | PENDING | Lịch nhận việc, khả năng đáp ứng và lần thử nội bộ |

Hạn chuẩn bị đề xuất 2026-11-22; thiếu điều kiện thì hoãn, không tự đánh dấu VERIFIED. Việc tuân thủ yêu cầu vận hành liên quan do đơn vị triển khai xác minh trước phục vụ; hồ sơ không tự xác nhận đủ điều kiện hoạt động.

## 2. KPI và sổ dữ liệu

- Đơn vị chính: một người có hội thoại đủ điều kiện trong đợt. Dùng mã nội bộ/pseudonym, không đưa dữ liệu cá nhân khách vào file gửi model.
- lead_qualified: đúng vùng, nhu cầu phù hợp, đủ thông tin phân loại và đồng ý trao đổi báo giá; loại tin tuyển dụng/spam/đối tác chào bán.
- quote_sent: báo giá thực đã gửi; không tính nháp chưa gửi.
- booking_confirmed: hai bên đã thống nhất giá, phạm vi và lịch, có người thực hiện.
- completed: ca thật đã hoàn thành; revenue_collected: khoản thật đã thu, tách hủy/hoàn.
- Nguồn: paid_verified khi có dấu vết quảng cáo kiểm được; paid_self_reported khi khách tự khai; organic_verified khi có căn cứ; unknown khi thiếu. Không cộng các nhãn chồng lấp thành nhiều khách.
- Chi tiêu lấy từ báo cáo tài khoản đúng kỳ, VND; ngày đóng sổ theo Asia/Saigon. Chưa có dữ liệu thì để thiếu, không ghi số 0 giả.

Trường sổ lead cần có: lead_id, first_contact_date, campaign_code, source_type, source_evidence_ref, area_eligible, service_fit, requested_window, qualification_status, exclusion_reason, quote_ref, booking_id, booking_status, completed_date, revenue_collected, missing_flags, owner.

Địa chỉ chi tiết/thông tin liên hệ nếu thực sự cần vận hành được giữ ở hệ thống nội bộ có phân quyền; bản gửi Agent chỉ dùng tổng hợp hoặc mã tham chiếu.

## 3. Nhịp theo dõi và quyết định

- Trước mở: thử luồng tiếp nhận và ghi nhận, xóa/đánh dấu dữ liệu thử khỏi báo cáo thật.
- Mỗi ngày: đối soát chi tiêu, lead hợp lệ, lịch nhận được, lỗi dữ liệu và tồn đọng. Giờ chốt do người phụ trách thống nhất trước khi mở.
- Giữa kỳ: 2026-11-29, xem chất lượng hội thoại, khả năng phục vụ và tính đầy đủ dữ liệu; không tuyên bố biến thể thắng khi chưa đủ cơ sở.
- Cuối kỳ: 2026-12-06 và đối soát sau kỳ cho lịch/hoàn tiền còn mở; không gộp doanh thu khác kỳ mà không nêu rõ.
- Dừng nhận lịch nếu chưa có người thực hiện; xử lý/tạm dừng phát hành nếu claim sai, dữ liệu nguồn lỗi, không kiểm được chi tiêu hoặc có sự cố dịch vụ. Đây là đề xuất quy tắc để chủ dự án chấp nhận trước mở.
- Không tự tăng tiền vì chưa đủ lead. Giữ trần 2.100.000 quảng cáo và 3.000.000 tổng; không bảo đảm cơ chế ngân sách nền tảng chặn chính xác nếu chưa kiểm tài khoản/cách thiết lập.

Không đặt ngưỡng học thống kê hay dự báo số lead từ ngân sách. Một thử nghiệm thăm dò creative là đủ phạm vi; kiểm kỹ thuật nằm trong checklist chuẩn bị, không tạo thêm test chi tiền không cần thiết.
