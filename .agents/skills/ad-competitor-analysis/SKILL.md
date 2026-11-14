---
name: ad-competitor-analysis
description: Phân tích đối thủ trực tiếp và thay thế để tìm khoảng trống định vị có
  bằng chứng cho chiến dịch quảng cáo.
---

# ad-competitor-analysis

## Chọn đối thủ có ý nghĩa
Đọc brief và market_research.md nếu có. Chọn đối thủ theo cùng nhu cầu, địa bàn, tầm giá hoặc tình huống sử dụng; tách đối thủ trực tiếp và lựa chọn thay thế. Chỉ chọn tên doanh nghiệp khi được xác minh hoặc người dùng cung cấp. Khi không có dữ liệu/web, mô tả nhóm đối thủ giả định; không bịa tên thật, giá hoặc kênh đang chạy.

So sánh trên cùng đơn vị: giá niêm yết/khuyến mãi, quy cách, phí giao và điều kiện ưu đãi. Chỉ mô tả quảng cáo đang hoạt động khi đã có bằng chứng hiện hành; trang mạng xã hội tồn tại không chứng minh đang chi quảng cáo. Không suy diễn doanh thu, ROAS hoặc ngân sách từ lượt theo dõi.

## Biến so sánh thành quyết định
Với mỗi đối thủ: nhu cầu phục vụ, thông điệp/offer, bằng chứng tin cậy, hành trình mua và rào cản. Tách quan sát trực tiếp với nhận định về điểm mạnh/yếu. SWOT chỉ dùng khi giúp chọn một cơ hội cụ thể, tránh nhận xét chung như 'thương hiệu mạnh' mà không có căn cứ.

Đề xuất khoảng trống gồm khách hàng nào chưa được phục vụ, thông điệp khác biệt nào doanh nghiệp có thể chứng minh, khả năng thực hiện và cách kiểm chứng. Không khuyên cạnh tranh giá nếu chưa biết biên lợi nhuận/công suất. Không sao chép nội dung đối thủ hoặc dùng claim so sánh chưa kiểm chứng.

competitor_analysis.md có bảng so sánh, phần quan sát/giả thuyết, khoảng trống ưu tiên, rủi ro và bảng nguồn. Mỗi số giá có đơn vị, điều kiện và thời điểm; thiếu thì ghi thiếu, không điền số để đủ bảng.

## File phải lưu

- `artifacts/competitor_analysis.md`

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
