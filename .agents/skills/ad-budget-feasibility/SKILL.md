---
name: ad-budget-feasibility
description: Đánh giá tính khả thi của ngân sách, số kênh và số thử nghiệm trong kế hoạch quảng cáo; dùng cho Strategy, Media hoặc QA trước khi đề nghị triển khai.
---

# Tính khả thi ngân sách quảng cáo

Kích hoạt khi cần đánh giá kế hoạch có thực hiện và học được trong ngân sách đã cho hay không. Đây là đánh giá nghiệp vụ, khác với Gate kiểm tổng tiền. Không được đổi ad_spend, đặt lệnh quảng cáo hay tăng chi tiêu thay người dùng.

## Dữ liệu cần biết

Đọc brief, phân bổ Media nếu có, mục tiêu, thời gian, khu vực, tài sản sáng tạo, chi phí sản xuất, công suất phục vụ và tracking. Ghi rõ đâu là dữ liệu thực, đâu là giả định được cho phép. Nếu thiếu CPC/CPM/CVR lịch sử hoặc dữ liệu tham chiếu phù hợp, không tạo một mức chi tối thiểu của nền tảng hay benchmark giả.

Tách trần quảng cáo, production, other và dự phòng nếu được brief quy định. Tài sản miễn phí hoặc nhân sự có sẵn vẫn có giới hạn thời gian; không tự biến ad_spend thành tiền sản xuất. Với ad_spend=0, loại kỳ vọng paid media và chỉ nêu phương án không trả phí trong phạm vi được giao.

## Đánh giá mức phân tán

Phân tích ngân sách theo kênh, chặng funnel, biến thể và lịch chạy thực tế. Một test gồm hai biến thể không có nghĩa toàn bộ số mẫu sẽ chia đều; nêu giả định phân phối. Không mặc định chiến dịch phải có đủ nhiều kênh hoặc mọi giai đoạn funnel nếu tiền và tài sản không cho phép.

Khi có căn cứ được chấp nhận, kiểm bằng phép tính minh bạch:
- Ngân sách trung bình/ngày = phân bổ / số ngày thật sự chạy.
- Click kỳ vọng = spend / CPC; mẫu chuyển đổi kỳ vọng = clicks × CVR, với CVR dạng tỷ lệ.
- Chi phí thu mẫu dự kiến = số mẫu × CPA tương ứng, chỉ khi CPA và định nghĩa mẫu cùng loại.

Đây là ước lượng điều kiện, không phải cam kết có thể mua được số mẫu đó. Dùng khoảng/độ nhạy nếu đầu vào biến động; không lấy giá trị lạc quan để hợp thức hóa kế hoạch. Không suy ra cỡ mẫu thống kê từ số tiền còn lại.

## Khuyến nghị có thể hành động

Chọn đánh giá: khả thi trong giả định đã nêu, khả thi có điều kiện, chưa đủ cơ sở hoặc không khả thi trong cấu hình hiện tại. Giải thích điểm nghẽn: chia quá nhỏ, không đủ thời gian, thiếu asset/tracking, chi phí thu mẫu hoặc khả năng xử lý lead.

Ưu tiên giảm số kênh/biến thể, chạy nối tiếp, tập trung một mục tiêu hoặc đặt kỳ học thăm dò trước; giữ tổng chi trong trần. Đề xuất đổi ngân sách/mục tiêu phải ghi là cần người dùng quyết định, không tự cập nhật brief.

Đưa bảng ngắn vào tài liệu node đang sở hữu: giả định và nguồn, hạng mục, phép tính, giới hạn, hành động và điều kiện xem lại. QA ghi phát hiện vào issue theo schema hiện có, không dùng dòng verdict của skill để thay QA: PASS/REVISE. Không tạo thêm file hoặc tự sửa bảng của node khác.
