# Team Report — Nhóm B7-E402 · VinAI K4 Hackathon

> **Hướng:** B — Trợ lý Học viên (Discord) · **Ngày:** 30/07/2026

---

## 1. Thành viên & Phân công

| Tên | Role | Nhiệm vụ cụ thể |
|---|---|---|
| Vũ | Role 1 | Kiểm chứng nguồn tài liệu, dẫn nguồn paper/GitHub/documentation, đánh giá độ tin cậy, xác định kiến thức cần bổ sung |
| Bình | Role 1 | Hỗ trợ Role 1 — phân tích bài chia sẻ, đối chiếu tài liệu chính thức |
| Linh | Role 2 | Tổng hợp thông tin trường + khoá VinAI Thực Chiến, quy định và chính sách |
| Liễu | Role 2 | Hỗ trợ Role 2 — thu thập và cập nhật thông tin khoá học |
| Hải Đăng | Role 3 ✅ Demo chính | Tổng hợp kiến thức đoạn chat + Summary tài liệu + Xác định vị trí tài liệu |

---

## 2. Hướng Đã Chốt

**Hướng B — Trợ lý Học viên (Discord)**

Nhóm chọn **Role 3** làm tính năng demo chính, phụ trách bởi **Hải Đăng**.

### Lý do chọn Role 3 cho demo

- Kênh `#tài-nguyên` trong Discord có nhiều link slide/PDF/video record do mentor share — phù hợp trực tiếp với tính năng document ingestion & summarization
- Tính năng có thể demo end-to-end với AI call thật trong thời gian ngắn (còn ~20 phút)
- Bao phủ pain point cốt lõi: học viên cần tóm tắt + định vị tài liệu nhanh thay vì xem toàn bộ
- Có bằng chứng cụ thể từ data pack: 46.2% tutor responses không có citations

### Ba Role trong kiến trúc tổng thể

```
Trợ lý Học viên (Discord) — Hướng B
├── Role 1: Knowledge Quality Assurance (Vũ · Bình)
│   Kiểm chứng nguồn, dẫn paper/GitHub/docs, Reliability Score
│
├── Role 2: Campus & Course Assistant (Linh · Liễu)
│   Thông tin trường, khoá VinAI, quy định, chính sách
│
└── Role 3: Knowledge Synthesis & Document Intelligence (Hải Đăng) ← Demo
    Tổng hợp chat, Summary tài liệu, Định vị trong syllabus
```

---

## 3. Cấu Trúc Project — Mô Tả Chi Tiết

### 3.1 File gốc (root level)

| File | Kích thước | Mô tả |
|---|---|---|
| `README.md` | 6.5 KB | File gốc của ban tổ chức — hướng dẫn hackathon Batch 03/04, lịch 6 mốc, rubric, luật bảo mật |
| `01-de-bai.md` | 4.7 KB | Đề bài 3 hướng (A-VLearn / B-Discord / C-Làn mở) · 5 tiêu chí nghiệm thu · ràng buộc chung |
| `02-guide.md` | 21 KB | Hướng dẫn đầy đủ 5 giai đoạn: §1 Khám phá → §2 Thiết kế & Spec → §3 Build → §4 Đo & Validate → §5 Demo & Nộp |
| `03-template-ai-spec.md` | 3 KB | Template spec.md cần điền §1–§9 |
| `04-rubric.md` | 7.3 KB | Rubric 100 điểm (25 nộp CP + 75 chấm bài) · Checklist 6 mốc CP1–CP6 |
| **`team-report.md`** | — | **File này** — báo cáo tổng quan nhóm B7-E402 |
| **`feature-knowledge-synthesis.md`** | — | Thiết kế chi tiết tính năng Role 3 (Hải Đăng) |
| `spec.md` | *[cần tạo]* | AI Spec đầy đủ theo template 03, nộp trước 23:59 Ngày 1 |
| `demo-slides.pdf` | *[cần tạo]* | Slide 6 trang demo |

### 3.2 data/vlearn-pack/

| File/Thư mục | Kích thước | Mô tả |
|---|---|---|
| `README.md` | 1.9 KB | Mô tả data pack, luật dùng & bảo mật |
| `chatlog/DATA_DICTIONARY.md` | 4.8 KB | Mô tả 22 field của CSV: role, content, move_used, citations, rating, asked_check_question, models_used, latency, v.v. |
| `chatlog/chat_history_anonymized_for_hackathon.csv` | 1.9 MB | **2.522 dòng** (1.261 cặp student+tutor) · 22/07–29/07/2026 · 369 users · 585 hội thoại · đã ẩn danh toàn bộ (U/C/T/M) |
| `slides/d1-slide-hackathon.pdf` | 9.8 MB | Slide Day 1: AI & LLM Foundation — bản hackathon có watermark |
| `slides/d2-slide-hackathon.pdf` | 2.4 MB | Slide Day 2: Xác định bài toán cho AI — bản hackathon có watermark |
| `transcript/README.md` | 2 KB | Bảng ánh xạ 6 transcript · ~700 đoạn mã [Txx-NNN] · ~465k ký tự sạch |
| `transcript/transcript-01-clean.md` | 86 KB | Day 2 sáng — Xác định bài toán kinh doanh cho AI (89 đoạn · Cao) |
| `transcript/transcript-02-clean.md` | 37 KB | Day 2 — Chỉ số thành công & mức tự động hoá (43 đoạn · Vừa) |
| `transcript/transcript-03-clean.md` | 156 KB | Day 2 chiều — Soi bài toán, tự động hoá & ràng buộc (154 đoạn · Vừa) |
| `transcript/transcript-04-clean.md` | 119 KB | Day 1 Foundation: cách LLM hoạt động (98 đoạn · Cao) |
| `transcript/transcript-05-clean.md` | 105 KB | Buổi bài toán · đánh giá · dữ liệu (154 đoạn) |
| `transcript/transcript-06-clean.md` | 107 KB | Foundation: transformer & attention mechanism (162 đoạn) |

