# Reflection — Hải Đăng · B7-E402 · VinAI K4 Hackathon

## Vai Trò & Phần Mình Làm

**Vai trò:** Role 3 owner — Knowledge Synthesis & Document Intelligence  
**Demo chính của nhóm**

**Phần mình làm cụ thể:**

| Phần | Chi tiết |
|---|---|
| **Feature Spec** | Viết `feature-knowledge-synthesis.md` và `spec.md` §1-§9 đầy đủ |
| **Backend** | `main.py` (FastAPI 5 routes) · `gemini_service.py` · `knowledge_base.py` · `pdf_service.py` |
| **Frontend** | `index.html` · `script.js` · `style.css` (Discord dark theme) |
| **Eval** | `golden_set.md` (21 cases) · `quality_bar.md` · `run_results_01.md` |
| **Validation** | Tổ chức 5 phiên user test · `feedback_log.md` · `changelog.md` |
| **Kiến trúc** | Quyết định không dùng Agent/MCP (Agentic Fit Score 8/20) · chọn Router+Conditional pattern |

## AI Hỗ Trợ Thế Nào

- **Gemini Flash:** Core AI call cho summarization và Q&A — đây là lời gọi AI thật, không phải hardcode
- **Cursor/AI code assistant:** Giúp generate skeleton FastAPI và HTML boilerplate — mình tự review và sửa từng phần
- **Mình tự làm:** Toàn bộ business logic (router, guardrail, knowledge_base search, prompt engineering), spec §1-§9, golden set, evaluation methodology

**Tôi có thể giải thích được:**
- Tại sao router check `is_logistics_query()` trước khi gọi Gemini — cost-of-error reasoning
- Tại sao dùng conditional automation, không phải full automation — citation sai kỹ thuật cost rất cao
- Tại sao không dùng ChromaDB trong prototype — thời gian vs value: keyword search + Gemini context đủ cho demo
- Từng case trong golden set và tại sao chọn case đó

## Bài Học Từ Case Fail

**Case fail đáng kể nhất:** Case G01 — softmax explanation thiếu disclaimer

**Tình huống:** Câu hỏi về softmax vs sigmoid trong attention — Gemini trả lời đúng về nội dung kỹ thuật nhưng thiếu dòng "xem nguyên văn để xác nhận". Khi 2 reviewer chấm tay, 1 người pass, 1 người fail → định nghĩa mơ hồ.

**Bài học:**
1. **"Đúng về nội dung" ≠ "đáp ứng quality bar"** — phải định nghĩa quality dimension rõ TRƯỚC khi chạy, không phải sau khi thấy output
2. **Hai reviewer chấm khác nhau = định nghĩa phải viết lại** — đây là tín hiệu, không phải bất đồng cá nhân
3. **System prompt engineering là iterative** — không thể viết prompt đúng ngay từ đầu; cần chạy, fail, fix, chạy lại

**Thay đổi cụ thể:** Thêm vào CHAT_SYSTEM: "Với câu hỏi kỹ thuật sâu, LUÔN kèm '🤖 Xem [TXX] để verify chi tiết kỹ thuật.'" → re-run case G01: Pass.

## Nếu Có Thêm 1 Tuần

1. **ChromaDB vector search** — thay keyword search bằng embedding search thật; từ chatlog feedback: citation quality sẽ tốt hơn nhiều
2. **Clickable citations** — Người 5 feedback đúng: link [T06-023] cần click được đến đúng đoạn trong transcript
3. **Discord bot integration** — thin client gọi FastAPI đã có; discord.py 30 phút là xong; phần khó nhất đã giải quyết (backend logic)

**Bài học lớn nhất:** *Guardrail không phải thứ thêm vào cuối — phải thiết kế từ đầu. Router + logistics filter là thứ đầu tiên viết, không phải feature chính.*
