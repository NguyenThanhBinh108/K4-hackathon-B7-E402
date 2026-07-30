# VinAI K4 Hackathon — Nhóm B7-E402
# Discord Knowledge Assistant · Hướng B — Trợ lý Học viên

## 👥 Thành Viên & Phân Công

| Tên | Mã HV | Role | Nhiệm vụ cụ thể |
|---|---|---|---|
| **Hải Đăng** | — | **Role 3 · Demo chính** | Toàn bộ codebase (backend + frontend) · spec.md §1-§9 · golden set (21 cases) · eval · validation · implementation plan |
| Vũ | — | Role 1 | Kiểm chứng nguồn tài liệu, dẫn nguồn paper/GitHub/documentation, đánh giá độ tin cậy |
| Bình | — | Role 1 | Hỗ trợ Role 1 — phân tích bài chia sẻ, đối chiếu tài liệu chính thức |
| Linh | — | Role 2 | Tổng hợp thông tin trường + khoá VinAI Thực Chiến, quy định và chính sách |
| Liễu | — | Role 2 | Hỗ trợ Role 2 — thu thập và cập nhật thông tin khoá học |

**Demo chính: Role 3 (Hải Đăng)** — Knowledge Synthesis & Document Intelligence

---

## 🗂️ Cấu Trúc Repo

```
K4-hackathon-B7-E402/
├── README.md                    ← File này (thành viên + phân công)
├── spec.md                      ← AI Spec §1-§9 (deadline 23:59 N1)
├── team-report.md               ← Báo cáo tổng quan nhóm
├── feature-knowledge-synthesis.md ← Feature spec Role 3 chi tiết
├── implementation_plan.md       ← Implementation plan v3
├── project-overview.md          ← Project overview
│
├── codebase/                    ← Prototype code
│   ├── HUONG_DAN_CHAY.md       ← Hướng dẫn chạy
│   ├── run.bat / start.ps1      ← Scripts chạy nhanh
│   ├── backend/
│   │   ├── main.py              ← FastAPI backend (5 routes)
│   │   ├── requirements.txt     ← Dependencies
│   │   ├── .env                 ← API keys (không commit)
│   │   ├── knowledge_base.json  ← Mock KB (8 docs từ data pack) [MOCK]
│   │   └── services/
│   │       ├── gemini_service.py ← AI calls thật (Gemini Flash) [REAL]
│   │       ├── knowledge_base.py ← Keyword search + routing [REAL]
│   │       └── pdf_service.py   ← PyMuPDF PDF extraction [REAL]
│   └── frontend/
│       ├── index.html           ← Discord dark UI
│       ├── script.js            ← Chat + upload logic
│       └── style.css            ← Styling
│
├── eval/                        ← Đánh giá & kiểm thử
│   ├── golden_set.md            ← 21 cases (≥2/layer, ≥10 từ chatlog thật)
│   ├── quality_bar.md           ← Quality bar commit (23:59 N1)
│   ├── run_results_01.md        ← Kết quả lượt chạy 1 (19/21 pass → fix → 21/21)
│   └── ai_call_log.jsonl        ← Log mọi AI call thật (auto-generated khi chạy)
│
├── validation/                  ← Validation với user thật
│   ├── feedback_log.md          ← Feedback ≥5 người (tên + task + quote nguyên văn)
│   ├── survey_log.md            ← Log khảo sát 22 người (Đường A evidence)
│   └── changelog.md             ← Thay đổi từ feedback + giữ nguyên có lý do
│
└── reflection/                  ← Reflection cá nhân
    └── hai-dang.md              ← Reflection của Hải Đăng
```

---

## 🚀 Chạy Prototype

```bash
# Cài dependencies
cd codebase/backend
pip install -r requirements.txt

# Set API key
echo GEMINI_API_KEY=your_key_here > .env

# Chạy server
python main.py
# → Mở http://localhost:8000
```

Xem chi tiết: [HUONG_DAN_CHAY.md](codebase/HUONG_DAN_CHAY.md)

---

## 🎯 Lát Cắt Một Câu

> **Khi học viên gửi link PDF/slide hoặc câu hỏi kiến thức AI/ML, hệ thống tự động phân loại intent — tóm tắt tài liệu có trích dẫn [TXX-NNN] hoặc trả lời từ Knowledge Base — từ chối đúng cách khi ngoài phạm vi — giúp học viên quyết định trong <1 phút thay vì 10-30 phút tìm thủ công.**

## 📊 Điểm Mạnh Chính

| Feature | Real vs Mock | Evidence |
|---|---|---|
| PDF summarization (Gemini Flash) | **REAL** | ai_call_log.jsonl |
| Q&A với KB context (Gemini Flash) | **REAL** | ai_call_log.jsonl |
| PDF text extraction (PyMuPDF) | **REAL** | — |
| Router (logistics/ambiguous/RAG) | **REAL** | run_results_01.md |
| Knowledge base search | MOCK (keyword) | — |
| Vector search | MOCK | roadmap |
| Discord integration | MOCK (Web UI) | roadmap |

## ✅ Tự Kiểm Checklist Nộp Bài

- [x] `spec.md` đầy đủ §1-§9, commit trước 23:59 N1
- [x] `eval/golden_set.md` 21 cases (≥2/layer, ≥10 từ chatlog thật)
- [x] `eval/run_results_01.md` bảng % đủ mọi case kể cả fail (honest)
- [x] `eval/quality_bar.md` quality bar commit: ≥75% + 100% citation + 100% scope
- [x] `validation/feedback_log.md` 5 người có tên + task + quote nguyên văn
- [x] `validation/survey_log.md` 22 người khảo sát (Đường A, 77% xác nhận)
- [x] `validation/changelog.md` thay đổi + giữ nguyên có lý do
- [x] `reflection/hai-dang.md` vai trò + AI hỗ trợ + failure case + bài học
- [x] `codebase/` chạy được end-to-end, ≥1 AI call thật
- [x] README phân công có tên từng phần

---

*B7-E402 · VinAI Thực Chiến K4 · Mini Hackathon AI · 30-31/07/2026*
