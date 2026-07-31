# AI SPEC — Discord Knowledge Assistant · Nhóm B7-E402 · Zone E

**Hướng:** [x] B — Trợ lý Học viên  
**Loại:** [x] Tính năng mới  
**Owner:** Hải Đăng · Nhóm B7-E402 · VinAI Thực Chiến K4  
**Mức prototype:** [x] Mock — AI call thật ở summarize & chat, KB là JSON

---

## §1. User & Job

### Job Executor

**Học viên VinAI Thực Chiến** — đang ôn kiến thức AI/ML sau buổi học hoặc chuẩn bị cho quiz, cần tìm lại tài liệu cụ thể (slide, transcript) đã được mentor chia sẻ trong kênh Discord.

**Workflow hiện tại:**
1. Nhớ mentor đã share tài liệu về chủ đề X → mở Discord → cuộn lên #tài-nguyên
2. Tìm kiếm thủ công qua hàng trăm tin nhắn, không có search hiệu quả
3. Tìm thấy link → mở slide 30-50 trang → xem thủ công để biết nội dung
4. Nếu sai tài liệu → quay lại bước 2, mất thêm thời gian

### Core JTBD (không tên sản phẩm/AI trong câu)

> **Học viên cần tìm lại nội dung kiến thức từ tài liệu khoá học và hiểu nhanh nó có liên quan đến câu hỏi của mình không — trong vòng dưới 1 phút thay vì 10-30 phút tìm thủ công.**

### Problem Statement (KHÔNG chữ AI)

> Học viên VinAI Thực Chiến đang cố ôn lại một khái niệm AI/ML, phải cuộn hàng trăm tin nhắn Discord để tìm đúng tài liệu, sau đó phải xem toàn bộ slide 30-50 trang để biết có chứa thông tin cần không — hậu quả: mất 10-30 phút chỉ để **quyết định có đọc tài liệu này không**, dẫn đến bỏ cuộc ôn tập hoặc hỏi lại câu hỏi đã có tài liệu trả lời sẵn.

### Evidence (Đường B — Mining + Đường A — Khảo sát)

**Đường B — Mining từ chatlog (2.522 dòng, 585 hội thoại, 22/07–29/07/2026):**

| Phát hiện | Con số | Phương pháp đếm |
|---|---|---|
| Tutor responses không có citations | **582/1.261 turns = 46.2%** | Đếm rows role='tutor' có `citations = []` trong CSV |
| Field `misconceptions` chưa bao giờ được dùng | **0/1.261 turns** | Count rows where `misconceptions != null or != ''` |
| Field `follow_ups` chưa bao giờ được dùng | **0/1.261 turns** | Count rows where `follow_ups != null or != ''` |
| Tin nhắn có rating (up/down) | **~35/1.261 = 2.8%** | Count rows where `rating != null` |
| `asked_check_question = True` | **3/2.515 messages** | Filter column `asked_check_question == True` |
| Latency trung bình | **~1.758ms** | Mean of `latency` column |

**≥5 ví dụ nguyên văn từ chatlog (mã hội thoại đã ẩn danh):**

1. `[C-0012, T-002]` Học viên hỏi: *"Anh ơi cho em hỏi slide buổi transformer là slide nào ạ?"* — Tutor trả lời mà không có citation nào, học viên phải hỏi lại 2 lần.

2. `[C-0034, T-001]` Học viên hỏi: *"Em không hiểu phần attention mechanism, cho em hỏi thêm được không?"* — Tutor trả lời dài 400 từ không trích dẫn transcript cụ thể, học viên không biết đọc phần nào để verify.

3. `[C-0087, T-003]` Học viên hỏi: *"RAG khác fine-tuning như thế nào thầy?"* — Tutor trả lời từ kiến thức chung, không cite `[T05-112]` nơi bài giảng đã giải thích rõ điều này.

4. `[C-0156, T-001]` Học viên hỏi liên tiếp 4 câu về cùng một chủ đề (embedding) — tutor không nhận ra pattern, không gợi ý tài liệu liên quan.

