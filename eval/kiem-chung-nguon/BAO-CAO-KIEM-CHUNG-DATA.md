# Báo cáo kiểm chứng dữ liệu — tính năng Kiểm Chứng Nguồn

> Đo trên data pack thật, ngày 30/07/2026. Mọi con số dưới đây chạy lại được bằng
> các script trong thư mục này. Không có con số nào là ước lượng.

---

## 1. Chatlog VLearn — `chat_history_anonymized_for_hackathon.csv`

| Chỉ số | Giá trị |
|---|---|
| Tổng dòng | 2.522 (1.261 student + 1.261 tutor) |
| Độ dài tin nhắn học viên | trung vị **97** ký tự · p90 294 · max 1.484 |
| Có tiền tố `(Trang N, đoạn được chọn: "...")` | **1.252/1.261 = 99,3%** |
| Gõ **không dấu** | **151/1.261 = 12,0%** |
| Tin nhắn **có link** | **0/1.261 = 0%** |
| Dạng "yêu cầu giải thích" | 567 (45,0%) |
| Dạng câu hỏi rõ | 222 (17,6%) |
| Dạng khẳng định cần kiểm chứng | **20/1.261 = 1,6%** |
| Tutor trả lời **không kèm trích dẫn** | 582/1.261 = **46,2%** |
| Có rating | 70/2.522 = 2,8% (33 up / 37 down) |

### Kết luận quan trọng nhất

**Chatlog KHÔNG phải nguồn tự nhiên cho bài toán kiểm chứng nguồn.** Không một tin nhắn học viên nào chứa link. Đây là hỏi–đáp trong lớp trên VLearn: học viên bôi đen một đoạn slide rồi hỏi "nghĩa là gì", không phải kênh chia sẻ tài nguyên như Discord.

Hệ quả cho rubric R4 (*"≥10 case lấy hoặc phát triển từ chatlog thật"*): không thể lấy trực tiếp case "có link cần kiểm chứng". Cách nhóm làm — **và ghi rõ vào spec** — là lấy ba thứ chatlog thật sự có:

1. **Khẳng định sai/cần kiểm chứng** (20 tin) — vd `M0503` hiểu lầm cách transformer xử lý câu, `M0347` định nghĩa lệch về prompt engineering.
2. **Câu cụt, mơ hồ** — bôi đen một từ rồi gõ "nghĩa là gì" (`M2413`, `M0544`).
3. **Cách gõ thật** — không dấu, sai chính tả (`M0270`: *"vay LangGraph kahc gi ReAct"*), tiền tố bôi đen.

### Sửa code theo phát hiện này

99,3% tin nhắn có tiền tố `(Trang N, đoạn được chọn: "...")`. Để nguyên thì claim trích ra bị nhiễm phần meta và đoạn slide bị lặp hai lần. Đã thêm `split_vlearn_context()` trong `source_verify.py`: tách đoạn bôi đen ra làm **ngữ cảnh**, phần sau mới là câu hỏi. Với câu cụt (<15 ký tự) thì ghép đoạn bôi đen vào để câu có nghĩa.

---

## 2. Transcript + slide — kho tri thức của bot

| Nguồn | Số đoạn | Ghi chú |
|---|---|---|
| 6 transcript bài giảng | **645** | mã `[Txx-NNN]`, đã bỏ các đoạn `[Hoạt động lớp: ...]` |
| **2 bộ slide** | **58** | mã `[D1-pNN]` / `[D2-pNN]`, 1 trang = 1 đoạn |
| **Tổng** | **703** | |

### Slide trước đây không được dùng — đó là lỗ hổng dữ liệu

Data pack cấp 2 bộ slide (58 trang, 39.147 ký tự text) mà index cũ bỏ qua hoàn toàn. Đo cho thấy nhiều thuật ngữ học viên hỏi thật **chỉ nằm trong slide, không nằm trong lời giảng**:

