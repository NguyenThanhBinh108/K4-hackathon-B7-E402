# AI SPEC — Trợ lý tra cứu khoá · Nhóm [XX] · Zone [X]

Hướng: [ ] A — VLearn · **[x] B — Trợ lý Học viên** · [ ] C — Làn mở
Loại: [ ] Tối ưu tính năng có sẵn · **[x] Tính năng mới**

> Trạng thái file: khung đã dựng ở CP2. **§1, §2 chờ số từ khảo sát** · **§7 kết quả chờ CP3** · hạn cứng commit bản đầy đủ **23:59 ngày 1**.

---

## §1. User & Job

- **Job executor:** Học viên K4 đang cần tra lại một thông tin đã từng có trong khoá — *không phải* "học viên nói chung".
- **Core JTBD:** *Tìm lại một thông tin đã tồn tại trong khoá, đủ tin để hành động theo, trong lúc đang làm bài.*
  *(Tự kiểm: bỏ AI đi, việc này vẫn tồn tại ✓)*
- **Job story:** Khi tôi sắp nộp bài lúc gần nửa đêm và không nhớ hạn chính xác, tôi muốn tra lại nhanh mà không phải đánh thức TA, để tôi nộp đúng hạn thay vì đoán.
- **Problem statement (KHÔNG chữ AI):** Thông tin của khoá nằm rải rác qua nhiều kênh và nhiều ngày; học viên cần tra lại thì phải cuộn tay hoặc hỏi lại, và thứ tìm được không biết còn hiệu lực không — hậu quả là nộp sai hạn, dùng link đã đóng, hoặc chiếm thời gian TA cho câu đã trả lời rồi.

### Evidence

- **Chuẩn A — khảo sát:** n = `[ĐIỀN]` người ngoài nhóm · xác nhận `[ĐIỀN]%` *(cần ≥50%)*
  - Định nghĩa "xác nhận" chốt trước khi phát form: **Câu 7 ≥1 lần/tuần VÀ (Câu 4 ≥5 phút HOẶC Câu 5 ∈ {không chắc bản mới nhất, phải hỏi người khác, dùng nhầm thông tin sai})**
  - Log đầy đủ: `validation/khao-sat-log.md`
- **Chuẩn B — mining:** `[ĐIỀN]` — số đếm được trên Discord khoá + phương pháp đếm
- **≥5 quote nguyên văn:** `[ĐIỀN từ ô "kể ngắn" của form]`

---

## §2. Impact & quyết định chọn

| Ứng viên | Bao nhiêu người | Tần suất | Mỗi lần tốn gì | Đo được? | Build nổi? | Chọn? |
|---|---|---|---|---|---|---|
| **U1 · Hỏi–đáp có trích nguồn** | `[ĐIỀN]` | `[ĐIỀN]` | `[ĐIỀN]` phút + rủi ro nộp sai hạn | ✅ nhãn vàng rõ | ✅ | **✅ CHỌN** |
| U2 · Bản tin cuối ngày cho TA | ~`[số TA]` | 1/ngày | 15–30' rà kênh | ⚠️ "tóm tắt tốt" không có nhãn vàng | ✅ | ❌ |
| U3 · Daily/Weekly summary cho học viên | `[ĐIỀN]` | 1/ngày | ~10' đọc bù | ❌ | ✅ | ❌ |
| U4 · Báo có tài liệu mới | `[ĐIỀN]` | vài lần/tuần | ~2' | ✅ nhưng gần như không cần AI | ✅ | ❌ |

**Ứng viên đã loại + vì sao:**
- **U2, U3** — quyết định AI là *tóm tắt*, không có nhãn vàng: hai người chấm ra hai kết quả, không đặt được quality bar bằng số.
- **U4** — không có quyết định AI nào ở giữa; một webhook làm được, không thoả yêu cầu "AI thật ở quyết định trung tâm".
- **Knowledge extraction / ingestion** — là hạ tầng, không phải tính năng user nhìn thấy → gộp vào U1.

**Vì sao chọn U1 (bằng số):** `[ĐIỀN]`/20 người xác nhận · `[ĐIỀN]`% chọn U1 là thứ muốn có nhất (câu 10) · `[ĐIỀN]`% nói chỉ dám hành động khi thấy nguồn gốc kèm thời gian (câu 8) · cost-of-error cao nhất trong 4 ứng viên.

---

## §3. Giải pháp tương tự đã nghiên cứu

