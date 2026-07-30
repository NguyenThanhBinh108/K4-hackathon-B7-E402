# Feature Spec — Knowledge Synthesis & Document Intelligence

> **Module:** Role 3 · **Owner:** Hải Đăng · **Nhóm:** B7-E402 · **Hướng:** B — Discord Knowledge Assistant

---

---

*Feature Spec — Knowledge Synthesis & Document Intelligence · Hải Đăng · Nhóm B7-E402 · VinAI K4 Hackath*


# Feature Spec v2 — Discord Knowledge Assistant (Production-Lite)

> **Cập nhật từ:** Production Plan (VinAI Resource Assistant) + Feature Spec (Knowledge Synthesis)
> **Bổ sung:** Continuous auto-ingestion, RAG Q&A đầy đủ (không chỉ summary), Router, Semantic Cache, Guardrail, Multi-provider Key Pool
> **Căn cứ thiết kế:** Agentic Fit Framework & Anthropic Agent Patterns (tài liệu khoá AICB Ngày 3-5)
> **Thời gian còn lại khi viết:** 6 giờ

---

## 0. Quyết định kiến trúc nền tảng — vì sao KHÔNG dùng Agent/Multi-agent/MCP

Đây là phần quan trọng nhất để trình bày với ban giám khảo — cho thấy lựa chọn kiến trúc có căn cứ, không chạy theo trend.

### Áp dụng Agentic Fit Scoring Matrix vào chính hệ thống này

| Tiêu chí            | Điểm (1-5) | Giải thích                                                                                                                                                                       |
| --------------------- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Multi-step reasoning  | 2            | Ingestion là chuỗi bước cố định (fetch→chunk→embed→summarize); Q&A là 1-2 bước (route→retrieve→generate), không cần lập kế hoạch động nhiều tầng           |
| Tool interaction      | 3            | Có gọi nhiều tool (Apps Script, Drive, GitHub, Firecrawl, embedding, LLM) nhưng**biết trước tool nào dùng khi nào** — không cần LLM tự chọn tool giữa chừng |
| Dynamic decision      | 2            | Router quyết định 1 lần đầu request, không phải vòng lặp action→observe→adapt liên tục như agent thật                                                              |
| Long horizon          | 1            | Mỗi request xử lý độc lập; conversational memory chỉ để tiện hỏi liên tiếp, không phải theo đuổi mục tiêu dài hạn                                             |
| **Tổng: 8/20** |              | Rơi vào vùng**"augmented chatbot"** (6-10 theo thang trong slide), không đạt ngưỡng "agent đáng thử" (11+)                                                        |

### Kết luận kiến trúc (theo thang Anthropic: Augmented LLM → Prompt Chaining → Routing → Orchestrator-Worker → Agent)

Hệ thống này dùng **3 pattern giữa**, dừng lại trước khi tới "Agent" thật:

| Pattern                        | Áp dụng ở đâu trong hệ thống                                                                                                                                                                           |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Augmented LLM**        | Building block cơ bản: mỗi lệnh gọi LLM đều có tool (retrieval) + structured output, không phải LLM trần                                                                                           |
| **Prompt Chaining**      | Ingestion pipeline: fetch → chunk → embed → summarize là chuỗi cố định, mỗi bước output feed vào bước sau, không rẽ nhánh động                                                             |
| **Routing**              | Router phân loại request → METADATA_LOOKUP / RAG_QUERY / OUT_OF_SCOPE / AMBIGUOUS / INGESTION — đây là trái tim của hệ thống                                                                       |
| **Orchestrator-Worker**  | Khi ingest, orchestrator chọn đúng "worker" fetcher theo loại URL (Slides/Drive/GitHub/generic), chạy song song nếu nhiều URL trong 1 message                                                          |
| **Agent (KHÔNG dùng)** | Không cần vòng lặp tự trị nhiều bước, không cần framework (LangGraph/CrewAI/AutoGen) — thêm vào sẽ tăng token, tăng latency, tăng điểm fail mà không giải quyết bài toán nào thêm |

**Trade-off nói thẳng với giám khảo nếu được hỏi:** "Tụi em cân nhắc multi-agent và MCP, nhưng áp dụng chính framework Agentic Fit đã học để đánh giá — bài toán này là augmented chatbot có routing, dùng agent framework sẽ over-engineering, tốn token vô ích." Đây là câu trả lời senior, không phải né tránh.

---

## 1. Vấn đề & Bằng chứng (giữ nguyên từ Feature Spec gốc, không đổi)

