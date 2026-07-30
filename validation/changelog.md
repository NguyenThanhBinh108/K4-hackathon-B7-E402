# Changelog — B7-E402
# Theo dõi thay đổi từ feedback user và eval results

| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) | File thay đổi |
|---|---|---|---|
| 31/07/2026 03:00 | Cập nhật out-of-scope message: thêm "Đây là giới hạn thiết kế" | Feedback [Người 3]: tưởng là lỗi thay vì by design | `services/knowledge_base.py` là_logistics_query response |
| 31/07/2026 03:05 | Thêm tooltip giải thích format citation [TXX-NNN] | Feedback [Người 5]: không biết citation có thể dùng để verify gì | `frontend/index.html` help text |
| 31/07/2026 03:10 | Fix system prompt CHAT_SYSTEM: enforce disclaimer cho domain-specific answers | Eval Case G01: fail vì thiếu "xem nguyên văn" cho câu hỏi kỹ thuật sâu | `services/gemini_service.py` CHAT_SYSTEM |
| 31/07/2026 03:15 | Thêm response length cap 900 chars vào system prompt | Eval Case H02: response dài 1340 ký tự (> 1000 chars limit) | `services/gemini_service.py` CHAT_SYSTEM |
| 31/07/2026 03:20 | Thêm 3 docs mới vào knowledge_base.json (T02, T03, D2-SLIDE) | KB cũ thiếu transcript T02, T03 — làm test case B03 thiếu context | `backend/knowledge_base.json` |

## Quyết Định Giữ Nguyên (có lý do)

| Đề xuất từ feedback | Quyết định | Lý do |
|---|---|---|
| Thêm "suggested next resources" vào synthesis (Người 4) | ❌ Không làm | Scope creep — ngoài lát cắt prototype; roadmap sau hackathon |
| Clickable citations link đến transcript (Người 5) | ❌ Không làm trong hackathon | Cần index đoạn [TXX-NNN] vào database, không phải JSON KB — roadmap tuần 2 |
| Gộp tab Chat và Summary thành 1 tab (Người 4) | ❌ Không làm | 2 tab phân biệt rõ 2 luồng (upload doc vs Q&A) — UX design decision có căn cứ |
