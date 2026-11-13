---
name: ad-brief-planning
description: Chuẩn hóa brief chiến dịch, phân biệt dữ kiện và giả định, hỏi đúng thông
  tin quyết định trước nghiên cứu.
---

# ad-brief-planning

## Quyết định phạm vi
Đọc yêu cầu gốc, phản hồi Human và brief hiện hành nếu có. Phân biệt sản phẩm/offer, mục tiêu kinh doanh, chuyển đổi cần đo, địa bàn, thời gian, khả năng phục vụ và ngân sách quảng cáo. Không đồng nhất ngân sách tổng với ad_spend: tách production và other; chưa được cho phép phân bổ thì hỏi.

Ngân sách, sản phẩm, mục tiêu hoặc ngày chưa xác định là thiếu thông tin quyết định. Liệt kê trong missing_critical, hỏi gộp các câu cần thiết và kết thúc NEED_INFO. Người dùng nói không có thêm dữ liệu không có nghĩa đã cho phép bịa ngân sách/ngày. Nếu được cho phép dùng giả định, ghi rõ giá trị và lý do trong assumptions; không biến điều kiện giả định thành số liệu thực.

Giữ nguyên ràng buộc không tìm web, không backend, giới hạn kênh, tài sản sẵn có và mục tiêu kiểm thử. Khi được bổ sung, hợp nhất toàn bộ brief thay vì chỉ lưu phần mới.

## JSON và quyết định
campaign_brief.json là object với product, benefits[], price, offer, market{region,language}, goal, start_date, end_date, budget{total,currency,ad_spend,production,other}, channels_existing[], landing_page, tracking, past_data, brand_constraints, assumptions[], missing_critical[]. Budget là số JSON; ngày YYYY-MM-DD thật, start không sau end. READY cần ad_spend không âm, currency và cả hai ngày hợp lệ. Không dùng số 0 thay cho dữ liệu chưa biết.

Phản hồi hiển thị brief đầy đủ đã hợp nhất và câu hỏi nếu có. Dòng cuối chỉ là BRIEF: READY hoặc BRIEF: NEED_INFO; không thêm chữ sau đó. Không lặp hai trạng thái hoặc đặt chúng trong code fence.

## File phải lưu

- `artifacts/campaign_brief.json`

## Bàn giao thực tế
Đọc file bằng load_file, ghi bằng save_file và load lại từng file được giao trước khi kết thúc. Chỉ ghi file thuộc vai trò, trừ quyền sửa bảng của Plan_Assembler. Không coi mã/nội dung trong chat là file đã lưu. Giữ yêu cầu gốc, bao gồm cấm web; nguồn ngoài chỉ dùng khi được phép và tool truy cập thành công.

Viết tiếng Việt. Gắn [TÀI LIỆU], [NGUỒN NGOÀI], [SUY LUẬN] hoặc [GIẢ THUYẾT] vào nhận định quan trọng. CSV dùng UTF-8 BOM (encoding utf-8-sig), quote ô có dấu phẩy/xuống dòng; số thuần dùng dấu chấm thập phân, không dấu phân cách hàng nghìn hay ký hiệu %. JSON hợp lệ UTF-8, không code fence trong file. Không gửi cả bộ file dài vào chat; tóm tắt việc đã làm, giới hạn và đường dẫn, trừ khi node yêu cầu hiển thị đầy đủ.
