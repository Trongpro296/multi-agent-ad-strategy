---
name: ad-strategy-quality-review
description: Nghiệm thu độc lập kế hoạch quảng cáo bằng brief, Evidence, Gate và phiên
  bản; tạo báo cáo lỗi có thể hành động.
---

# ad-strategy-quality-review

Publication_QA dùng skill riêng ad-publication-quality-review; skill này chỉ dành cho Strategy_QA và schema QA v2 của kế hoạch.

## Đúng đầu vào và phiên bản
Đọc advertising_strategy_draft.md, brief, evidence_digest.md, sources.csv, các bảng liên quan và review/review_manifest.json. Dùng đúng plan_version hiện hành của Plan_Gate; không dùng báo cáo/vòng cũ. Nếu phiên bản trong message và manifest không nhất quán, nêu vấn đề, không tự chọn bản thuận tiện.

## Review theo rủi ro
Ưu tiên lỗi làm sai quyết định: vượt/nhầm ngân sách, ID không nối được, claim chưa có bằng chứng, funnel không thực hiện được, KPI không đo được, dự báo không có công thức/cơ sở, đầu vào bắt buộc thiếu và lịch phi thực tế. Gate OK chứng minh kiểm tra cấu trúc/số học đã chạy, không chứng minh chiến lược tốt. Không chạy lại việc cộng tiền bằng nhẩm hoặc dùng sở thích văn phong để bắt sửa không cần thiết.

Phân biệt lỗi phải sửa với giả thuyết đã được khai báo và chấp nhận thử nghiệm. Mỗi issue có id, severity (chỉ high|medium|low, chữ thường; không dùng CRITICAL/MAJOR/MINOR), area, description, fix, owner và evidence_refs; nêu vị trí cụ thể và điều kiện được coi là đã sửa. Chỉ giao owner=Plan_Assembler khi thuộc quyền sửa của Assembler; lỗi cần chủ nguồn hoặc dữ liệu mới phải chỉ đúng người xử lý và dùng BLOCKED nếu vòng tổng hợp không thể khắc phục, không giao Assembler nhiệm vụ bịa nghiên cứu.

## Báo cáo và quyết định nhất quán
qa_report.json dùng schema_version=2.0 với các trường review/readiness bắt buộc bên dưới; giữ plan_version, verdict, plan_gate_status và issues[]. PASS chỉ khi không còn lỗi chặn, Gate OK, đủ bàn giao và mọi giả định còn mở được trình bày đúng. REVISE dùng khi Assembler có thể sửa trong phạm vi; BLOCKED khi không thể hoàn thành bằng vòng tổng hợp hiện tại. Không xóa dấu vết hoặc đổi snapshot để hợp thức hóa PASS.

Chỉ ghi qa_report.json, không sửa nguồn/draft. Dòng cuối phản hồi là QA: PASS hoặc QA: REVISE, đúng verdict trong file. Trường hợp BLOCKED ghi lý do và QA: BLOCKED; Router hiện tại chuyển sang nhánh dừng/invalid, không coi đó là PASS hay tự động rework. Không chép token hai ngoặc vuông vào output.

## File phải lưu

- `artifacts/qa_report.json`

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không dán lại toàn bộ file vào Chat; tóm tắt việc đã làm, giới hạn và đường dẫn, giữ câu hỏi/issue và dòng trạng thái cuối nếu có. Node sau đọc file thật bằng load_file.


REVIEW XUYÊN SUỐT HỒ SƠ:
- Không PASS chỉ vì bản tổng hợp đã sửa đẹp. Đọc brief, sources/digest, market_research, competitor_analysis, audience/customer journey, brand_positioning, campaign_strategy/registry và ba nhánh kế hoạch hiện hành. Đối chiếu claim giá/sức chi trả, tiện ích/chất lượng, so sánh đối thủ, offer, ID, tiền, KPI và lịch giữa các file liên quan.
- Nhận định sai nhãn bằng chứng hoặc claim chưa có căn cứ còn nằm trong tài liệu nguồn là issue của bộ giao, kể cả bản tổng hợp đã bỏ. Nêu rõ file/đoạn hoặc dòng CSV, claim/source ID nếu có, kết luận mâu thuẫn và sửa ở đâu trong schema issues hiện có; giữ cấu trúc báo cáo QA 2.0 bên dưới.
- Kiểm bản kế hoạch sạch và đúng tên file giao; đọc internal/assembly_notes.md nếu có để biết phần chưa xử lý, nhưng không dùng ghi chú này thay nguồn được review/snapshot. Ghi chú không có không phải bằng chứng đủ/thiếu bàn giao: kiểm các file thật.
- Phân biệt giới hạn/giả thuyết trung thực với lỗi claim khẳng định sai. Không yêu cầu bịa dữ liệu để đạt PASS. Nếu sửa được trong quyền Assembler thì REVISE; nếu cần chủ nguồn/đầu vào mới ngoài quyền sửa thì giải thích cần dừng, không cho PASS chỉ để kết thúc vòng.