| Thuật ngữ | Trước (chỉ transcript) | Sau (thêm slide) |
|---|---|---|
| `rlhf` | không có | ✅ có |
| `temperature` | không có | ✅ có |
| `benchmark` | không có | ✅ có |
| `rag` | không có | ✅ có |
| `hallucination` | không có | ✅ có |

Đã nạp slide vào index (`build_slide_index()`), trích dẫn theo số trang đúng quy ước khoá.

### Lỗ hổng còn lại — khai báo trung thực

`react`, `langgraph`, `nfc` **không xuất hiện trong bất kỳ đoạn nào của cả 703 đoạn**. Data pack chỉ có 6 transcript (Day 1–Day 2 foundation) trong khi học viên hỏi cả nội dung buổi sau. Bot **không trả lời được** những câu này, và đó là hành vi đúng — im lặng còn hơn gợi ý bừa.

---

## 3. Ba cách chấm điểm bằng từ khoá đã thử và thất bại

Mục tiêu: quyết định khi nào **nên im lặng**. Đã thử ba cách, đo trên dữ liệu thật, ghi lại để không ai chỉnh ngưỡng lại mà không có bằng chứng:

| Cách | Kết quả đo | Vì sao hỏng |
|---|---|---|
| Tỷ lệ khớp IDF | `giá vàng hôm nay bao nhiêu` đạt **0,70** | Khớp toàn từ phổ biến vẫn ra tỷ lệ cao |
| Khối lượng IDF ≥ 6,0 | Chặn được câu rác, nhưng chặn luôn `benchmark là gì` (4,71) và `ReAct... trong Agent` (5,62) | Câu hỏi về **đúng một thuật ngữ** không đủ khối lượng |
| Max-IDF | `cách nấu phở bò` có max **5,96** > `benchmark` **4,71** | Từ hiếm ≠ thuật ngữ khoá học. "nấu" hiếm nên IDF cao |
| Từ vựng ≥2 file nguồn | 940 từ, vẫn dính `phở`←`phổ biến`, `vàng`, `mai` | Từ tiếng Việt thường cũng xuất hiện ở nhiều file |

**Kết luận:** bag-of-words trên tiếng Việt đã bỏ dấu không tự phân biệt được "thuật ngữ của khoá" với "từ tiếng Việt thông thường". Bỏ dấu gây trùng thật: `phở`→`pho`←`phổ`.

### Đổi kiến trúc theo kết luận đó

```
trước:  từ khoá  ──(ngưỡng chặt)──>  gợi ý           (vừa sót vừa sai)
sau:    từ khoá  ──(ngưỡng lỏng)──>  5 ứng viên  ──>  LLM lọc  ──>  gợi ý
        độ phủ                                        độ chính xác
```

Không tốn thêm lời gọi AI nào — ứng viên được nhét vào chính prompt kiểm chứng đang có, model trả thêm trường `reading_codes`.

**Đo trên 6 case khó:**

| Case | Từ khoá đưa lên | LLM giữ | Kết quả |
|---|---|---|---|
| M17 — hướng dẫn clone thẻ NFC | 4 đoạn | **0** | ✅ sửa được lỗi cũ |
| M13 — lách hệ thống tải slide | 5 đoạn | **0** | ✅ sửa được lỗi cũ |
| G01 — hiểu lầm về transformer | 5 đoạn | 2 (`T04-037`, `D1-p08`) | ✅ đúng, có cả slide |
| M05 — temperature=0 hết hallucinate | 3 đoạn | 2 (`T04-072`, `D1-p29`) | ✅ |
| G10 — LangGraph/ReAct | 0 đoạn | 0 | ✅ (kho không phủ chủ đề) |
| G06 — "tóm tắt" (một từ) | 5 đoạn | 2 | ❌ **chưa đạt** — vẫn gợi ý cho câu cụt |

---

## 4. Golden set — `golden-set.csv`

**31 case**, vượt yêu cầu rubric (≥20 case, ≥2 case/lớp, ≥10 case từ chatlog thật):

