# 🚀 Hướng Dẫn Chạy — VinAI Knowledge Assistant v2.0

> **Role 3 · Hải Đăng · Nhóm B7-E402** | Python 3.9+

---

## ⚡ Chạy Nhanh (Đã Cài Sẵn)

```powershell
# Double-click: codebase/run.bat
# Hoặc PowerShell:
cd d:\VINAI_Team_093\LAB\K4-hackathon-B7-E402\codebase
.\start.ps1
```

Mở: **`http://localhost:8000`**

---

## Lần Đầu — Cài & Chạy Thủ Công

```powershell
# 1. Vào thư mục backend
cd d:\VINAI_Team_093\LAB\K4-hackathon-B7-E402\codebase\backend

# 2. Tạo môi trường ảo
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Cài packages
pip install -r requirements.txt

# 4. Cấu hình API key
copy .env.example .env
# Mở .env và điền GEMINI_API_KEY=<key của bạn>
# Lấy key miễn phí tại: https://aistudio.google.com/app/apikey

# 5. Chạy server
python main.py
```

> Nếu lỗi "scripts is disabled": `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

## Kiểm Tra Nhanh

| URL | Mong đợi |
|---|---|
| `http://localhost:8000/api/health` | `{"status":"ok","gemini_configured":true,"kb_docs":8}` |
| `http://localhost:8000/docs` | Swagger UI — test API trực tiếp |
| `http://localhost:8000` | Web UI Discord dark theme |

---

## Cấu Trúc Code (v2.0)

```
backend/
├── main.py                 ← FastAPI: 5 routes + conversational memory
├── requirements.txt
├── .env.example            ← Copy → .env, điền key
├── knowledge_base.json     ← 8 docs (6 transcripts + 2 slides) [MOCK KB]
└── services/
    ├── gemini_service.py   ← Gemini Flash calls + AI call logging [REAL AI]
    ├── knowledge_base.py   ← Router: injection→logistics→ambiguous→RAG
    └── pdf_service.py      ← PyMuPDF extraction [REAL]

frontend/
├── index.html              ← 3 tabs: Chat / Documents / Synthesize
├── script.js               ← v2: feedback 👍👎, citation tooltip, session memory
└── style.css               ← Aurora dark theme + route tags + feedback styles
```

---

## Tính Năng v2.0

| Feature | Mô tả |
|---|---|
| **4-layer routing** | Injection ③ → Logistics ③ → Ambiguous ② → RAG ① |
| **Conversational memory** | 4 turns per session — hỏi follow-up không cần nhắc lại context |
| **AI call logging** | Mọi Gemini call → `eval/ai_call_log.jsonl` tự động |
| **Feedback 👍👎** | Mỗi tin nhắn có nút feedback → `validation/feedback.jsonl` |
| **Citation tooltip** | Hover vào [TXX-NNN] để thấy hướng dẫn verify |
| **Route tag** | Màu xanh (KB answer), đỏ (blocked), vàng (ambiguous) |
| **Auto-disclaimer** | Mọi AI output kèm "🤖 Tóm tắt tự động — xem nguyên văn" |
| **Injection detection** | Block prompt injection trước khi vào Gemini |

---

## Demo 5 Phút (CP6)

```
[0:00] Mở http://localhost:8000 — Status bar hiện "Gemini ✓ · 8 docs"

[0:30] CASE CHUẨN — Upload PDF:
       Kéo d1-slide-hackathon.pdf vào dropzone
       → Summary với citations, route tag "📄 PDF Summary"
       → Hover citation chip → tooltip hiện

[1:30] CASE CHUẨN — Q&A:
       Gõ: "Transformer và attention mechanism hoạt động thế nào?"
       → Route tag xanh "📚 KB Answer", có [T06-NNN]
       → Nút 👍👎 ở dưới mỗi câu trả lời

[2:30] CASE KHÓ — Out-of-scope:
       Gõ: "Deadline nộp bài hackathon là bao giờ?"
       → Route tag đỏ "⛔ Ngoài phạm vi", không gọi Gemini

[3:00] CASE KHÓ — Ambiguous:
       Gõ: "tài liệu" (1 từ)
       → Route tag vàng "💭 Hỏi lại", gợi ý 5 chủ đề cụ thể

[3:30] CASE ĐA LƯỢT — Conversational:
       Hỏi: "Transformer là gì?" → nhận trả lời
       Hỏi tiếp: "Còn positional encoding?" → nhớ context Transformer

[4:00] Tab Tổng hợp → paste chat → synthesis kết quả

[4:30] Số liệu: 19/21 golden set pass → fix 2 → 21/21 (100%)
       Quality bar: ≥75% ✅ · 100% citation ✅ · 100% scope ✅
```

---

## Troubleshooting

| Lỗi | Fix |
|---|---|
| `scripts is disabled` | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `Port 8000 in use` | `netstat -ano \| findstr :8000` → `taskkill /PID <N> /F` |
| `INVALID_API_KEY` | Lấy key mới tại [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| PDF không đọc được | PDF dạng scan ảnh → error message hướng dẫn rõ |
| `No module named fastapi` | Activate .venv trước: `.\.venv\Scripts\Activate.ps1` |

---

*VinAI Knowledge Assistant v2.0 · Nhóm B7-E402 · K4 Hackathon*
