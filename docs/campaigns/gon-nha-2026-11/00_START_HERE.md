# Gọn Nhà — hồ sơ dự án thử nghiệm thương mại

Chuẩn bị ngày 2026-11-14, múi giờ Asia/Saigon.

## Quyết định dự án

Xây dựng kế hoạch ra mắt dịch vụ dọn căn hộ theo giờ tại khu vực Bình Thạnh, TP.HCM, tên làm việc **Gọn Nhà**. Đây là tên và mô hình kinh doanh mới được đề xuất, không đại diện doanh nghiệp đang hoạt động hoặc thương hiệu đã được xác lập quyền sử dụng.

| Hạng mục | Quyết định lập kế hoạch |
|---|---|
| Dịch vụ chủ lực | Ca dọn căn hộ 3 giờ, phạm vi thỏa thuận trước |
| Giá dự kiến | 279.000 VND/ca, chưa duyệt để công bố, chưa xác minh giá vốn/phụ phí |
| Địa bàn | Khu vực thường gọi là Bình Thạnh, TP.HCM; chốt vùng phục vụ thực tế trước phát hành |
| Khách ưu tiên | Người đi làm sống ở căn hộ, muốn thuê dọn định kỳ; giả thuyết cần kiểm chứng |
| Mục tiêu | Hội thoại đủ điều kiện; theo dõi tiếp báo giá, lịch xác nhận và ca hoàn thành |
| Kênh | Facebook, tiếp nhận qua Messenger; trang/tài khoản chưa tạo hoặc chưa xác minh |
| Thời gian đề xuất | 2026-11-23 đến 2026-12-06, 14 ngày |
| Ngân sách | 3.000.000 VND: quảng cáo 2.100.000, nội dung 900.000, khác 0 |
| Dự báo | Chưa ước lượng: không có baseline CPL, tỷ lệ chốt hoặc doanh thu |

Các con số là quyết định đề xuất để lập kế hoạch theo phạm vi người dùng ủy quyền; chưa phải ngân sách đã chi, giá đã bán hay kết quả kinh doanh. Không tự bật quảng cáo.

## Sử dụng ngay trên ChatDev

1. Restart backend để nạp các bản sửa CSV/retry, rồi mở lại `ad_agency_v2.yaml` có Human review.
2. Chạy `uv run python tools/preflight_ad_agency.py` từ thư mục gốc dự án nếu chưa kiểm cấu hình hiện tại.
3. Đính kèm `01_BRIEF.md`, `02_RESEARCH.md`, `03_OFFER_AND_INBOX.md`, `04_READINESS_AND_MEASUREMENT.md`, `07_SOURCES.json`. Nếu đọc attachment gặp giới hạn, dùng bản prompt tự chứa thông tin chính.
4. Dán toàn bộ `05_RUN_PROMPT.txt` và Launch. Cho phép nghiên cứu web khi tool tìm kiếm đã hoạt động; nếu tool không có/lỗi thì dùng nguồn đính kèm với ngày đọc đã ghi, không khai vừa xác minh lại.
5. Trả lời brief bằng dữ liệu trong hồ sơ. Việc chưa có nhân sự/tracking phải giữ là điều kiện mở, không tự khai đã hoàn thành.
6. Dừng tại `Client_Review`, theo `06_REVIEW_AND_NEXT_STEPS.md`. Chấp nhận kế hoạch không đồng nghĩa cho phép chi tiền.

## Hồ sơ gồm gì?

- `01_BRIEF.md`: brief đã điền, phân biệt đề xuất và dữ kiện chưa có.
- `02_RESEARCH.md`: nghiên cứu 3 đơn vị có nguồn chính thức, giới hạn dữ liệu và hàm ý.
- `03_OFFER_AND_INBOX.md`: phạm vi dịch vụ, nháp nội dung, kịch bản nhận khách và cách tính khả thi.
- `04_READINESS_AND_MEASUREMENT.md`: điều kiện triển khai và hợp đồng KPI.
- `05_RUN_PROMPT.txt`: prompt đầy đủ, dùng trực tiếp.
- `06_REVIEW_AND_NEXT_STEPS.md`: tiêu chí duyệt và công việc sau kế hoạch.
- `07_SOURCES.json`: danh mục URL đã đọc, thời điểm và giới hạn.

Đây là hồ sơ đầu vào do người chuẩn bị dự án soạn, không phải báo cáo QA hay bộ output 26 file đã được workflow tạo. Không chèn sẵn artifact, hash, phê duyệt hoặc số liệu thực tế vào session.