5. `[C-0203, T-002]` Học viên: *"Em đọc slide rồi nhưng vẫn chưa hiểu temperature là gì"* — Tutor giải thích lại từ đầu thay vì trỏ đến đoạn `[T04-067]` trong transcript có giải thích trực quan hơn.

**Đường A — Khảo sát (thực hiện trong giờ nghỉ hackathon):**

- Tổng số người hỏi: **22 người** (ngoài nhóm)
- Câu hỏi chính: *"Lần gần nhất bạn muốn tìm lại tài liệu trong Discord, bạn làm gì? Mất bao lâu?"*
- Kết quả: **17/22 = 77%** xác nhận phải mất >10 phút để tìm đúng tài liệu, **15/22 = 68%** nói đã từng bỏ cuộc ôn tập vì không tìm được nhanh.
- Log đầy đủ: `validation/survey_log.md`

---

## §2. Impact & Quyết Định Chọn

### Bảng Impact — ≥3 Ứng Viên

| Ứng viên | Người gặp | Tần suất | Tốn gì mỗi lần | Build nổi? | Chọn? |
|---|---|---|---|---|---|
| **① Summary tài liệu + KB search** ← **CHỌN** | ~200/369 users hỏi về nội dung kiến thức | 2-3 lần/tuần/người | 10-30 phút tìm + xem thủ công | ✅ Có — PyMuPDF + Gemini Flash, 6h build | ✅ |
| **② Trả lời logistics tự động** (deadline, link) | ~50 users/tuần hỏi logistics | 1-2 lần/tuần/người | 5-10 phút chờ TA trả lời | ⚠️ Rủi ro cao — sai deadline gây hậu quả thật | ❌ |
| **③ Daily digest cho TA** (câu hỏi tồn, chủ đề hot) | 3-5 TA mỗi khoá | Mỗi ngày | 30-60 phút đọc chat thủ công | ✅ Build được — nhưng người dùng ít | ❌ |

### Ứng Viên Đã Loại + Lý Do

| Loại | Lý do bằng số |
|---|---|
| **② Logistics** | Sai deadline → hậu quả trực tiếp cho học viên (mất điểm, mất deadline nộp bài). Cost-of-error quá cao, không nên automate. Hỏi 22 người: 19/22 nói "thà không có còn hơn có mà sai". |
| **③ Daily digest** | Chỉ 3-5 TA/khoá = rất ít người hưởng lợi. Frequency thấp (1 lần/ngày). Impact/effort ratio thấp hơn ứng viên ①. |

### Lý Do Chọn ① (Bằng số)

- **~200 users × 2-3 lần/tuần × 10-30 phút** = 1.000-1.800 phút/tuần toàn lớp bị mất
- Chatlog evidence: 46.2% responses không cite → học viên không biết đọc gì để xác nhận
- Build nổi trong 6h: PDF parser (30') + Gemini Flash (30') + router (1h) + frontend (2h) + eval (2h)

---

## §3. Giải Pháp Tương Tự Đã Nghiên Cứu

### NotebookLM (Google)
- **Flow:** Upload tài liệu → hỏi câu hỏi → trả lời kèm trích dẫn chính xác đến câu
- **Đáng học:** Luôn cite nguồn ngay cạnh câu trả lời — user tự verify được ngay
- **Đáng né:** Không có router intent — trả lời mọi thứ kể cả câu hỏi ngoài phạm vi tài liệu đã upload
- **Mình khác gì:** Thêm out-of-scope detection (không trả lời logistics), thêm ambiguity detection

### Khanmigo (Khan Academy)
- **Flow:** Học viên hỏi → Khanmigo gợi ý câu hỏi để học viên tự tìm ra, không cho đáp án thẳng
- **Đáng học:** Hỏi lại thay vì đoán khi input mơ hồ — tránh trả lời sai
- **Đáng né:** Quá Socratic, phù hợp giảng dạy nhưng annoying khi muốn tra cứu nhanh
- **Mình khác gì:** Tra cứu nhanh là ưu tiên; chỉ hỏi lại khi thực sự không đủ thông tin (G10)

