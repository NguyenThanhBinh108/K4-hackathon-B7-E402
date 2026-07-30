# Feedback Log — Validation User Testing
# B7-E402 · VinAI K4 Hackathon · Thực hiện trước CP5

> **Task giao cho mỗi người:** "Hãy dùng công cụ này để tìm thông tin về [chủ đề X] trong tài liệu khoá học"
> **Phương pháp:** Giao task → im lặng quan sát → hỏi 3 câu chuẩn sau khi dùng xong

---

## Bảng Feedback Log (≥5 người ngoài nhóm)

| Người thử (tên/vai) | Willing user? | Task giao | Quan sát (bấm gì, kẹt đâu) | Quote nguyên văn | Mức nghiêm trọng |
|---|---|---|---|---|---|
| **[Người 1] — Học viên cùng lớp** | ✅ Willing user từ CP1 | Upload d1-slide.pdf → hỏi "attention là gì" | Bấm upload PDF thành công; chờ ~3s; đọc summary; hỏi follow-up bằng chat | *"Citation [T06] rõ ràng, mình tự mở transcript ra check được"* | Low |
| **[Người 2] — Học viên cùng lớp** | ✅ Willing user từ CP1 | Hỏi "RAG khác fine-tuning thế nào" | Gõ câu hỏi → nhận trả lời → rate 👍 | *"Cái này hữu ích hơn hỏi ChatGPT vì có nguồn cụ thể trong khoá"* | Low |
| **[Người 3] — Học viên cùng lớp** | ✅ Willing user từ CP1 | Hỏi "deadline submit hackathon?" | Nhận response từ chối → thử lại với câu hỏi kỹ thuật | *"Lần đầu tưởng bị lỗi, nhưng đọc message thì hiểu — nên nói rõ hơn rằng đây là by design"* | Medium |
| **[Người 4] — Học viên zone khác** | — | Tổng hợp đoạn chat về embedding | Paste chat → nhận synthesis → hỏi "mình dùng cái này cho tuần sau được không?" | *"Output tổng hợp ngắn gọn, nhưng muốn có thêm 'tài liệu nên đọc tiếp theo'"* | Low |
| **[Người 5] — Học viên zone khác** | — | Upload PDF + hỏi câu hỏi về JTBD | Không biết format citation [T01-NNN], hỏi "cái [T01-034] là cái gì" | *"Nếu click được vào citation thì hay hơn, giờ phải tự mở transcript ra tìm"* | Medium |

---

## Tổng Hợp 4 Dòng

**Chủ đề lặp nhiều nhất:**
1. Citation reference không clickable → user phải tự mở file transcript tìm → friction
2. Out-of-scope message cần giải thích rõ hơn (không phải lỗi, là by design)

**1-2 thay đổi làm trước demo:**
1. ✅ **ĐÃ LÀM:** Thêm tooltip/note giải thích citation format: "Click vào [TXX-NNN] để biết tài liệu nào và đoạn mấy"
2. ✅ **ĐÃ LÀM:** Cập nhật out-of-scope message: thêm "Đây là giới hạn thiết kế — mình chỉ trả lời về kiến thức AI/ML" để user không tưởng lỗi

**Giữ nguyên có lý do:**
- Không thêm "suggested next resources" vào synthesis (Người 4 muốn) → scope creep, nằm ngoài lát cắt prototype

**Backlog (không làm trong hackathon):**
- Clickable citations → roadmap tuần 2 (cần link đến đúng đoạn trong transcript)
- Real-time Discord integration → roadmap tuần 1

---

## Chi Tiết Phiên Test

### Phiên [Người 1]
- **Thời gian:** ~10 phút
- **Task:** Upload d1-slide.pdf → hỏi follow-up về attention
- **Quan sát:** Upload thành công sau 1 lần thử (ban đầu không thấy nút upload), đọc summary ~2 phút, gõ câu hỏi tiếp theo
- **3 câu hỏi chuẩn:**
  - "Điều gì khó hiểu nhất?" → *"Không biết [T06] là gì, phải hỏi mới biết là transcript"*
  - "Kết quả có tin không?" → *"Tin vì có citation, mình verify được"*
  - "Dùng thật không?" → *"Có, đặc biệt khi ôn trước quiz"*

### Phiên [Người 2]
- **Thời gian:** ~8 phút
- **Task:** Q&A về RAG
- **Quan sát:** Gõ ngay câu hỏi, không upload gì, nhận trả lời, rate 👍
- **3 câu hỏi chuẩn:**
  - "Khó hiểu nhất?" → *"Không có gì khó hiểu, rõ ràng"*
  - "Tin không?" → *"Tin vì so với những gì thầy dạy thì đúng"*
  - "Dùng thật không?" → *"Có, tiện hơn tìm trong Discord"*

### Phiên [Người 3]
- **Thời gian:** ~12 phút
- **Task:** Hỏi logistics → sau đó hỏi kỹ thuật
- **Quan sát:** Bị confuse khi out-of-scope message xuất hiện, dừng lại hỏi người hướng dẫn (vi phạm quy trình silent observation — ghi lại)
- **3 câu hỏi chuẩn:**
  - "Khó hiểu nhất?" → *"Message từ chối — không biết là feature hay bug"*
  - "Tin không?" → *"Sau khi hiểu thì tin; phần kỹ thuật trả lời đúng"*
  - "Dùng thật không?" → *"Có nhưng phải biết cái gì nên hỏi, cái gì không"*
  - → **Action:** Update out-of-scope message thêm "đây là giới hạn thiết kế"

### Phiên [Người 4]
- **Thời gian:** ~9 phút
- **Task:** Chat synthesis
- **Quan sát:** Paste đoạn chat Discord thật (ẩn danh), nhận synthesis, hài lòng với stuck_points
- **3 câu hỏi chuẩn:**
  - "Khó hiểu nhất?" → *"Không biết tại sao phần synthesis lại tách ra tab riêng"*
  - "Tin không?" → *"Tin về phần topic, không chắc về stuck_points"*
  - "Dùng thật không?" → *"Muốn dùng nếu có thêm gợi ý tài liệu đọc tiếp"*

### Phiên [Người 5]
- **Thời gian:** ~13 phút
- **Task:** Upload PDF + Q&A JTBD
- **Quan sát:** Upload PDF xong đọc summary, gõ câu hỏi về JTBD, nhận trả lời, click citation không được
- **3 câu hỏi chuẩn:**
  - "Khó hiểu nhất?" → *"Citation [T01-034] — không biết click được không, tưởng là link"*
  - "Tin không?" → *"Tin về content, nhưng muốn click verify ngay"*
  - "Dùng thật không?" → *"Có, nếu citation có thể click thì càng tốt"*
  - → **Backlog:** Clickable citations (roadmap)
