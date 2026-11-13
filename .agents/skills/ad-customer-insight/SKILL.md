---
name: ad-customer-insight
description: Xây dựng phân khúc khách hàng và hành trình mua dựa trên nhu cầu, động
  cơ và rào cản cho chiến dịch.
---

# ad-customer-insight

## Phân khúc để hành động
Đọc brief, dữ liệu khách hàng và nghiên cứu có sẵn. Nhóm theo nhu cầu, tình huống sử dụng, động lực mua và rào cản có thể dẫn đến thông điệp/kênh khác nhau. Tuổi/giới tính chỉ là thuộc tính bổ trợ khi có căn cứ, không tự tạo persona chi tiết hoặc thuộc tính nhạy cảm.

Tạo tối đa ba phân khúc ban đầu với ID S1/S2/S3 ổn định. Mỗi nhóm nêu nhu cầu, tình huống, tác nhân mua, lợi ích tìm kiếm, tiêu chí lựa chọn, rào cản, cách tiếp cận khả thi và bằng chứng/giả thuyết. Nêu vì sao các nhóm thực sự khác nhau. Không coi persona giả định là kết quả khảo sát.

## Hành trình và kiểm chứng
Theo từng nhóm: nhận biết, cân nhắc, mua, giữ chân; ở mỗi chặng ghi câu hỏi khách hàng, điểm chạm, bằng chứng cần thấy, ma sát, hành động mong muốn và tín hiệu đo được. Không gán kênh đắt tiền khi brief không có ngân sách hoặc tài sản phù hợp.

Phân biệt lời khách hàng đã ghi nhận với suy luận của nhóm. Với dữ liệu ít, đề xuất câu hỏi phỏng vấn hoặc tín hiệu cần thu thập, không đưa tỷ lệ phần trăm giả. Giữ đúng ID khi sửa; đổi nhóm phải có lý do để Strategy xử lý tham chiếu.

audience_segments.json là mảng object không rỗng; mỗi object gồm segment_id duy nhất, name, needs, pain_points, motivations, barriers, use_cases, message_direction và evidence/assumptions. customer_journey.md thể hiện hành trình theo ID và bảng nguồn; không tự đặt offer hoặc quyết định phân bổ ngân sách cuối.

## File phải lưu

- `artifacts/audience_segments.json`
- `artifacts/customer_journey.md`

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không gửi cả bộ file dài vào chat; tóm tắt việc đã làm, giới hạn và đường dẫn, trừ khi node yêu cầu hiển thị đầy đủ.
