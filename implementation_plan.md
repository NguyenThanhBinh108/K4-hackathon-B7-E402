# Implementation Plan v3 — Discord Knowledge Assistant (B7-E402)

> **Cập nhật:** 31/07/2026 · **Owner:** Hải Đăng · **Nhóm:** B7-E402 · **Hướng:** B
> Đây là plan thực thi cuối cùng sau khi đã có codebase + đánh giá gap vs rubric.

---

## 0. Trạng Thái Hiện Tại (As-Is)

### Codebase đã có (✅ hoạt động)

```
codebase/backend/
├── main.py              ✅ FastAPI + 5 routes (health, kb, summarize, chat, synthesize)
├── services/
│   ├── gemini_service.py ✅ Gemini Flash, JSON output, 3 functions
│   ├── knowledge_base.py ✅ JSON KB, keyword search, logistics/ambiguous detection
│   └── pdf_service.py   ✅ PyMuPDF PDF parsing
└── knowledge_base.json  ⚠️ Mock data — cần mở rộng

codebase/frontend/
├── index.html  ✅ Discord dark UI
├── script.js   ✅ Chat + PDF upload
└── style.css   ✅
```

### Thiếu để nộp bài (❌ chưa có)

| Cần tạo | Điểm rubric | Priority |
|---|:---:|:---:|
| `spec.md` đầy đủ §1-§9 | R1+R2+R3 unlock | 🔴 P0 |
| `eval/golden_set.md` ≥20 cases | R4: +9 | 🔴 P0 |
| `eval/run_results_01.md` bảng % | R4: +4 | 🔴 P0 |
| `validation/feedback_log.md` ≥5 người | R6: +8 | 🔴 P0 |
| `validation/changelog.md` | R6: +4 | 🔴 P0 |
| Quality bar commit trong spec.md | R4: +3 | 🔴 P0 |
| `reflection/` 5 files | Điểm cá nhân | 🟡 P1 |
| `eval/ai_call_log.jsonl` | R5: +3 | 🟡 P1 |
| Bảng impact 3 ứng viên | R1: +3 | 🟡 P1 |

---

## 1. Kiến Trúc Quyết Định Cuối (To-Be)

### Lý do chọn Sketch/Mock (không phải Full Working)

Áp dụng Agentic Fit Scoring (từ tài liệu khoá Ngày 3-5):

| Tiêu chí | Điểm | Lý do |
|---|:---:|---|
| Multi-step reasoning | 2/5 | Route → retrieve → generate là chuỗi cố định, không có plan động |
| Tool interaction | 3/5 | Gọi Gemini + KB search — biết trước tool nào dùng khi nào |
| Dynamic decision | 2/5 | Router quyết định 1 lần, không loop action→observe→adapt |
| Long horizon | 1/5 | Mỗi request độc lập |
| **Tổng: 8/20** | | Vùng "augmented chatbot" (6-10) — KHÔNG cần Agent/MCP |

**Mức prototype chọn: Mock** — flow bấm được hoàn toàn, AI thật ở quyết định trung tâm (summarize + chat), KB là JSON (không phải vector DB).

### Kiến Trúc Hệ Thống

```
┌────────────────────────────────────────────────────────┐
│          Web Demo UI (Discord Dark Theme)               │
│  [Chat Q&A] [Document Summary] [Knowledge Base]        │
└───────────────────────┬────────────────────────────────┘
                        │ HTTP REST
                        ▼
┌────────────────────────────────────────────────────────┐
│              FastAPI Backend (main.py)                  │
│                                                         │
│  POST /api/chat ──→ [ROUTER]                           │
│                       ├─ LOGISTICS → từ chối cứng      │
│                       ├─ AMBIGUOUS → hỏi lại 1 câu     │
│                       └─ RAG_QUERY                      │
│                           │                             │
│                     [KB SEARCH] (keyword)               │
│                           │                             │
│                     [GEMINI GENERATE]                   │
│                     system: CHỈ từ KB, PHẢI cite       │
│                           │                             │
│                     [OUTPUT GUARDRAIL]                  │
│                     check citation, cap length          │
│                                                         │
│  POST /api/summarize → [PyMuPDF] → [GEMINI FLASH]     │
│                         structured JSON + citations     │
│                                                         │
│  POST /api/synthesize → [GEMINI FLASH]                 │
│                          Discord chat → insights        │
│                                                         │
│  GET  /api/knowledge-base → JSON KB read               │
│  GET  /api/health          → health check               │
└────────────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│       Knowledge Base (knowledge_base.json)              │
│  8-10 docs từ transcript [T01-T06] của data pack       │
│  Mỗi doc: title, module, level, key_concepts,          │
│           citations [Txx-NNN], key_takeaways           │
└────────────────────────────────────────────────────────┘
```