Xem "Feature Spec — Knowledge Synthesis & Document Intelligence" gốc, mục 1. Giữ nguyên toàn bộ evidence (46.2% response không citation, misconceptions/follow_ups chưa dùng, rating rate ~2.8%, asked_check_question gần như 0).

### Lát cắt MỘT CÂU (cập nhật, mở rộng phạm vi so với bản gốc)

> **Khi mentor/BTC đăng tài liệu vào kênh Discord, hệ thống tự động trích xuất, tóm tắt, và nạp vào Knowledge Base liên tục (không cần trigger thủ công); học viên có thể hỏi đáp bất kỳ lúc nào — kể cả để ôn tập nhiều câu liên tiếp — và nhận câu trả lời có trích dẫn cụ thể, được route đúng loại truy vấn, cache thông minh để tiết kiệm chi phí, và guardrail 2 chiều đảm bảo không bịa/không lệch phạm vi.**

### Non-goals (vẫn giữ, bổ sung 2 mục)

1. Không xử lý video/audio (transcript thủ công nếu cần demo)
2. Không multi-agent framework, không MCP (đã giải thích ở mục 0)
3. Không web search ngoài phạm vi tài liệu khoá học (không dùng Tavily — xem mục 9)
4. Không quản lý permission/role Discord phức tạp
5. Không real-time multi-user sync trên HTML clone (single-session demo là đủ)

---

## 2. Feature Components (đầy đủ)

### 2.1 Auto-Ingestion (event-driven, liên tục)

Bot lắng nghe kênh tài nguyên, mỗi khi có URL mới:

1. Detect loại URL (Google Slides / Drive PDF / GitHub / generic web)
2. Check dedup (đã ingest chưa) qua bảng tracking
3. Đẩy vào queue, xử lý nền (không block gateway)
4. Fetch nội dung bằng đúng "worker" tương ứng
5. Parse metadata từ chính message Discord (title, presenter, session, passcode...) bằng regex trước, LLM fallback nếu message không theo format chuẩn
6. Sinh **quick_summary** (1 câu + 3-5 bullet) lưu vào metadata — dùng trả lời nhanh
7. Chunk (500 ký tự, overlap 50) → batch embed → lưu ChromaDB
8. Reply lại đúng message: `✅ Đã phân tích: [tên tài liệu] — Chủ đề: ... — Đã thêm vào Knowledge Base`

### 2.2 RAG Q&A đầy đủ (không chỉ summary — đây là phần mở rộng lớn nhất so với bản gốc)

Học viên có thể hỏi bất kỳ lúc nào trong kênh (không cần link):

- Câu hỏi lookup ("Slide WS2 ở đâu") → trả lời từ **metadata trực tiếp**, không cần vector search
- Câu hỏi nội dung ("Pain point trong WS2 là gì") → **RAG thật**: retrieve top-k chunks đúng resource → generate có citation
- Câu hỏi ôn tập đa lượt ("còn phần MVP Canvas thì sao?" — hỏi tiếp không nhắc lại context) → dùng **conversational memory ngắn hạn** theo `(channel_id, user_id)`, 3-5 turn gần nhất
- Câu hỏi tổng hợp nhiều tài liệu ("tôi cần ôn gì cho buổi thi") → multi-resource retrieval + tổng hợp, kèm cảnh báo "phân loại tự động — verify lại"

### 2.3 Router (rule-based trước, LLM chỉ khi cần)

```
has_url                          → INGESTION
matches out-of-scope keywords    → OUT_OF_SCOPE (trả lời cứng, không qua LLM)
matches lookup pattern           → METADATA_LOOKUP (query trực tiếp, không qua LLM)
câu hỏi quá ngắn/mơ hồ (<3 từ)   → AMBIGUOUS (hỏi lại 1 câu rõ ràng)
còn lại                          → RAG_QUERY (cần LLM + retrieval)
```

Mục tiêu: giảm >60% lệnh gọi LLM so với việc route bằng LLM cho mọi câu.

### 2.4 Semantic Cache

Cache theo embedding câu hỏi, threshold cosine ~0.90-0.92 (cần calibrate 15 phút trước demo). Cache **theo resource_id** — khi resource được re-ingest, invalidate toàn bộ cache liên quan resource đó. Log hit-rate để trình bày con số cụ thể với giám khảo.

### 2.5 Guardrail 2 chiều

**Input:**

