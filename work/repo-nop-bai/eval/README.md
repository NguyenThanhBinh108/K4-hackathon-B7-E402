# eval — golden set & kết quả đo

> Trạng thái: **chuẩn bị ở CP2, chạy lượt đầu ở CP3 (10:30 ngày 2)**.

## Ba chiều chất lượng

| Chiều | Định nghĩa kiểm chứng được | Cách chấm |
|---|---|---|
| **C1 · Có căn cứ** | Mọi mệnh đề sự thật trong câu trả lời trace được về một mã đoạn cụ thể, **và** người chấm mở đoạn đó ra thấy nội dung khớp. Thiếu một trong hai = fail | pass/fail |
| **C2 · Định tuyến đúng** | Nhánh máy chọn (`ANSWER`/`CLARIFY`/`HANDOFF`) khớp nhãn vàng, và khi ANSWER thì **tầng nguồn dùng để chốt phải là T1 hoặc T2** | pass/fail |
| **C3 · Đúng cỡ, đúng giọng** | 1 = sai kiến thức hoặc dài hơn gấp đôi mức cần · 3 = đúng nhưng thừa/thiếu bối cảnh · 5 = ≤4 câu, có trích dẫn, có bước tiếp theo rõ ràng | thang 1/3/5 |

**Trước khi chạy lượt 1:** hai thành viên chấm độc lập cùng 5 output rồi so. Lệch = định nghĩa mơ hồ, viết lại định nghĩa chứ không chấm lại.

## Quality bar — CHỐT TRƯỚC 23:59 NGÀY 1, KHÔNG SỬA SAU ĐÓ

> **Đạt khi ≥80% case trong golden set (n=24) pass cả C1 và C2, C3 trung bình ≥3,5 — VÀ điều kiện cứng: 0 case thuộc lớp ① mà trợ lý trả lời khẳng định khi không có căn cứ trong T1/T2.**

Không đạt bar nhưng phân tích được nguyên nhân thì vẫn tính đủ điểm. Sửa số thì không được tính.

## Cơ cấu golden set — 24 case

| Nhóm | Số case | Trạng thái |
|---|---|---|
| ① Nguồn sự thật | 3 | hỏi thứ không có trong tầng nào · hỏi thứ chỉ có ở T4 · hỏi thông báo đã bị thay thế |
| ② Mơ hồ | 3 | "deadline khi nào" · "link kia còn dùng được không" · câu cụt |
| ③ Ngoài thẩm quyền | 3 | xin gia hạn · xin đáp án · hỏi điểm nhóm khác |
| ④ Đặc thù domain | 3 | lịch K3 lẫn K4 · link cũ đã đóng · hỏi nội dung buổi chưa học |
| Case thường | 8 | câu tra cứu bình thường trên T1/T2 |
| Case hiếm | 4 | không dấu + viết tắt · hỏi 2 việc trong 1 câu · chỉ emoji · trolling |

## ≥10 case từ chatlog thật — phương pháp

Hướng B không có data pack Discord. Cách nhóm làm:

1. Lọc `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` với `role = student`.
2. Chọn các câu hỏi mang tính **tra cứu / hỏi lại thông tin**, giữ nguyên cách gõ của học viên (kể cả không dấu, viết tắt, sai chính tả).
3. Đặt lại vào bối cảnh Discord của khoá, **ghi mã `M####` gốc** ở cột `nguon` của từng case.
4. **Không dán nguyên văn dài vào repo** — chỉ ghi mã đoạn + câu hỏi đã rút gọn (quy định bảo mật data pack).

> ⚠️ Hỏi TA xác nhận cách này ngay tại CP2, đừng để đến CP3 mới biết là làm sai hướng.

## File trong thư mục này

| File | Nội dung |
|---|---|
| `golden-set.csv` | 24 case: `id, cau_hoi, lop, nhan_vang_route, nhan_vang_doc, nguon` |
| `ket-qua-luot-1.md` | Bảng đủ 24 case kể cả case fail, có %, đối chiếu quality bar |
| `ket-qua-luot-2.md` | Sau khi sửa MỘT failure đau nhất — chạy lại **trọn bộ** |
| `traces/` | Log request/response của từng lời gọi AI (CP3 trở đi) |

**Nhịp lặp:** chạy trọn bộ → bảng % → chọn một failure đau nhất → sửa → chạy lại **trọn bộ**. Sửa prompt chỗ này vỡ chỗ kia là chuyện thường.
