# 🚀 Hướng Dẫn Chạy — VinAI Knowledge Assistant

> **Role 3 · Hải Đăng · Nhóm B7-E402** | Yêu cầu: Python 3.9+

---

## Yêu Cầu

```
Python >= 3.9   →  python --version
```
> Chưa có Python? [python.org/downloads](https://www.python.org/downloads/) — tick **"Add Python to PATH"**

---

## ⚡ Lần Sau Chỉ Cần (Đã Cài Xong Rồi)

> Sau khi đã chạy lần đầu thành công (`.venv` và packages đã có sẵn), **không cần cài lại** — chỉ cần:

### Cách nhanh nhất — Double-click `run.bat`

Chạy `run.bat` là xong — script tự bỏ qua cài packages nếu đã có, thẳng tới bước khởi động server.

### Hoặc thủ công trong PowerShell

```powershell
cd d:\VINAI_Team_093\LAB\K4-hackathon-B7-E402\codebase\backend

# Kích hoạt môi trường ảo (đã tồn tại)
.\.venv\Scripts\Activate.ps1

# Chạy server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Khi nào cần cài lại? Chỉ khi:
- Thêm package mới vào `requirements.txt`
- Xóa thư mục `.venv` đi
- Chuyển sang máy khác / clone repo về máy mới

---

## Cách 1 — PowerShell (Khuyên dùng — Lần đầu)

```powershell
cd d:\VINAI_Team_093\LAB\K4-hackathon-B7-E402\codebase
.\start.ps1
```

Nếu bị lỗi _"scripts is disabled"_, chạy lệnh này **một lần** rồi thử lại:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Cách 2 — Double-click `run.bat`

1. Vào thư mục `codebase/`
2. Double-click `run.bat` → tự động mở cửa sổ CMD

> Nếu cửa sổ chớp rồi tắt ngay → chuột phải → **"Run as administrator"**

---

## Cách 3 — Thủ công (nếu 2 cách trên lỗi)

```powershell
# Vào thư mục backend
cd d:\VINAI_Team_093\LAB\K4-hackathon-B7-E402\codebase\backend

# Tạo môi trường ảo .venv
python -m venv .venv

# Kích hoạt
.\.venv\Scripts\Activate.ps1

# Cài packages
pip install -r requirements.txt

# Chạy server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Mở App

Sau khi thấy `Uvicorn running on http://0.0.0.0:8000`:

→ Mở trình duyệt vào **`http://localhost:8000`**

---

## Kiểm Tra Nhanh

| URL | Kết quả mong đợi |
|---|---|
| `http://localhost:8000/api/health` | `{"status":"ok","gemini_configured":true}` |
| `http://localhost:8000/docs` | Swagger UI |

---

## Cấu Trúc File

```
codebase/
├── run.bat          ← Double-click (Windows CMD)
├── start.ps1        ← Chạy trong PowerShell
│
└── backend/
    ├── main.py              ← FastAPI app
    ├── requirements.txt     ← Dependencies
    ├── .env                 ← API key (KHÔNG commit Git)
    ├── knowledge_base.json  ← 5 tài liệu mock
    ├── .venv/               ← Tự sinh ra (gitignore)
    └── services/
        ├── gemini_service.py
        ├── pdf_service.py
        └── knowledge_base.py

frontend/
├── index.html
├── style.css
└── script.js
```

---

## Troubleshooting

| Lỗi | Cách fix |
|---|---|
| `scripts is disabled` | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `Port 8000 in use` | `netstat -ano \| findstr :8000` rồi `taskkill /PID <số> /F` |
| `No module named fastapi` | `.venv` chưa activate — kiểm tra prompt có `(.venv)` chưa |
| `INVALID_API_KEY` | Lấy key mới tại [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| PDF không đọc được | PDF dạng ảnh scan → dùng PDF có text thật |

---

## Demo 5 Phút (CP6)

```
[0:00] Mở http://localhost:8000 — giao diện Aurora dark

[0:30] HAPPY PATH — Upload PDF:
       Kéo d1-slide-hackathon.pdf vào dropzone
       → AI phân tích ~5-10s → hiện Analysis Card
       → Hỏi follow-up: "Có nói về attention mechanism không?"
       → AI trả lời kèm citation [T06-xxx]

[2:00] FAILURE HANDLING:
       "Deadline nộp bài là bao giờ?" → AI từ chối (Layer 3)
       "tài liệu" (quá chung) → AI hỏi lại (Layer 2)

[3:30] Tab Tổng hợp → paste chat → show kết quả phân tích

[4:00] Show Golden Set: X/20 pass · ≥75% accuracy · 100% citations
```

---

*VinAI Knowledge Assistant · Nhóm B7-E402 · K4 Hackathon*
