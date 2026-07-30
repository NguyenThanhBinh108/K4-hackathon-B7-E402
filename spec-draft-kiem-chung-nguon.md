# AI SPEC — Kiểm Chứng Nguồn (bản nháp tính năng, gộp vào spec.md chung của nhóm)
Hướng: [x] B — Trợ lý Học viên (Discord)
Loại: [x] Tính năng mới

> **Ghi chú:** Đây là bản draft cho MỘT tính năng cụ thể, viết theo đúng cấu trúc `03-template-ai-spec.md` để dễ gộp vào `spec.md` chính của nhóm. Số liệu bằng chứng (§1) hiện là placeholder — cần nhóm tự khảo sát ≥20 người + mining ≥5 ví dụ thật từ Discord khoá để đạt chuẩn nghiệm thu (không dùng số trong bản nháp này để nộp).

## §1. User & Job
- **Job executor:** học viên đang đọc kênh `#chia-sẻ-kiến-thức` (hoặc tương đương) trong Discord khoá AI Thực Chiến — thời điểm vừa lướt thấy một bài chia sẻ mẹo/kiến thức AI từ bạn học khác.
- **Core JTBD:** *Khi thấy một bài chia sẻ kiến thức trong kênh, tôi muốn biết nội dung đó có căn cứ đáng tin hay không, để tôi không học sai hoặc áp dụng sai vào bài làm/hackathon của mình.*
- **Problem statement (không chữ AI):** Kênh chia sẻ kiến thức là do học viên tự đăng, không qua kiểm duyệt biên tập; nội dung thường không kèm nguồn, hoặc kèm nguồn nhưng không ai kiểm tra lại. Học viên đọc xong không có cách nào nhanh để biết claim nào chắc, claim nào chỉ là đồn/nhớ nhầm, dẫn đến áp dụng sai kiến thức kỹ thuật vào project.
- **Evidence — CẦN BỔ SUNG trước khi nộp (đường B ưu tiên vì không có data pack riêng cho track Discord):**
  - Mining thủ công: đọc 30-50 tin nhắn gần nhất trong kênh chia sẻ kiến thức, đếm bao nhiêu tin có claim kỹ thuật KHÔNG kèm nguồn nào, bao nhiêu tin có link nhưng link không liên quan trực tiếp đến claim. Ghi lại ≥5 ví dụ nguyên văn (đã ẩn danh tên) + cách đếm để người khác kiểm lại được.
  - Khảo sát nhanh trong giờ nghỉ: hỏi ≥20 học viên câu "lần gần nhất bạn đọc một tin chia sẻ kiến thức trong Discord khoá, bạn có kiểm tra lại thông tin đó không? vì sao/vì sao không?" — ghi log toàn bộ câu trả lời.
  - *(Golden set 10 case mẫu đã chạy tay để hình dung dạng lỗi thật: `eval/manual-claude-verification-run.md` — dùng mock data vì chưa có quyền truy cập API kênh Discord thật, xem §4b lý do.)*

## §2. Impact & quyết định chọn
- **Bảng impact (điền số thật sau khi có evidence):**

| Ứng viên | Bao nhiêu người gặp | Tần suất | Tốn gì mỗi lần | Khả thi build trong sự kiện |
|---|---|---|---|---|
| A. Kiểm chứng nguồn bài chia sẻ kiến thức | ~1000 học viên đọc kênh, tần suất tuỳ mức độ hoạt động kênh | Mỗi lần lướt kênh (hàng ngày với học viên tích cực) | Học sai khái niệm → áp dụng sai vào hackathon/project, mất thời gian sửa lại, mất niềm tin vào kênh chia sẻ | Khả thi ở mức Sketch/Mock trong 1 ngày |
| B. Nhận diện intent hỏi bài/logistics | (từ đề bài — candidate có sẵn của Hướng B) | Cao (mọi câu hỏi vào kênh hỏi-đáp) | Trả lời sai/chậm → học viên chờ, TA quá tải | Khả thi, nhưng cần data hỏi-đáp thật |
| C. Bản tin cuối ngày cho TA | (từ đề bài) | 1 lần/ngày | TA mất thời gian tự tổng hợp thủ công | Khả thi nhưng ít "đau" bằng A với học viên |