---

## 2. Lát Cắt Chính Thức (MỘT CÂU)

> **Khi học viên gửi link tài liệu hoặc câu hỏi kiến thức vào kênh Discord, hệ thống tự động phân loại intent, tóm tắt tài liệu có trích dẫn [TXX-NNN] hoặc trả lời từ Knowledge Base — từ chối đúng cách khi ngoài phạm vi — giúp học viên tiết kiệm 10-30 phút tìm kiếm thủ công.**

### Non-goals (≥3 — bắt buộc cho rubric R2):
1. Không xử lý video/audio (text/PDF only)
2. Không tích hợp Discord bot thật (demo qua Web UI)
3. Không RAG với vector DB (dùng JSON KB + Gemini context)
4. Không web search ngoài tài liệu khoá
5. Không quản lý permission Discord

---

## 3. Bốn Đường Đi Trải Nghiệm (Rubric R3)

### ① Happy Path — RAG Query có căn cứ
```
Input: "Transformer và attention mechanism hoạt động thế nào?"
→ Router: RAG_QUERY (>3 từ, không logistics, không vague)
→ KB search: tìm [T06] Foundation: Transformer & Attention
→ Gemini: "Self-attention tính score bằng... [T06-023]"
→ Output: câu trả lời + citations + "Xem thêm: [T06]"
```

### ② Low-confidence — Câu hỏi mơ hồ
```
Input: "slide về AI" (2 từ)
→ Router: AMBIGUOUS
→ Output: "Bạn muốn tìm về khía cạnh nào?
   • LLM & Foundation  • Transformer  • Prompt Engineering
   • RAG & Evaluation  • Bài toán AI"
→ User làm rõ → xử lý lại
```

### ③ Failure — Ngoài phạm vi / không có căn cứ
```
Input: "Deadline nộp bài tuần này?"
→ Router: OUT_OF_SCOPE (match logistics keywords)
→ Output: "⚠️ Ngoài phạm vi. Hỏi Lab Coach hoặc #announcements"
→ KHÔNG gọi Gemini, KHÔNG tốn token
```

### ④ Correction — User sửa output
```
User: "Citation [T06-050] này sai rồi, slide không nói vậy"
→ System: "Cảm ơn! Đây là đoạn mình dựa vào: [text trích dẫn].
   Nếu tài liệu bạn có phiên bản khác, hãy xem nguyên văn để verify.
   [👍 Đúng / 👎 Sai] — feedback giúp mình cải thiện."
→ Log feedback vào eval/feedback.jsonl
```

---

## 4. HAX/PAIR Nguyên Tắc (≥4 — Rubric R2)

> **Mỗi nguyên tắc PHẢI trỏ vào vị trí cụ thể trong prototype**

| Nguyên tắc | Vị trí áp dụng cụ thể | File / Dòng |
|---|---|---|
| **G1 — Làm rõ scope** | Welcome message khi load app: liệt kê CÓ THỂ và KHÔNG | `frontend/index.html` — welcome banner |
| **G2 — Làm rõ độ chính xác** | Mọi summary có "🤖 Tóm tắt tự động — xem nguyên văn" | `gemini_service.py` — mọi output |
| **G10 — Thu hẹp khi nghi ngờ** | `is_ambiguous_query()` hỏi lại 1 câu, không đoán | `knowledge_base.py` L75-80 |
| **G11 — Giải thích vì sao** | Citation kèm context: "Mình tìm thấy vì [keyword] xuất hiện ở [TXX-NNN]" | `gemini_service.py` — system prompt |
| **G8 — Gạt bỏ dễ dàng** | Nút 👍👎 trên mỗi câu trả lời → log feedback | `frontend/script.js` — feedback handler |
| **PAIR Explainability** | Mọi recommendation kèm lý do từ tài liệu gốc | `gemini_service.py` — CHAT_SYSTEM |

---

## 5. Golden Set Structure (≥20 Cases — Rubric R4)

Lưu tại: `eval/golden_set.md`

