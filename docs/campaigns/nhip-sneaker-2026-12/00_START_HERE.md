# NHỊP Sneaker — bộ đầu vào chiến dịch

Thông số thương hiệu, sản phẩm, giá, ngân sách và cách vận hành đã được điền theo ủy quyền người dùng. Đây là các quyết định kinh doanh để áp dụng, không phải dữ liệu lịch sử được xác minh. Không có đơn hàng, doanh thu, tồn kho, tài khoản hoặc ảnh sản phẩm thật giả được tạo.

1. Khởi động backend với code mới và nạp `ad_agency_v2.yaml` (có Publication_Editor và Publication_QA).
2. Có thể upload `01_BRIEF.json` và `02_MARKET_SOURCES.md`.
3. Dán nội dung `03_RUN_PROMPT.txt` vào ô nhập, bấm Launch. Prompt tự đủ dữ liệu nếu không upload.
4. Xem bản kế hoạch tại Client_Review; nhập `HUMAN: APPROVE` để duyệt và ủy quyền hoàn thiện bộ cuối một lần.
5. Lấy bài/ảnh từ publish/, kịch bản từ production/. Các điều kiện về hàng thật, tài khoản, tracking cần hoàn tất trước khi chạy quảng cáo thật.

Bộ đầu vào không tự chạy workflow, tạo ảnh, đăng bài hoặc chi tiền. Không có lịch sử kết quả nên forecast giữ NOT_ESTIMATED thay vì số liệu giả.
