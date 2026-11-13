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
test_id,hypothesis,variant_a,variant_b,primary_metric,min_sample,duration_days,decision_rule
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
