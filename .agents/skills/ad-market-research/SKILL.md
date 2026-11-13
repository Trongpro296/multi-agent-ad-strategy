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

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không gửi cả bộ file dài vào chat; tóm tắt việc đã làm, giới hạn và đường dẫn, trừ khi node yêu cầu hiển thị đầy đủ.
