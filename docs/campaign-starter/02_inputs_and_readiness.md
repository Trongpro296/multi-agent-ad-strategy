# Đầu vào và mức sẵn sàng

Chỉ chọn VERIFIED khi có kết quả kiểm và bằng chứng; chưa kiểm giữ PENDING. Người phụ trách chưa có ghi CẦN CHỈ ĐỊNH.

## 1. Tài liệu gửi Agent

| Nhóm | Đầu vào cần cung cấp | Tình trạng | Người cung cấp |
|---|---|---|---|
| Sản phẩm | Mô tả, giá, quy cách, điều kiện ưu đãi và chính sách | CHƯA CUNG CẤP | CẦN CHỈ ĐỊNH |
| Bằng chứng | Tài liệu chứng minh từng claim, phạm vi và thời hạn nếu có | CHƯA CUNG CẤP | CẦN CHỈ ĐỊNH |
| Khách hàng | Nhu cầu/tình huống mua đã quan sát, nguồn và giới hạn | CHƯA CUNG CẤP | CẦN CHỈ ĐỊNH |
| Kinh doanh | Báo cáo tổng hợp, kỳ dữ liệu và cách tính kết quả | CHƯA CUNG CẤP | CẦN CHỈ ĐỊNH |
| Quảng cáo cũ | Chi tiêu, kết quả, định nghĩa KPI và kỳ báo cáo nếu có | CHƯA CUNG CẤP | CẦN CHỈ ĐỊNH |
| Nội dung | Logo, ảnh/video thật, hướng dẫn thương hiệu và quyền sử dụng | CHƯA CUNG CẤP | CẦN CHỈ ĐỊNH |
| Vận hành | Tồn kho/năng lực phục vụ, giờ trực, quy trình xác nhận khách/đơn | CHƯA CUNG CẤP | CẦN CHỈ ĐỊNH |

Mỗi file kèm: file nói gì, nguồn/chủ sở hữu, ngày/kỳ dữ liệu, được dùng để phát hành hay chỉ tham khảo. Không đưa mật khẩu, API key hoặc danh sách cá nhân khách hàng vào brief; dùng dữ liệu tổng hợp phù hợp. Không có dữ liệu cũ thì ghi CHƯA CÓ, không tạo báo cáo giả.

## 2. Claim cần xác minh

| Claim dự kiến | Nguồn/file/đoạn | Điều nguồn thực sự chứng minh | Phạm vi/giới hạn | Người duyệt | Trạng thái |
|---|---|---|---|---|---|
| CẦN LIỆT KÊ | CHƯA CÓ | CHƯA XÁC MINH | CẦN ĐIỀN | CẦN CHỈ ĐỊNH | PENDING |

Không biến phản hồi một khách thành kết quả bảo đảm cho mọi khách. Nguồn không hỗ trợ đúng claim thì sửa thông điệp hoặc giữ claim ngoài nội dung phát hành.

## 3. Năm điều kiện trước triển khai

| ID | Việc kiểm thực tế | Chủ trì | Kết quả/bằng chứng | Trạng thái |
|---|---|---|---|---|
| TRACKING | Thử hành động chính, nguồn dữ liệu, mã chiến dịch, đơn vị và khử trùng | CẦN CHỈ ĐỊNH | CHƯA KIỂM | PENDING |
| ASSETS | Có nội dung/hình/video cuối, quyền sử dụng và người duyệt | CẦN CHỈ ĐỊNH | CHƯA KIỂM | PENDING |
| ACCOUNT_SETUP | Đúng tài khoản/kênh, quyền truy cập và khả năng thanh toán | CẦN CHỈ ĐỊNH | CHƯA KIỂM | PENDING |
| OFFER_CLAIMS | Giá/ưu đãi/điều kiện đúng, claim có căn cứ để phát hành | CẦN CHỈ ĐỊNH | CHƯA KIỂM | PENDING |
| OPERATIONS | Người tiếp nhận, quy trình xử lý và năng lực phục vụ | CẦN CHỈ ĐỊNH | CHƯA KIỂM | PENDING |

NOT_APPLICABLE cần lý do rõ ràng, không dùng để né việc chưa làm. Checklist này là đầu vào con người, không thay báo cáo QA của workflow.

## 4. Hợp đồng đo lường

- KPI kinh doanh và điều kiện tính: CẦN CHỐT.
- Đơn vị: CẦN CHỐT (người, hội thoại, lượt nhóm, đơn, lịch... không tự hoán đổi).
- Nguồn ghi nhận và hiện trạng: CẦN CHỐT.
- Cách phân biệt nguồn trả phí/tự nhiên/chưa rõ: CẦN CHỐT.
- Cách loại trùng và xử lý dữ liệu thiếu: CẦN CHỐT; chưa rõ không đổi thành 0.
- Người ghi, người đối soát, lịch chốt số và múi giờ: CẦN CHỐT.
- Chi tiêu thực tế lấy từ đâu, loại tiền và kỳ báo cáo: CẦN CHỐT.
- Điều kiện dừng để xử lý sự cố hoặc vượt ngân sách: CẦN CHỦ DỰ ÁN DUYỆT; không tự áp một ngưỡng mặc định.

Biểu mẫu vận hành chính thức do Build tạo sau duyệt. Nếu không đo lượt ghé, điều chỉnh bản sao mẫu theo KPI đã chốt, không ép mọi hành động thành “lượt khách”.
