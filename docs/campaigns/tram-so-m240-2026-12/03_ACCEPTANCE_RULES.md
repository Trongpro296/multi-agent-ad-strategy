# Quy tắc nghiệm thu đầu vào và đầu ra

## Một nguồn dữ kiện
- CLIENT_BRIEF giữ quyết định kinh doanh. PRODUCT_TRUTH giữ bốn claim được phép và giới hạn. SOURCES giữ URL. Không coi giá bán được chọn là giá hãng hoặc biến nhu cầu nhắm mục tiêu thành dữ liệu khảo sát.
- Chỉ một sản phẩm, S1/O1, một nền tảng. Không tự thêm SKU màu, quà, giảm giá, website hoặc số liên hệ.
- Agent chuyên môn dẫn file hiện hành, không chép số liệu từ message cũ sau khi file đã sửa.

## Số và lịch
- Ngân sách: 2.800.000 quảng cáo + 1.400.000 sản xuất = 4.200.000 VNĐ. Other=0 là quyết định ngân sách, không có nghĩa giá vốn/giao hàng bằng 0.
- 14 ngày: 07–20/12/2026, tính cả ngày đầu và cuối. Tuần 1: 07–13/12; tuần 2: 14–20/12.
- Hai hook cùng phân khúc/offer: mỗi hook 700.000 VNĐ/tuần. Không để thử nghiệm yêu cầu B chạy nhưng bảng media chỉ cấp tiền cho A.
- Công việc chuẩn bị trước 07/12 nằm trong checklist, không nhét vào execution_calendar.csv ngoài khung chiến dịch.
- Không có baseline nên không cam kết lead/đơn/CPL/CPA/ROAS. Dùng trạng thái thiếu dữ liệu theo hợp đồng node; không ước số cho đẹp bảng.

## Hợp đồng kỹ thuật
- Schema, tên trường, enum và token lấy từ System Prompt/skill đúng node và mẫu do engine phát. Bộ brief khách hàng không thay schema.
- Publication_QA dùng ad-publication-quality-review và JSON template đầu vào. Không dùng schema QA kế hoạch, không tự tính hoặc đặt plan_version/hash.
- evidence/source refs trong báo cáo cuối chỉ tên file thuộc snapshot và vị trí thực. Không dẫn review_manifest làm evidence file.
- Nếu tool từ chối ghi, sửa đúng lỗi được trả, không chỉ sửa lời chat; không đổi verdict để vượt kiểm tra.
- Kiểm tra nội dung công khai không buộc tracking hoặc tồn kho chưa biết thành VERIFIED.

## Nội dung cuối
- Sáu bài hoàn chỉnh; hai kịch bản 30 và 45 giây; hai banner. Không tạo video.
- Chữ công khai không có nhãn nội bộ, câu hướng dẫn người viết, placeholder hoặc đường dẫn workspace.
- Chỉ dùng ba lợi ích ngắn trong brief; không mở rộng thành thông số marketing khác.
- Khi chưa có ảnh thật, dùng đồ họa minh họa góc làm việc và biểu tượng kết nối/chuột. Không tạo render rồi gọi là ảnh chụp chính xác M240 hoặc ảnh hàng đang có.
- Hồ sơ nguồn và xuất xứ ảnh nằm ở internal; bài/ảnh đăng ở publish; kịch bản ở production.
- HUMAN: APPROVE một lần ủy quyền hoàn thiện đầu ra; không tự đăng/chạy quảng cáo.
