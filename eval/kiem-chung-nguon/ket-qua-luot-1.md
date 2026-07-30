# Lượt chạy 1 — golden set, chiều có AI thật · DỞ DANG

**Trạng thái: KHÔNG hoàn thành.** Chạy được 15/31 case ở chế độ LIVE_AI thì
OpenRouter free tier trả 429 Too Many Requests liên tục; sau 4 lần thử lại với
backoff (8s → 16s → 32s → 64s) script rơi sang MOCK MODE. Đã dừng tay tại đó.

Lý do dừng thay vì để chạy tiếp: kết quả MOCK không phải AI thật, để lẫn vào
bảng là làm hỏng bằng chứng. Rubric ghi rõ số liệu bị che giấu hoặc trộn lẫn
không được tính.

**Nguyên nhân hết quota:** cùng lúc có bot Discord đang chạy, các lượt test tay,
và lượt chạy này — tất cả dùng chung một OPENROUTER_API_KEY free tier.

**Việc phải làm:** chạy lại trọn bộ khi quota reset, một mình, không chạy bot
song song:

    python3 run_golden_set.py --dim full

**Lưu ý:** lượt này đo hành vi TRƯỚC khi có định tuyến ý định (commit e15dab4).
Sau thay đổi đó, nhiều case hỏi kiến thức sẽ ra intent=hoi_kien_thuc thay vì
verdict — nên lượt 2 không so sánh trực tiếp được với lượt này ở chiều C2.

---

## Kết quả 15 case chạy được (LIVE_AI)

```
G01   ④ domain            ✓ UNVERIFIED_NO_SOURCE                0     ✓ T04-037,D1-p08      ✓
G02   ④ domain            ✓ UNVERIFIED_NO_SOURCE                0     ✓ T01-066,T04-089     ✓
G03   ① nguồn sự thật     ✓ UNVERIFIED_NO_SOURCE                0     ✓ T04-046             ✓
G04   thường              ✓ UNVERIFIED_NO_SOURCE                0     ✓ T04-082             ✗ lẫn: осбен
G05   thường              ✓ UNVERIFIED_NO_SOURCE                0     ✓ D2-p19,T05-137      ✗ lẫn: 主張駁
G06   ② mơ hồ             ✓ UNVERIFIED_NO_SOURCE                0     ✗ D1-p10,T01-036      ✓
G07   ② mơ hồ             ✓ UNVERIFIED_NO_SOURCE                0     ✓ —                   ✓
G08   ② mơ hồ             ✓ OPINION_NOT_APPLICABLE              0     ✓ —                   ✗ lẫn: 모
G09   ② mơ hồ             LỖI ValueError: Khong tach duoc JSON tu cau tra loi cua LLM: 'corr CST Lump 
G10   hiếm                ✓ UNVERIFIED_NO_SOURCE                0     ✓ —                   ✓
G11   hiếm                ✗ VERIFIED                            70    ✓ —                   ✓
G12   hiếm                ✓ UNVERIFIED_NO_SOURCE                0     ✓ —                   ✓
G13   hiếm                ✓ UNVERIFIED_NO_SOURCE                0     ✓ —                   ✓
G14   ③ ngoài thẩm quyền  ✓ UNVERIFIED_NO_SOURCE                0     ✓ T01-034             ✓
M01   ① nguồn sự thật     ✗ PARTIALLY_VERIFIED                  70    ✓ T03-122             ✓
M02   thường              ✓ PARTIALLY_VERIFIED                  66    ✗ —                   ✓
```


## Đọc nhanh

- **C5 (đúng ngôn ngữ) trượt 3/16 case** — model lẫn ký tự Kirin (осбен),
  Hán (主張駁), Hàn (모) vào giữa câu tiếng Việt dù prompt cấm rõ ràng.
  Đây là failure tái lặp, đáng đưa lên slide 4.
- **M01 trượt C2**: kỳ vọng VERIFIED, thực tế PARTIALLY_VERIFIED (70/100).
- Toàn bộ case từ chatlog (G01–G14) ra UNVERIFIED_NO_SOURCE 0/100 — đúng như
  thiết kế cũ, và chính là lý do phải làm định tuyến ý định ở e15dab4.
