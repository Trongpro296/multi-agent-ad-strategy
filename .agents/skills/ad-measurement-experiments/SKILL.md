---
name: ad-measurement-experiments
description: Thiết kế KPI, tracking và thử nghiệm quảng cáo; phân biệt tín hiệu vận
  hành với kết luận thống kê.
---

# ad-measurement-experiments

## Đo đúng kết quả
Đọc brief, strategy_ids.json, funnel và tracking hiện có. Chọn KPI chính tương ứng mục tiêu (ví dụ hội thoại đủ điều kiện, đơn xác nhận), định nghĩa điều kiện tính, đơn vị, mẫu số, cửa sổ ghi nhận và nguồn dữ liệu. KPI phụ giúp chẩn đoán, không thay kết quả kinh doanh bằng reach/clicks.

measurement_plan liệt kê event, thuộc tính cần thiết, UTM, cách khử trùng, liên kết lead/đơn, chủ dữ liệu và lịch đánh giá. Phân biệt tracking đang hoạt động với đề xuất cấu hình; không nói event đã được cài. Nếu chưa có website/analytics, đề xuất cách ghi nhận thủ công phù hợp, không tự bịa dashboard hoặc endpoint.

## Thử nghiệm có thể diễn giải
Mỗi test có giả thuyết, hai biến thể khác nhau ở yếu tố quan trọng, KPI chính, min_sample, duration_days và quy tắc quyết định. Tránh chạy quá nhiều test đồng thời trên ngân sách nhỏ. min_sample là số nguyên dương thuần, ví dụ 6; đơn vị và giải thích nằm ở decision_rule. duration_days là số nguyên dương không vượt campaign.

Ngưỡng học vận hành không phải cỡ mẫu đủ ý nghĩa thống kê. Khi thiếu baseline/effect size, chỉ đặt ngưỡng thăm dò được giải thích, không tuyên bố power hay mức tin cậy giả. Quy tắc phải có nhánh chưa đủ mẫu/khác biệt chưa rõ; không tăng ngân sách chỉ để ép đủ mẫu.

Nêu điều kiện dừng vì dữ liệu lỗi, chất lượng lead thấp hoặc giới hạn kinh doanh; ngưỡng số phải có cơ sở/giả định minh bạch. Không tự thay chi tiêu hay chạy ads. Dự báo theo ngân sách thuộc Media; không xuất bộ dự báo thứ hai mâu thuẫn.

## File phải lưu

- `artifacts/measurement_plan.md`
- `artifacts/experiment_plan.csv`

`experiment_plan.csv` giữ nguyên thứ tự header:

```csv
test_id,hypothesis,variant_a,variant_b,primary_metric,min_sample,duration_days,decision_rule,test_type,sample_unit,sample_basis,data_source,business_kpi,decision_supported,decision_not_supported,decision_owner,prerequisites,missing_data_rule,start,end
```

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không dán lại toàn bộ file vào Chat; tóm tắt việc đã làm, giới hạn và đường dẫn, giữ câu hỏi/issue và dòng trạng thái cuối nếu có. Node sau đọc file thật bằng load_file.


ĐO LƯỜNG VÀ THỬ NGHIỆM V2:
- measurement_plan.md phải chốt mục tiêu kinh doanh, định nghĩa hành động được tính, đơn vị (người/lượt nhóm/lead/đơn...), điều kiện loại/trùng, nguồn dữ liệu, người ghi nhận, cửa sổ/múi giờ, hiện trạng tracking và phần cần chuẩn bị. Không tự đổi đơn vị giữa kỳ; chưa có thì nêu cần chủ dự án xác nhận, không viết đã triển khai.
- Mỗi dòng experiment_plan.csv có test_type: TECHNICAL_CHECK (đo có phân phối/ghi nhận được không), CREATIVE_EXPLORATION (thăm dò một thay đổi nội dung), BUSINESS_EVALUATION (đánh giá kết quả kinh doanh có dữ liệu phù hợp). Không buộc phải tạo đủ ba loại hoặc thêm test vượt số lượng brief. Kiểm tra tracking kỹ thuật có thể nằm trong checklist chuẩn bị, không chiếm thêm test.
- sample_unit và sample_basis giải thích min_sample đo gì và vì sao có ngưỡng. Không bịa baseline/effect size/power. 30 impressions chỉ có thể là ngưỡng kiểm phân phối được giải thích, không phải cỡ mẫu chứng minh hiệu quả. Thiếu cơ sở thì chọn loại thăm dò và ghi rõ không được kết luận thắng hoặc nhân quả.
- data_source là nơi thực sự dự kiến lấy dữ liệu và mức sẵn có; business_kpi chỉ rõ quan hệ với mục tiêu. primary_metric phải được phân biệt là chỉ số chẩn đoán hay kết quả kinh doanh; click/tương tác không thay lượt ghé. Không so hai test khác metric như cùng một phép đo hiệu quả.
- decision_supported nêu quyết định quan sát có thể hỗ trợ; decision_not_supported nêu điều không thể suy ra. decision_rule nêu cách đọc tử/mẫu, điều kiện kết luận và thẩm quyền; decision_owner là người duyệt hành động, không tự tăng tiền.
- prerequisites nêu tracking/asset/tài khoản/claim phải xác nhận; missing_data_rule nêu thiếu mẫu, lỗi tracking, dữ liệu mâu thuẫn hoặc trễ lịch thì giữ/dừng/INCONCLUSIVE và ai xử lý. Không coi thiếu dữ liệu là không có khách; không tự dời test ngoài kế hoạch đã duyệt.
- start/end là YYYY-MM-DD trong campaign; duration_days=(end-start)+1. Variant A/B chỉ khác một yếu tố chính, giữ điều kiện khác; ngân sách test nằm trong Media, không cộng thêm. Dữ liệu thật cần thiết để quyết định kinh doanh được ghi thành việc thu thập cho vòng sau, không bịa số dự báo.

## Độ dài và tái sử dụng đầu vào
Viết phần nghiệp vụ của vai trò, dẫn file/claim ID thay chép lại brief. Chat tóm tắt file, kết luận và giới hạn; giữ quyết định cuối nếu có. Đọc lại sau ghi, không lặp load khi nguồn chưa đổi. Mốc độ dài trong nhiệm vụ là tham khảo, không cắt schema hoặc bằng chứng để đủ số từ.

## Truyền bảng CSV qua save_file
Chỉ khi vai trò được giao xuất CSV: content của save_file có thể là chuỗi JSON gồm columns (tên cột theo schema) và rows (mảng object có đúng các key cột). Ưu tiên cách này để Python tự quote nội dung có dấu phẩy, dấu ngoặc kép hoặc xuống dòng và lưu UTF-8 BOM. Không bỏ dấu tiếng Việt để sửa số cột. Không dùng cấu trúc này cho qa_report.json hoặc publication JSON. Không tự thay dữ liệu thiếu bằng 0 hoặc cắt/ghép ô.