- Rule-based out-of-scope filter (deadline, điểm số, thông tin học viên khác) — chặn trước khi tốn token
- Prompt injection filter (pattern "ignore previous instructions", "system:"...)
- Rate limit theo user (chống spam làm cạn key pool)

**Output:**

- Bắt buộc có citation `[resource_id-chunk_N]` nếu route là RAG_QUERY, nếu không có → fallback "không tìm thấy đủ căn cứ"
- Cap độ dài 2000 ký tự (giới hạn Discord)
- Luôn kèm dòng "🤖 Tóm tắt tự động — xem nguồn gốc để xác nhận" (HAX G2)

### 2.6 Multi-Provider Key Pool (Gemini + Groq)

Phân công theo tác vụ, không round-robin ngây thơ:

| Tác vụ                                 | Provider chính             | Fallback                                           | Lý do                                                                               |
| ---------------------------------------- | --------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Embedding                                | Gemini text-embedding-004   | (không có fallback — Groq không có embedding) | Bắt buộc dùng Gemini, cần pool 2-3 key riêng                                    |
| Router LLM fallback + Guardrail classify | Groq (llama-3.1-8b-instant) | Gemini Flash                                       | Cần nhanh, rẻ, chất lượng thấp vẫn đủ dùng                                 |
| Summarization (ingest, không real-time) | Gemini Flash                | Groq (llama-3.3-70b-versatile)                     | Không gấp, ưu tiên chất lượng tiếng Việt                                    |
| RAG Answer generation (real-time)        | Gemini Flash                | Groq (llama-3.3-70b-versatile)                     | Latency-sensitive, cần fallback provider khác hẳn để né rate-limit toàn phần |

Key pool có health-check + cooldown + exponential backoff + jitter, không chỉ round-robin (chi tiết code trong Implementation Plan).

### 2.7 Content Fetcher (mở rộng — thêm Firecrawl)

| Loại URL                           | Cách fetch                                                                                                                          |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Google Slides                       | Google Apps Script Web App (đã có sẵn kế hoạch, execute as Me)                                                                 |
| Google Drive PDF                    | Download trực tiếp (nếu public) → PyMuPDF                                                                                        |
| GitHub repo/file                    | GitHub REST API                                                                                                                      |
| Generic web (blog, docs site khác) | **Firecrawl API** (free tier) — fallback khi không match 3 loại trên, xử lý JS-rendered page tốt hơn tự viết scraper |

### 2.8 Discord Test Channel (thật, để test đúng thực tế)

1 kênh với ~15-20 tin nhắn đa dạng tình huống (chi tiết danh sách trong Implementation Plan mục 6) — dùng làm cả môi trường test lẫn kịch bản demo trực tiếp.

### 2.9 HTML Discord-Clone (demo UI)

2 tab: **Chat** (giao diện giống Discord dark theme, gọi thẳng `/api/chat`) và **Resources** (grid card tài nguyên, filter theo loại, gọi `/api/resources`). Không cần real-time đa người dùng — single-session là đủ cho demo.

---

## 3. Kiến trúc hệ thống tổng thể

