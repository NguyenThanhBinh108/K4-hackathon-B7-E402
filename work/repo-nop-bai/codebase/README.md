# codebase — ghi chú kỹ thuật

## Chạy

Mở `index.html` bằng trình duyệt. Không cần server, không dependency, không build.
`data/corpus.js` nạp qua thẻ `<script>` nên chạy được cả khi mở bằng `file://`.

## Ba hàm cần biết (tất cả nằm trong `index.html`)

| Hàm | Việc | Trạng thái |
|---|---|---|
| `retrieve(query)` | Chấm điểm 25 tài liệu theo token trùng, trả về các đoạn qua ngưỡng | **Thật** |
| `decide(query, cands)` | **Quyết định trung tâm** — chọn `ANSWER` / `CLARIFY` / `HANDOFF` | **Mock ở CP2**, thay ở CP3 |
| `addBot(...)` | Render 5 trạng thái + trace + feedback | Thật |

## Ngưỡng "có căn cứ" trong `retrieve()`

Một đoạn được coi là ứng viên khi **trùng ≥2 token nội dung**, hoặc **điểm ≥0.6**
(điểm = tổng trọng số token trùng chia số token nội dung của câu hỏi; trùng ở `keywords` tính 1.0, chỉ trùng ở `text` tính 0.6).
Token nội dung = đã bỏ dấu tiếng Việt, bỏ stopword, độ dài >1.

Vì vậy các câu như `hii`, `alo`, `ok bạn` rơi thẳng vào nhánh HANDOFF — không có căn cứ thì không trả lời.

## Thứ tự luật trong `decide()` — quan trọng, đừng đảo

```
1. ③ ngoài thẩm quyền   (gia hạn / đáp án / điểm nhóm)   → HANDOFF
2. ② mơ hồ              (hỏi thời hạn nhưng không rõ mốc) → CLARIFY
3. ① không có T1/T2     (chỉ có T3 → tham khảo; không có gì → HANDOFF)
4. thông báo cũ         (có supersededBy → chuyển sang bản mới)
5. mâu thuẫn T4         (conflictsWith → ANSWER kèm cảnh báo)
6. còn lại              → ANSWER
```

Luật ③ đặt trước cùng là có chủ ý: câu "cho mình xin gia hạn nộp **spec**" vẫn truy hồi ra T1-02 với điểm 0.57 — nếu để retrieval quyết thì nó sẽ trả lời hạn nộp thay vì từ chối đúng thẩm quyền.

## Việc của CP3 — thay `decide()` bằng 1 lời gọi AI thật

Giữ nguyên chữ ký hàm, chỉ đổi ruột:

```js
async function decide(query, cands){
  const ctx = cands.slice(0, 6).map(c =>
    `[${c.doc.id} · tầng ${c.doc.tier} · ${c.doc.date}] ${c.doc.text}`).join('\n');
  // gọi model, yêu cầu trả JSON: {route, doc_id, conflict_id, rule}
  // system prompt phải nêu luật tầng: T1/T2 được chốt · T3 chỉ tham khảo · T4 KHÔNG làm căn cứ
}
```

Ba việc bắt buộc kèm theo:
- API key để **biến môi trường**, không commit (`02-guide.md` §3.4).
- Lưu request/response mỗi lượt vào `eval/traces/` — CP3 kiểm "lời gọi AI thật, không hardcode".
- Phần nào vẫn mock thì ghi vào `spec.md §4`.

## Chưa làm (cố ý)

- Không có bot Discord thật — trang web giả giao diện. Rubric chấm chuỗi quyết định, không chấm chỗ nó chạy.
- Không có vector DB — 25 tài liệu thì keyword là đủ, CP3 nhét thẳng đoạn vào prompt.
- Không có đăng nhập, không có lịch sử hội thoại nhiều phiên.

## Nút "Tải log/trace"

Xuất `trace-cp2.json`: mỗi lượt gồm câu hỏi, nhánh đã chọn, luật đã bắn, 3 ứng viên top kèm điểm, và feedback 👍👎 nếu có.
Bỏ file này vào `eval/` (kết quả chạy) và `validation/` (feedback từ người thử).
