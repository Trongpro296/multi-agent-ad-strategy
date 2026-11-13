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
test_id,hypothesis,variant_a,variant_b,primary_metric,min_sample,duration_days,decision_rule
```

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không gửi cả bộ file dài vào chat; tóm tắt việc đã làm, giới hạn và đường dẫn, trừ khi node yêu cầu hiển thị đầy đủ.