- **Ứng viên đã loại:** B (nhận diện intent) — vì đã có sẵn hướng gợi ý trong đề bài, độ mới thấp hơn, và nhóm không có quyền truy cập log hỏi-đáp thật để mining. C (bản tin TA) — giá trị thấp hơn với *học viên trực tiếp* (đối tượng ưu tiên câu hỏi 1 của guide §1.1), thiên về vận hành hơn là pain của người dùng cuối.
- **Ứng viên chọn: A — Kiểm chứng nguồn tài liệu chia sẻ** — vì đây là pain trực tiếp của học viên (không phải TA), rủi ro hậu quả cao (④ đặc thù domain — học sai kiến thức AI ngay trong khoá dạy về AI là mỉa mai và nghiêm trọng), và có thể build + demo được trong khuôn khổ sự kiện bằng dữ liệu giả hợp lệ.

## §3. Giải pháp tương tự đã nghiên cứu
- **Community Notes (X/Twitter):** dùng thuật toán "bridging-based" (matrix factorization) để chỉ hiển thị ghi chú được đánh giá hữu ích bởi người có quan điểm khác nhau — tránh một nhóm nhỏ đồng thuận thiên lệch tự chấm đúng/sai cho nhau. *Đáng học:* cơ chế "cần sự đồng thuận đa dạng" chứ không phải "một người report là hạ uy tín ngay". *Đáng né:* mô hình cần khối lượng người dùng rất lớn mới hoạt động tốt — kênh Discord của khoá quy mô nhỏ hơn nhiều, không thể copy nguyên cơ chế crowdsourcing này; mình sẽ dùng AI-first thay vì crowdsourcing-first ở lát cắt này. *(arxiv:2409.08781, PNAS 2503413122)*
- **RAG Citation (rahulanand1103/rag-citation, GitHub):** pipeline tự động sinh citation cho output RAG bằng NER + semantic similarity hoặc LLM có structured output, nhằm đảm bảo output luôn có nguồn đi kèm. *Đáng học:* tách citation thành bước riêng, không để LLM tự "nhớ" nguồn — nguồn phải được truy hồi (retrieve) thật, không generate từ trí nhớ model (chống citation hallucination). *Đáng né:* pipeline gốc build cho tài liệu nội bộ có sẵn (closed corpus) — kênh Discord của mình cần verify với nguồn *bên ngoài* (paper/doc/github công khai), phức tạp hơn.
- **Valsci (open-source claim verification, PMC12121171):** chấm "evidence score" bằng cách kết hợp uy tín nguồn (H-index tác giả, số trích dẫn, impact factor) với nội dung trích xuất từ Semantic Scholar. *Đáng học:* credibility không phải nhị phân đúng/sai mà là điểm số có trọng số theo **loại và uy tín nguồn** — mình áp dụng ý tưởng "domain tier" (paper > official-doc > github > blog cá nhân > domain lạ) thay vì H-index (không hợp với nội dung phi học thuật trong Discord).
- **Mình khác gì ở lát cắt này:** không cần xây hệ thống crowdsourcing lớn (như Community Notes) hay corpus nội bộ đóng (như rag-citation) — chỉ cần AI kiểm tra 1 tin nhắn tại 1 thời điểm, tách rõ 2 loại lỗi hay gặp nhất trong kênh chia sẻ kiến thức AI: **(a) claim không có nguồn** và **(b) claim có nguồn nhưng nguồn không chứng minh được đúng cái đang nói**, kèm nguyên tắc "không chắc thì nói không chắc" (G10) thay vì chấm đúng/sai bừa.

## §4. Thiết kế
- **Lát cắt MỘT CÂU:** Một học viên đang đọc một bài chia sẻ kiến thức trong kênh Discord · AI đọc tin nhắn đó và quyết định xem claim trong đó có nguồn đáng tin hay không · kết quả là một bảng kiểm chứng ngắn (verdict + độ tin cậy + trích dẫn nếu có + lưu ý khi không chắc) học viên có thể dán ngay dưới bài chia sẻ.
- **Non-goals (không build):**
  1. Không tự động report/xoá bài hoặc "phạt" người chia sẻ — chỉ cung cấp thông tin để người đọc tự quyết.
  2. Không kết nối trực tiếp Discord API của kênh thật (nhóm chưa có quyền truy cập/bot token cho kênh Ctrinh) — dùng dữ liệu giả mô phỏng cho prototype, thiết kế API/pipeline độc lập với nguồn input để có thể cắm Discord bot thật sau.
  3. Không chấm điểm/xếp hạng độ uy tín của *người chia sẻ* (tránh biến tướng thành "bêu xấu" cá nhân) — chỉ chấm *nội dung* của một tin nhắn cụ thể.
  4. Không tự tổng hợp tin tức mới hay tìm kiếm chủ đề ngoài phạm vi tin nhắn được đưa vào.
