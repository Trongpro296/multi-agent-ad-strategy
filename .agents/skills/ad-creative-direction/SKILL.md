---
name: ad-creative-direction
description: Chuyển định vị và chiến lược thành concept quảng cáo, thông điệp, CTA
  và yêu cầu sản xuất có bằng chứng.
---

# ad-creative-direction

## Từ insight tới concept
Đọc campaign_strategy.md, strategy_ids.json, brand_positioning.md và bằng chứng. Mỗi concept nêu phân khúc, tình huống/vấn đề, insight, hook, lợi ích, proof, CTA và điểm đến. Concept khác nhau ở lập luận sáng tạo, không chỉ thay từ ngữ. Giữ offer, giá, vùng phục vụ và giọng thương hiệu như brief.

Proof là dữ kiện/tài sản thực hỗ trợ claim. Nếu chỉ là giả thuyết, đánh dấu rõ và không viết như testimonial, chứng nhận hoặc kết quả khách hàng đã có. Không tạo claim số, 'tốt nhất' hay bảo đảm kết quả khi chưa có căn cứ. Thiếu ảnh, đánh giá hoặc chứng nhận thì ghi yêu cầu asset, không khẳng định đã tạo chúng.

## Sản xuất và thử nghiệm
creative_brief gồm Big Idea, tối đa ba slogan, thông điệp theo nhóm, video 30 giây, brief hình ảnh và asset cần thiết. Kịch bản chia mốc thời gian, hình/âm thanh, lời thoại/chữ, CTA; phù hợp độ dài thực tế. Nếu sản phẩm không phù hợp video, vẫn nêu cách triển khai tối giản trong phạm vi brief, không mặc nhiên tăng production budget.

creative_matrix dùng concept_id duy nhất và segment_id đã chọn trong Strategy; test_variant mô tả biến thể kiểm tra được. Nếu muốn học về hook thì giữ offer/CTA tương đương, tránh thay mọi yếu tố cùng lúc. Ghi asset_requirement có người phụ trách/đầu vào khi biết, không tự hứa khả năng chưa có.

Đối chiếu thông điệp, offer và CTA với điểm đến. Nêu rõ thứ nào sẵn sàng, thứ nào cần xác minh hoặc sản xuất. Bàn giao văn bản/đặc tả sáng tạo; không báo đã tạo ảnh/video nếu không có công cụ và kết quả file tương ứng.

## File phải lưu

- `artifacts/creative_brief.md`
- `artifacts/creative_matrix.csv`

`creative_matrix.csv` giữ nguyên thứ tự header:

```csv
concept_id,segment_id,insight,hook,benefit,proof,cta,format,asset_requirement,test_variant
```

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không gửi cả bộ file dài vào chat; tóm tắt việc đã làm, giới hạn và đường dẫn, trừ khi node yêu cầu hiển thị đầy đủ.
