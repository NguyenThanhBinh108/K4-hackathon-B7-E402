# Feature Spec — Knowledge Synthesis & Document Intelligence

> **Module:** Role 3 · **Owner:** Hải Đăng · **Nhóm:** B7-E402 · **Hướng:** B — Discord Knowledge Assistant

---

## 1. Problem Statement & Evidence

### Pain Point (Ai — Làm gì — Vướng đâu — Hậu quả)

Trong khoá VinAI Thực Chiến, kênh `#tài-nguyên` trên Discord là nơi mentor và Lab Coach chia sẻ tài liệu học tập:
- **Slide bài giảng** (PDF, Google Slides)
- **Video record** buổi học, Office Hour (YouTube, Google Drive)
- **Bài viết, paper, blog** kỹ thuật
- **GitHub repo**, notebook, code mẫu

| Ai | Đang làm gì | Vướng đâu | Hậu quả |
|---|---|---|---|
| Học viên VinAI | Tìm lại tài liệu cụ thể trong #tài-nguyên | Phải cuộn lịch sử chat dài, link bị chôn vùi, không biết tài liệu đó dạy gì | Tốn 10–15 phút chỉ để tìm đúng slide |
| Học viên VinAI | Xem nhanh một tài liệu dài (slide 30 trang, video 90 phút) | Không có tóm tắt, phải xem toàn bộ để biết có liên quan không | Mất 30–60 phút chỉ để kết luận "không phải cái cần tìm" |
| Lab Coach / TA | Biết học viên đang gặp khó khăn với kiến thức nào | Không có tổng hợp tự động từ chat history | Phải đọc hàng trăm tin nhắn để nhận ra pattern câu hỏi |

### Evidence (từ data pack)

Từ `chatlog/chat_history_anonymized_for_hackathon.csv` (2.522 dòng, 585 hội thoại):
- **46.2% tutor responses** không có citations — trả lời không grounding vào tài liệu
- Fields `misconceptions` và `follow_ups` chưa từng được dùng (0/1.261 turns) — bỏ phí signal học tập quan trọng
- Chỉ ~2.8% tin nhắn có rating (up/down) — feedback loop rất yếu
- `asked_check_question` chỉ True 3/2515 lần — tutor gần như không chủ động kiểm tra hiểu bài

---

## 2. Feature Scope

### Lát cắt MỘT CÂU

> **Khi học viên gửi link tài liệu (slide/PDF) vào Discord, AI tự động trích xuất nội dung, tạo tóm tắt có cấu trúc kèm vị trí định vị trong syllabus, giúp học viên quyết định trong 30 giây có nên đọc đầy đủ không.**

### Non-goals (KHÔNG build trong hackathon này)

1. Không xử lý video (chỉ text/PDF trong prototype)
2. Không tích hợp thật vào Discord bot (dùng giao diện web demo)
3. Không build hệ thống search toàn bộ knowledge base
4. Không hỗ trợ real-time streaming từ live Discord
5. Không quản lý permission hay role Discord

---

## 3. Feature Components

### 3.1 Chat Knowledge Synthesis

**Input:** Đoạn chat Discord (text)
**Output:**
- Danh sách **chủ đề kiến thức** được đề cập
- **Câu hỏi phổ biến** và câu trả lời tương ứng
- **Điểm học viên đang bị stuck** (từ pattern câu hỏi lặp)
- Gợi ý tài liệu liên quan từ Knowledge Base

```
Vi du output:
---
Tong hop chat #ai-questions (30/07/2026)
Chu de: Prompt Engineering (8 cau hoi), RAG vs Fine-tuning (5 cau hoi)
Cau hoi pho bien nhat: "Khi nao dung RAG, khi nao fine-tune?" — 4 hoc vien hoi
Hoc vien dang stuck: Khai niem embedding distance trong vector search
Tai lieu lien quan: [T04-045] Buoi Foundation — cach LLM hoat dong
---
```

### 3.2 Document Summarization

**Input:** Link PDF / slide (URL hoặc file upload)
**Output có cấu trúc:**
- **Tiêu đề & chủ đề chính** (1 câu)
- **Key takeaways** (3–5 bullet points, mỗi cái 1–2 câu)
- **Khái niệm quan trọng** được giới thiệu
- **Prerequisites** — cần biết gì trước khi đọc tài liệu này
- **Liên kết với syllabus** — tài liệu này thuộc buổi/module nào

### 3.3 Knowledge Extraction

Từ tài liệu đã được đọc, AI tạo ra:
- **Knowledge map** dạng outline có phân cấp
- **Trích dẫn có định vị** (trang N / slide N / timestamp)
- **Câu hỏi ôn tập** tự động từ nội dung
- **Liên kết chéo** với các tài liệu khác trong hệ thống

