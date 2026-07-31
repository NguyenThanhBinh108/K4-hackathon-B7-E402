# Reflection — Vũ · B7-E402 · VinAI K4 Hackathon

## Vai Trò & Phần Mình Làm

**Vai trò:** Role 1 — Kiểm chứng nguồn tài liệu (Source Verification)

**Phần mình làm cụ thể:**

| Phần | Chi tiết |
|---|---|
| **Pipeline Core** | `source_verify.py` (600+ dòng) — domain-tier, risk scan, content extraction, LLM verify, intent classification, grounded verification, aggregate score |
| **Supporting Modules** | `risk_patterns.py` (rule-based risk scan), `knowledge_index.py` (703 đoạn transcript+slide), `doc_index.py` (KB tài liệu), `campus_kb.py` (KB campus) |
| **Eval & Data** | Golden set 31 case (14 case chatlog VLearn thật), `run_golden_set.py`, `test_knowledge_index.py`, `BAO-CAO-KIEM-CHUNG-DATA.md` |
| **Prompt & Spec** | System prompt 300+ dòng (VERIFY_PROMPT_TEMPLATE), `spec-draft-kiem-chung-nguon.md` §1-§9 |
| **Fixes** | FIX-01 (scorer ngược), FIX-17/24 (intent classification), FIX-05 (content extraction), FIX-04 (missing libs warning) |

## AI Hỗ Trợ Thế Nào

- **Nemotron-3-Super (OpenRouter):** Core LLM cho verify claim, phân loại intent, đối chiếu grounded — đây là lời gọi AI thật, không phải mock
- **Gemini Flash / Claude Sonnet:** Fallback khi OpenRouter rate-limit
- **Cursor/AI code assistant:** Giúp generate skeleton, regex, dataclass boilerplate — mình tự review và sửa từng phần logic
- **Mình tự làm:** Toàn bộ pipeline architecture, scorer design, rule-based gates, prompt engineering tiếng Việt, golden set curation, evaluation methodology

**Tôi có thể giải thích được:**

- Tại sao verdict quyết định dải điểm, chất lượng bằng chứng quyết định vị trí trong dải — không dùng llm_confidence làm weight
- Tại sao rule-based (`scan_risk_patterns`, `DOC_QUESTION_RE`) chạy TRƯỚC LLM — tránh LLM bỏ sót risk vì "nghe hợp lý" hoặc mặc định intent "kiem_chung"
- Tại sao grounded verification (trích xuất nội dung thật + đối chiếu) quan trọng hơn domain-tier heuristic — M02 domain github=70 nhưng nội dung KHÔNG chứng minh claim
- Tại sao log đầy đủ `last-run-results.json` để `rescore_results.py` tính lại điểm 0 quota AI khi công thức đổi

## Bài Học Từ Case Fail

**Case fail đáng kể nhất: Scorer ngược hướng (FIX-01) — M05 CONTRADICTED 54/100, M02 UNVERIFIED 79/100**

**Tình huống:** Công thức cũ `0.4×domain_score + 0.6×llm_confidence` nhầm `confidence_llm` (AI tự tin vào verdict) với độ tin cậy claim. AI càng chắc "claim này SAI" (CONTRADICTED, confidence 90) thì điểm càng CAO. Hậu quả: claim SAI (temperature=0 hết hallucinate) được 54/100 tô xanh, claim CHƯA XÁC MINH được 79/100 tô xanh lá. UI hiển thị ngược logic nghiệp vụ.

**Bài học:**

1. **Scorer = contract, Prompt = implementation** — phải định nghĩa dải điểm/nghĩa verdict TRƯỚC, mới viết prompt ép LLM ra đúng schema đó. Không viết prompt xong mới phát hiện scorer ngược.
2. **Đo lường đúng đại lượng** — `llm_confidence` = "mức độ AI tự tin vào verdict", KHÔNG phải "mức độ claim đáng tin". Hai đại lượng khác nhau, không thể cộng weight.
3. **Chạy AI thật sớm** — mock mode che giấu được lỗi scorer ngược, LLM trộn ngoại ngữ (`决定論`, `crédito`, `발표`), JSON bị cắt giữa chừng. Mock chỉ test pipeline chảy, không test chất lượng output.

**Thay đổi cụ thể:** Viết `VERDICT_BANDS` + `aggregate_score()` mới (verdict quyet định dải, evidence quyet định vị trí), `llm_confidence` không còn cộng điểm chỉ lưu tra cứu, trần 95. Chạy `rescore_results.py` trên 17 case AI thật: 14/17 đổi điểm, 0 quota AI.

## Nếu Có Thêm 1 Tuần

1. **Tách intent classifier riêng** — rule-based (regex + từ khóa) cho `hoi_tai_lieu`, `hoi_campus`, `ngoai_pham_vi` TRƯỚC, chỉ để LLM làm `kiem_chung` + `hoi_kien_thuc`. Giảm token 40%, tăng đúng intent từ ~67% lên >90%.
2. **Đo độ phủ từ khoá trên data thật TRƯỚC build index** — phát hiện sớm bag-of-words tiếng Việt bỏ dấu trùng `phở`/`phổ`, không tự phân biệt thuật ngữ khoá vs từ thường. Kiến trúc "từ khoá lỏng → 5 ứng viên → LLM lọc" nên làm ngay từ đầu.
3. **Chữa LLM trộn ngoại ngữ** — thêm post-process regex strip CJK/Hangul khỏi output tiếng Việt, hoặc fine-tune prompt với few-shot cấm chèn ngoại ngữ.
4. **Attachment support** — đọc file đính kèm (PDF, txt, ảnh) thay vì chỉ URL đầu tiên. M16 (file .txt UI Design Keywords) hiện bỏ qua.

## Bài Học Lớn Nhất

**Grounded verification > domain heuristic.** Nội dung thật trích xuất được từ link (TIP-05: trafilatura + pypdf) + đối chiếu claim quan trọng hơn domain-tier suy đoán. M02 domain github=70 nhưng nội dung KHÔNG chứa hướng dẫn batch_size/gradient checkpointing → hạ xuống UNVERIFIED. Nguyên tắc: "nội dung thật > đoán theo domain" — đúng精神 của RAG Citation và Valsci tham khảo ở spec §3.