BÁO CÁO QA V2 (schema_version="2.0"):
- Giữ plan_version hiện hành, verdict=PASS|REVISE|BLOCKED, plan_gate_status=OK, issues[]. Thêm review_summary, criteria_results[], open_assumptions[], prelaunch_conditions[], implementation_readiness.
- criteria_results phải đủ đúng 8 criterion_id: BRIEF_ALIGNMENT, EVIDENCE, CROSS_FILE_CONSISTENCY, BUDGET, EXPERIMENTS, MEASUREMENT, DELIVERY, IMPLEMENTATION_CONDITIONS. Mỗi mục có status=PASS|FAIL|NOT_REVIEWED, rationale và evidence_refs:[{file,location}]. file là tên file nguồn thuộc snapshot (ví dụ advertising_strategy_draft.md, không phải tên đổi sau build); location là mục/dòng/ID kiểm được. Không dẫn internal notes thay bằng chứng. Không dùng review/review_manifest.json hoặc qa_report.json làm evidence_refs.file: chúng không thuộc snapshot. Dùng tên file nguồn thực tế và vị trí đã đọc.
- PASS chỉ khi cả 8 tiêu chí PASS và issues rỗng. REVISE/BLOCKED phải có tiêu chí FAIL/NOT_REVIEWED và issue hành động được gồm id,severity,area,description,fix,owner,evidence_refs; NOT_REVIEWED phải giải thích vì sao, không tuyên bố đã đọc. Mọi ref phải trỏ file nguồn của phiên bản hiện tại.
- open_assumptions là danh sách (có thể rỗng), mỗi mục id,description,impact,owner,evidence_refs. Giả thuyết trung thực không tự là lỗi cần bịa bằng chứng để xóa.
- prelaunch_conditions đủ 5 condition_id: TRACKING, ASSETS, ACCOUNT_SETUP, OFFER_CLAIMS, OPERATIONS. Mỗi mục có status=PENDING|VERIFIED|BLOCKED|NOT_APPLICABLE, description,owner,verification,evidence_refs. verification nêu căn cứ thực tế đã kiểm nếu VERIFIED; nếu PENDING/BLOCKED thì nêu việc còn cần làm và cách xác nhận; NOT_APPLICABLE cần lý do. Tài liệu đề xuất cài đặt không phải bằng chứng đã cài.
- implementation_readiness:{status,reason}. Nếu verdict không PASS hoặc có condition BLOCKED thì NOT_READY; còn PENDING thì CONDITIONAL; chỉ khi mọi condition VERIFIED/NOT_APPLICABLE mới READY. PASS cho chất lượng kế hoạch không đồng nghĩa READY, không phải duyệt chi tiền và không bảo đảm kết quả quảng cáo.
- Kiểm rõ mục đích test, đơn vị/cơ sở min_sample, ngày chạy, dữ liệu và quyết định được phép rút ra. Đừng PASS một kế hoạch gọi ngưỡng kiểm phân phối là bằng chứng kinh doanh. Nếu thiếu dữ liệu nền nhưng đã có kế hoạch thu thập và giới hạn trung thực, có thể PASS kế hoạch với điều kiện triển khai còn mở.
- Sau lưu/load lại qa_report.json, Chat chỉ tóm tắt verdict, plan_version, readiness và điều kiện còn mở; code lấy verdict từ báo cáo hợp lệ để định tuyến, không cần dòng quyết định trong chat. Nếu save_file từ chối schema, sửa đúng trường được báo rồi lưu lại, không đổi verdict hoặc xóa issue để vượt kiểm tra. Không sửa file nguồn/manifest và không tự tạo xác nhận Human.

## Độ dài và tái sử dụng đầu vào
Viết phần nghiệp vụ của vai trò, dẫn file/claim ID thay chép lại brief. Chat tóm tắt file, kết luận và giới hạn; giữ quyết định cuối nếu có. Đọc lại sau ghi, không lặp load khi nguồn chưa đổi. Mốc độ dài trong nhiệm vụ là tham khảo, không cắt schema hoặc bằng chứng để đủ số từ.