### 3.4 Syllabus Position Mapping

AI phân loại tài liệu vào:
- **Buổi học** (Day 1 Foundation / Day 2 Bài toán / ...)
- **Chủ đề** (LLM / Prompt Engineering / RAG / Evaluation / ...)
- **Cấp độ** (Foundation / Intermediate / Advanced)
- **Loại tài liệu** (Slide / Transcript / Paper / Code / Blog)

---

## 4. System Architecture

```
Discord #tai-nguyen
(Link PDF, Slide, Video, GitHub...)
         | User gui link / cau hoi
         v
Document Ingestion
+-- PDF Parser (PyMuPDF)
+-- Slide Parser (python-pptx)
+-- Web Scraper (URL to text)
         | Raw text chunks
         v
AI Processing Layer (Gemini Flash)
(1) Chunking + Embedding
(2) Summary Generation
(3) Keyword + Topic Extraction
(4) Syllabus Position Classification
(5) Cross-reference voi Knowledge Base
         | Structured output
         v
Knowledge Base
(Vector store: Chroma / JSON file cho prototype)
         |
    +----+----+
    v         v
Discord Bot  Web Demo Interface
Response     (Discord-like dark UI)
```

---

## 5. Interaction Flows

### Happy Path — Tìm tài liệu theo câu hỏi

```
1. Hoc vien: "Slide buoi transformer o dau vay?"
2. AI detect: truy van tai lieu → lookup flow
3. Search knowledge base: "transformer slide"
4. Tim thay: transcript-06-clean.md
5. AI tra loi:
   "[T06] Foundation: Transformer & Attention Mechanism
   Vi tri: Buoi Foundation
   Noi dung: Self-attention, Multi-head attention, Positional encoding
   Xem transcript: [T06-001] den [T06-162]"
```

### Happy Path — Share link tài liệu mới

```
1. Mentor share link Google Slides
2. AI detect: URL tai lieu moi → ingestion flow
3. Download + extract text
4. AI summarize + classify
5. Tra loi:
   "Da phan tich tai lieu: Prompt Engineering Best Practices
   Chu de: Prompt Engineering, Chain-of-Thought
   Thuoc: Module 2 — Ung dung LLM | Cap do: Intermediate
   Takeaways:
   - Zero-shot vs Few-shot
   - Chain-of-Thought tang reasoning 30-40%
   Da them vao Knowledge Base."
```

### Out-of-Scope Handling

```
1. Hoc vien: "Deadline nop bai la bao gio?"
2. AI detect: logistics query → out of scope
3. AI tra loi:
   "Cau hoi ve deadline nam ngoai pham vi cua minh.
   Vui long hoi Lab Coach hoac kiem tra #announcements.
   Neu muon tim tai lieu hoc thuat, minh san sang ho tro!"
```

---

## 6. Risk Scenarios — 4 Failure Layers

### Layer 1: Ground Truth — AI Hallucination Risk

| Scenario | Expected Behavior |
|---|---|
| Hỏi thông tin không có trong Knowledge Base | Trả lời "không tìm thấy", KHÔNG bịa |
| Tài liệu chưa được ingestion | Thông báo "chưa có tài liệu này" |
| Trích dẫn sai trang/slide | Luôn kèm mã đoạn [Txx-NNN] hoặc page number |

### Layer 2: Ambiguity — Insufficient Input

| Scenario | Expected Behavior |
|---|---|
| Hỏi "tài liệu về AI" (quá chung) | Hỏi lại: "Bạn muốn tìm về khía cạnh nào?" |
| Link bị lỗi / không truy cập được | Báo lỗi, đề nghị upload file trực tiếp |
| Câu hỏi vừa logistics vừa kiến thức | Tách rõ: trả lời kiến thức, chuyển logistics cho TA |

### Layer 3: Out-of-Scope — Authorization Boundary

| Scenario | Expected Behavior |
|---|---|
| Hỏi deadline, điểm số | "Ngoài phạm vi — hỏi Lab Coach" |
| Yêu cầu giải bài tập thay học viên | Từ chối, gợi ý tài liệu liên quan |
| Hỏi thông tin cá nhân học viên khác | Từ chối tuyệt đối |

### Layer 4: Domain-Specific — Wrong Info = Wrong Learning

| Scenario | Expected Behavior |
|---|---|
| Tóm tắt sai khái niệm kỹ thuật (attention, embedding...) | Luôn kèm nguồn trích dẫn để học viên tự verify |
| Phân loại tài liệu sai module | Hiển thị confidence, cho phép user correct |
| Syllabus mapping sai buổi học | Ghi rõ "phân loại tự động — chưa verified" |

---

