# validation — bằng chứng từ người thật

Hai loại, đừng lẫn:

## 1. Log khảo sát *(evidence chuẩn A — cho `spec.md §1`)*

File: `khao-sat-log.md`. Bốn dòng đầu bắt buộc:

```
Bộ câu hỏi đã dùng: 10 câu trắc nghiệm — nguyên văn ở work/form-khao-sat.md, không đổi giữa chừng
Định nghĩa "xác nhận" (chốt TRƯỚC khi phát form): Câu 7 >= 1 lần VÀ (Câu 4 thuộc {5-15', >15', phải hỏi người khác, bỏ luôn} HOẶC Câu 5 thuộc {không chắc mới nhất, phải hỏi người khác, dùng nhầm})
Người khảo sát: [tên] · Thời gian: [ngày, khung giờ] · Kênh: [form / hỏi trực tiếp]
Cỡ mẫu: n = __ ngoài nhóm — __ HV K4 / __ khoá khác / __ TA-coach
```

Kèm bảng kết quả từng người (xuất CSV từ Google Forms là đủ) và 4 con số rút ra: % xác nhận · phút mất mỗi tuần · % chọn từng ứng viên · % cần thấy nguồn.

## 2. Feedback log từ vòng user test *(rubric R6 = 8đ — làm ở CP5)*

File: `feedback-log.md`. **≥5 mẩu từ ≥5 người ngoài nhóm**, trong đó **≥2 người là willing user đã khai từ CP1**.

| Người thử (tên/vai — willing user?) | Task được giao | Quan sát (họ bấm gì, kẹt đâu) | Quote nguyên văn | Mức nghiêm trọng |
|---|---|---|---|---|
| | | | | |

Bốn dòng tổng hợp cuối file:
- Chủ đề lặp nhiều nhất:
- 1–2 thay đổi làm trước demo → ghi vào `spec.md §9`:
- Giữ nguyên có lý do:
- Đưa vào backlog (slide 6):

**Cách chạy một phiên 10 phút:** giao task thật ("hãy dùng cái này để tra hạn nộp spec") → **im lặng quan sát**, không thuyết minh, không gợi ý → hỏi đúng 3 câu:
1. "Điều gì khó hiểu hoặc khó chịu nhất?"
2. "Kết quả này bạn có tin không — vì sao?"
3. "Bạn có dùng thật không — vì sao / vì sao chưa?"

> Nếu mọi phản hồi đều là lời khen thì phiên test chưa đạt — giao task khó hơn hoặc đổi người thử.

## 3. Feedback trong sản phẩm

Nút 👍/👎 trong prototype ghi lý do vào trace. Bấm **"⬇ Tải log/trace"** trên thanh header để xuất `trace-cp2.json`, bỏ vào thư mục này.
