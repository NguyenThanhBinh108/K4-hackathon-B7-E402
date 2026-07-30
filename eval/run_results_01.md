# Run Results — Lượt 1 · B7-E402
# Ngày chạy: 31/07/2026 · Người chạy: Hải Đăng
# Backend: uvicorn main:app --reload (localhost:8000) · Model: gemini-1.5-flash

## Cấu Hình Lượt Chạy

- **Model:** gemini-1.5-flash
- **KB version:** knowledge_base.json v1.0 (8 docs)
- **Quality bar:** ≥75% pass + 100% citation (RAG) + 100% scope refusal
- **Phương pháp:** Chạy tay từng case qua Web UI hoặc curl, ghi kết quả

---

## Bảng Kết Quả

| Case | Input (tóm tắt) | Route | Citation? | Scope? | Relevant? | Pass? | Ghi chú |
|---|---|---|---|---|---|---|---|
| A01 | Upload d1-slide.pdf | SUMMARY | ✅ | ✅ | — | **✅** | Có citations D1-slide-p[N] |
| A02 | Hỏi Transformer attention | RAG_QUERY | ✅ [T06] | ✅ | ✅ | **✅** | |
| A03 | Tìm tài liệu về RAG | RAG_QUERY | ✅ [T05] | ✅ | ✅ | **✅** | |
| B01 | LLM dự đoán token thế nào | RAG_QUERY | ✅ [T04] | ✅ | ✅ | **✅** | |
| B02 | RAG vs fine-tuning | RAG_QUERY | ✅ [T05] | ✅ | ✅ | **✅** | |
| B03 | JTBD là gì | RAG_QUERY | ✅ [T01] | ✅ | ✅ | **✅** | |
| B04 | Positional encoding (đa lượt) | RAG_QUERY | ✅ [T06] | ✅ | ✅ | **✅** | Memory context hoạt động |
| C01 | Tổng hợp chat embedding | SYNTHESIZE | — | ✅ | ✅ | **✅** | |
| C02 | Chat lẫn kỹ thuật + logistics | SYNTHESIZE | — | ✅ | ✅ | **✅** | Bỏ được phần logistics |
| D01 | Deadline nộp bài | OUT_OF_SCOPE | — | ✅ | — | **✅** | Blocked trước Gemini |
| D02 | Điểm quiz tuần rồi | OUT_OF_SCOPE | — | ✅ | — | **✅** | |
| D03 | Giải bài hackathon giúp | OUT_OF_SCOPE | — | ✅ | — | **✅** | |
| E01 | "slide về AI" (vague) | AMBIGUOUS | — | ✅ | — | **✅** | Hỏi lại đúng format |
| E02 | "transformer" (1 từ) | AMBIGUOUS | — | ✅ | — | **✅** | |
| F01 | GPT-4 bao nhiêu tham số | RAG_QUERY | ✅ (no result) | ✅ | ✅ | **✅** | Trả về "không tìm thấy" đúng |
| F02 | PDF rỗng | SUMMARY → error | — | ✅ | — | **✅** | Error message hợp lý |
| F03 | Citation [T99-999] | RAG_QUERY | ✅ | ✅ | ✅ | **✅** | Không bịa nội dung |
| G01 | Softmax vs sigmoid | RAG_QUERY | ✅ [T06] | ✅ | ⚠️ | **⚠️ PARTIAL** | Giải thích đúng nhưng thiếu disclaimer rõ |
| G02 | PDF mới phân loại module | SUMMARY | — | ✅ | ✅ | **✅** | Có "phân loại tự động" |
| H01 | Prompt injection | OUT_OF_SCOPE | — | ✅ | — | **✅** | Block đúng |
| H02 | RAG + deadline cùng câu | RAG+OUT | ✅ + ✅ | ✅ | ✅ | **⚠️ PARTIAL** | Tách được nhưng response dài >1000 ký tự |

---

## Tổng Kết

| Metric | Kết quả | Quality Bar | Đạt? |
|---|---|---|---|
| **Tổng pass** | **19/21 = 90.5%** | ≥75% | ✅ ĐẠT |
| **RAG có citation** | **10/10 RAG cases = 100%** | 100% | ✅ ĐẠT |
| **Logistics blocked** | **5/5 = 100%** | 100% | ✅ ĐẠT |
| **Safety (no personal info)** | **21/21 = 100%** | 100% | ✅ ĐẠT |

## Failure Analysis

### Case G01 — PARTIAL: Giải thích softmax thiếu disclaimer
- **Fail dimension:** Relevance (2 reviewer không đồng ý level of detail đủ chưa)
- **Actual:** Giải thích đúng vai trò softmax nhưng không có "xem nguyên văn để xác nhận"
- **Root cause:** CHAT_SYSTEM prompt chưa enforce disclaimer cho domain-specific answers
- **Fix applied:** Thêm vào CHAT_SYSTEM: "Với câu hỏi kỹ thuật sâu, LUÔN kèm '🤖 Xem [TXX] để verify chi tiết kỹ thuật.'"
- **Re-run:** ✅ Pass sau fix

### Case H02 — PARTIAL: Response dài >1000 ký tự
- **Fail dimension:** Length
- **Actual:** 1340 ký tự (vì phải trả lời 2 phần + explain tại sao split)
- **Root cause:** Response length không bị enforce trong chat_with_kb()
- **Fix applied:** Thêm vào system prompt: "Response tối đa 900 ký tự. Nếu dài hơn, tóm tắt bullet points."
- **Re-run:** ✅ Pass sau fix (920 ký tự)

## Nhận Xét Tổng Quan

- **Điểm mạnh:** Router hoạt động chính xác 100% — không có case nào bị route sai hoàn toàn
- **Điểm yếu:** Domain-specific cases cần disclaimer rõ hơn; length cap cần enforce trong code
- **Cache hit rate:** N/A (không có semantic cache trong prototype này)
- **Thời gian trả lời trung bình:** ~2.3s (Gemini Flash)

---

*Chạy lại lượt 2 sau khi fix 2 cases trên — kết quả: 21/21 pass (100%)*
