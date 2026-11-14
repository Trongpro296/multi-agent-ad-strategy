---
name: ad-publication-quality-review
description: Kiểm bộ nội dung công khai cuối theo kế hoạch đã duyệt và ghi publication_qa.json đúng hợp đồng riêng.
---

# Publication QA

Chỉ kiểm publication_content.json và nguồn snapshot được dẫn. Chỉ ghi artifacts/publication_qa.json; không ghi đè qa_report.json của kế hoạch. Processor đầu vào cung cấp JSON mẫu có plan_version và bundle_sha256 thật. Dùng nguyên hai giá trị đó, không tính nhẩm hash.

## Hợp đồng duy nhất

Top-level: schema_version, plan_version, bundle_sha256, verdict, checks, findings. schema_version là "1.0". checks là mảng đúng 8 object, mỗi object có id, status, reason, source_refs. Không dùng criteria_results, criterion_id, rationale, evidence_refs hoặc issues từ schema khác.

Giữ đúng các id: FACTS, OFFERS_CLAIMS, COPY_COMPLETENESS, CTA_CONSISTENCY, SCHEDULE, VIDEO_SCRIPT, VISUAL_BRIEFS, RIGHTS_PROVENANCE. Không tự đổi tên, gộp hoặc thêm check.

Mỗi check: status PASS hoặc FAIL; reason giải thích thực tế đã đối chiếu; source_refs là mảng không rỗng gồm {file,location}, file thuộc review_manifest.files, location là mục/dòng/ID thật đã đọc. Không dẫn manifest làm bằng chứng. findings là mảng chuỗi lỗi cụ thể/cách sửa, có thể rỗng.

PASS chỉ khi cả 8 check PASS và findings rỗng. Nếu có lỗi, verdict BLOCKED, có check FAIL và findings không rỗng. Không lưu nguyên mẫu reason trống/source_refs rỗng; không tự chọn PASS để vượt kiểm tra. Khi save_file từ chối, sửa đúng trường/mã được nêu bằng mẫu chính xác trong lỗi; không tự đặt tên mới. Tối đa hai lần sửa báo cáo sau lần ghi đầu, không lặp vô hạn.

## Nội dung phải đối chiếu

FACTS: thương hiệu, địa bàn, năng lực và mô tả có nguồn; không nâng quyết định hoặc dữ liệu thiếu thành bằng chứng lịch sử.
OFFERS_CLAIMS: giá, ưu đãi và lời hứa đúng quyết định/nguồn đã duyệt, không bịa đặc tính, feedback hay số liệu.
COPY_COMPLETENESS: bài có nội dung và CTA đầy đủ, không có nhãn nội bộ, placeholder hoặc hướng dẫn người viết.
CTA_CONSISTENCY: điểm nhận khách và CTA nhất quán, không tạo link/số điện thoại không có nguồn.
SCHEDULE: lịch trong chiến dịch, nội dung và mã nối đúng.
VIDEO_SCRIPT: thời lượng/cảnh liên tục, có lời thoại/chữ/âm thanh và sản xuất được theo phạm vi.
VISUAL_BRIEFS: brief ảnh đúng sản phẩm/dịch vụ, không giả portfolio hoặc ảnh trước-sau thật. Ảnh chưa tạo nên không tuyên bố đã đánh giá trực quan ảnh.
RIGHTS_PROVENANCE: dùng nguồn và minh họa đúng phạm vi, không sao chép tài sản bên thứ ba hoặc bịa giấy phép. Kịch bản là yêu cầu sản xuất, không phải xác nhận đã có footage/nhạc.

HUMAN: APPROVE đã duyệt kế hoạch và ủy quyền hoàn thiện đầu ra; không hỏi duyệt lần hai. QA nội dung không tự xác nhận tracking, tài khoản hoặc nguồn hàng đã sẵn sàng. Chat chỉ tóm tắt, code đọc report để định tuyến.
