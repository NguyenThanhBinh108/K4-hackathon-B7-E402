# Feature Spec — Knowledge Synthesis & Document Intelligence

> **Module:** Role 3 · **Owner:** Hải Đăng · **Nhóm:** B7-E402 · **Hướng:** B — Discord Knowledge Assistant

---

## 1. Bối cảnh & Pain Point

### Vấn đề cụ thể

Trong khoá VinAI Thực Chiến, kênh `#tài-nguyên` trên Discord là nơi mentor và Lab Coach chia sẻ tài liệu học tập:
- **Slide bài giảng** (PDF, Google Slides)
- **Video record** buổi học, Office Hour (YouTube, Google Drive)
- **Bài viết, paper, blog** kỹ thuật
- **GitHub repo**, notebook, code mẫu

**Pain point thực tế:**

| Ai | Đang làm gì | Vướng đâu | Hậu quả |
|---|---|---|---|
| Học viên VinAI | Tìm lại tài liệu cụ thể trong #tài-nguyên | Phải cuộn lịch sử chat dài, link bị chôn vùi, không biết tài liệu đó dạy gì | Tốn 10–15 phút chỉ để tìm đúng slide |
| Học viên VinAI | Xem nhanh một tài liệu dài (slide 30 trang, video 90 phút) | Không có tóm tắt, phải xem toàn bộ để biết có liên quan không | Mất 30–60 phút chỉ để kết luận "không phải cái cần tìm" |
| Lab Coach / TA | Biết học viên đang gặp khó khăn với kiến thức nào | Không có tổng hợp tự động từ chat history | Phải đọc hàng trăm tin nhắn để nhận ra pattern câu hỏi |

### Bằng chứng (từ data pack)

Từ `chatlog/chat_history_anonymized_for_hackathon.csv` (2.522 dòng, 585 hội thoại):
- **46.2% tutor responses** không có citations — trả lời không grounding vào tài liệu
- Fields `misconceptions` và `follow_ups` chưa từng được dùng (0/1.261 turns) — bỏ phí signal học tập quan trọng
- Chỉ ~2.8% tin nhắn có rating (up/down) — feedback loop rất yếu
- `asked_check_question` chỉ True 3/2515 lần — tutor gần như không chủ động kiểm tra hiểu bài

---

## 2. Lát Cắt (Prototype Scope)

### Lát cắt MỘT CÂU

> **Khi học viên gửi link tài liệu (slide/PDF) vào Discord, AI tự động trích xuất nội dung, tạo tóm tắt có cấu trúc kèm vị trí định vị trong syllabus, giúp học viên quyết định trong 30 giây có nên đọc đầy đủ không.**

### Non-goals (KHÔNG build trong hackathon này)

1. Không xử lý video (chỉ text/PDF trong prototype)
2. Không tích hợp thật vào Discord bot (dùng giao diện web demo)
3. Không build hệ thống search toàn bộ knowledge base
4. Không hỗ trợ real-time streaming từ live Discord
5. Không quản lý permission hay role Discord

---

## 3. Tính Năng Chi Tiết (Role 3)

### 3.1 Tổng hợp kiến thức chung của đoạn chat

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

### 3.2 Summary tài liệu (Document Summarization)

**Input:** Link PDF / slide (URL hoặc file upload)
**Output có cấu trúc:**
- **Tiêu đề & chủ đề chính** (1 câu)
- **Key takeaways** (3–5 bullet points, mỗi cái 1–2 câu)
- **Khái niệm quan trọng** được giới thiệu
- **Prerequisites** — cần biết gì trước khi đọc tài liệu này
- **Liên kết với syllabus** — tài liệu này thuộc buổi/module nào

### 3.3 Tổng hợp kiến thức tài liệu

Từ tài liệu đã được đọc, AI tạo ra:
- **Knowledge map** dạng outline có phân cấp
- **Trích dẫn có định vị** (trang N / slide N / timestamp)
- **Câu hỏi ôn tập** tự động từ nội dung
- **Liên kết chéo** với các tài liệu khác trong hệ thống

### 3.4 Xác định vị trí tài liệu

AI phân loại tài liệu vào:
- **Buổi học** (Day 1 Foundation / Day 2 Bài toán / ...)
- **Chủ đề** (LLM / Prompt Engineering / RAG / Evaluation / ...)
- **Cấp độ** (Foundation / Intermediate / Advanced)
- **Loại tài liệu** (Slide / Transcript / Paper / Code / Blog)

---

## 4. Kiến Trúc Hệ Thống