| Nhóm | Cases | Layer | Nguồn |
|---|:---:|---|---|
| A — Summary PDF thật | 3 | Thường | d1-slide, d2-slide |
| B — RAG content Q&A | 4 | Thường | transcript T01-T06 |
| C — Chat synthesis | 2 | Thường | chatlog export |
| D — Out-of-scope | 3 | ③ | Tự tạo |
| E — Ambiguous | 2 | ② | Tự tạo |
| F — Hallucination risk | 3 | ① | Tự tạo + chatlog |
| G — Domain specific | 2 | ④ | transcript + chatlog |
| H — Edge cases | 2 | ① | Tự tạo |
| **Tổng** | **21** | | **≥10 từ chatlog thật** |

---

## 6. Quality Bar Commit (Rubric R4)

```
Quality Bar — B7-E402 v1.0
Commit tại spec.md 23:59 N1 — KHÔNG đổi sau đó

Đạt khi:
  ≥75% cases trong golden set pass (theo định nghĩa từng chiều)
  VÀ 100% RAG_QUERY có citation [TXX-NNN]
  VÀ 100% câu hỏi logistics bị từ chối trước khi vào LLM
  VÀ 0 case nào output thông tin tài chính/cá nhân/điểm số

Định nghĩa pass từng chiều:
  Citation: Pass = citation trace được về doc trong knowledge_base.json
  Scope: Pass = logistics query bị block ở layer is_logistics_query()
  Relevance: Pass = 2 reviewer đồng ý câu trả lời đúng chủ đề (chấm tay)
  Length: Pass = response ≤ 1000 ký tự (Discord-friendly)
  Safety: Pass = không bịa, không có thông tin ngoài KB
```

---

## 7. Timeline Thực Thi

| Thời gian | Việc | Output kiểm chứng | Owner |
|---|---|---|---|
| **NGAY BÂY GIỜ** | Tạo `eval/golden_set.md` ≥20 cases | File commit | Bình |
| **NGAY BÂY GIỜ** | Tạo `spec.md` §1-§9 | File commit | Hải Đăng |
| **Trước CP3 (10:30 N2)** | Chạy golden set, log `eval/run_results_01.md` | Bảng % | Bình + Hải Đăng |
| **Trước CP3** | Thêm `eval/ai_call_log.jsonl` | File log | Hải Đăng |
| **Trước 23:59 N1** | Commit `spec.md` + quality bar | Git commit | Hải Đăng |
| **Trước CP5 (14:00 N2)** | `validation/feedback_log.md` ≥5 người | File commit | Linh |
| **Trước CP5** | `validation/changelog.md` | File commit | Linh |
| **Trước CP5** | `reflection/` 5 files | Files commit | Liễu + mọi người |
| **Trước CP6 (15:00 N2)** | `demo-slides.pdf` 6 trang | PDF file | Liễu |

---

## 8. Cải Tiến Code Cần Làm (Nhỏ)

### 8.1 Thêm AI Call Logging vào `gemini_service.py`

```python
import json, hashlib, time, os

LOG_PATH = os.path.join(os.path.dirname(__file__), "../../eval/ai_call_log.jsonl")

def log_ai_call(route: str, model: str, prompt: str, has_citation: bool, case_id: str = None):
    """Log mỗi lời gọi AI để có evidence trong repo."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "route": route,
        "model": model,
        "input_hash": hashlib.md5(prompt.encode()).hexdigest()[:8],
        "prompt_length": len(prompt),
        "has_citation": has_citation,
        "golden_case": case_id
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
```

Gọi sau mỗi `model.generate_content()`:
```python
# Sau summarize_document():
log_ai_call("SUMMARY", MODEL_NAME, prompt, has_citation=True)

# Sau chat_with_kb():
has_cite = bool(result.get("citations"))
log_ai_call("RAG_QUERY", MODEL_NAME, prompt, has_citation=has_cite)
```

### 8.2 Mở Rộng `knowledge_base.json` (Từ Transcript Thật)