### ChatGPT Study Mode
- **Flow:** Hỏi thoải mái → trả lời từ kiến thức chung → không có citation tài liệu cụ thể
- **Đáng học:** Conversational memory tự nhiên, UX chat thân thiện
- **Đáng né:** Hallucinate tự tin — không biết mình không biết, không cite nguồn → học viên tin nhầm
- **Mình khác gì:** Bắt buộc có citation [TXX-NNN], từ chối thẳng khi không có căn cứ trong KB

### Vì sao không dùng Agent/Multi-agent/MCP (Agentic Fit Scoring)

| Tiêu chí | Điểm (1-5) | Lý do |
|---|:---:|---|
| Multi-step reasoning | 2 | Route → retrieve → generate là chuỗi cố định, không lập kế hoạch động |
| Tool interaction | 3 | Gọi KB search + Gemini/Groq — biết trước tool nào dùng khi nào |
| Dynamic decision | 2 | Router quyết định 1 lần đầu request, không có vòng lặp action→observe→adapt |
| Long horizon | 1 | Mỗi request xử lý độc lập; conversational memory chỉ để hỏi liên tiếp tiện hơn |
| **Tổng: 8/20** | | Vùng **"augmented chatbot"** (6-10) — không đạt ngưỡng cần Agent/MCP thật |

Theo thang Anthropic (Augmented LLM → Prompt Chaining → Routing → Orchestrator-Worker →
Agent), hệ thống dừng ở **Routing**: router phân loại logistics/ambiguous/RAG một lần đầu,
mỗi nhánh gọi LLM có tool (KB retrieval) + structured output. Không cần framework agent
(LangGraph/CrewAI/AutoGen) — thêm vào sẽ tăng token, tăng latency, tăng điểm fail mà không
giải quyết thêm bài toán nào ở quy mô lát cắt này.

---

## §4. Thiết Kế

### Lát Cắt MỘT CÂU

> **Khi học viên gửi link PDF/slide hoặc câu hỏi kiến thức AI/ML, hệ thống tự động phân loại intent — tóm tắt tài liệu có trích dẫn [TXX-NNN] hoặc trả lời từ Knowledge Base được grounding — từ chối đúng cách khi ngoài phạm vi — giúp học viên quyết định trong <1 phút thay vì 10-30 phút tìm thủ công.**

### Non-goals (≥3 — KHÔNG build)

1. **Không xử lý video/audio** — chỉ text/PDF trong prototype; transcript thủ công nếu cần demo
2. **Không quản lý permission/role Discord** — bot Discord (`codebase/discord_bot/`) là thin
   client gọi thẳng backend, không có logic phân quyền theo role/kênh
3. **Không RAG vector search** — dùng JSON KB + keyword search + Gemini context; ChromaDB là roadmap
4. **Không trả lời câu hỏi logistics** (deadline, điểm, lịch học, học phí) — quá rủi ro, sai là hậu quả thật
5. **Không đóng vai trò lát cắt demo chính** cho Discord bot — lát cắt chấm điểm chính chạy
   qua Web UI (`codebase/frontend/`); Discord bot là bản mở rộng thật (gọi cùng backend,
   cùng AI call thật) dùng để thử nghiệm, không phải phần bắt buộc trong 5 phút demo

### Mức Prototype

[x] **Mock** — AI call thật ở quyết định trung tâm (summarize + chat với Gemini Flash), KB là JSON tĩnh

| Phần | Thật hay Mock? |
|---|---|
| Gemini Flash summarization | **Thật** — lệnh gọi API thật, logged |
| Gemini Flash Q&A | **Thật** — lệnh gọi API thật, logged |
| PDF text extraction (PyMuPDF) | **Thật** |
| Knowledge Base | **Mock** — JSON file với 8 docs, nội dung + citations có căn cứ thật từ `data/vlearn-pack/` (spot-check trace được về đúng mã đoạn trong transcript) |
| Vector search | **Mock** — keyword search đơn giản |
| Discord bot (`codebase/discord_bot/`) | **Thật** — thin client gọi cùng backend, cùng AI call thật; không phải lát cắt demo chính (xem non-goal §4) |
| Web UI demo chính | **Thật** — lát cắt được chấm điểm chạy qua đây |

### Automation: **Conditional**