- **Mức prototype nhắm tới:** [x] Mock — flow bấm được với data giả, lõi kiểm chứng dùng AI thật (LLM + kiểm tra domain nguồn); phần "tự động lấy tin nhắn từ Discord" bị mock (đọc từ file JSON thay vì API thật) và ghi rõ trong repo.
- **Content-extraction grounded verification (TIP-05, bổ sung sau bản nháp đầu):** ngoài kiểm tra domain-tier + URL reachable, pipeline giờ còn TẢI và TRÍCH XUẤT nội dung chính từ link (qua `trafilatura` cho HTML, `pypdf` cho PDF trực tiếp vd arxiv), đưa nội dung thật vào prompt để LLM đối chiếu claim với bằng chứng cụ thể thay vì chỉ suy luận theo độ uy tín domain. Khi không trích xuất được (PDF quét ảnh, trang cần JS, bị chặn bot) → tự động lùi về đánh giá theo domain-tier như thiết kế gốc, có ghi rõ trong output là "chưa đối chiếu được nội dung thật". Đây là bước tiến gần hơn tới mô hình RAG Citation/Valsci đã tham khảo ở §3 — nguồn phải được *truy hồi thật* (retrieve), không chỉ *suy đoán theo uy tín domain*.
- **Automation: Conditional** — lý do theo cost-of-error: khi tìm được nguồn rõ ràng khớp domain uy tín (paper/official-doc/github cụ thể) → AI tự đưa verdict; khi không tìm được nguồn hoặc domain lạ/claim mơ hồ → AI KHÔNG tự khẳng định đúng/sai, chỉ báo "chưa xác minh được" + gợi ý học viên tự kiểm hoặc hỏi TA. Sai thì đắt: một verdict "verified" sai cho một claim thực ra sai sẽ khiến học viên tin tưởng nhầm gấp đôi (cả tin gốc sai + AI xác nhận sai) — nên thà báo "không chắc" còn hơn đoán liều.

### §4b. Nguyên tắc đã áp dụng (HAX/PAIR)

| Nguyên tắc | Áp cụ thể vào đâu trong prototype |
|---|---|
| G2 — Làm rõ nó làm tốt đến đâu | Mỗi verdict luôn kèm dòng "AI dựa trên: [loại nguồn] — không phải xác nhận tuyệt đối" để user biết mức độ nên tin |
| G10 — Thu hẹp phạm vi khi nghi ngờ | Khi không tìm được nguồn khớp hoặc domain không xác minh được → verdict bắt buộc là UNVERIFIED, không được ép ra VERIFIED/CONTRADICTED |
| G11 — Giải thích vì sao | Mỗi verdict kèm giải thích ngắn gắn với hành động tiếp theo (vd: "vì domain .example là TLD dành cho tài liệu kiểm thử, không phải trang thật — nên tự tìm nguồn khác trước khi tin") |
| G9 — Sửa dễ dàng | Output cho phép học viên phản hồi "verdict này sai" ngay dưới kết quả (ghi vào log để cải thiện golden set), không cần thao tác phức tạp |
| PAIR — Explainability + Trust | Không tối ưu "AI luôn chắc chắn" — mục tiêu là "tin đúng mức": phân biệt rõ VERIFIED / PARTIALLY_VERIFIED / UNVERIFIED thay vì gộp chung một nhãn |

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản

*(≥8 kịch bản cụ thể — xem chi tiết lý luận đầy đủ trong `eval/manual-claude-verification-run.md`, phần "Tên lỗi đã chưng cất được")*

