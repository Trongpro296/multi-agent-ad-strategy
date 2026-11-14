# Duyệt và đưa kế hoạch vào vận hành

## 1. Trước Launch workflow

- [ ] Brief có dữ liệu thật, không còn ô chưa điền ở các mục quyết định.
- [ ] Tổng tiền khớp các khoản và đã có người duyệt.
- [ ] Ngày hợp lệ, còn thời gian chuẩn bị.
- [ ] Quyền nghiên cứu web và phạm vi sử dụng tài liệu rõ ràng.
- [ ] Chỉ định người duyệt kế hoạch và người vận hành.
- [ ] Backend restart sau bản sửa, preflight đạt, mở đúng YAML có Human review.

## 2. Tại Client_Review

Đọc bản nháp hiện hành, Plan_Gate, qa_report.json và plan_version; đối chiếu file nguồn khi cần. Chưa có bộ Office đóng gói ở bước này.

- [ ] Đúng mục tiêu, địa bàn, giá và điều kiện ưu đãi.
- [ ] Tiền, lịch, kênh, phân khúc, offer, concept và ID nhất quán giữa các file.
- [ ] Claim có căn cứ, không biến giả thuyết thành sự thật.
- [ ] Phạm vi phù hợp năng lực phục vụ đã xác nhận.
- [ ] Dự báo có cơ sở hoặc ghi chưa ước lượng, không dùng số giả.
- [ ] KPI, đơn vị, nguồn dữ liệu và loại trùng rõ ràng.
- [ ] Thử nghiệm nêu điều được/không được kết luận.
- [ ] QA đúng phiên bản; điều kiện còn mở có người xử lý và cách xác minh.
- [ ] Hiểu đây là duyệt kế hoạch, chưa phải lệnh chạy quảng cáo.

Yêu cầu sửa bằng cú pháp sau, thay phần trong ngoặc bằng góp ý thực tế:

```text
HUMAN: REVISE
[Nêu file/mục cần sửa, vấn đề, thông tin đúng và ràng buộc phải giữ.]
```

Chỉ khi chấp nhận bản kế hoạch hiện hành, nhập đúng một dòng:

```text
HUMAN: APPROVE
```

Không dùng lệnh duyệt chỉ để thử đi tiếp. Đổi kế hoạch sau duyệt phải quay lại review/phiên bản tương ứng, không chỉnh hash để bỏ kiểm tra.

## 3. Sau Build thành công

- [ ] BUILD: OK, đúng session, không chỉ nhìn thấy thư mục output.
- [ ] Đủ 26 file theo manifest; đọc handoff_notes, advertising_strategy và Overview Excel.
- [ ] Kiểm tiếng Việt, số, ngày và bố cục trong Excel/PowerPoint thực tế.
- [ ] Tạo bản sao biểu mẫu vận hành; giữ bộ bàn giao gốc làm mốc đối chiếu.
- [ ] CONDITIONAL hoặc NOT_READY thì xử lý điều kiện còn mở trước triển khai.

## 4. Trước khi bật quảng cáo ngoài hệ thống

Người vận hành kiểm và lưu bằng chứng cho TRACKING, ASSETS, ACCOUNT_SETUP, OFFER_CLAIMS, OPERATIONS. Không áp dụng cần lý do; chưa kiểm không chuyển VERIFIED. Chốt người cho phép bắt đầu chi tiêu và ngân sách được phép. Hệ thống hiện lập kế hoạch/bàn giao, không tự cấu hình tài khoản hay chạy quảng cáo.

## 5. Trong và sau chiến dịch

Ghi chi tiêu và kết quả theo KPI đã chốt, tách dữ liệu thiếu/chưa rõ nguồn. Đối soát theo lịch do người phụ trách xác nhận. Không cộng nhóm có thể trùng hoặc suy ra nhân quả chỉ từ tự khai nguồn.

Khi dữ liệu lỗi, nội dung sai, không đáp ứng năng lực phục vụ hoặc chi tiêu vượt quyền duyệt, người vận hành xử lý theo quy tắc đã chốt và ghi quyết định. Agent không tự thay ngân sách/thông điệp ngoài quyền được giao.

Cuối đợt tổng hợp: kỳ thời gian, tiền thực chi, kết quả hợp lệ, dữ liệu thiếu, giới hạn đo lường, điều học được và quyết định tiếp theo cần duyệt. Chỉ phân tích học từ chiến dịch khi có dữ liệu thực tế, không tạo kết quả giả để hoàn tất báo cáo.
