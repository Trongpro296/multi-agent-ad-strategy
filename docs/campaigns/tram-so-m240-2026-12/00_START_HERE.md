# TRẠM SỐ — M240: bộ đầu vào chặt cho workflow quảng cáo

Sản phẩm có thật, claim kỹ thuật được giới hạn theo nguồn hãng. Giá, ngân sách và cách tổ chức là quyết định được người dùng ủy quyền chọn, không phải số liệu vận hành đã quan sát. Không tạo kho hàng, lịch sử, tài khoản hoặc quyền ảnh giả.

1. Khởi động lại backend để nạp bản sửa Publication_QA và nạp ad_agency_v2.yaml hiện hành. Không dùng recovery cũ cho dự án mới.
2. Có thể upload 01_CLIENT_BRIEF.json, 02_PRODUCT_TRUTH.json, 03_ACCEPTANCE_RULES.md, 04_SOURCES.md. Chúng là tài liệu đầu vào, không phải artifact đầu ra để ghi đè thủ công.
3. Dán toàn bộ 05_RUN_PROMPT.txt và Launch. Prompt tự đủ dữ liệu nếu không upload.
4. Khi Client_Review hỏi, xem kế hoạch và nhập HUMAN: APPROVE một lần.
5. Lấy nội dung đăng từ publish/, kịch bản từ production/. Kiểm nguồn hàng, ảnh thật, tài khoản và tracking trước khi thực sự chạy ads.

Bộ này giảm phạm vi suy diễn: một sản phẩm, một offer, một phân khúc, một nền tảng, một phép thử; các số tiền/ngày và nguồn claim đã đối chiếu. Prompt không bảo đảm model/provider không bao giờ lỗi tool; schema và khả năng sửa vẫn cần code runtime. Không có workflow/model/ảnh nào được tự chạy khi chuẩn bị bộ này.
