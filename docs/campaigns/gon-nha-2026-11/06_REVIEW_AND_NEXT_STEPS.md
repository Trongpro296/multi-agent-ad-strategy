# Duyệt kế hoạch và việc còn phải làm

## Trước Client_Review

Agent phải tạo kế hoạch và giữ trạng thái chưa sẵn sàng của dự án. Không yêu cầu workflow chứng minh các điều kiện thực địa chưa được thực hiện. Nếu thiếu thông tin thiết yếu không được hồ sơ cho phép giả định, hỏi lại thay vì điền giả.

## Checklist duyệt kế hoạch

- [ ] Giữ 2.100.000 quảng cáo + 900.000 nội dung = 3.000.000 VND, không tính lương/chi phí ca bằng 0.
- [ ] Giá 279.000 được ghi là đề xuất cần kiểm chi phí/phụ phí trước phát hành, không có “trọn gói” hoặc giảm giá giả.
- [ ] Kế hoạch 14 ngày, một kênh, một nhóm ưu tiên, hai hook; không tự kéo thêm kênh/test vượt ngân sách.
- [ ] Dữ kiện đối thủ dẫn nguồn; JupViec 2024 giữ nhãn lịch sử; không suy ra kích thước thị trường, CPL hay khả năng thắng của dự án.
- [ ] Tin nhắn, lead đủ điều kiện, booking, completed và tiền thu là các bước khác nhau, có khử trùng/nguồn/múi giờ.
- [ ] Dự báo chưa có dữ liệu dùng NOT_ESTIMATED, không tự dự phóng số khách hoặc ROI.
- [ ] QA đúng plan_version; cả 5 điều kiện chưa làm giữ PENDING/BLOCKED tùy kết quả review, không tự chuyển VERIFIED.
- [ ] Nội dung nháp không bịa ảnh, nhân sự, bảo hiểm, chứng nhận, review hoặc lời hứa an toàn tuyệt đối.

Nếu cần sửa:

```text
HUMAN: REVISE
Giữ phạm vi/ngân sách. [Nêu lỗi cụ thể, file/mục cần sửa và điều đúng cần thay.]
```

Nếu chấp nhận đúng phiên bản kế hoạch hiện hành, nhập đúng một dòng:

```text
HUMAN: APPROVE
```

Sau Build, kiểm đúng session, BUILD: OK, manifest và bộ 26 file; mở Excel/PowerPoint thực tế. Duyệt ở đây chỉ cho phép bàn giao hồ sơ, không tự cấp quyền chạy quảng cáo.

## Để biến kế hoạch thành hoạt động thật

1. Người dùng xác nhận muốn triển khai dịch vụ này, chốt tên/quyền sử dụng và người chịu trách nhiệm vận hành.
2. Có nhân sự/đối tác thật, phạm vi phục vụ, dụng cụ, lịch nhận ca, chi phí và xử lý sự cố phù hợp; kiểm các điều kiện hoạt động cần thiết trước phục vụ.
3. Chốt giá/phụ phí/đổi-hủy dựa trên chi phí, thông tin đầy đủ cho khách, không chỉ theo giá tham khảo của đối thủ.
4. Tạo/kiểm trang và tài khoản do người dùng quản lý; chưa có link hay quyền truy cập trong hồ sơ này.
5. Sản xuất bộ ảnh thật và nội dung cuối, lấy quyền sử dụng, duyệt claim.
6. Thử tiếp nhận và ghi lead/booking, loại dữ liệu thử, phân công người trực và đối soát.
7. Người dùng chấp nhận ngân sách thật, mốc triển khai và điều kiện dừng; nếu chưa kịp thì sửa ngày qua review.

Không có bước nào ở trên được coi đã hoàn thành vì Agent viết kế hoạch hoặc QA cho PASS. Chưa liên hệ nhà cung cấp, chưa tạo tài khoản, chưa gọi model workflow hay chi tiền.
