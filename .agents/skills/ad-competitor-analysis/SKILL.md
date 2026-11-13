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

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không gửi cả bộ file dài vào chat; tóm tắt việc đã làm, giới hạn và đường dẫn, trừ khi node yêu cầu hiển thị đầy đủ.
