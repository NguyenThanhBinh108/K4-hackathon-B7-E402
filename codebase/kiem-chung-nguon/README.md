# Prototype: Kiểm Chứng Nguồn (Source Verification Assistant)

Mock-level prototype cho tính năng "Kiểm chứng nguồn tài liệu" — Hướng B (Trợ lý Học viên, Discord).
Xem thiết kế đầy đủ tại `../../spec-draft-kiem-chung-nguon.md`.

## Vì sao dùng data giả thay vì Discord API thật

Track Hướng B không được cấp data pack riêng, và nhóm chưa có bot token/quyền truy cập API
cho kênh Discord thật của khoá. Theo đúng luật hackathon (không dùng data thật của người thật
ngoài data pack được cấp), prototype này đọc tin nhắn từ
`../../eval/kiem-chung-nguon/mock-messages.json` (**17 tin nhắn tự soạn**, mô phỏng các dạng case
thường gặp trong kênh chia sẻ kiến thức) thay vì gọi Discord API. Hàm `load_messages()` trong
`source_verify.py` là điểm duy nhất cần thay khi có bot token thật — phần còn lại của pipeline
không phụ thuộc vào nguồn input.

## Cách chạy

```bash
# 1. Cài thư viện — CẦN ĐỦ CẢ BA, không chỉ requests.
#    Thiếu trafilatura/pypdf thì tính năng đối chiếu nội dung thật (TIP-05) sẽ TẮT.
pip install -r requirements.txt

# 2. Cắm API key. Ưu tiên OpenRouter; không có thì Gemini hoặc Claude.
#    Gọn nhất: cp .env.example .env  rồi điền key vào .env (.env đã nằm trong .gitignore)
export OPENROUTER_API_KEY=xxxxx        # ưu tiên — code thử OpenRouter trước
export GEMINI_API_KEY=xxxxx            # hoặc — free tier theo guide §3.4
export ANTHROPIC_API_KEY=xxxxx         # hoặc

# 3. Chạy
python3 source_verify.py               # trọn 17 case
python3 source_verify.py M15 M16 M17   # chỉ vài case, tiết kiệm quota

# 4. Sau mỗi lượt chạy AI thật, nạp lại dữ liệu cho demo UI
python3 update_demo_ui.py
```

**Chạy khi chưa có key** vẫn được — pipeline chuyển sang MOCK MODE để kiểm tra chạy thông, và ghi
kết quả ra file `*-MOCK.json` riêng. Bản MOCK **không phải AI thật**, không dùng để demo/nộp bài.

## Các file trong thư mục này

| File | Việc |
|---|---|
| `source_verify.py` | Pipeline chính: phân loại domain → quét rủi ro → gọi LLM → gộp điểm |
| `risk_patterns.py` | Quét rủi ro rule-based, chạy **trước** LLM (không để LLM tự quyết `risk_flag`) |
| `demo-discord-ui.html` | Giao diện demo mô phỏng Discord — mở thẳng bằng trình duyệt, không cần server |
| `kiem-chung-nguon-pitch.html` | Slide pitch |
| `update_demo_ui.py` | Nạp lại `const DATA` trong demo UI từ file kết quả mới nhất |
| `rescore_results.py` | Tính lại điểm tin cậy cho lượt chạy cũ khi công thức đổi, không tốn quota AI |

## Kết quả các lượt chạy

- `../../eval/kiem-chung-nguon/last-run-results.json` — lượt chạy **AI thật** (17/17 LIVE_AI).
  Đây là artifact bằng chứng cho spec §7.
- `../../eval/kiem-chung-nguon/last-run-results-MOCK.json` — sinh ra khi chạy thử không có key.
  Không tính là bằng chứng, đã nằm trong `.gitignore`.

## Đã sửa sau vòng kiểm thử tích hợp

| # | Lỗi | Sửa thế nào |
|---|---|---|
| 1 | **Điểm tin cậy tính ngược hướng.** Công thức cũ `0.4×domain + 0.6×llm_confidence` cộng "độ tự tin của AI vào phán quyết" vào "độ khả tín của claim" — hai đại lượng khác nhau. Hậu quả đo được: M05 CONTRADICTED được 54/100, M02 UNVERIFIED được 79/100 và hiện thanh xanh trên UI | Verdict quyết định **dải điểm**; chất lượng bằng chứng (domain + có đối chiếu được nội dung thật không) quyết định **vị trí trong dải**. `llm_confidence` không còn cộng vào điểm, vẫn lưu để tra cứu. Trần 95 chứ không phải 100 |
| 2 | **Crash trên Windows** — console cp1252 không in được tiếng Việt có dấu, `UnicodeEncodeError` ngay tin nhắn đầu tiên | Ép `sys.stdout`/`stderr` sang UTF-8 khi `sys.platform == "win32"` |
| 3 | **Chạy không key làm mất bằng chứng** — lượt MOCK ghi đè `last-run-results.json` đang chứa 17 kết quả AI thật | Lượt có case MOCK ghi ra `*-MOCK.json`, không đụng file LIVE |
| 4 | **Thiếu thư viện thì tính năng tắt âm thầm** và báo sai nguyên nhân ("PDF ảnh/bị chặn") | Cảnh báo rõ ngay đầu lượt chạy; phân biệt `thieu-thu-vien` với `khong-trich-xuat` |
| 5 | Demo UI tô màu thanh theo **điểm**, nên "Chưa xác minh được — 79/100" hiện thanh xanh lá | Tô theo **verdict**; ẩn thanh với verdict không phán xử đúng-sai |
| 6 | `risk_class` rỗng vẫn hiện nhãn "LỚP CHỖ KHÓ" trống | Ẩn hẳn ô khi rỗng |
| 7 | Demo UI nhúng cứng dữ liệu nên lệch dần so với `eval/` | Thêm `update_demo_ui.py` để đồng bộ sau mỗi lượt chạy |
| 8 | URL regex bắt cả dấu câu cuối (`https://agentrouter.org,` ở M15) | Cắt dấu câu ở cuối URL |
| 9 | Thông báo thiếu key chỉ nhắc GEMINI/ANTHROPIC dù code ưu tiên OPENROUTER | Nhắc đủ ba key |

> Sau khi đổi công thức, `rescore_results.py` đã chạy trên `last-run-results.json` để áp điểm mới.
> **Verdict, explanation và mọi thứ AI thật trả về đều giữ nguyên** — chỉ bước gộp điểm cuối được
> tính lại, nên không phải gọi lại AI và không tốn quota. 14/17 case đổi điểm.

## Giới hạn còn lại (khai báo trung thực)

- Chỉ kiểm URL **đầu tiên** trong tin nhắn; các link còn lại chỉ được đếm số.
- `check_url_reachable()` trả `False` cho cả link chết lẫn mạng bị chặn — không phân biệt được hai trường hợp.
- Script **thật sự gọi mạng** tới URL trong tin nhắn khi chạy, gồm cả domain đáng ngờ ở M14/M15.
- Thao tác "chuyển TA" và giao diện Discord là **mock** — chưa nối bot thật.
- Golden set hiện là 17 case tự soạn; rubric R4 yêu cầu ≥20 case và ≥10 case phát triển từ chatlog thật — **còn thiếu, cần bổ sung trước CP3**.
