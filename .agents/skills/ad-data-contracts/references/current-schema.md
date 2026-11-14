# Hợp đồng dữ liệu ad_agency_v2 tại thời điểm tạo skill

Chỉ dùng với schema tương ứng. Khi schema nhiệm vụ khác, đối chiếu System Prompt/Gate thực tế trước khi tạo hoặc sửa bảng; tài liệu này không tự thay schema runtime.

## CSV

Giữ đúng thứ tự header, số cột mỗi dòng; CSV UTF-8 BOM. Quote ô chứa dấu phẩy, dấu nháy hoặc xuống dòng.

media_plan.csv:
```csv
channel,role,objective,segment_id,offer_id,budget_pct,budget_amount,currency,start,end,landing_page,assumption
```

budget_scenarios.csv:
```csv
scenario,channel,budget_amount,metric,metric_value,formula,assumption,estimate_status
```

creative_matrix.csv:
```csv
concept_id,segment_id,insight,hook,benefit,proof,cta,format,asset_requirement,test_variant
```

experiment_plan.csv:
```csv
test_id,hypothesis,variant_a,variant_b,primary_metric,min_sample,duration_days,decision_rule,test_type,sample_unit,sample_basis,data_source,business_kpi,decision_supported,decision_not_supported,decision_owner,prerequisites,missing_data_rule,start,end
```

execution_calendar.csv:
```csv
week,start,end,channel,activity,owner,deliverable
```

sources.csv:
```csv
id,claim,source_url,access_date,scope,evidence_type
```

evidence_type là document/external/inference/hypothesis. Khi không có nguồn ngoài, có thể dùng hypothesis với URL/ngày truy cập trống và giải thích ở claim/scope; không tạo URL giả. Ngày truy cập chỉ ghi khi thực sự truy cập.

## Giá trị và ví dụ sửa

- budget_pct=25 tương ứng 25%, không phải 0.25 trong bảng. amount được đối chiếu với budget.ad_spend, cùng currency; không cộng production vào media.
- Số 12.5 hợp lệ; chuỗi 12,5% mơ hồ cả dấu thập phân/đơn vị, phải kiểm ý nghĩa trước khi chuyển. Không tự xóa dấu phẩy hoặc %.
- min_sample có giá trị 6, không phải '6 hội thoại, 3 mỗi biến thể'. Giữ nguyên phần diễn giải trong decision_rule khi nhiệm vụ cho phép sửa.
- Hai metric cho cùng kịch bản/kênh dùng cùng budget_amount. Hai dòng 'leads' và 'CPA' mỗi dòng ngân sách 100 mô tả một phân bổ 100, không phải hai khoản chi tổng 200; nếu hai giá trị khác nhau phải xử lý mâu thuẫn, không bỏ dòng tùy ý.
- week là số nguyên dương; duration_days và min_sample là số nguyên dương. start/end là ngày YYYY-MM-DD thật, trong khoảng campaign, start không sau end.
- estimate_status: ESTIMATED yêu cầu metric_value là số hữu hạn không âm, có formula/assumption. NOT_ESTIMATED yêu cầu metric_value trống và assumption giải thích dữ liệu thiếu; formula có thể trống. Không dùng chữ hoặc 0 thay unknown. Bảng cũ bảy cột không có estimate_status vẫn được đọc như ESTIMATED và phải có số hợp lệ. Cột status có mặt thì từng dòng phải dùng đúng một trong hai giá trị trên. budget_amount vẫn bắt buộc là số không âm ở cả hai trạng thái.

## JSON và tham chiếu

campaign_brief.json là object; budget.ad_spend là số không âm, budget.currency không rỗng; start_date/end_date hợp lệ. Không thay unknown bằng 0; brief thiếu thông tin quyết định phải được xử lý bởi Director_Brief.

audience_segments.json của workflow dùng mảng phân khúc với segment_id và name. strategy_ids.json dùng goal{goal_id,statement,primary_kpi}, segments[{segment_id,name,priority}], offers[{offer_id,description}], funnel[], alternatives[], validation_conditions[]. Kế thừa segment ID từ Audience, không tạo lại trong lúc sửa CSV.

qa_report.json gồm plan_version, verdict, plan_gate_status và issues[] theo schema QA. Skill sửa dữ liệu không được sửa báo cáo QA, review_manifest hoặc snapshot; không chép hay phát token điều phối hai ngoặc vuông trong tài liệu.

## Measurement và QA v2