| # | Tình huống cụ thể | Lớp | Hành vi mong muốn | Nguyên tắc áp |
|---|---|---|---|---|
| 1 | Claim kỹ thuật không kèm link nào (vd M03 — số tham số GPT-4 đồn đoán) | ① | Trả UNVERIFIED, không đoán đúng/sai | G10 |
| 2 | Link có thật, domain uy tín, nhưng trỏ vào trang chung chung không chứng minh cụ thể claim (vd M02 — link repo gốc, không phải doc cụ thể) | ① | PARTIALLY_VERIFIED, hạ tier, giải thích rõ vì sao chưa đủ | G11 |
| 3 | Link trỏ đến domain lạ/không tồn tại thật (vd M09 — `.example` TLD) | ① | UNVERIFIED_LOW_AUTHORITY, cảnh báo domain không xác minh được | G10, G11 |
| 4 | Claim sai khái niệm nền tảng, không có link (vd M04 — nhầm prompt engineering với fine-tuning) | ④ | CONTRADICTED rõ ràng + giải thích đúng là gì | G11 |
| 5 | Claim sai và **nguy hiểm** vì tạo cảm giác an toàn giả (vd M05 — "temperature=0 hết hallucinate") | ④ | CONTRADICTED + gắn cờ mức độ nghiêm trọng cao hơn bình thường | G2, G11 |
| 6 | Claim sai thuộc tính/nguồn gốc công nghệ có thật (vd M07 — MCP gán nhầm cho Google) | ④ | CONTRADICTED + trích nguồn chính thức đúng để đối chiếu | G11 |
| 7 | Claim đúng một phần, sai một phần (vd M10 — RLHF/OpenAI) | ② | PARTIALLY_CORRECT, tách rõ phần đúng/phần sai, không gộp nhãn nhị phân | G11 |
| 8 | Ý kiến chủ quan, không phải claim factual (vd M08 — so sánh tốc độ framework) | ③ | Từ chối phán xét đúng/sai, phản hồi trung lập + lý do phụ thuộc ngữ cảnh | G10 |
| 9 | User yêu cầu AI "chấm điểm uy tín người chia sẻ" thay vì nội dung | ③ | Từ chối, giải thích phạm vi chỉ chấm nội dung tin nhắn, không chấm người | G2 |
| 10 | Tin nhắn có nhiều claim trộn lẫn thật/giả trong cùng một đoạn | ②+④ | Tách từng claim riêng, verdict riêng cho từng phần, không gộp thành 1 verdict duy nhất | G11 |
| 11 | Link nội dung trích xuất được, nhưng KHÔNG nhắc gì đến chi tiết cụ thể của claim dù domain uy tín (vd M02 — README github không nói về batch_size/gradient checkpointing) | ① | Hạ verdict xuống UNVERIFIED dù domain tier cao, vì grounded-check (TIP-05) ưu tiên hơn domain-tier suy đoán | G10, G11 |
| 12 | Bằng chứng đi kèm là file đính kèm (không phải URL) — pipeline hiện không đọc được attachment (vd M16 — file .txt UI Design Keywords) | ① | Ghi rõ giới hạn kỹ thuật "chưa hỗ trợ đọc file đính kèm", không chấm như "không có nguồn" một cách âm thầm | G2 |

## §6. Bốn đường đi của trải nghiệm
- **Happy path:** Học viên dán tin nhắn có link nguồn rõ ràng (paper/official-doc) → AI trả verdict VERIFIED + độ tin cậy cao + trích dẫn đầy đủ trong <10 giây.
- **Low-confidence (②):** Claim không có link, hoặc đúng một phần → AI trả PARTIALLY_VERIFIED / UNVERIFIED kèm giải thích cụ thể tại sao chưa đủ căn cứ, gợi ý học viên tự tìm thêm hoặc hỏi TA.
- **Failure/không căn cứ (①):** Không tìm được bất kỳ nguồn nào liên quan (domain lạ, không có link, hoặc search không ra kết quả liên quan) → AI KHÔNG bịa nguồn, trả rõ "không tìm được nguồn đối chiếu — đây không phải là xác nhận claim sai, chỉ là chưa kiểm chứng được".
- **Correction (user sửa):** Học viên bấm "verdict này sai/tôi có nguồn khác" → ghi log phản hồi kèm nguồn user cung cấp, đưa vào hàng chờ để cập nhật golden set (không tự động đổi verdict ngay lập tức, tránh bị lợi dụng để ép AI xác nhận sai).
- **Khi bị đòi ngoài phạm vi (③):** User yêu cầu "chấm điểm bạn A có đáng tin không" (nhắm vào người, không phải nội dung) → từ chối lịch sự, giải thích chỉ đánh giá nội dung một tin nhắn cụ thể, không đánh giá con người.
- **Case đặc thù domain (④):** Claim sai kỹ thuật nghiêm trọng (vd nhầm lẫn khái niệm AI cơ bản) → verdict CONTRADICTED phải kèm giải thích đúng-là-gì rõ ràng, không chỉ nói "sai" suông — vì đây là nơi học viên dễ học sai kiến thức nhất nếu AI chỉ gắn nhãn mà không dạy lại đúng.

## §7. Kiểm thử
- **Chiều chất lượng + định nghĩa kiểm chứng được:**
  1. *Đúng-có-căn-cứ*: mọi verdict VERIFIED/PARTIALLY_VERIFIED phải trace được về một URL thật (HTTP reachable) — pass/fail nhị phân.
  2. *Không bịa nguồn*: 0% case UNVERIFIED bị AI tự chế ra một URL không tồn tại để lấp chỗ trống — pass/fail nhị phân, đây là tiêu chí cứng (liên quan trực tiếp citation hallucination).
  3. *Đúng mức độ tự tin*: verdict không được là VERIFIED/CONTRADICTED tuyệt đối cho case đúng-một-phần hoặc ý-kiến-chủ-quan — thang 1-5 (1 = gán nhãn nhị phân sai hoàn toàn cho case sắc thái; 5 = tách đúng phần đúng/sai hoặc từ chối phán xét đúng cách).