```
╔══════════════════════════════════════════════════════════════╗
║ DISCORD SERVER (test) — kênh #tài-nguyên                     ║
╚═══════════════════════╦════════════════════════════════════════╝
                        ║ discord.py (thin client)
                        ▼
╔══════════════════════════════════════════════════════════════╗
║ GUARDRAIL INPUT (rule-based, không tốn token)                ║
║  - out-of-scope filter · injection filter · rate limit       ║
╚═══════════════════════╦════════════════════════════════════════╝
                        ▼
╔══════════════════════════════════════════════════════════════╗
║ ROUTER (rule-based → LLM fallback qua Groq nếu cần)          ║
║  INGESTION | METADATA_LOOKUP | RAG_QUERY | OUT_OF_SCOPE | AMBIGUOUS ║
╚═══╦═══════════╦═══════════════╦═══════════════════════════════╝
    ▼           ▼               ▼
INGESTION   METADATA        RAG_QUERY
ORCHESTRATOR LOOKUP         │
    │       (query metadata  ├─ SEMANTIC CACHE (check trước)
    │        Chroma trực     │     │ hit → trả ngay
    │        tiếp, không     │     │ miss ▼
    │        cần LLM)        ├─ Retrieve top-k chunks (Chroma)
    ▼                        ├─ Conversational memory (RAM, per channel+user)
WORKER theo loại URL         ├─ LLM GENERATE (Gemini→Groq fallback)
(Slides/Drive/GitHub/        │     qua KEY POOL multi-provider
 Firecrawl generic)          ▼
    │                    GUARDRAIL OUTPUT
    ▼                    (citation check · length cap · confidence tag)
chunk → batch embed          │
→ summarize → lưu Chroma     ▼
+ metadata                REPLY về Discord / HTML clone
    │
    ▼
╔══════════════════════════════════════════════════════════════╗
║ CHROMADB (persistent) + SQLite (dedup/job tracking)           ║
╚══════════════════════════╦════════════════════════════════════╝
                            ▼
╔══════════════════════════════════════════════════════════════╗
║ FASTAPI BACKEND (dùng chung cho Discord bot VÀ HTML clone)    ║
║  /api/chat  /api/resources  /api/sync  /api/health /api/feedback ║
╚══════════════════════════╦════════════════════════════════════╝
                            ▼
╔══════════════════════════════════════════════════════════════╗
║ HTML DISCORD-CLONE (demo UI, single-session)                  ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 4. Interaction Flows

### 4.1 Happy Path — Auto-ingest khi mentor share link

```
1. Mentor paste link Google Slides vào #tài-nguyên
2. Bot react ⏳ ngay lập tức (feedback tức thì)
3. [Nền] Router → INGESTION → Orchestrator chọn worker "gslides"
4. Fetch qua Apps Script → parse metadata từ message text
5. Quick summary (Gemini Flash) → chunk → batch embed → lưu Chroma
6. Bot sửa reaction ⏳ → ✅, reply:
   "Đã phân tích: Workshop 2 — Problem → MVP Canvas
    Diễn giả: Anh Lê Anh Tiến | Chủ đề: Pain point, MVP Canvas
    Đã thêm vào Knowledge Base."
```

### 4.2 Happy Path — Học viên ôn tập nhiều câu liên tiếp

```
1. HV: "Pain point trong WS2 là gì?"
   → Router: RAG_QUERY → cache miss → retrieve chunks WS2 → generate
   → "Pain point là... [WS2-slide-chunk-003]"
2. HV: "còn MVP Canvas thì sao?" (không nhắc lại "WS2")
   → Conversational memory nhớ context đang nói về WS2
   → Router: RAG_QUERY → retrieve chunks liên quan MVP Canvas trong WS2
   → trả lời có citation
3. HV: "Khi nào dùng RAG khi nào fine-tune?" (câu hỏi tương tự đã hỏi trước bởi bạn khác)
   → Semantic cache HIT (similarity 0.94) → trả lời ngay, không gọi LLM
```

### 4.3 Out-of-scope

```
HV: "Deadline nộp bài tuần này là bao giờ?"
→ Guardrail input rule-based match ngay → KHÔNG qua router/LLM
→ "Câu hỏi về deadline nằm ngoài phạm vi của mình.
   Vui lòng hỏi Lab Coach hoặc check #announcements."
