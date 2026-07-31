# 🚀 Hướng Dẫn Chạy Chi Tiết — VinAI Knowledge Assistant v2.1

> **Role 3 · Hải Đăng · Nhóm B7-E402** | Python 3.9+
> File này hướng dẫn chạy **từ đầu đến hết**, kể cả xử lý rate-limit và chạy Discord bot thật.
> Xem [README.md](../README.md) ở gốc repo để biết phân công + cấu trúc repo tổng quan.

---

## Mục lục

1. [Chạy nhanh (đã cài sẵn)](#1-chạy-nhanh-đã-cài-sẵn)
2. [Lần đầu — cài & chạy thủ công](#2-lần-đầu--cài--chạy-thủ-công)
3. [Cấu hình `.env` — bắt buộc và tuỳ chọn](#3-cấu-hình-env--bắt-buộc-và-tuỳ-chọn)
4. [Kiểm tra hệ thống chạy đúng](#4-kiểm-tra-hệ-thống-chạy-đúng)
5. [Chạy Discord bot thật (tuỳ chọn)](#5-chạy-discord-bot-thật-tuỳ-chọn)
6. [Cấu trúc code](#6-cấu-trúc-code)
7. [Demo 5 phút (CP6)](#7-demo-5-phút-cp6)
8. [Troubleshooting — kể cả rate-limit / quota](#8-troubleshooting--kể-cả-rate-limit--quota)

---

## 1. Chạy Nhanh (Đã Cài Sẵn)

```powershell
# Double-click: codebase/run.bat
# Hoặc PowerShell:
cd d:\VINAI_Team_093\LAB\K4-hackathon-B7-E402\codebase
.\start.ps1
```

Mở: **`http://localhost:8000`**

Script tự tạo `.venv`, cài `requirements.txt`, và copy `.env.example` → `.env` nếu chưa có —
nhưng **vẫn phải tự điền API key** vào `.env` (xem mục 3), script không làm hộ bước này.

---

## 2. Lần Đầu — Cài & Chạy Thủ Công

```powershell
# 1. Vào thư mục backend
cd d:\VINAI_Team_093\LAB\K4-hackathon-B7-E402\codebase\backend

# 2. Tạo môi trường ảo
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Cài packages
pip install -r requirements.txt

# 4. Cấu hình API key — xem chi tiết mục 3
copy .env.example .env
# Mở .env và điền GEMINI_API_KEY=<key của bạn>
# Lấy key miễn phí tại: https://aistudio.google.com/app/apikey

# 5. Chạy server
python main.py
```

> Nếu lỗi "scripts is disabled": `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

> ⚠️ **Kiểm tra `groq` đã cài thật** (dùng làm fallback khi Gemini rate-limit):
> `.\.venv\Scripts\python.exe -c "import groq; print('groq OK')"`.
> Nếu báo `No module named 'groq'` dù có trong `requirements.txt` → chạy lại
> `pip install -r requirements.txt`. Đây là lỗi từng gặp thật trong quá trình dev
> khiến fallback không hoạt động dù code đã viết đúng.

---

## 3. Cấu Hình `.env` — Bắt Buộc Và Tuỳ Chọn

`codebase/backend/.env.example`:

```ini
GEMINI_API_KEY=your_gemini_api_key_here     # BẮT BUỘC — https://aistudio.google.com/app/apikey
GEMINI_MODEL=gemini-2.0-flash               # đổi model chỉ cần sửa dòng này, không sửa code

# Fallback provider — dùng khi Gemini bị rate-limit (429) hoặc lỗi giữa chừng.
# Không set thì hệ thống vẫn chạy, chỉ mất khả năng fallback lúc Gemini quá tải.
GROQ_API_KEY=your_groq_api_key_here         # https://console.groq.com/keys — free tier
GROQ_MODEL=llama-3.3-70b-versatile

# Retry / rate-limit resilience — mặc định đã hợp lý, chỉnh nếu cần
LLM_RETRY_MAX_ATTEMPTS=3      # số lần thử lại mỗi provider trước khi bỏ cuộc
LLM_RETRY_BASE_DELAY=1.0      # giây, backoff tăng dần: 1s → 2s → 4s + jitter
LLM_CACHE_TTL_SECONDS=600     # cache câu trả lời trùng lặp trong 10 phút
LLM_CACHE_MAX_ENTRIES=200
LLM_MAX_CONCURRENT=2          # số lệnh gọi LLM chạy đồng thời tối đa (chống burst vượt RPM)
```

**Vì sao cần `GROQ_API_KEY`:** free-tier Gemini có thể bị giới hạn rất thấp (đôi khi
`limit: 0` nếu project chưa bật free-tier — kiểm tra tại
[ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits)
nếu 429 xảy ra ngay từ request đầu tiên). Không có Groq key, hệ thống vẫn chạy nhưng
sẽ trả lỗi "quá tải" cho người dùng thay vì tự chuyển provider.

---

## 4. Kiểm Tra Hệ Thống Chạy Đúng

| URL | Mong đợi |
|---|---|
| `http://localhost:8000/api/health` | `{"status":"ok","gemini_configured":true,"kb_docs":8}` |
| `http://localhost:8000/docs` | Swagger UI — test API trực tiếp |
| `http://localhost:8000` | Web UI Discord dark theme |

**Kiểm tra retry/fallback/cache hoạt động thật** (không bắt buộc, hữu ích khi debug rate-limit):

```powershell
# Gửi 1 câu hỏi, xem log server — nếu Gemini rate-limit sẽ thấy dòng:
#   [LLM] gemini attempt 1 failed (rate_limit), retry in 1.1s
#   [LLM] Gemini exhausted (rate_limit): ...
# rồi tự chuyển Groq nếu có key.

# Mở eval/ai_call_log.jsonl, dòng cuối phải có đủ field:
#   provider, attempt, error_type, latency_ms, cache_hit
# Gửi lại đúng câu hỏi cũ (session khác) → dòng log mới phải có "cache_hit": true
```

---

## 5. Chạy Discord Bot Thật (Tuỳ Chọn)

`codebase/discord_bot/bot.py` là bot Discord thật (không phải mock), gọi thẳng vào backend
FastAPI qua HTTP. Chỉ cần chạy nếu muốn demo trực tiếp trong Discord thay vì Web UI.

```powershell
# 1. Backend phải đang chạy (mục 1 hoặc 2) tại http://localhost:8000

# 2. Cài dependencies riêng cho bot
cd d:\VINAI_Team_093\LAB\K4-hackathon-B7-E402\codebase\discord_bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Cấu hình token
copy .env.example .env
# Mở .env, điền:
#   DISCORD_BOT_TOKEN=<token bot từ Discord Developer Portal>
#   KB_API_BASE=http://localhost:8000

# 4. Chạy bot
python bot.py
```

Lệnh dùng trong Discord: `!ka hỏi <câu hỏi>` · `!ka tóm tắt` (reply vào tin có PDF đính kèm)
· `!ka tổng hợp <đoạn chat>` · `!ka kb` · `!ka help`.

> Lưu ý: nếu `spec.md` khai non-goal "không tích hợp Discord bot thật", hãy xác nhận lại
> phạm vi nộp bài trước khi demo phần này — mục này chỉ mô tả cách chạy, không quyết định
> việc có đưa vào phạm vi chấm hay không.

---

## 6. Cấu Trúc Code

```
backend/
├── main.py                 ← FastAPI: 5 routes + conversational memory + xử lý lỗi 503 khi hết provider
├── requirements.txt
├── .env.example            ← Copy → .env, điền key (xem mục 3)
├── knowledge_base.json     ← 8 docs (6 transcripts + 2 slides) [MOCK KB]
└── services/
    ├── gemini_service.py   ← Gemini/Groq calls + retry/backoff + fallback + cache + AI call logging [REAL AI]
    ├── knowledge_base.py   ← Router: injection→logistics→ambiguous→RAG
    └── pdf_service.py      ← PyMuPDF extraction [REAL]

frontend/
├── index.html               ← 3 tabs: Chat / Documents / Synthesize
├── script.js                ← Feedback 👍👎, citation tooltip, session memory
└── style.css                ← Aurora dark theme + route tags + feedback styles

discord_bot/                ← Bot Discord thật, thin client gọi backend qua HTTP
├── bot.py
├── requirements.txt
└── .env.example
```

---

## 7. Demo 5 Phút (CP6)

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

[4:30] Số liệu: xem eval/run_results_01.md — đối chiếu quality bar
       (≥75% pass · 100% citation · 100% scope refusal), đảm bảo bảng khớp với
       eval/ai_call_log.jsonl trước khi trình bày
```

---

## 8. Troubleshooting — Kể Cả Rate-Limit / Quota

| Lỗi | Fix |
|---|---|
| `scripts is disabled` | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `Port 8000 in use` | `netstat -ano \| findstr :8000` → `taskkill /PID <N> /F` |
| `INVALID_API_KEY` | Lấy key mới tại [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| `429 RESOURCE_EXHAUSTED`, `limit: 0` trong log | Free-tier Gemini chưa bật cho project này — không phải lỗi code. Kiểm tra billing/quota tại link trong message lỗi, hoặc dùng `GROQ_API_KEY` để hệ thống tự fallback trong lúc chờ |
| Response chậm bất thường / hay bị "quá tải" | Kiểm tra `LLM_MAX_CONCURRENT` trong `.env` — hạ xuống 1 nếu free-tier RPM quá thấp; xem `eval/ai_call_log.jsonl` field `error_type` để biết đang rate_limit hay lỗi khác |
| `No module named 'groq'` dù có trong requirements.txt | Chạy lại `pip install -r requirements.txt` trong đúng `.venv` đang active — từng gặp thật khi venv cũ chưa cài lại sau khi thêm dependency |
| PDF không đọc được | PDF dạng scan ảnh → error message hướng dẫn rõ, không crash |
| `No module named fastapi` | Activate `.venv` trước: `.\.venv\Scripts\Activate.ps1` |
| Discord bot không phản hồi | Kiểm tra backend đang chạy tại `KB_API_BASE`, và `DISCORD_BOT_TOKEN` đúng quyền `message_content` intent |

---

*VinAI Knowledge Assistant v2.1 · Nhóm B7-E402 · K4 Hackathon*
