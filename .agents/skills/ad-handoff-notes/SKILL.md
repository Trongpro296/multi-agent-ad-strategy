---
name: ad-handoff-notes
description: Viết ghi chú bàn giao dễ sử dụng cho kế hoạch quảng cáo đã qua review,
  giữ rõ giả định và phần chưa triển khai.
---

# ad-handoff-notes

## Xác nhận bộ hồ sơ đang bàn giao
Đọc brief, bản nháp hiện hành, qa_report và review_manifest; đối chiếu cùng plan_version. Dùng list_directory để biết file thực sự tồn tại. Không coi trạng thái workflow kết thúc là chiến dịch hoàn tất; node này viết ghi chú trước Build_Files, nên chưa được nói XLSX/PPTX đã build thành công.

## Ghi chú cho người thực thi
handoff_notes.md tóm tắt kế hoạch trong 5–8 dòng, giải thích đọc tài liệu nào trước, ai cần làm gì tiếp và thứ tự: xác minh giả định → chuẩn bị asset/offer → cài tracking → kiểm tra → triển khai theo kế hoạch đã duyệt. Chỉ liệt kê tên tài liệu đã xác nhận tồn tại; không đoán URL tải xuống hay thư mục của máy người dùng.

Nêu giới hạn dữ liệu, số liệu giả định, claim cần kiểm chứng, nguồn chưa truy cập, asset/tracking còn phải tạo và điều kiện dừng/mở rộng đã được duyệt. Không biến danh sách đề xuất thành công việc đã thực hiện hoặc hứa kết quả doanh thu.

Chỉ lưu handoff_notes.md; không copy file, tạo manifest, sửa QA, đổi ngân sách hoặc đụng snapshot. Danh sách file bàn giao cuối và hash do Build_Files tạo trong manifest.json. Có thể chỉ dẫn người dùng đối chiếu plan_version ở đó sau khi BUILD OK, nhưng không tự phát BUILD: OK hoặc APPROVED.

Phản hồi chat là ghi chú đã lưu kèm đúng đường dẫn. Nếu phát hiện phiên bản/file quan trọng không khớp, báo rõ; không dùng ghi chú để che thiếu sót. Bàn giao chiến lược và tài liệu, không tuyên bố tài khoản quảng cáo đã được cấu hình hoặc chiến dịch đã chạy.

## File phải lưu

- `artifacts/handoff_notes.md`

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không dán lại toàn bộ file vào Chat; tóm tắt việc đã làm, giới hạn và đường dẫn, giữ câu hỏi/issue và dòng trạng thái cuối nếu có. Node sau đọc file thật bằng load_file.


TÊN FILE VÀ TRẠNG THÁI BÀN GIAO:
- Dùng tên file trong bộ output: advertising_strategy.md thay cho advertising_strategy_draft.md; các file khác giữ tên. Chỉ dùng tên tương đối trong bộ giao, không chèn artifacts/, code_workspace/ hoặc đường dẫn máy chủ.
- Đọc/xác nhận file nguồn bằng tool trong artifacts/ rồi áp ánh xạ tên giao trên; không coi advertising_strategy.md thiếu chỉ vì nguồn trước build còn tên draft. Excel/PPTX/manifest là file script sẽ sinh: không tuyên bố đã tạo trước Build thành công.
- Ghi đúng plan_version, QA và lệnh Human hiện hành; phân biệt “kế hoạch được duyệt” với asset/tracking/claim thực địa còn phải xác nhận. Không lặp nhật ký rework, không ghi bản này còn chờ QA khi đã có QA PASS và Human duyệt.


TRÌNH BÀY QA VÀ MỨC SẴN SÀNG:
Đọc QA schema 2.0 cùng plan_version đã được người dùng duyệt. Trong handoff_notes.md tách rõ “Kết luận chất lượng kế hoạch”, “Mức sẵn sàng triển khai” và “Điều kiện trước launch”. Chép đúng implementation_readiness.status và giải thích dễ hiểu, liệt kê điều kiện PENDING/BLOCKED cùng owner/cách xác nhận. Nếu PASS nhưng CONDITIONAL/NOT_READY, ghi kế hoạch đã duyệt nhưng chưa được xem là đủ điều kiện chạy. Không biến QA PASS hoặc Human duyệt tài liệu thành xác nhận tracking/asset đã có, không tự mở chiến dịch.

## Độ dài và tái sử dụng đầu vào
Viết phần nghiệp vụ của vai trò, dẫn file/claim ID thay chép lại brief. Chat tóm tắt file, kết luận và giới hạn; giữ quyết định cuối nếu có. Đọc lại sau ghi, không lặp load khi nguồn chưa đổi. Mốc độ dài trong nhiệm vụ là tham khảo, không cắt schema hoặc bằng chứng để đủ số từ.