```

### 4.4 Rate-limit resilience (điểm ăn điểm production)

```
Gemini key A bị rate-limited khi generate câu trả lời
→ KeyPool mark cooldown key A, thử key B (Gemini) → vẫn rate-limited
→ Fallback sang provider khác hẳn: Groq llama-3.3-70b-versatile
→ Trả lời vẫn ra, có thể note nhỏ nội bộ "generated via fallback provider"
→ Không bao giờ để học viên thấy lỗi 429 trần trụi
```

---

## 5. Risk Scenarios — 4 Layers (mở rộng từ bản gốc, thêm layer 5)

### Layer 1 — Ground Truth / Hallucination

Giữ nguyên bản gốc + bổ sung: guardrail output enforce citation bằng code, không dựa LLM tự giác.

### Layer 2 — Ambiguity

Giữ nguyên bản gốc.

### Layer 3 — Out-of-scope

Giữ nguyên bản gốc + chuyển từ "LLM tự nhận diện" sang **rule-based filter chặn trước** (nhanh hơn, ổn định hơn).

### Layer 4 — Domain-specific

Giữ nguyên bản gốc.

### Layer 5 — Hệ thống/Hạ tầng (MỚI — do mở rộng scope)

| Scenario                                                               | Expected Behavior                                                                                                     |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Tất cả Gemini key rate-limited cùng lúc                            | Fallback sang Groq, không để lỗi lộ ra ngoài                                                                    |
| Semantic cache trả lời sai vì threshold quá thấp (false-positive) | Calibrate threshold trước demo bằng vài cặp câu hỏi thật; log mọi cache hit để audit sau                   |
| Resource bị re-ingest (update) nhưng cache cũ vẫn tồn tại        | Invalidate cache theo resource_id khi re-ingest                                                                       |
| Discord bot mất kết nối gateway giữa demo                          | Ingestion queue vẫn giữ job (không mất dữ liệu), bot tự reconnect, dùng discord.py auto-reconnect mặc định |
| 1 user spam nhiều câu hỏi liên tục                                | Rate limit theo user ở tầng guardrail input, tránh cạn key pool                                                   |

---

## 6. Design Principles (HAX/PAIR) — giữ nguyên bản gốc, không đổi

Xem bản gốc mục 7 — G1, G2, G8, G10, G11, PAIR Explainability đều áp dụng nguyên vẹn cho cả 2 luồng ingest và Q&A.

---

## 7. Golden Set (mở rộng lên ~20 case thực tế, đủ đại diện, không cần 50)

| Nhóm                             | Số case | Nội dung                                                     |
| --------------------------------- | -------- | ------------------------------------------------------------- |
| A — Auto-ingest happy path       | 4        | Slides, PDF, GitHub, generic web (Firecrawl)                  |
| B — Metadata lookup              | 3        | "Slide WS2 ở đâu", "Video WS1 passcode", "Ai dạy WS3"     |
| C — RAG content Q&A              | 4        | Pain point, MVP Canvas, tóm tắt WS, so sánh 2 khái niệm  |
| D — Ôn tập đa lượt (memory) | 3        | Hỏi tiếp không nhắc context, đổi chủ đề giữa chừng |
| E — Out-of-scope                 | 2        | Deadline, điểm số                                          |
| F — Ambiguous                    | 2        | "tài liệu về AI", câu hỏi 2 từ                          |
| G — Hệ thống (Layer 5)         | 2        | Giả lập rate-limit, giả lập cache false-positive          |

---

## 8. Demo Script (5 phút, cập nhật)

1. **Live auto-ingest** (1 phút): paste link Slides thật trước mặt giám khảo → bot react ⏳ → reply ✅ có metadata + summary trong vài giây
2. **Ôn tập đa lượt** (1.5 phút): hỏi 2-3 câu liên tiếp trong kênh, có 1 câu dùng lại ý đã hỏi trước (show cache hit qua log/console)
3. **Out-of-scope + Ambiguous** (1 phút): demo từ chối đúng cách
4. **Trình bày kiến trúc + lý do không dùng agent/MCP** (1 phút): dùng chính bảng Agentic Fit Scoring ở mục 0
5. **Golden set results** (0.5 phút): bảng %pass + cache hit-rate + số lần fallback provider thành công

---

## 9. Quyết định KHÔNG dùng — nói rõ để tránh bị hỏi ngược

| Công nghệ                                      | Quyết định       | Lý do                                                                                                                                                  |
| ------------------------------------------------ | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Multi-agent framework (CrewAI/AutoGen/LangGraph) | Không dùng        | Agentic Fit score 8/20, không đạt ngưỡng cần agent thật                                                                                          |
| MCP                                              | Không dùng        | Chỉ có 3-4 tool cố định, biết trước lúc code — MCP giải quyết bài toán chuẩn hoá nhiều tool động, không phải bài toán của mình |
| Tavily (web search)                              | Không dùng        | Phá vỡ nguyên tắc "chỉ trả lời trong phạm vi Knowledge Base", tăng rủi ro hallucination ngoài phạm vi                                       |
| RapidAPI                                         | Không dùng        | Không có nhu cầu API niên lẻ, 3 nguồn chính (Slides/Drive/GitHub) đã có API chính chủ free                                                  |
| Firecrawl                                        | **Có dùng** | Fallback fetcher cho URL ngoài 3 loại chính, xử lý JS-rendered tốt hơn tự viết scraper, có free tier                                          |

---

## 10. Quality Bar & Metrics (mở rộng)

| Metric                                | Target                                                             |
| ------------------------------------- | ------------------------------------------------------------------ |
| Summary accuracy                      | ≥75% golden set pass                                              |
| Citation correctness                  | 100% khi route RAG_QUERY                                           |
| Scope refusal rate                    | 100% out-of-scope bị chặn đúng                                 |
| Router accuracy                       | ≥90% route đúng nhóm (đo qua golden set)                      |
| Cache hit-rate (sau vài chục query) | Ghi nhận số thực tế để trình bày, không cần target cứng |
| Fallback provider success rate        | 100% (khi Gemini rate-limited, Groq phải cứu được)            |