ĐO LƯỜNG VÀ THỬ NGHIỆM V2:
- measurement_plan.md phải chốt mục tiêu kinh doanh, định nghĩa hành động được tính, đơn vị (người/lượt nhóm/lead/đơn...), điều kiện loại/trùng, nguồn dữ liệu, người ghi nhận, cửa sổ/múi giờ, hiện trạng tracking và phần cần chuẩn bị. Không tự đổi đơn vị giữa kỳ; chưa có thì nêu cần chủ dự án xác nhận, không viết đã triển khai.
- Mỗi dòng experiment_plan.csv có test_type: TECHNICAL_CHECK (đo có phân phối/ghi nhận được không), CREATIVE_EXPLORATION (thăm dò một thay đổi nội dung), BUSINESS_EVALUATION (đánh giá kết quả kinh doanh có dữ liệu phù hợp). Không buộc phải tạo đủ ba loại hoặc thêm test vượt số lượng brief. Kiểm tra tracking kỹ thuật có thể nằm trong checklist chuẩn bị, không chiếm thêm test.
- sample_unit và sample_basis giải thích min_sample đo gì và vì sao có ngưỡng. Không bịa baseline/effect size/power. 30 impressions chỉ có thể là ngưỡng kiểm phân phối được giải thích, không phải cỡ mẫu chứng minh hiệu quả. Thiếu cơ sở thì chọn loại thăm dò và ghi rõ không được kết luận thắng hoặc nhân quả.
- data_source là nơi thực sự dự kiến lấy dữ liệu và mức sẵn có; business_kpi chỉ rõ quan hệ với mục tiêu. primary_metric phải được phân biệt là chỉ số chẩn đoán hay kết quả kinh doanh; click/tương tác không thay lượt ghé. Không so hai test khác metric như cùng một phép đo hiệu quả.
- decision_supported nêu quyết định quan sát có thể hỗ trợ; decision_not_supported nêu điều không thể suy ra. decision_rule nêu cách đọc tử/mẫu, điều kiện kết luận và thẩm quyền; decision_owner là người duyệt hành động, không tự tăng tiền.
- prerequisites nêu tracking/asset/tài khoản/claim phải xác nhận; missing_data_rule nêu thiếu mẫu, lỗi tracking, dữ liệu mâu thuẫn hoặc trễ lịch thì giữ/dừng/INCONCLUSIVE và ai xử lý. Không coi thiếu dữ liệu là không có khách; không tự dời test ngoài kế hoạch đã duyệt.
- start/end là YYYY-MM-DD trong campaign; duration_days=(end-start)+1. Variant A/B chỉ khác một yếu tố chính, giữ điều kiện khác; ngân sách test nằm trong Media, không cộng thêm. Dữ liệu thật cần thiết để quyết định kinh doanh được ghi thành việc thu thập cho vòng sau, không bịa số dự báo.


BÁO CÁO QA V2 (schema_version="2.0"):
- Giữ plan_version hiện hành, verdict=PASS|REVISE|BLOCKED, plan_gate_status=OK, issues[]. Thêm review_summary, criteria_results[], open_assumptions[], prelaunch_conditions[], implementation_readiness.
- criteria_results phải đủ đúng 8 criterion_id: BRIEF_ALIGNMENT, EVIDENCE, CROSS_FILE_CONSISTENCY, BUDGET, EXPERIMENTS, MEASUREMENT, DELIVERY, IMPLEMENTATION_CONDITIONS. Mỗi mục có status=PASS|FAIL|NOT_REVIEWED, rationale và evidence_refs:[{file,location}]. file là tên file nguồn thuộc snapshot (ví dụ advertising_strategy_draft.md, không phải tên đổi sau build); location là mục/dòng/ID kiểm được. Không dẫn internal notes thay bằng chứng.
- PASS chỉ khi cả 8 tiêu chí PASS và issues rỗng. REVISE/BLOCKED phải có tiêu chí FAIL/NOT_REVIEWED và issue hành động được gồm id,severity,area,description,fix,owner,evidence_refs; NOT_REVIEWED phải giải thích vì sao, không tuyên bố đã đọc. Mọi ref phải trỏ file nguồn của phiên bản hiện tại.
- open_assumptions là danh sách (có thể rỗng), mỗi mục id,description,impact,owner,evidence_refs. Giả thuyết trung thực không tự là lỗi cần bịa bằng chứng để xóa.
- prelaunch_conditions đủ 5 condition_id: TRACKING, ASSETS, ACCOUNT_SETUP, OFFER_CLAIMS, OPERATIONS. Mỗi mục có status=PENDING|VERIFIED|BLOCKED|NOT_APPLICABLE, description,owner,verification,evidence_refs. verification nêu căn cứ thực tế đã kiểm nếu VERIFIED; nếu PENDING/BLOCKED thì nêu việc còn cần làm và cách xác nhận; NOT_APPLICABLE cần lý do. Tài liệu đề xuất cài đặt không phải bằng chứng đã cài.
- implementation_readiness:{status,reason}. Nếu verdict không PASS hoặc có condition BLOCKED thì NOT_READY; còn PENDING thì CONDITIONAL; chỉ khi mọi condition VERIFIED/NOT_APPLICABLE mới READY. PASS cho chất lượng kế hoạch không đồng nghĩa READY, không phải duyệt chi tiền và không bảo đảm kết quả quảng cáo.
- Kiểm rõ mục đích test, đơn vị/cơ sở min_sample, ngày chạy, dữ liệu và quyết định được phép rút ra. Đừng PASS một kế hoạch gọi ngưỡng kiểm phân phối là bằng chứng kinh doanh. Nếu thiếu dữ liệu nền nhưng đã có kế hoạch thu thập và giới hạn trung thực, có thể PASS kế hoạch với điều kiện triển khai còn mở.
- Sau lưu/load lại qa_report.json, Chat tóm tắt verdict, plan_version, readiness, điều kiện còn mở rồi kết thúc bằng dòng QA đúng quy tắc. Không sửa file nguồn/manifest và không tự tạo xác nhận Human.