### 3.3 tham-khao/

| File | Kích thước | Mô tả |
|---|---|---|
| `Strategyn_JTBD_Playbook.pdf` | 5.2 MB | JTBD Playbook đầy đủ (48 trang) — chỉ cần đọc Chapter 2 & Chapter 3 |
| `worksheet-jtbd-day-du.md` | 4.8 KB | Worksheet JTBD 6 bước chi tiết: Executor → Workflow → Core JTBD → Job Stories → Alternatives → AI Leverage |

### 3.4 Thư mục cần tạo (cấu trúc nộp bài)

```
K4-hackathon-B7-E402/
├── codebase/       <- Prototype code (ghi rõ phần nào mock, phần nào thật)
├── eval/           <- Golden set >=20 case + bảng kết quả các lượt chạy
├── validation/     <- Feedback log từ >=5 người user test (có tên, quote nguyên văn)
└── reflection/     <- Mỗi thành viên 1 file riêng
```

---

## 4. Insights Từ Data Pack

### Từ chatlog CSV (2.522 dòng)

| Phát hiện | Con số | Ý nghĩa |
|---|---|---|
| Tutor responses không có citations | 46.2% | AI trả lời không grounding vào tài liệu |
| Field `misconceptions` chưa dùng | 0/1.261 turns | Bỏ phí signal phát hiện hiểu lầm |
| Field `follow_ups` chưa dùng | 0/1.261 turns | Bỏ phí signal gợi ý câu hỏi tiếp theo |
| Tin nhắn có rating | ~2.8% | Feedback loop rất yếu |
| `asked_check_question = True` | 3/2.515 | Tutor gần như không chủ động check hiểu bài |
| Latency trung bình | ~1.758ms | P90: 3.686ms, Max: 23.848ms |

### Từ transcript (6 file, ~700 đoạn)

- Phủ đầy đủ nội dung: Foundation (LLM, Transformer) + Bài toán AI + Đánh giá & dữ liệu
- Có mã định vị `[Txx-NNN]` cho mỗi đoạn → dùng để trích dẫn trong golden set
- Tổng ~465k ký tự sạch (từ ~854k thô, giữ ~54%)

---

## 5. Lịch 6 Mốc (Khoá 4)

| Mốc | Thời gian | Nhóm cần show | Trạng thái |
|---|---|---|---|
| CP1 · Chốt Canvas | 15:00 Ngày 1 | Canvas 7 dòng: hướng · job executor · pain · bằng chứng · lát cắt · automation · willing users · phân công | ☐ |
| CP2 · Bấm được | 17:00 Ngày 1 | Flow chính bấm hết được + commit đầu tiên | ☐ |
| CP3 · AI thật + đo lượt đầu | 10:30 Ngày 2 | AI call thật + golden set >=20 + bảng kết quả % | ☐ |
| CP4 · Chốt tiến độ | 12:00 Ngày 2 | Spec gần cuối · **spec.md commit cứng 23:59 N1** | ☐ |
| CP5 · Xác minh + validation | 14:00 Ngày 2 | Feedback log >=5 người + changelog + slide final + dry run | ☐ |
| CP6 · Demo | 15:00 Ngày 2 | 5' trình bày + 5' Q&A · thẻ giám khảo chạy case lạ | ☐ |

---

## 6. Checklist Nộp Bài

- [ ] `README.md` — giữ nguyên file gốc ban tổ chức
- [ ] `team-report.md` — file này, báo cáo tổng quan nhóm
- [ ] `feature-knowledge-synthesis.md` — thiết kế tính năng Role 3
- [ ] `spec.md` — AI Spec đầy đủ §1–§9 (deadline 23:59 Ngày 1)
- [ ] `demo-slides.pdf` — slide 6 trang theo guide §5.1
- [ ] `codebase/` — prototype (ghi rõ mock vs thật)
- [ ] `eval/` — golden set >=20 case + kết quả các lượt chạy
- [ ] `validation/` — feedback log >=5 người có tên + quote nguyên văn
- [ ] `reflection/` — mỗi thành viên 1 file

---

*Nhóm B7-E402 · VinAI Thực Chiến K4 · Mini Hackathon AI · 30/07/2026*