```
Discord #tai-nguyen
(Link PDF, Slide, Video, GitHub...)
         | User gui link
         v
Document Ingestion
+-- PDF Parser (PyMuPDF)
+-- Slide Parser (python-pptx)
+-- Web Scraper (URL→text)
         | Raw text chunks
         v
AI Processing Layer
(1) Chunking + Embedding (text-embedding-004)
(2) Summary Generation (Gemini Flash)
(3) Keyword + Topic Extraction
(4) Position Classification (syllabus mapping)
(5) Cross-reference voi existing Knowledge Base
         | Structured output
         v
Knowledge Base
(Vector store: Chroma / file-based cho prototype)
+ Structured metadata JSON
         |
    +----+----+
    v         v
Discord Bot  Web Demo Interface
Response     (Chat UI + Document viewer)
```

---

## 5. Flow Hoạt Động Chi Tiết

### Happy Path — Tìm tài liệu

```
1. Hoc vien hoi: "Anh oi cho em hoi slide buoi transformer la slide nao a?"
2. AI detect: cau hoi ve tai lieu → trigger lookup flow
3. AI search knowledge base voi query "transformer slide"
4. Tim thay: transcript-06-clean.md (Foundation: transformer & attention)
5. AI tra loi:
   "Tai lieu ve Transformer:
   - [T06] Foundation: Transformer & Attention Mechanism
   - Vi tri: Buoi Foundation
   - Noi dung chinh: Self-attention, Multi-head attention, Positional encoding
   - Key concepts: Query/Key/Value, Attention score, Softmax
   - Xem transcript: [T06-001] den [T06-162]"
```

### Happy Path — Gửi link tài liệu mới

```
1. Mentor share: "https://docs.google.com/presentation/d/..."
2. AI detect: link tai lieu moi → trigger ingestion flow
3. Download & extract text tu tai lieu
4. AI summarize & classify
5. Thong bao:
   "Da phan tich tai lieu moi:
   Tieu de: Prompt Engineering Best Practices
   Chu de: Prompt Engineering, Chain-of-Thought, Few-shot Learning
   Thuoc ve: Module 2 — Ung dung LLM
   Cap do: Intermediate
   Key takeaways:
   - Zero-shot vs Few-shot: khi nao dung cai nao
   - Chain-of-Thought giup reasoning tot hon 30-40% voi bai toan phuc tap
   Da them vao Knowledge Base."
```

### Khi ngoài phạm vi

```
1. Hoc vien hoi: "Deadline nop assignment week 3 la bao gio?"
2. AI detect: cau hoi logistics → NOT trong scope Role 3
3. AI tra loi:
   "Cau hoi ve deadline thuoc thong tin logistics khoa hoc.
   Minh khong co thong tin chinh thuc ve deadline trong Knowledge Base.
   Ban vui long hoi truc tiep Lab Coach hoac xem kenh #announcements nhe.
   Neu muon tim tai lieu hoc thuat, minh san sang ho tro!"
```

---

## 6. Bốn Lớp Chỗ Khó

### Lop 1: Nguồn sự thật — Chỗ AI có thể bịa

| Kịch bản | Lớp | Hành vi mong muốn |
|---|---|---|
| Hỏi thông tin không có trong Knowledge Base | 1 | Trả lời "không tìm thấy", KHÔNG bịa |
| Tài liệu chưa được ingestion | 1 | "Chưa có tài liệu này trong hệ thống" |
| Trích dẫn trang/slide sai vị trí | 1+4 | Luôn kèm mã đoạn [Txx-NNN] hoặc page number |

### Lop 2: Mơ hồ / thiếu thông tin

| Kịch bản | Lớp | Hành vi mong muốn |
|---|---|---|
| Hỏi "tài liệu về AI" (quá chung) | 2 | Hỏi lại: "Bạn muốn tìm về khía cạnh nào?" |
| Link bị lỗi / không truy cập được | 2 | Báo lỗi, đề nghị upload file trực tiếp |
| Câu vừa logistics vừa kiến thức | 2+3 | Tách rõ: trả lời kiến thức, chuyển logistics |

### Lop 3: Ngoài phạm vi / thẩm quyền

| Kịch bản | Lớp | Hành vi mong muốn |
|---|---|---|
| Hỏi deadline, điểm số | 3 | "Ngoài phạm vi — hỏi Lab Coach" |
| Yêu cầu giải bài tập thay học viên | 3 | Từ chối, gợi ý tài liệu liên quan |
| Hỏi thông tin cá nhân học viên khác | 3 | Từ chối tuyệt đối |

### Lop 4: Đặc thù domain — Sai thì học sai kiến thức

| Kịch bản | Lớp | Hành vi mong muốn |
|---|---|---|
| Tóm tắt sai khái niệm kỹ thuật | 4 | Luôn trích dẫn nguồn để người đọc tự verify |
| Phân loại tài liệu sai module | 4 | Hiển thị confidence, cho phép correct |
| Syllabus mapping sai buổi học | 4 | Ghi rõ "phân loại tự động — chưa được verify" |

