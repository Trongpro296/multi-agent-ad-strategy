---
name: ad-evidence-synthesis
description: Tổng hợp và phân loại bằng chứng từ nghiên cứu thị trường, đối thủ và
  khách hàng, đồng thời tạo sổ nguồn CSV.
---

# ad-evidence-synthesis

## Đọc và đối chiếu
Load market_research.md, competitor_analysis.md, audience_segments.json và customer_journey.md. Ghi ĐÃ NHẬN, THIẾU hoặc KHÔNG HỢP LỆ cho ba nhánh; không coi tên file hay bản tóm tắt là bằng chứng đã đọc nội dung. Đối chiếu phát hiện với sản phẩm, địa bàn, kỳ dữ liệu và câu hỏi chiến dịch.

Tách dữ kiện có nguồn, suy luận, giả thuyết, mâu thuẫn và khoảng trống. Giữ liên kết claim → nguồn → phạm vi sử dụng. Trích dẫn lặp cùng URL không tạo thành nhiều bằng chứng độc lập. Nếu nguồn không truy cập được, đánh dấu chưa xác minh truy cập; không sửa điều đó thành đã đọc.

## Sổ nguồn và giới hạn
Mỗi dòng sources.csv mô tả một claim cần theo dõi, ID ổn định, nguồn thực tế và evidence_type thuộc document/external/inference/hypothesis. external chỉ dùng khi có nguồn ngoài thật; document ghi tên tài liệu ở scope nếu không có URL. access_date là ngày thực tế truy cập hoặc để trống khi chưa truy cập, không điền ngày tưởng tượng. Suy luận phải nói nó dựa vào dữ kiện nào.

Nếu không có nguồn ngoài, vẫn tạo sources.csv với ít nhất một dòng hypothesis nêu giới hạn dữ liệu; source_url/access_date có thể trống. Không tạo URL giả hay dấu '-' để trông giống bằng chứng.

## Hai file là một bàn giao
Tạo evidence_digest.md ngắn theo: tình trạng bàn giao, dữ kiện, giả thuyết, mâu thuẫn, khoảng trống và ảnh hưởng tới chiến lược. Tạo sources.csv trong cùng lượt nhiệm vụ, load lại cả hai; chưa có file thứ hai thì chưa kết thúc. Không chép toàn bộ nghiên cứu vào chat: tóm tắt giới hạn và đường dẫn hai file. Node này không phát quyết định QA hoặc phê duyệt kế hoạch.

## File phải lưu

- `artifacts/evidence_digest.md`
- `artifacts/sources.csv`

`sources.csv` giữ nguyên thứ tự header:

```csv
id,claim,source_url,access_date,scope,evidence_type
```

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không dán lại toàn bộ file vào Chat; tóm tắt việc đã làm, giới hạn và đường dẫn, giữ câu hỏi/issue và dòng trạng thái cuối nếu có. Node sau đọc file thật bằng load_file.


ĐỐI CHIẾU CLAIM:
Trong evidence_digest.md, giữ bảng claim → nguồn/file/đoạn → loại căn cứ → phạm vi → điều chưa được chứng minh. Nêu rõ khi dữ liệu bắt nguồn từ brief giả định. sources.csv dùng ID duy nhất; external cần URL thật và ngày thực sự truy cập. Tài liệu được dẫn nhưng chưa đọc không được khai là đã xác minh. Báo mâu thuẫn để QA xử lý, không tự biến giả định thành dữ kiện.

## Độ dài và tái sử dụng đầu vào
Viết phần nghiệp vụ của vai trò, dẫn file/claim ID thay chép lại brief. Chat tóm tắt file, kết luận và giới hạn; giữ quyết định cuối nếu có. Đọc lại sau ghi, không lặp load khi nguồn chưa đổi. Mốc độ dài trong nhiệm vụ là tham khảo, không cắt schema hoặc bằng chứng để đủ số từ.

## Truyền bảng CSV qua save_file
Chỉ khi vai trò được giao xuất CSV: content của save_file có thể là chuỗi JSON gồm columns (tên cột theo schema) và rows (mảng object có đúng các key cột). Ưu tiên cách này để Python tự quote nội dung có dấu phẩy, dấu ngoặc kép hoặc xuống dòng và lưu UTF-8 BOM. Không bỏ dấu tiếng Việt để sửa số cột. Không dùng cấu trúc này cho qa_report.json hoặc publication JSON. Không tự thay dữ liệu thiếu bằng 0 hoặc cắt/ghép ô.

## URL và ngày nguồn
Nguồn external phải có URL tuyệt đối http/https và access_date thực tế YYYY-MM-DD, không trong tương lai. Dùng URL và dấu thời gian thực tế của lần truy cập; ngày chiến dịch hoặc TRUSTED_RUNTIME_DATE chỉ là thông tin thời gian, không chứng minh đã mở trang. Không tự thêm ngày, đổi loại nguồn hoặc xóa dòng để né kiểm tra. Nếu chỉ có tài liệu bàn giao, ghi đúng xuất xứ và phạm vi, không biến thành lần truy cập web mới. sources.csv được kiểm trước ghi và trước bàn giao; lỗi nguồn không gửi Assembler sửa thuyết minh lặp lại.