Thêm ít nhất 6 docs từ transcript data pack (T01-T06), mỗi doc bao gồm:
```json
{
  "id": "T06",
  "title": "Foundation: Transformer & Attention Mechanism",
  "module": "Day 1 Foundation",
  "level": "Intermediate",
  "key_concepts": ["self-attention", "multi-head attention", "positional encoding", "Query/Key/Value"],
  "key_takeaways": [
    "Self-attention cho phép model \"nhìn\" toàn bộ sequence cùng lúc — [T06-023]",
    "Multi-head attention học nhiều loại relationship khác nhau — [T06-045]",
    "Positional encoding thêm thông tin vị trí vì attention không có order — [T06-067]"
  ],
  "citations": ["[T06-001]", "[T06-023]", "[T06-045]", "[T06-067]", "[T06-089]"],
  "summary": "Giải thích cơ chế Transformer và Attention từ căn bản — khối kiến thức nền tảng cho mọi LLM hiện đại",
  "source_file": "transcript-06-clean.md",
  "total_segments": 162
}
```

### 8.3 Thêm Endpoint Feedback (Optional nhưng tốt cho R2/R6)

```python
class FeedbackRequest(BaseModel):
    message_id: str
    rating: str  # "up" | "down"
    comment: str = ""

@app.post("/api/feedback")
def log_feedback(req: FeedbackRequest):
    """Log user feedback để improve và làm evidence validation."""
    import json, time
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "message_id": req.message_id,
        "rating": req.rating,
        "comment": req.comment
    }
    os.makedirs("../../validation", exist_ok=True)
    with open("../../validation/feedback.jsonl", "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"status": "logged"}
```

---

## 9. Kịch Bản Demo 5 Phút (CP6)

```
0:00 → Slide 1: User & Job
       "Học viên VinAI cần tìm lại tài liệu trong Discord — mất 10-30 phút"
       Con số: 46.2% tutor responses không có citations (mining 2.522 dòng chatlog)
               XX/20 người khảo sát xác nhận pain (≥50% required)

0:45 → Slide 2: Vì sao chọn tính năng này
       Bảng 3 ứng viên: Summary tài liệu vs Trợ lý logistics vs Chat synthesis
       Ứng viên loại + lý do bằng số

1:30 → Demo live Case Chuẩn:
       Upload d1-slide-hackathon.pdf → Gemini summary có citations
       Hỏi "Transformer attention là gì?" → trả lời kèm [T06-023]

2:30 → Demo live Case Khó:
       Hỏi "Deadline nộp bài?" → từ chối đúng cách (không gọi LLM)
       Hỏi "slide về AI" → hỏi lại thông minh
       (Giám khảo có thể bắn case lạ — mình sẵn sàng)

3:30 → Slide 4: Kết quả đo
       XX/21 golden set pass (vs quality bar 75%)
       Failure analysis: case nào fail + lý do + đã sửa gì

4:15 → Slide 5+6: User thật nói gì + roadmap
       ≥2 quote nguyên văn (tên cụ thể) từ validation log
       Nếu có thêm 1 tuần: ChromaDB thật + conversational memory + Discord bot
```

---

## 10. Checklist Nộp Bài (Đầy Đủ)

### Repo Structure (Đạt R7)
- [ ] `README.md` — phân công có tên từng phần
- [ ] `spec.md` — §1-§9 đầy đủ, commit trước 23:59 N1
- [ ] `demo-slides.pdf` — 6 trang theo guide §5.1
- [ ] `team-report.md` ✅
- [ ] `feature-knowledge-synthesis.md` ✅
- [ ] `implementation_plan.md` ✅ (file này)

### Codebase (Đạt R5)
- [ ] `codebase/` chạy được end-to-end không can thiệp tay
- [ ] ≥1 lời gọi AI thật ở quyết định trung tâm (summarize + chat)
- [ ] Ghi rõ phần nào mock (knowledge_base.json = mock KB)
- [ ] `eval/ai_call_log.jsonl` có log AI calls thật

### Eval (Đạt R4)
- [ ] `eval/golden_set.md` ≥20 cases, ≥2 case/layer
- [ ] `eval/run_results_01.md` bảng % đủ mọi case kể cả fail
- [ ] Quality bar commit trong `spec.md` §7

### Validation (Đạt R6)
- [ ] `validation/feedback_log.md` ≥5 người có tên + quote nguyên văn
- [ ] `validation/changelog.md` ≥1 thay đổi từ feedback

### Reflection (Điểm cá nhân)
- [ ] `reflection/vu.md`
- [ ] `reflection/binh.md`
- [ ] `reflection/linh.md`
- [ ] `reflection/lieu.md`
- [ ] `reflection/hai-dang.md`

---

*B7-E402 · Implementation Plan v3 · Cập nhật 31/07/2026*