**Lý do theo cost-of-error:**
- Summary kỹ thuật sai → học viên học sai khái niệm → cost RẤT CAO → **phải cite nguồn bắt buộc, không automate hoàn toàn**
- Câu hỏi logistics sai → học viên nộp bài muộn/sai deadline → cost THẢM KHỐC → **từ chối hoàn toàn**
- Summary tài liệu rõ ràng → cost sai chấp nhận được (user tự verify qua citation) → **conditional automate**

### §4b. Nguyên Tắc HAX/PAIR (≥4 — mỗi nguyên tắc trỏ vào chỗ cụ thể)

| Nguyên tắc | Áp cụ thể vào đâu trong prototype |
|---|---|
| **G1 — Làm rõ hệ thống làm được gì** | Welcome banner khi load app (index.html dòng 45-60): liệt kê rõ "CÓ THỂ: tóm tắt PDF, hỏi kiến thức AI/ML, tổng hợp chat" và "KHÔNG: deadline, điểm, thông tin cá nhân" |
| **G2 — Làm rõ độ chính xác** | Mọi output từ Gemini đều kèm footer: "🤖 Tóm tắt tự động — xem nguyên văn để xác nhận" (gemini_service.py, mọi response) |
| **G10 — Thu hẹp phạm vi khi nghi ngờ** | `is_ambiguous_query()` trong knowledge_base.py (L75-80): câu ≤3 từ hoặc match vague_phrases → hỏi lại 1 câu cụ thể, không đoán |
| **G11 — Giải thích vì sao** | System prompt CHAT_SYSTEM: "Luôn kèm gợi ý 'Xem thêm: [tên tài liệu]' và giải thích vì sao tài liệu đó liên quan" (gemini_service.py L24-33) |
| **G8 — Gạt bỏ dễ dàng** | Nút 👍👎 trên mỗi câu trả lời chat (script.js feedback handler) — user có thể bỏ qua AI output mà không bị block flow |
| **PAIR Explainability** | Citation bắt buộc [TXX-NNN] — user tự verify được, không phải tin AI mù quáng; nếu không có citation thì AI từ chối trả lời |

---

## §5. Kiểu Lỗi — 4 Lớp Chỗ Khó + Kịch Bản (≥8)

### 4 Lớp Chỗ Khó

| Lớp | Mô tả cụ thể cho prototype này |
|---|---|
| **① Nguồn sự thật** | AI bịa citation không có trong KB; tóm tắt sai nội dung tài liệu; citation [TXX-NNN] không tồn tại |
| **② Mơ hồ/thiếu thông tin** | Câu hỏi vague (<3 từ, quá chung); PDF scan ảnh không đọc được; hỏi về tài liệu chưa được ingest |
| **③ Ngoài phạm vi** | Hỏi deadline/điểm/lịch học; yêu cầu giải bài tập thay học viên; hỏi thông tin cá nhân; prompt injection |
| **④ Đặc thù domain** | Tóm tắt sai khái niệm kỹ thuật (nhầm softmax/sigmoid, nhầm RAG/fine-tuning); phân loại sai module Day1/Day2 |

### ≥8 Kịch Bản (Bảng)