## 7. Design Principles (HAX/PAIR)

| Principle | Implementation |
|---|---|
| **G1 — Set Expectations** | Onboarding message: CÓ THỂ (tóm tắt, tìm kiếm, tổng hợp) / KHÔNG (deadline, điểm số, giải bài) |
| **G2 — Show Confidence Level** | Mọi summary kèm nguồn trích dẫn + "Tóm tắt tự động — xem nguyên văn để xác nhận" |
| **G10 — Narrow Scope When Uncertain** | Không chắc → hỏi lại 1 câu rõ ràng, không đoán mò |
| **G11 — Explain Reasoning** | "Chọn tài liệu này vì có đề cập đến [keyword] tại [vị trí cụ thể]" |
| **G8 — Easy Dismissal** | Nút feedback "Không phải cái cần tìm" trên mỗi response |
| **PAIR Explainability** | Mọi recommendation kèm lý do từ tài liệu gốc, không phải "AI cho rằng..." |

---

## 8. Prototype Specification

### Build Level: Sketch → Mock

| Component | Real or Mock | Detail |
|---|---|---|
| AI call (summarization) | **Real** | Gemini Flash API với extracted PDF text |
| Document parsing (PDF) | **Real** | PyMuPDF — extract plain text |
| Knowledge Base | **Mock** | JSON file với 5–10 tài liệu mẫu từ data pack |
| Discord integration | **Mock** | Web UI giả lập Discord dark interface |
| Vector search | **Mock** | Keyword matching đơn giản |

### Tech Stack

```
Backend:
- Python + FastAPI (hoac script CLI)
- PyMuPDF — doc PDF, extract text
- Google Gemini Flash API (free tier)
- JSON file — mock Knowledge Base

Frontend:
- HTML + CSS + Vanilla JS
- Discord-like dark theme
- File upload drag-and-drop
```

---

## 9. Automation Level

**Selected: Conditional Automation**

> AI tự động summarize khi input rõ ràng và chất lượng cao. Khi không chắc (file lạ, text scan kém), báo người dùng và yêu cầu clarification.

**Rationale (cost-of-error):**
- Summary sai kỹ thuật → học viên học sai kiến thức → **cost CAO**
- Luôn kèm nguồn gốc trích dẫn để học viên tự verify
- Syllabus classification chỉ là gợi ý — cần Lab Coach confirm để chính thức

---

## 10. Demo Script (5 phút)

### Case 1 — Happy Path (2 phút)
1. Upload `d1-slide-hackathon.pdf` (có sẵn trong data pack)
2. AI trả về summary + key concepts + vị trí trong syllabus
3. Follow-up: "Slide này có nói về attention mechanism không?"
4. AI trả lời với trích dẫn cụ thể (trang/slide number)

### Case 2 — Failure Handling (1.5 phút)
1. Hỏi: "Deadline nộp bài tuần này là bao giờ?"
2. Demo: AI từ chối đúng cách + chuyển hướng sang TA
3. Gửi link không truy cập được
4. Demo: AI báo lỗi rõ ràng + hướng dẫn upload trực tiếp

### Case 3 — Evaluation Results (1.5 phút)
- Bảng golden set: X/20 case pass
- Quality bar đã chốt: >=75% pass + 100% citations correctness
- Failure case đáng kể nhất + root cause analysis

---

## 11. Quality Bar & Success Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| Summary accuracy | >=75% golden set pass | Manual scoring by 2 reviewers |
| Source citation correctness | 100% citations when summarizing | Trace back to source document |
| Scope refusal rate | 100% logistics queries rejected correctly | Test set of 5 logistics questions |
| User satisfaction | >=3/5 testers say "helpful" | CP5 validation round |

### Golden Set Composition (>=20 cases)

| Category | Count | Source |
|---|---|---|
| Happy path — document found | 4 | From data pack transcripts |
| Happy path — new doc ingestion | 3 | Simulated from slides |
| Layer 1 failure — hallucination risk | 3 | Edge cases |
| Layer 2 failure — ambiguous query | 3 | Real chat patterns |
| Layer 3 failure — out of scope | 3 | Logistics questions |
| Layer 4 failure — domain specifics | 4 | Technical misconceptions |

---

## 12. Post-Hackathon Roadmap

1. **Week 1:** Integrate real Discord bot (webhook + slash commands)
2. **Week 2:** Real vector search (Chroma/Qdrant) replacing keyword matching
3. **Week 3:** Video processing (Office Hour recordings → transcript → summary with timestamps)
4. **Week 4:** Automated daily digest for TA — pending questions, trending topics

---

*Feature Spec — Knowledge Synthesis & Document Intelligence · Hải Đăng · Nhóm B7-E402 · VinAI K4 Hackathon*

