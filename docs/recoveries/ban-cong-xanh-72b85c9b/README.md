# Khôi phục phiên Ban Công Xanh

Nguồn: `session_72b85c9b-9ed1-479b-8c96-3c8fa86914b9`, plan_version `83585453a706`. Báo cáo nguồn REVISE; đây không phải phê duyệt QA.

Chọn `ad_agency_recovery_72b85c9b_qa_fix.yaml` trên Launch. Prompt: “Tiếp tục phiên khôi phục Ban Công Xanh theo chỉ dẫn đã nhúng; sửa ba issue của QA và dừng tại Client_Review.”

Bản khôi phục tự phục hồi 18 file từ snapshot đã kiểm hash, dùng lại 10 Agent nguồn, chỉ chạy Assembler/QA/Packager cùng các bước kiểm tra và tạo ảnh theo cấu hình nếu được duyệt. Không cần upload lại tài liệu hoặc dán brief dài. Source session giữ nguyên.

Không có log đầy đủ cho phiên nguồn: cache dựa trên file đã kiểm hash và hợp đồng artifact, không giả lập NODE_END. recovery_request.txt là chỉ dẫn khôi phục cùng brief chuẩn hóa, không phải prompt gốc nguyên văn.

Khởi động lại backend để nạp code kiểm QA mới, tải lại danh sách workflow rồi chọn bản recovery. Việc chuẩn bị không gửi request model hoặc tự khởi chạy.
