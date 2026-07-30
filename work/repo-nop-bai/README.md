# Trợ lý tra cứu khoá — Nhóm [XX] · Zone [X]

Hướng **B — Trợ lý Học viên (Discord)** · Loại: **Tính năng mới**

## Lát cắt (MỘT CÂU)

> Khi học viên K4 hỏi một câu tra cứu trong kênh Discord của khoá, trợ lý quyết định câu đó **có đủ căn cứ trong nguồn chính thức hay không**, rồi trả lời kèm trích dẫn có ghi rõ tầng nguồn — hoặc chuyển TA thay vì đoán.

## Thành viên & phân công

| Tên | Mã HV | Phần phụ trách | Artifact |
|---|---|---|---|
| Vũ | | Tầng **T3** — nguồn ngoài (paper/github/docs) + case golden set của T3 | `codebase/data/corpus.js`, `eval/` |
| Bình | | Tầng **T3** + luật "chỉ tham khảo, không chốt" | `codebase/`, `spec.md §5` |
| Linh | | Tầng **T1** — thông báo, quy định chính thức + bẫy thông báo cũ/mới | `codebase/data/corpus.js` |
| Liễu | | Tầng **T1** + khảo sát evidence | `spec.md §1`, `validation/` |
| Hải Đăng | | Tầng **T2/T4** — tài liệu bài giảng + chat học viên, bẫy mâu thuẫn | `codebase/data/corpus.js`, `eval/` |

> Điền tên đầy đủ + mã HV trước CP4. **Vibe-coding rule:** ai đứng tên phần nào phải giải thích được phần đó ở CP5.

## Chạy thử

Mở `codebase/index.html` bằng trình duyệt — **không cần server, không cần cài gì**.
Bấm 6 câu gợi ý dưới ô nhập là đi hết 5 trạng thái.

## Mức prototype khai báo

**Mock** — flow bấm hết được, data giả.

| Phần | Trạng thái ở CP2 | Kế hoạch CP3 |
|---|---|---|
| Giao diện chat | Thật (web giả giao diện Discord) | giữ nguyên |
| Corpus 4 tầng nguồn | Thật, **data giả tự sinh** | thêm 4-6 mục từ transcript, ghi mã đoạn |
| Truy hồi | Thật (keyword scoring trong `retrieve()`) | giữ nguyên — corpus chỉ ~25 mục |
| **Quyết định ANSWER/CLARIFY/HANDOFF** | **Mock — luật cứng trong `decide()`** | **thay bằng 1 lời gọi AI thật** |
| Chuyển TA | Mock — ghi vào log, không gửi đi đâu | giữ mock, ghi rõ trong spec |
| Feedback 👍👎 + trace | Thật, tải được ra JSON | đổ vào `validation/` và `eval/` |

## Cấu trúc repo

```
├── README.md          ← file này
├── spec.md            ← AI Spec (hạn cứng 23:59 ngày 1)
├── demo-slides.pdf    ← 6 trang, nộp trước CP6
├── codebase/          ← prototype
├── eval/              ← golden set + các lượt chạy
├── validation/        ← feedback log từ user test
└── reflection/        ← mỗi người 1 file
```

## Dữ liệu

Toàn bộ corpus trong `codebase/data/corpus.js` là **data giả tự sinh**. Không có tin nhắn thật của người thật, không có nội dung data pack. T2 trích từ tài liệu công khai của khoá (`01-de-bai.md`, `02-guide.md`, `04-rubric.md`). Không commit API key.
