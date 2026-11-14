---
name: ad-brand-positioning
description: Xác định định vị và thông điệp thương hiệu có thể chứng minh, phù hợp
  khách hàng và khả năng thực tế của sản phẩm.
---

# ad-brand-positioning

## Chọn điểm khác biệt có thể bảo vệ
Đọc brief, Evidence Digest, đối thủ và phân khúc. Xác định khách hàng ưu tiên, ngữ cảnh cạnh tranh, nhu cầu cốt lõi, lợi ích sản phẩm có thể cung cấp và bằng chứng hỗ trợ. Phân biệt thuộc tính sản phẩm, lợi ích và lý do tin; không coi tính từ 'cao cấp/chất lượng' là định vị.

Viết tuyên bố định vị theo khách hàng → nhu cầu → lợi ích → khác biệt → lý do tin. Khi bằng chứng chưa có, đề xuất định vị như giả thuyết và điều kiện cần kiểm chứng; không biến mong muốn thương hiệu thành claim thật. Tránh chọn nhiều điểm mạnh ngang nhau làm mất trọng tâm.

## Kiến trúc thông điệp
Xây lời hứa chính và các thông điệp hỗ trợ theo phân khúc; mỗi thông điệp gắn lợi ích, bằng chứng sẵn có và giới hạn được phép nói. Chọn giọng điệu theo thương hiệu và kênh đã có. Nêu cách diễn đạt nên dùng/tránh dựa trên brief, không tự nhận một claim đã được pháp lý hoặc nền tảng phê duyệt.

Kiểm tra độ khác biệt so với đối thủ, tính liên quan tới nhu cầu và khả năng doanh nghiệp thực hiện. Nếu chỉ có khác biệt giả định, ghi rõ cách thử bằng phản hồi khách hàng hoặc biến thể thông điệp. Không tự đổi sản phẩm, giá hay điều kiện offer.

brand_positioning.md gồm định vị, nhóm ưu tiên, lời hứa, lý do tin, bảng thông điệp và bằng chứng, giọng điệu, điều chưa được khẳng định và kiểm chứng còn thiếu. Bàn giao cơ sở cho Director_Strategy; không quyết định KPI hay ngân sách thay họ.

## File phải lưu

- `artifacts/brand_positioning.md`

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