| Lớp | Số case |
|---|---|
| ① Nguồn sự thật | 4 |
| ② Mơ hồ / thiếu thông tin | 5 |
| ③ Ngoài phạm vi / thẩm quyền | 4 |
| ④ Đặc thù domain | 5 |
| Thường | 8 |
| Hiếm | 5 |

| Nguồn | Số case |
|---|---|
| **Chatlog thật** (ghi mã `M####`) | **14** |
| Tự soạn kiểu Discord | 17 |

### Hai nhãn đã sửa — nêu rõ để không bị hiểu là chỉnh số cho đẹp

- **G10** `co` → `khong`. Đã kiểm: `react`/`langgraph` không có trong bất kỳ đoạn nào của 703 đoạn. Nhãn cũ đặt theo phỏng đoán của người viết, không theo dữ liệu.
- **G11** `co` → `co|khong`. `ReAct` không có trong kho nhưng `Agent` thì có — case biên, chấp nhận cả hai.

Không sửa nhãn nào khác. **G06 giữ nguyên là case trượt.**

---

## 5. Kết quả đo

```bash
# Lớp từ khoá thô (miễn phí) — theo dõi độ phủ, KHÔNG phải chất lượng sản phẩm
python3 run_golden_set.py

# Sản phẩm thật (tốn quota AI) — đây là số đưa vào spec §7
python3 run_golden_set.py --dim full
```

| Chiều | Kết quả | Ghi chú |
|---|---|---|
| Lớp từ khoá thô (31 case) | **25/31 = 80,6%** | Cố ý để lỏng, đây là đầu vào cho bước lọc |
| Sau khi LLM lọc (6 case khó) | **4/6** | So với 2/6 trước khi đổi kiến trúc |
| `test_knowledge_index.py` (13 case) | **12/13 = 92%** | Chiều "biết khi nào nên im lặng" |

**Chưa chạy `--dim full` trọn 31 case** — mỗi case 10–40 giây, ~15–20 phút cho cả bộ. Phải chạy trước CP3 và ghi kết quả vào spec §7.

---

## 6. Failure còn lại, không giấu

| # | Vấn đề | Bằng chứng | Ảnh hưởng |
|---|---|---|---|
| 1 | **Model trộn ngoại ngữ vào tiếng Việt** dù prompt cấm | `决定論` (M05), `khôngofficial`, `官方`, `crédito` (M14), `발표` (M03) | Tái lặp qua nhiều lượt chạy. Là giới hạn của `nemotron:free` |
| 2 | Câu cụt một từ vẫn được gợi ý bài giảng | G06 "tóm tắt" → LLM vẫn giữ 2 đoạn | Nên thêm luật: input < 15 ký tự thì bỏ qua bước gợi ý |
| 3 | Chỉ kiểm URL đầu tiên | M14 có 2 link, chỉ kiểm 1 | Đã ghi trên UI |
| 4 | `check_url_reachable` trả `False` cho cả link chết lẫn mạng bị chặn | — | Không phân biệt được hai trường hợp |
| 5 | Kho tri thức không phủ nội dung buổi sau | `react`, `langgraph` = 0/703 đoạn | Bot im lặng — đúng hành vi, nhưng phủ được ít câu hỏi hơn |

Failure #1 đáng đưa lên **slide 4** — nó cho thấy nhóm có đo thật, và là ứng viên hàng đầu để thêm một chiều chất lượng "đúng ngôn ngữ" (kiểm bằng regex tìm ký tự CJK/Hangul).

---

## 7. Cách chạy lại toàn bộ

```bash
cd codebase/kiem-chung-nguon && pip install -r requirements.txt

python3 knowledge_index.py                    # in số đoạn đã nạp + thử vài câu
cd ../../eval/kiem-chung-nguon
python3 test_knowledge_index.py               # 13 case, miễn phí
python3 run_golden_set.py                     # 31 case, lớp từ khoá, miễn phí
python3 run_golden_set.py --dim full          # 31 case, AI thật — cần API key
```