---

## 7. Nguyên Tắc Thiết Kế (HAX/PAIR)

| Nguyên tắc | Áp dụng cụ thể trong prototype |
|---|---|
| **G1 — Làm rõ hệ thống làm được gì** | Onboarding message liệt kê rõ: CÓ THỂ (tóm tắt, tìm kiếm, tổng hợp) và KHÔNG (deadline, điểm số, giải bài) |
| **G2 — Làm rõ độ chính xác** | Mọi summary đều có nguồn trích dẫn + note "Tóm tắt tự động — xem nguyên văn để xác nhận" |
| **G10 — Thu hẹp phạm vi khi nghi ngờ** | Khi không chắc tài liệu nào liên quan → hỏi lại 1 câu, không đoán mò |
| **G11 — Giải thích vì sao** | "Mình chọn tài liệu này vì có đề cập đến [keyword] ở [vị trí cụ thể]" |
| **G8 — Gạt bỏ dễ dàng** | Mỗi summary có nút feedback để học viên nói "Không phải cái cần tìm" |
| **PAIR Explainability** | Mọi recommendation kèm lý do cụ thể từ tài liệu gốc, không phải "AI nghĩ rằng..." |

---

## 8. Mức Prototype & Technology Stack

### Mức prototype: Sketch → Mock

| Phần | Thật hay Mock? | Chi tiết |
|---|---|---|
| AI call (summarization) | **Thật** | Gemini Flash với PDF text |
| Document parsing (PDF) | **Thật** | PyMuPDF extract text |
| Knowledge Base | **Mock** | JSON file với 5–10 tài liệu mẫu từ data pack |
| Discord integration | **Mock** | Web UI giả lập Discord interface |
| Vector search | **Mock** | Keyword search đơn giản |

### Tech stack gợi ý

```
Backend:
- Python + FastAPI (hoac script CLI don gian)
- PyMuPDF (doc PDF)
- Google Gemini API (Gemini Flash — free tier)
- JSON file (mock Knowledge Base)

Frontend (Web Demo):
- HTML/CSS/JS (vanilla)
- Discord-like dark UI, message bubbles
- File upload support
```

---

## 9. Mức Độ Automation

**Chọn: Conditional Automation**

> AI tự động summarize khi input rõ ràng. Khi chất lượng thấp (file lạ, scan kém), báo người dùng biết.

**Lý do theo cost-of-error:**
- Summary sai kỹ thuật → học viên học sai → cost RẤT CAO
- Vì vậy: luôn kèm nguồn gốc trích dẫn để học viên tự verify
- Classification vào syllabus chỉ là gợi ý — cần Lab Coach confirm để chính thức

---

## 10. Kế Hoạch Demo (5 phút)

### Case 1 — Happy path (2 phút)
1. Upload slide d1-slide-hackathon.pdf (đã có trong data pack)
2. AI trả về summary + key concepts + vị trí trong syllabus
3. Hỏi follow-up: "Slide này có đề cập đến attention mechanism không?"
4. AI trả lời với trích dẫn cụ thể (trang/slide)

### Case 2 — Chỗ khó (1.5 phút)
1. Hỏi: "Deadline nộp bài tuần này là bao giờ?"
2. Demo: AI từ chối đúng cách, chuyển hướng sang TA
3. Gửi link tài liệu không truy cập được
4. Demo: AI báo lỗi rõ ràng, hướng dẫn upload trực tiếp

### Case 3 — Kết quả đo (1.5 phút)
- Bảng golden set: X/20 case pass
- Quality bar đã chốt: >=75% pass + 100% citations
- Failure case đáng kể + phân tích nguyên nhân

---

## 11. Success Metrics

| Metric | Target | Đo bằng |
|---|---|---|
| Summary accuracy | >=75% golden set pass | Chấm tay theo rubric 2 người |
| Source citation | 100% có citation khi summary | Kiểm tra trace về tài liệu gốc |
| Scope refusal | 100% câu hỏi logistics bị từ chối đúng | Test với 5 câu hỏi logistics |
| User satisfaction | >=3/5 người nói "hữu ích" | Vòng validation CP5 |

---

## 12. Roadmap Sau Hackathon

1. **Tuần 1:** Tích hợp Discord bot thật (webhook/slash command)
2. **Tuần 2:** Vector search thật (Chroma/Qdrant) thay keyword search
3. **Tuần 3:** Xử lý video record (transcript → summary với timestamps)
4. **Tuần 4:** Daily digest tự động cho TA — câu hỏi tồn, chủ đề hot nhất

---

*File này là tài liệu thiết kế tính năng Role 3 — Hải Đăng — Nhóm B7-E402 — VinAI K4 Hackathon*

