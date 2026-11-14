# Hồ sơ bắt đầu chiến dịch thực tế

Trạng thái: bộ mẫu đã chuẩn bị, chưa có dữ liệu doanh nghiệp. Các ô `[CẦN ĐIỀN]` không phải thông tin đã xác nhận; đừng Launch nguyên bộ mẫu.

## Thứ tự sử dụng

1. Điền `01_campaign_brief.md`: chốt sản phẩm, mục tiêu, địa bàn, ngân sách và ngày.
2. Hoàn thành danh mục đầu vào và người phụ trách trong `02_inputs_and_readiness.md`.
3. Thay các ô trong `03_workflow_prompt.txt`, dán brief đã điền và đính kèm tài liệu được phép dùng trên giao diện.
4. Restart backend sau cập nhật code. Từ thư mục dự án, chạy:

   ```powershell
   uv run python tools/preflight_ad_agency.py
   ```

5. Mở lại `ad_agency_v2.yaml`, dùng bản có người duyệt. Preflight kiểm cấu hình cục bộ, không chứng minh model/gateway luôn hoạt động hoặc chiến lược hiệu quả.
6. Launch một phiên. Nếu Brief hỏi, trả lời thông tin thiếu; không điền giả để vượt Gate.
7. Tại `Client_Review`, theo `04_review_and_launch.md`. Sau duyệt, Build mới tạo bộ bàn giao 26 file. Trước Build, đọc artifact hiện hành và báo cáo review.

## Bộ hồ sơ

| File | Công dụng |
|---|---|
| `01_campaign_brief.md` | Thông tin kinh doanh, mục tiêu, ngân sách và giới hạn |
| `02_inputs_and_readiness.md` | Tài liệu, bằng chứng, tài sản, tracking và người phụ trách |
| `03_workflow_prompt.txt` | Prompt đưa vào workflow sau khi điền thông tin |
| `04_review_and_launch.md` | Duyệt kế hoạch, kiểm trước triển khai và theo dõi thực tế |

## Chưa thực hiện

Chưa chọn doanh nghiệp, xác minh thị trường, cấu hình tài khoản/tracking, tạo asset cuối, gọi model hoặc chi ngân sách. Không có giá, ngày, ngân sách hay claim nào được tự đặt thay chủ dự án.

Hướng dẫn hệ thống: [ad_agency_v2_guide.md](../../ad_agency_v2_guide.md).
Giữ mẫu trống trong Git; bản điền dữ liệu kinh doanh nội bộ nên lưu riêng và chỉ chia sẻ phần được phép.