| Sản phẩm | Flow của họ | Đáng học | Đáng né | Mình khác gì |
|---|---|---|---|---|
| NotebookLM | `[ĐIỀN]` | Trích dẫn nằm cạnh câu trả lời, bấm mở được | `[ĐIỀN]` | Mình có **tầng nguồn**, không phải nguồn nào cũng ngang nhau |
| ChatGPT study mode | `[ĐIỀN]` | `[ĐIỀN]` | Luôn cố trả lời, không biết nói "không có căn cứ" | Mình từ chối và chuyển TA khi không có T1/T2 |
| `[thành viên 3 điền]` | | | | |

---

## §4. Thiết kế

**Lát cắt MỘT CÂU:**
> Khi học viên K4 hỏi một câu tra cứu trong kênh Discord của khoá, trợ lý quyết định câu đó có đủ căn cứ trong nguồn chính thức hay không, rồi trả lời kèm trích dẫn có ghi rõ tầng nguồn — hoặc chuyển TA thay vì đoán.

**Non-goals (KHÔNG build):**
1. Không tóm tắt hội thoại theo ngày/tuần.
2. Không sinh FAQ tự động.
3. Không dạy kiến thức mới ngoài nguồn — chỉ tra cứu và trích dẫn, không giảng bài, không giải bài tập.
4. Không chủ động nhắn tin cho học viên — chỉ trả lời khi được hỏi.
5. Không đọc/ghi tin nhắn Discord thật của người thật — corpus là data giả tự sinh.

**Mức prototype: Mock.** Thật: giao diện, corpus, truy hồi, trace, feedback. Mock: quyết định `decide()` ở CP2 (thay bằng AI thật ở CP3), và thao tác chuyển TA (ghi log, không gửi đi đâu).

**Automation: Conditional.**
> Trợ lý tự trả lời khi có căn cứ trực tiếp trong T1/T2; mọi trường hợp còn lại chuyển TA. Lý do: hai loại lỗi có giá rất khác nhau. **Lỗi bịa** (trả lời sai hạn nộp, sai link) do học viên gánh, phát hiện muộn — lúc phát hiện thì đã nộp muộn, không sửa được, và mất luôn niềm tin. **Lỗi thận trọng thừa** (chuyển TA một câu đáng ra trả lời được) do TA gánh, tốn ~30 giây, sửa được ngay. Vì chi phí lệch hẳn về một phía, ngưỡng đặt nghiêng về HANDOFF và chấp nhận tỷ lệ tự trả lời thấp hơn.

### §4b. Nguyên tắc đã áp dụng

| Nguyên tắc | Áp cụ thể vào đâu trong prototype |
|---|---|
| **G1** — làm rõ hệ thống làm được gì | Placeholder ô nhập + dòng dưới composer: "Mình không duyệt gia hạn, không chấm điểm, không đưa đáp án" |
| **G2** — làm rõ nó làm tốt đến đâu | Chip nguồn `T1 · T1-04 · 29/07` dưới mỗi câu trả lời; T3 luôn kèm dải "chỉ tham khảo, không chốt" |
| **G10** — thu hẹp phạm vi khi nghi ngờ | Nhánh `CLARIFY` và `HANDOFF` trong `decide()`; ngưỡng nghiêng về HANDOFF |
| **G11** — giải thích vì sao | Ô gập "Xem cách mình quyết định": nhánh đã chọn + luật đã bắn + 3 ứng viên kèm điểm |
| **G9** — sửa dễ dàng | Nút "✏️ Chưa đúng ý?" mở ô sửa ngay dưới câu trả lời |
| **G15** — mời feedback chi tiết | 👎 mở 3 lý do: *sai thông tin · thiếu nguồn · không đúng câu mình hỏi* → ghi vào trace |

---

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản

| # | Tình huống cụ thể | Lớp | Hành vi mong muốn | Nguyên tắc |
|---|---|---|---|---|
| 1 | Hỏi một mốc thời gian không có trong nguồn nào | ① | Nói thẳng không tìm thấy, không suy đoán, hiện phiếu chuyển TA kèm câu hỏi tóm tắt | G10, G11 |
| 2 | Hỏi nội dung có trong T2 | ① | Trả lời ≤4 câu + chip mã đoạn mở ra xem được | G2, G11 |
| 3 | Hỏi link nộp bài — nguồn có bản cũ (đã đóng) và bản mới | ②④ | Dùng bản mới, nêu rõ có thông báo cũ hơn nói khác | G10 |
| 4 | "deadline khi nào" — không rõ mốc nào | ② | Hỏi lại đúng một câu + 3 nút bấm | G10, G9 |
| 5 | "Cho mình xin gia hạn thêm 1 ngày" | ③ | Từ chối vì ngoài thẩm quyền, chỉ sang người/kênh xử lý được | G1, G10 |
| 6 | "Điểm nhóm 3 bao nhiêu / nhóm nào dẫn đầu" | ③ | Từ chối, nêu lý do phạm vi | G1 |
| 7 | Trong chat có học viên nói sai giờ CP3, thông báo chính thức nói khác | ①④ | Trả lời theo T1, hiện tin nhắn T4 và nói rõ **không dùng chat làm căn cứ** | G2, G11 |
| 8 | Gõ không dấu, viết tắt: "spec nop luc may h dc a" | ②④ | Vẫn hiểu, trả lời đúng, giọng ngang hàng | G5 |
| 9 | Học viên nói "sai rồi, cái đó của K3" | ④ | Nhận sai, mở ô sửa, chạy lại; vẫn không có căn cứ thì chuyển TA | G9, G15 |
| 10 | Cùng một câu hỏi 5 người hỏi trong 1 giờ | ④ | Trả lời nhất quán y hệt nhau | G12 |
| 11 | Câu cụt "hii", "alo", emoji | ② | Không đoán ý; hỏi lại hoặc nói rõ phạm vi | G1, G10 |

*Kịch bản nhóm sợ nhất khi demo: **#7** và **#1** → chọn đúng hai case này để demo live.*

---

## §6. Bốn đường đi của trải nghiệm

- **Happy path:** kịch bản #2 — trả lời + chip nguồn bấm mở được.
- **Low-confidence ②:** kịch bản #4 — hỏi lại một câu + 3 nút, không trả lời bừa.
- **Failure / không căn cứ ①:** kịch bản #1 — từ chối thẳng + phiếu chuyển TA đã kèm tóm tắt câu hỏi.
- **Correction:** kịch bản #9 — nút "Chưa đúng ý?" giữ nguyên bối cảnh, gửi lại.
- **Ngoài phạm vi ③:** kịch bản #5, #6 — từ chối nêu lý do, chỉ sang chỗ giải quyết được.
- **Đặc thù domain ④:** kịch bản #3, #7 — ưu tiên bản mới / tầng cao hơn, nói rõ có nguồn nói khác.

---

## §7. Kiểm thử

Chi tiết trong `eval/README.md`.

- **Ba chiều:** C1 có căn cứ (pass/fail) · C2 định tuyến đúng (pass/fail) · C3 đúng cỡ đúng giọng (1/3/5).
- **Golden set:** 24 case — `eval/golden-set.csv`.
- **Quality bar (chốt 23:59 ngày 1, không sửa sau đó):**
  > **Đạt khi ≥80% case pass cả C1 và C2, C3 trung bình ≥3,5 — VÀ điều kiện cứng: 0 case lớp ① mà trợ lý trả lời khẳng định khi không có căn cứ trong T1/T2.**
- **Kết quả các lượt chạy:** `[ĐIỀN sau CP3]`

| Lượt | Thời điểm | C1 | C2 | C3 tb | Đạt bar? | Failure đau nhất |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |

---

## §8. Phân công & kế hoạch

- **Phân công:** xem bảng trong `README.md` (mỗi người sở hữu một tầng nguồn + case golden set của tầng đó).
- **Willing users (≥3 tên):** `[ĐIỀN từ phần cuối form khảo sát]`
- **Kế hoạch validation CP5:** 5 phiên × 10 phút. Giao task thật → **im lặng quan sát** → hỏi đúng 3 câu: *"Điều gì khó hiểu hoặc khó chịu nhất?"* · *"Kết quả này bạn có tin không — vì sao?"* · *"Bạn có dùng thật không — vì sao chưa?"* → log nguyên văn vào `validation/`.
- **Multi-prototype:** trục khác biệt cân nhắc — *khi không chắc thì hỏi lại (CLARIFY) hay trả lời kèm cảnh báo*. Dữ liệu quyết định: câu 9 của form khảo sát. `[ĐIỀN lựa chọn + lý do]`

---

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
|---|---|---|
| CP2 | Gộp 3 role của nhóm thành 4 tầng nguồn của một lát cắt duy nhất | 3 role đang là 3 sản phẩm nhỏ, vi phạm format lát cắt MỘT CÂU |
| CP2 | Bỏ "AI chấm điểm độ tin cậy", đổi thành luật tầng nguồn cứng | Điểm tin cậy do AI sinh không kiểm chứng được → không đặt được nhãn vàng cho C2 |