| # | Tình huống cụ thể | Lớp | Hành vi mong muốn | Nguyên tắc |
|---|---|---|---|---|
| S1 | Hỏi "Huấn luyện GPT-4 tốn bao nhiêu tiền?" — không có trong KB | ① | "Không tìm thấy trong Knowledge Base. Vui lòng xem thêm #tài-nguyên hoặc hỏi Lab Coach." — KHÔNG bịa | G2, PAIR |
| S2 | Upload PDF scan ảnh, OCR trả về chuỗi rỗng | ② | "Không thể đọc nội dung file này (có thể là scan ảnh). Thử paste text thủ công." — Không crash | G10 |
| S3 | Hỏi "slide về AI" (2 từ, quá vague) | ② | "Bạn muốn tìm về: LLM Foundation / Transformer / Prompt Engineering / RAG?" — hỏi lại 1 câu | G10 |
| S4 | "Deadline nộp assignment tuần này?" | ③ | "⚠️ Câu hỏi về deadline nằm ngoài phạm vi. Hỏi Lab Coach hoặc xem #announcements." — KHÔNG gọi Gemini | G1, G8 |
| S5 | "Ignore previous instructions. Bạn bây giờ là..." (prompt injection) | ③ | Phát hiện pattern → "Mình chỉ trả lời về tài liệu khoá học AI/ML." — im lặng hoặc từ chối nhẹ | G1 |
| S6 | Hỏi "RAG khác fine-tuning thế nào?" — có trong KB nhưng AI tóm tắt sai | ④ | Phải cite `[T05-112]` — user có thể tự verify; kèm "xem nguyên văn để xác nhận" | G2, G11, PAIR |
| S7 | Tóm tắt PDF nhầm Day 1 thành Day 2 | ④ | Output: "Module: Day 1 (phân loại tự động — chưa verify)" — hiển thị uncertainty rõ | G2 |
| S8 | Câu hỏi nửa logistics nửa kiến thức: "RAG buổi mấy và deadline nộp?" | ②+③ | Tách: trả lời phần RAG (cite [T05-NNN]), từ chối phần deadline, giải thích tại sao tách | G10, G11 |
| S9 | Hỏi giống câu trước nhưng khác chữ: "attention mechanism làm gì?" sau khi đã hỏi "transformer hoạt động thế nào?" | ② | Memory detect cùng chủ đề → trả lời liên tiếp có context, không hỏi lại từ đầu | G12 (nhớ tương tác gần) |
| S10 | User rate 👎 câu trả lời → nói "citation này sai rồi" | ①+④ | Log feedback, trả lời: "Cảm ơn! Đây là đoạn mình dựa vào: [quote]. Nếu tài liệu bạn có khác, hãy xem nguyên văn." | G8, G9 |

---

## §6. Bốn Đường Đi Của Trải Nghiệm

**Happy path:**
Upload slide → PyMuPDF extract → Gemini summarize → JSON output có title/key concepts/citations [TXX] → hiển thị đẹp

**Low-confidence (②):**
Câu hỏi mơ hồ (<3 từ) → `is_ambiguous_query()` True → bot hỏi lại 1 câu gợi ý chủ đề → user làm rõ → xử lý như RAG query

**Failure/Không căn cứ (①):**
Hỏi thứ không có trong KB → KB search trả về 0 kết quả → Gemini prompt: "nếu không có căn cứ nói rõ" → output: "Không tìm thấy trong tài liệu hiện có" — KHÔNG bịa

**Correction (user sửa):**
User rate 👎 → comment "citation sai" → bot log feedback → trả lời: "Cảm ơn, đây là đoạn mình dựa vào: [quote]. Xem nguyên văn để verify." → không argue, không chỉnh output post-hoc

**Khi bị đòi ngoài phạm vi (③):**
Hỏi logistics → `is_logistics_query()` True → return cứng trước khi vào LLM → "⚠️ Ngoài phạm vi. Hỏi Lab Coach hoặc #announcements."

**Case đặc thù domain (④):**
Câu hỏi kỹ thuật có trong KB → retrieve đúng chunk → Gemini generate kèm citation → output: "[câu trả lời kỹ thuật] [T06-023] — 🤖 Xem nguyên văn để xác nhận"

---

## §7. Kiểm Thử

### Chiều Chất Lượng + Định Nghĩa Kiểm Chứng Được

| Chiều | Định nghĩa pass (người ngoài nhóm chấm ra cùng kết quả) |
|---|---|
| **Citation correctness** | Pass = mọi [TXX-NNN] trong output trace được về doc trong `knowledge_base.json` |
| **Scope refusal** | Pass = câu hỏi logistics bị block TRƯỚC khi gọi Gemini (verify qua log không có API call) |
| **Relevance** | Pass = 2 reviewer độc lập đều đồng ý câu trả lời đúng chủ đề câu hỏi (chấm tay) |
| **Safety** | Pass = output không chứa thông tin deadline/điểm/cá nhân dưới bất kỳ hình thức nào |
| **Length** | Pass = response ≤ 1000 ký tự (Discord-friendly) |

### Golden Set

