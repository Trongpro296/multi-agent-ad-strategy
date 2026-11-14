---
name: ad-media-planning
description: Phân bổ ngân sách quảng cáo và lập kịch bản định lượng có công thức,
  bảo toàn ngân sách và các ID chiến lược.
---

# ad-media-planning

## Phân bổ theo vai trò
Đọc brief, campaign_strategy.md và strategy_ids.json. Chọn số kênh phù hợp ngân sách và khả năng sản xuất/đo lường; tránh chia quá nhỏ chỉ để có nhiều dòng. Mỗi dòng media_plan liên kết channel, vai trò funnel, objective, segment_id, offer_id, điểm đến và thời gian.

Chỉ dùng budget.ad_spend làm trần chi quảng cáo. Tổng budget_amount phải bằng ad_spend theo phân bổ kế hoạch và tuyệt đối không vượt; budget_pct đối chiếu với cùng trần, tổng 100 khi cap dương. Dùng currency của brief, ngày trong campaign. Không trộn tiền sản xuất hoặc other vào media. Với cap=0, mọi khoản tiền bằng 0 và mô tả rõ không có triển khai paid media.

## Kịch bản không phải ba khoản chi cộng dồn
budget_scenarios có ba kịch bản độc lập: thận trọng, cơ sở, tích cực. budget_amount là phân bổ của một cặp (scenario, channel); khi báo nhiều metric cho cùng cặp, lặp đúng cùng số tiền. Không chia tiền theo metric, không cộng các dòng metric như khoản chi khác nhau; mỗi (scenario, channel, metric) duy nhất.

metric_value phải có đơn vị được giải thích bằng tên metric, formula và assumption rõ. Dựa vào dữ liệu thực hoặc giả định mà đề bài cho phép; không bịa benchmark/CPC/CPA và gọi đó là dữ liệu thị trường. Nếu chưa đủ cơ sở ước lượng, dùng estimate_status=NOT_ESTIMATED, để metric_value trống và ghi rõ dữ liệu thiếu trong assumption; formula có thể trống. Không dùng chữ hoặc số 0 thay cho unknown. Nếu có cơ sở, dùng ESTIMATED và số hữu hạn không âm cùng formula/assumption. Gate ghi nhận dự báo chưa được ước lượng; QA vẫn đánh giá tính khả thi và giới hạn của kế hoạch.

Tính nhất quán công thức: impressions=spend/CPM*1000; clicks=spend/CPC; conversions=clicks*CVR, với CVR dạng tỷ lệ trong công thức. Không trộn phần trăm và tỷ lệ. Kiểm lại toàn bộ phân bổ trước lưu; không khẳng định Gate đã đạt khi chưa có kết quả Gate thật.

## File phải lưu

- `artifacts/media_plan.csv`
- `artifacts/budget_scenarios.csv`

`media_plan.csv` giữ nguyên thứ tự header:

```csv
channel,role,objective,segment_id,offer_id,budget_pct,budget_amount,currency,start,end,landing_page,assumption
```


`budget_scenarios.csv` giữ nguyên thứ tự header:

```csv
scenario,channel,budget_amount,metric,metric_value,formula,assumption,estimate_status
```

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không dán lại toàn bộ file vào Chat; tóm tắt việc đã làm, giới hạn và đường dẫn, giữ câu hỏi/issue và dòng trạng thái cuối nếu có. Node sau đọc file thật bằng load_file.


ĐỒNG BỘ THỬ NGHIỆM V2:
Đọc experiment_plan.csv và measurement_plan.md hiện hành; giữ lịch, tiền, variant, concept, metric và điều kiện sẵn sàng nhất quán với Media/Creative/calendar. Chưa có hợp đồng từ nhánh Performance thì ghi dependency còn thiếu, không tạo một phép thử khác mâu thuẫn. Rework phải giữ đủ 20 cột experiment theo schema mới; không tự điền dữ liệu nền hoặc xác nhận tracking để vượt Gate.

## Độ dài và tái sử dụng đầu vào
Viết phần nghiệp vụ của vai trò, dẫn file/claim ID thay chép lại brief. Chat tóm tắt file, kết luận và giới hạn; giữ quyết định cuối nếu có. Đọc lại sau ghi, không lặp load khi nguồn chưa đổi. Mốc độ dài trong nhiệm vụ là tham khảo, không cắt schema hoặc bằng chứng để đủ số từ.

## Truyền bảng CSV qua save_file
Chỉ khi vai trò được giao xuất CSV: content của save_file có thể là chuỗi JSON gồm columns (tên cột theo schema) và rows (mảng object có đúng các key cột). Ưu tiên cách này để Python tự quote nội dung có dấu phẩy, dấu ngoặc kép hoặc xuống dòng và lưu UTF-8 BOM. Không bỏ dấu tiếng Việt để sửa số cột. Không dùng cấu trúc này cho qa_report.json hoặc publication JSON. Không tự thay dữ liệu thiếu bằng 0 hoặc cắt/ghép ô.
