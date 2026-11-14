---
name: ad-market-research
description: Nghiên cứu thị trường cho brief quảng cáo, xác định cơ hội có căn cứ
  và giới hạn dữ liệu thay vì gom nhận định chung.
---

# ad-market-research

## Chọn câu hỏi nghiên cứu
Đọc campaign_brief.json và xác định những quyết định cần bằng chứng: nhu cầu/tình huống mua, địa bàn, mức giá, mùa vụ, thói quen tìm kiếm và kênh khách thực sự tiếp cận. Tập trung dữ liệu có thể làm đổi lựa chọn chiến lược; tránh báo cáo ngành dài nhưng không liên quan ngân sách và vùng phục vụ.

Nếu được phép web, chọn truy vấn có địa bàn, ngành và kỳ dữ liệu; ưu tiên nguồn gốc số liệu, thông tin sản phẩm chính thức và dữ liệu người dùng. Tái sử dụng nguồn phù hợp giữa các phát hiện. Kết quả tìm kiếm chỉ là manh mối; chỉ ghi đã đọc khi tool trả nội dung nguồn. Không lấy xu hướng toàn quốc làm bằng chứng trực tiếp cho một cửa hàng địa phương.

Với mỗi phát hiện, ghi dữ kiện, nguồn/kỳ/phạm vi, độ chắc chắn, hệ quả cho chiến dịch và phần cần kiểm chứng. Không suy ra quy mô thị trường, nhu cầu, CPC hoặc hiệu quả bán hàng từ số lượt xem một nội dung. Nếu nguồn mâu thuẫn, trình bày khác biệt về kỳ/định nghĩa; không lấy trung bình vô căn cứ.

## Khi không có nguồn ngoài
Nếu đề bài cấm web hoặc tool không có, dùng tài liệu hiện có. Gắn giả thuyết cho nhận định ngoài tài liệu, nêu cách kiểm chứng bằng phỏng vấn, dữ liệu bán hàng hoặc thử nghiệm nhỏ; không dựng URL hay số liệu để báo cáo có vẻ đầy đủ.

market_research.md gồm phạm vi/phương pháp, phát hiện có nhãn và căn cứ, cơ hội/rủi ro, khoảng trống và bảng nguồn: URL hoặc tên tài liệu, ngày truy cập thực tế nếu có, dữ kiện đã dùng. Kết thúc bằng các hàm ý hành động theo mức ưu tiên, không tự quyết định ngân sách cuối cùng.

## File phải lưu

- `artifacts/market_research.md`

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

## URL và ngày nguồn
Nguồn external phải có URL tuyệt đối http/https và access_date thực tế YYYY-MM-DD, không trong tương lai. Dùng URL và dấu thời gian thực tế của lần truy cập; ngày chiến dịch hoặc TRUSTED_RUNTIME_DATE chỉ là thông tin thời gian, không chứng minh đã mở trang. Không tự thêm ngày, đổi loại nguồn hoặc xóa dòng để né kiểm tra. Nếu chỉ có tài liệu bàn giao, ghi đúng xuất xứ và phạm vi, không biến thành lần truy cập web mới. sources.csv được kiểm trước ghi và trước bàn giao; lỗi nguồn không gửi Assembler sửa thuyết minh lặp lại.
