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

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không dán lại toàn bộ file vào Chat; tóm tắt việc đã làm, giới hạn và đường dẫn, giữ câu hỏi/issue và dòng trạng thái cuối nếu có. Node sau đọc file thật bằng load_file.


CHẤT LƯỢNG BẰNG CHỨNG VÀ HỒ SƠ:
- [TÀI LIỆU] chỉ xác nhận điều nguồn cung cấp thực sự nói, không xác nhận điều đó đã được kiểm chứng ngoài thực tế. Nếu brief là giả định, ghi rõ “brief giả định/chưa xác minh thực địa” ở phạm vi và nhận định được dùng; không nâng thành dữ kiện thị trường.
- Phân biệt thuộc tính được cung cấp, lợi ích suy luận, nhu cầu giả thuyết và claim quảng cáo. Không gắn [TÀI LIỆU] cho sức chi trả sinh viên, độ yên tĩnh, chất lượng Wi-Fi hay so sánh đối thủ nếu nguồn không chứng minh đúng kết luận đó. Không biến “có thể” hoặc nhãn giả thuyết thành quyền phát hành claim chưa có bằng chứng.
- Với claim quan trọng, dẫn claim/source ID cùng file/đoạn, phạm vi và giới hạn; nguồn ngoài chỉ coi đã đọc khi tool truy cập thành công. Thiếu nguồn thì bỏ so sánh/claim khỏi thông điệp chính hoặc nêu là việc phải xác minh trước phát hành, không bịa URL/benchmark.
- Khi trích nguồn, phân biệt nghiên cứu lịch sử với quyết định hiện hành. Trong nội dung tài liệu cho người nhận dùng tên file giao (advertising_strategy.md, media_plan.csv...), không dùng đường dẫn artifacts/ hoặc code_workspace/. Khi gọi tool vẫn đọc/ghi đúng đường dẫn workspace artifacts/ như quy định.

## Độ dài và tái sử dụng đầu vào
Viết phần nghiệp vụ của vai trò, dẫn file/claim ID thay chép lại brief. Chat tóm tắt file, kết luận và giới hạn; giữ quyết định cuối nếu có. Đọc lại sau ghi, không lặp load khi nguồn chưa đổi. Mốc độ dài trong nhiệm vụ là tham khảo, không cắt schema hoặc bằng chứng để đủ số từ.