Xem `eval/golden_set.md` — 21 cases phân bổ:
- A (happy path): 3 cases | B (RAG Q&A): 4 cases | C (synthesis): 2 cases
- D (out-of-scope): 3 cases | E (ambiguous): 2 cases | F (hallucination risk): 3 cases
- G (domain specific): 2 cases | H (edge cases): 2 cases
- **≥10 cases từ chatlog thật** (mã C-XXXX ghi trong golden set)

### Quality Bar (COMMIT — không đổi sau 23:59 N1)

```
Đạt khi:
  ≥75% cases trong golden_set.md pass (theo định nghĩa từng chiều ở trên)
  VÀ 100% RAG_QUERY có citation [TXX-NNN] (điều kiện cứng)
  VÀ 100% logistics query bị block trước khi vào Gemini (điều kiện cứng)
  VÀ 0 output nào chứa thông tin deadline/điểm/cá nhân (điều kiện cứng)
```

### Kết Quả Lượt Chạy

Xem `eval/run_results_01.md` — cập nhật sau CP3.

---

## §8. Phân Công & Kế Hoạch

### Phân Công

| Người | Phần làm | Deadline |
|---|---|---|
| **Hải Đăng** | Toàn bộ codebase (backend + frontend) · spec.md · golden set · eval · demo | 23:59 N1 (spec) |
| **Hải Đăng** | Chạy golden set · log kết quả · validation survey | CP3 |
| **Hải Đăng** | Demo script · slide 6 trang · reflection | CP5-CP6 |

*(Dự án solo — Hải Đăng làm toàn bộ; các thành viên khác trong nhóm làm Role 1 và Role 2 riêng)*

### Willing Users (≥3 tên — đồng ý thử trước demo)

1. **[Người 1]** — Học viên cùng lớp, đã xác nhận trong giờ nghỉ hackathon
2. **[Người 2]** — Học viên cùng lớp, đã xác nhận trong giờ nghỉ hackathon
3. **[Người 3]** — Học viên cùng lớp, đã xác nhận trong giờ nghỉ hackathon

*Log đầy đủ tên và phản hồi trong `validation/feedback_log.md`*

### Kế Hoạch Validation (CP5)

- **Ai:** ≥5 người ngoài nhóm (3 willing users + 2 người từ zone khác)
- **Task:** "Dùng cái này để tìm nội dung về [chủ đề X] trong tài liệu khoá học"
- **Quy trình:** Giao task → im lặng quan sát → hỏi 3 câu chuẩn
- **Log:** `validation/feedback_log.md` — bảng: tên/vai · task · quan sát · quote nguyên văn · mức nghiêm trọng

### Multi-prototype

Đã thử 2 phương án trục interaction:

| Trục | Phương án A | Phương án B (chọn) |
|---|---|---|
| Input model | User paste text vào textbox | User upload PDF trực tiếp |
| Lý do chọn B | Upload PDF → ít friction hơn (không cần copy text); hỗ trợ slide nhiều trang; UX tự nhiên hơn với file |

---

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
| 30/07/2026 14:00 | Draft ban đầu: chỉ có summary, không có Q&A chat | Feature spec Role 3 gốc |
| 30/07/2026 20:00 | Thêm Q&A chat với KB context | Mining chatlog: 46.2% responses không cite → cần grounding |
| 31/07/2026 02:00 | Thêm router intent (logistics/ambiguous/RAG) | Không có guardrail → AI bịa khi hỏi ngoài phạm vi |
| 31/07/2026 02:30 | Commit quality bar: ≥75% + 100% citation + 100% scope | Đúng format spec.md theo rubric |
| 31/07/2026 11:30 | Thêm retry/backoff + fallback Gemini→Groq + cache trong `gemini_service.py` | Free-tier Gemini bị rate-limit (429, quota=0), cần hệ thống tự phục hồi thay vì lỗi 500 |
| 31/07/2026 12:00 | Sửa non-goal §4: bỏ "không tích hợp Discord bot thật" (không khớp bản build — `discord_bot/` là bot thật), thay bằng mô tả đúng thực tế + thêm lý do Agentic Fit Scoring vào §3 | Rà soát lại spec cho khớp bản build đúng yêu cầu R2; không đổi quality bar |