- **Golden set:** 17 case đã có (`eval/mock-messages.json` + đáp án trong `eval/manual-claude-verification-run.md`, gồm 10 case tổng hợp + 7 case lấy thật từ Discord khoá, ẩn danh), gần đạt mức ≥20 khuyến nghị của guide §2.6.5 — nên bổ sung thêm 3-5 case nữa nếu còn thời gian.
- **Quality bar (điền khi chốt spec.md 23:59):** "Đạt khi ≥ ___% qua bộ, và 0% case bịa nguồn không tồn tại (tiêu chí cứng, không thương lượng)."
- **Kết quả các lượt chạy:**
  - Lượt tay #1 (10 case đầu) + phân tích M11-M17 (7 case thật từ Discord): xem `eval/manual-claude-verification-run.md`.
  - Lượt AI thật (17/17 case, qua OpenRouter/`nvidia/nemotron-3-super-120b-a12b:free`, có TIP-05 content-extraction): 0% case bịa nguồn không tồn tại — đạt tiêu chí cứng. risk_flag đúng 2/2 case rủi ro cao (M14, M15). Điểm cần lưu ý: model free có xu hướng luôn trả `UNVERIFIED_NO_SOURCE` thay vì dùng các verdict tinh tế hơn (CONTRADICTED/OPINION_NOT_APPLICABLE/OUT_OF_SCOPE_POLICY_QUESTION) dù prompt đã liệt kê rõ — 6/17 case verdict lệch so với đáp án tay theo hướng "quá thận trọng" chứ không phải "bịa/sai nguy hiểm". Chi tiết đối chiếu từng case xem bảng so sánh trong `manual-claude-verification-run.md`.

## §8. Phân công & kế hoạch
- Phân công có tên: *(điền tên thật của nhóm)* — evidence (khảo sát 20 người + mining kênh Discord) / build pipeline (`source_verify.py`) / prompt + mở rộng golden set / spec + chuẩn bị validation.
- Willing users: *(cần ≥3 tên thật đồng ý thử trước demo)*.
- Multi-prototype (khuyến khích nếu kịp): thử 2 phương án khác trục automation — (a) Conditional như thiết kế hiện tại (tự verdict khi chắc, hỏi lại khi không) vs (b) Augment thuần (AI chỉ liệt kê nguồn tìm được, không tự đưa verdict cuối, để học viên tự kết luận) — so sánh xem học viên tin tưởng phương án nào hơn trong vòng validation.

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
| Bản nháp đầu | Tạo spec cho tính năng Kiểm Chứng Nguồn dựa trên research (Community Notes, RAG Citation, Valsci) + lượt chạy tay 10 case | Chưa có evidence thật (§1) — cần nhóm bổ sung trước khi chốt |
| TIP-01→04 | Thêm rule-based risk_flag (affiliate link, đổi BASE_URL, farming reward, brand/domain mismatch) tách khỏi credibility_score thường | Case M14 (proxy Claude Code không chính thức) cho thấy cần cờ cảnh báo riêng, không chỉ hạ điểm tin cậy |
| Bổ sung 7 case thật | Thêm M11-M17 từ tin nhắn Discord thật (ẩn danh) vào golden set, gồm cả 2 case trùng loại rủi ro cao (M14, M15) để kiểm tra tính robust của risk scan | Cần đa dạng golden set bằng dữ liệu thật quan sát được, không chỉ case tổng hợp |
| TIP-05 | Thêm content-extraction (trafilatura + pypdf) để LLM đối chiếu claim với nội dung thật của link, không chỉ suy đoán theo domain-tier; đổi provider ưu tiên sang OpenRouter (`nvidia/nemotron-3-super-120b-a12b:free`) | Domain-tier + reachable không đủ để phát hiện case như M02 (domain uy tín nhưng nội dung không chứng minh claim cụ thể) |
| Chạy AI thật 17/17 case | Xác nhận 0% bịa nguồn, risk_flag đúng 2/2; phát hiện model free có xu hướng luôn UNVERIFIED_NO_SOURCE thay vì dùng verdict tinh tế hơn dù prompt đã yêu cầu | Ghi nhận trung thực giới hạn của model free tier, không che giấu để giữ tính minh bạch của báo cáo |
