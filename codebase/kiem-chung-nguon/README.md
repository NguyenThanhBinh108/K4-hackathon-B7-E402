# Prototype: Kiểm Chứng Nguồn (Source Verification Assistant)

Mock-level prototype cho tính năng "Kiểm chứng nguồn tài liệu" — Hướng B (Trợ lý Học viên, Discord).
Xem thiết kế đầy đủ tại `../spec-draft-kiem-chung-nguon.md`.

## Vì sao dùng data giả thay vì Discord API thật

Track Hướng B không được cấp data pack riêng, và nhóm chưa có bot token/quyền truy cập API
cho kênh Discord thật của khoá. Theo đúng luật hackathon (không dùng data thật của người thật
ngoài data pack được cấp), prototype này đọc tin nhắn từ `../eval/mock-messages.json` (10 tin
nhắn tự soạn, mô phỏng các dạng case thường gặp trong kênh chia sẻ kiến thức) thay vì gọi
Discord API. Hàm `load_messages()` trong `source_verify.py` là điểm duy nhất cần thay khi có
bot token thật — phần còn lại của pipeline không phụ thuộc vào nguồn input.

## Cách chạy

```bash
pip install requests

# Chạy ở MOCK MODE (không cần key, chỉ để test pipeline chạy được — KHÔNG dùng để demo)
python3 source_verify.py

# Chạy với AI thật (bắt buộc trước khi demo/nộp bài — luật hackathon yêu cầu ≥1 lời gọi AI thật)
export GEMINI_API_KEY=xxxxx        # khuyến nghị — free tier theo guide §3.4
python3 source_verify.py

# hoặc dùng Claude
export ANTHROPIC_API_KEY=xxxxx
python3 source_verify.py
```

Kết quả mỗi lượt chạy được lưu vào `../eval/last-run-results.json` để dùng làm bảng % trong spec §7.

## Đã kiểm tra (verify) trong sandbox

- Chạy `python3 source_verify.py` ở MOCK MODE: pipeline chạy hết 10/10 message, không lỗi,
  sinh đúng cấu trúc output (verdict, độ tin cậy, trích dẫn, giải thích, lớp chỗ khó).
- Domain classification hoạt động đúng: `github.com`, `docs.claude.com` → reachable=True (kiểm
  tra HTTP thật qua `requests`); domain `.fakedomain.example` → nhận diện đúng là reserved-test-
  domain, không phải nguồn thật.
- Lưu ý: sandbox môi trường build hiện tại chặn truy cập `arxiv.org` (network allowlist) nên
  URL đó trả `reachable=False` dù link có thật — không phải lỗi logic, chỉ là giới hạn mạng của
  sandbox. Khi chạy trên máy nhóm/môi trường demo bình thường sẽ không gặp vấn đề này.
- **Việc còn lại trước khi demo:** cắm `GEMINI_API_KEY` thật và chạy lại để có lời gọi AI thật
  (hiện tại trong sandbox không có key nên tự động rơi vào MOCK MODE — script tự cảnh báo rõ
  điều này ở cuối mỗi lần chạy, không âm thầm giả vờ là AI thật).

## Golden set / lượt chạy tay đầu tiên

`../eval/manual-claude-verification-run.md` chứa lượt kiểm chứng thủ công (dùng Claude làm AI
xác minh trực tiếp, theo đúng cách guide §2.6 khuyến nghị "chạy tay trước khi code hoá") cho
cùng 10 case — dùng làm đáp án đối chiếu khi so kết quả của `source_verify.py` chạy với API thật.
