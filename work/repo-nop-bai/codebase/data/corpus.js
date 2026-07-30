/* ============================================================================
 * CORPUS — 4 tầng nguồn
 * ---------------------------------------------------------------------------
 * TOÀN BỘ DỮ LIỆU TRONG FILE NÀY LÀ DATA GIẢ TỰ SINH cho prototype.
 * Không chứa tin nhắn thật của người thật, không chứa nội dung data pack.
 * T2 trích từ tài liệu công khai của khoá (01-de-bai / 02-guide / 04-rubric).
 *
 * Luật tầng nguồn (kiểm chứng bằng mắt, KHÔNG do AI chấm điểm):
 *   T1 Nguồn chính thức khoá   → được trả lời chốt
 *   T2 Tài liệu chính thức     → được trả lời chốt, kèm mục/mã đoạn
 *   T3 Nguồn ngoài             → chỉ được nói "tham khảo", không chốt
 *   T4 Lời học viên trong chat → KHÔNG được dùng làm căn cứ
 *
 * Ba cái bẫy đã gài sẵn:
 *   #1 Mâu thuẫn T1 ↔ T4 : T1-01 (CP3 10:30) vs T4-01 (học viên nói 9h)
 *   #2 Thông báo cũ/mới  : T1-03 (link cũ, đã đóng) bị T1-04 thay thế
 *   #3 Không có căn cứ   : không tầng nào nói về tiệc closing, phòng ốc, ăn uống
 * ========================================================================== */

window.CORPUS = [
  /* ---------------------------- T1 · Nguồn chính thức khoá ---------------- */
  {
    id: 'T1-01', tier: 'T1', title: 'Lịch 6 mốc checkpoint — Khoá 4',
    source: 'Kênh #thong-bao', author: 'BTC', date: '2026-07-29',
    text: 'Lịch mốc Khoá 4: Khai mạc 14:00 ngày 1 · CP1 Canvas 15:00 ngày 1 · CP2 Bấm được 17:00 ngày 1 · CP3 AI thật + đo lượt đầu 10:30 ngày 2 · CP4 Chốt tiến độ 12:00 ngày 2 · CP5 Validation + dry run 14:00 ngày 2 · CP6 Demo 15:00 ngày 2.',
    answer: 'Lịch mốc của Khoá 4: CP1 15:00 ngày 1 · CP2 17:00 ngày 1 · CP3 10:30 ngày 2 · CP4 12:00 ngày 2 · CP5 14:00 ngày 2 · CP6 Demo 15:00 ngày 2.',
    keywords: ['cp1', 'cp2', 'cp3', 'cp4', 'cp5', 'cp6', 'checkpoint', 'moc', 'lich', 'demo', 'khai mac', 'canvas']
  },
  {
    id: 'T1-02', tier: 'T1', title: 'Hạn nộp spec.md — hạn cứng',
    source: 'Kênh #thong-bao', author: 'BTC', date: '2026-07-29',
    text: 'spec.md phải được commit trước 23:59 ngày 1. Đây là hạn cứng. Quality bar chốt từ thời điểm này và giữ nguyên sau đó — không sửa bar sau khi đã thấy kết quả đo.',
    answer: 'spec.md phải commit trước 23:59 ngày 1 — đây là hạn cứng. Quality bar chốt từ thời điểm đó và không được sửa sau khi thấy kết quả đo.',
    keywords: ['spec', 'nop', 'han', 'deadline', 'quality bar', 'commit', '2359', 'ngay 1']
  },
  {
    id: 'T1-03', tier: 'T1', title: 'Link nộp bài (BẢN CŨ — đã đóng)',
    source: 'Kênh #thong-bao', author: 'BTC', date: '2026-07-24',
    text: 'Nhóm nộp link repo qua form: https://forms.example/hackathon-nop-bai-v1',
    answer: 'Form nộp bài bản cũ (đã đóng): https://forms.example/hackathon-nop-bai-v1',
    keywords: ['link', 'nop', 'bai', 'form', 'repo'],
    supersededBy: 'T1-04'
  },
  {
    id: 'T1-04', tier: 'T1', title: 'Link nộp bài — BẢN THAY THẾ',
    source: 'Kênh #thong-bao', author: 'BTC', date: '2026-07-29',
    text: 'Form nộp bài đã đổi. Dùng link mới: https://forms.example/hackathon-nop-bai-v2 . Form cũ (thông báo ngày 24/07) đã đóng, nộp vào đó sẽ không được ghi nhận. Mỗi thành viên nộp riêng, cả nhóm dùng chung một link repo.',
    answer: 'Link nộp bài hiện tại: https://forms.example/hackathon-nop-bai-v2 . Mỗi thành viên nộp riêng, cả nhóm dùng chung một link repo.',
    keywords: ['link', 'nop', 'bai', 'form', 'repo', 'moi'],
    supersedes: 'T1-03'
  },
  {
    id: 'T1-05', tier: 'T1', title: 'Quy định bảo mật data pack',
    source: 'Kênh #thong-bao', author: 'BTC', date: '2026-07-28',
    text: 'Data trong data/ chỉ dùng trong phạm vi hackathon. Không chia sẻ ra ngoài khoá, không commit data pack vào repo nộp bài — chỉ trích ngắn vài dòng để minh hoạ, golden set ghi mã đoạn/mã hội thoại thay vì dán nguyên văn dài.',
    answer: 'Data pack chỉ dùng trong hackathon, không chia sẻ ra ngoài và không commit vào repo. Trong repo chỉ để trích ngắn hoặc ghi mã đoạn/mã hội thoại.',
    keywords: ['data', 'bao mat', 'commit', 'chia se', 'quy dinh', 'pack']
  },
  {
    id: 'T1-06', tier: 'T1', title: 'Quy định nộp checkpoint & điểm',
    source: 'Kênh #thong-bao', author: 'BTC', date: '2026-07-28',
    text: 'Tổng 100 điểm = 25 điểm nộp checkpoint + 75 điểm chấm bài. Mỗi checkpoint CP1-CP5 là 5 điểm: nộp đúng hạn được 5, nộp muộn được 0 cho mốc đó. Mỗi thành viên nộp riêng, cả nhóm dùng chung một link repo.',
    answer: 'Tổng 100 điểm = 25 điểm nộp checkpoint (CP1-CP5, mỗi mốc 5 điểm) + 75 điểm chấm bài. Nộp muộn một mốc thì mốc đó 0 điểm.',
    keywords: ['diem', 'cham', 'checkpoint', 'nop muon', 'rubric', '100', '25', '75']
  },
  {
    id: 'T1-07', tier: 'T1', title: 'Quy định nhóm & prototype',
    source: 'Kênh #thong-bao', author: 'BTC', date: '2026-07-28',
    text: 'Nhóm 4-5 người, zone tối đa 5 nhóm. Prototype có 3 mức Sketch/Mock/Working — mức nào cũng bắt buộc có ít nhất 1 lời gọi AI chạy thật. Không yêu cầu deploy.',
    answer: 'Nhóm 4-5 người. Prototype chọn 1 trong 3 mức Sketch/Mock/Working, mức nào cũng bắt buộc có ≥1 lời gọi AI chạy thật. Không cần deploy.',
    keywords: ['nhom', 'prototype', 'sketch', 'mock', 'working', 'ai call', 'deploy', 'zone']
  },

  /* ---------------------------- T2 · Tài liệu chính thức ------------------ */
  {
    id: 'T2-01', tier: 'T2', title: 'Ba mức automation',
    source: '02-guide.md §2.3', author: 'Tài liệu khoá', date: '2026-07-29',
    text: 'Augment — AI gợi ý, người quyết, dùng khi sai thì đắt. Conditional — AI tự làm case chắc, chuyển người case mơ hồ, dùng khi đa số case lành và số ít hiểm. Automate — AI tự làm, dùng khi sai thì rẻ và user tự sửa được. Lý do trong spec viết theo cost-of-error: sai thì ai chịu gì, sửa đắt hay rẻ.',
    answer: 'Có 3 mức: Augment (AI gợi ý, người quyết — khi sai thì đắt), Conditional (AI làm case chắc, chuyển người case mơ hồ), Automate (AI tự làm — khi sai thì rẻ). Lý do phải viết theo cost-of-error, không viết "vì tiện".',
    keywords: ['automation', 'augment', 'conditional', 'automate', 'cost of error', 'muc']
  },
  {
    id: 'T2-02', tier: 'T2', title: 'Quality bar & golden set',
    source: '02-guide.md §2.6 + 04-rubric.md R4', author: 'Tài liệu khoá', date: '2026-07-29',
    text: 'Golden set tối thiểu 20 case nhóm tự xây: ít nhất 2 case cho mỗi lớp chỗ khó, 8-10 case thường, 2-4 case hiếm, trong đó ít nhất 10 case lấy hoặc phát triển từ chatlog thật. Quality bar phải là con số, chốt trong spec.md trước 23:59 ngày 1 và giữ nguyên sau đó. Không đạt bar nhưng phân tích được nguyên nhân vẫn tính đủ điểm; số liệu bị chỉnh sửa thì không được tính.',
    answer: 'Quality bar do nhóm tự đặt, nhưng phải là con số và phải chốt trong spec.md trước 23:59 ngày 1, sau đó không sửa. Golden set tối thiểu 20 case, trong đó ≥2 case/lớp chỗ khó và ≥10 case từ chatlog thật. Không đạt bar mà phân tích được nguyên nhân thì vẫn đủ điểm.',
    keywords: ['quality bar', 'golden set', 'case', 'do', 'phan tram', 'kiem thu', 'eval', 'bar']
  },
  {
    id: 'T2-03', tier: 'T2', title: 'Bốn lớp chỗ khó',
    source: '01-de-bai.md ràng buộc 2', author: 'Tài liệu khoá', date: '2026-07-29',
    text: 'Lớp ① Nguồn sự thật — chỗ nào AI bịa được, không có căn cứ thì làm gì. Lớp ② Mơ hồ / thiếu thông tin — input không đủ chắc thì hỏi lại, đoán có báo, hay từ chối. Lớp ③ Ngoài phạm vi / thẩm quyền — user đòi thứ không được phép làm, từ chối sao cho vẫn hữu ích. Lớp ④ Đặc thù domain — sai cái gì thì user mất điểm, mất niềm tin, học sai kiến thức ngay.',
    answer: 'Bốn lớp: ① Nguồn sự thật (AI bịa được ở đâu) · ② Mơ hồ/thiếu thông tin · ③ Ngoài phạm vi/thẩm quyền · ④ Đặc thù domain (sai là mất điểm, mất niềm tin ngay). Mỗi lớp cần ≥2 case trong golden set.',
    keywords: ['cho kho', 'lop', 'taxonomy', 'nguon su that', 'mo ho', 'tham quyen', 'domain']
  },
  {
    id: 'T2-04', tier: 'T2', title: 'Lát cắt MỘT CÂU',
    source: '01-de-bai.md', author: 'Tài liệu khoá', date: '2026-07-29',
    text: 'Lát cắt viết thành một câu duy nhất theo format: một người dùng · một công việc · một quyết định AI · một kết quả. Demo được trong 5 phút, build được trong thời gian sự kiện.',
    answer: 'Lát cắt phải viết thành MỘT câu theo format: một người dùng · một công việc · một quyết định AI · một kết quả — và phải khớp với bản build.',
    keywords: ['lat cat', 'mot cau', 'format', 'nguoi dung', 'quyet dinh ai']
  },
  {
    id: 'T2-05', tier: 'T2', title: 'Chuẩn bằng chứng A và B',
    source: '02-guide.md §1.3', author: 'Tài liệu khoá', date: '2026-07-29',
    text: 'Đường A — khảo sát: tối thiểu 20 người ngoài nhóm, tối thiểu 50% xác nhận, log đầy đủ câu hỏi và từng câu trả lời. Đường B — mining: số đếm được, tối thiểu 5 ví dụ nguyên văn, và phương pháp đếm kiểm lại được. Không có log thì không được tính là bằng chứng.',
    answer: 'Chuẩn A: khảo sát ≥20 người ngoài nhóm, ≥50% xác nhận, có log đầy đủ. Chuẩn B: mining có số đếm được + ≥5 ví dụ nguyên văn + phương pháp đếm kiểm lại được. Không có log thì không tính là bằng chứng.',
    keywords: ['bang chung', 'evidence', 'khao sat', 'mining', 'chuan a', 'chuan b', '20 nguoi', 'log']
  },
  {
    id: 'T2-06', tier: 'T2', title: 'Ba mức prototype',
    source: '02-guide.md §3.2', author: 'Tài liệu khoá', date: '2026-07-29',
    text: 'Sketch — màn hình dựng nhanh + 1 AI call demo được. Mock — flow bấm được, data giả, AI thật ở lõi. Working — chạy end-to-end với data pack thật. Một bản Sketch làm kỹ được đánh giá cao hơn một bản Working làm vội.',
    answer: 'Sketch (màn hình nhanh + 1 AI call) · Mock (flow bấm được, data giả, AI thật ở lõi) · Working (end-to-end với data thật). Sketch làm kỹ được đánh giá cao hơn Working làm vội.',
    keywords: ['prototype', 'sketch', 'mock', 'working', 'muc']
  },

  /* ---------------------------- T3 · Nguồn ngoài -------------------------- */
  {
    id: 'T3-01', tier: 'T3', title: 'Microsoft HAX Toolkit — 18 guidelines',
    source: 'microsoft.com/haxtoolkit', author: 'Microsoft Research', date: '2026-07-01',
    text: 'Bộ 18 nguyên tắc thiết kế tương tác người-AI. G1 làm rõ hệ thống làm được gì · G2 làm rõ nó làm tốt đến đâu · G8 gạt bỏ dễ dàng · G9 sửa dễ dàng · G10 thu hẹp phạm vi khi nghi ngờ · G11 giải thích vì sao. HAX Playbook sinh kịch bản lỗi từ bộ câu hỏi config.',
    answer: 'HAX Toolkit là bộ 18 nguyên tắc thiết kế tương tác người-AI của Microsoft (G1, G2, G8-G11...), kèm HAX Playbook để sinh kịch bản lỗi.',
    keywords: ['hax', 'guideline', 'g10', 'g11', 'microsoft', 'playbook', 'nguyen tac']
  },
  {
    id: 'T3-02', tier: 'T3', title: 'Google PAIR Guidebook',
    source: 'pair.withgoogle.com/guidebook', author: 'Google PAIR', date: '2026-07-01',
    text: 'Các chương: Mental Models (đặt kỳ vọng thấp hơn khả năng một chút), Explainability + Trust (tin đúng mức tốt hơn tin tối đa), Feedback + Control, Errors + Graceful Failure.',
    answer: 'PAIR Guidebook của Google, các chương hay dùng: Mental Models, Explainability + Trust, Feedback + Control, Errors + Graceful Failure.',
    keywords: ['pair', 'google', 'guidebook', 'mental model', 'trust', 'explainability']
  },
  {
    id: 'T3-03', tier: 'T3', title: 'promptfoo — chạy golden set tự động',
    source: 'promptfoo.dev', author: 'promptfoo', date: '2026-07-01',
    text: 'Công cụ chạy eval cho prompt: npx promptfoo@latest init. Biến golden set thành test tự động, có red-team mode sinh thêm case hiểm.',
    answer: 'promptfoo biến golden set thành test tự động (npx promptfoo@latest init), có red-team mode sinh case hiểm. Đây là công cụ ngoài, không phải quy định của khoá.',
    keywords: ['promptfoo', 'eval', 'test', 'tu dong', 'red team']
  },

  /* ---------------------------- T4 · Lời học viên trong chat -------------- */
  {
    id: 'T4-01', tier: 'T4', title: 'hocvien_A trong #hoi-dap',
    source: 'Kênh #hoi-dap', author: 'hocvien_A', date: '2026-07-29',
    text: 'CP3 hình như 9h sáng mai đúng không mọi người, mình nhớ mang máng thế',
    answer: '',
    keywords: ['cp3', '9h', 'sang', 'mai', 'moc'],
    conflictsWith: 'T1-01'
  },
  {
    id: 'T4-02', tier: 'T4', title: 'hocvien_B trong #hoi-dap',
    source: 'Kênh #hoi-dap', author: 'hocvien_B', date: '2026-07-28',
    text: 'mình dùng cái form hôm trước vẫn nộp được mà, chắc không sao đâu',
    answer: '',
    keywords: ['form', 'nop', 'link', 'cu']
  },
  {
    id: 'T4-03', tier: 'T4', title: 'hocvien_C trong #hoi-dap',
    source: 'Kênh #hoi-dap', author: 'hocvien_C', date: '2026-07-29',
    text: 'quality bar cứ để 90% cho nó ngầu, thấp quá nhìn không đẹp',
    answer: '',
    keywords: ['quality bar', '90', 'phan tram']
  },
  {
    id: 'T4-04', tier: 'T4', title: 'hocvien_D trong #hoi-dap',
    source: 'Kênh #hoi-dap', author: 'hocvien_D', date: '2026-07-29',
    text: 'ai có slide buổi 2 không cho mình xin với',
    answer: '',
    keywords: ['slide', 'buoi 2', 'tai lieu']
  },
  {
    id: 'T4-05', tier: 'T4', title: 'hocvien_E trong #hoi-dap',
    source: 'Kênh #hoi-dap', author: 'hocvien_E', date: '2026-07-29',
    text: 'nhóm mình định làm chatbot RAG cho discord, không biết có bị trùng ý tưởng không',
    answer: '',
    keywords: ['chatbot', 'rag', 'discord', 'y tuong']
  }
];

/* ============================================================================
 * CẦN BỔ SUNG TRƯỚC CP3 (Hải Đăng — tầng T2)
 * ---------------------------------------------------------------------------
 * Thêm 4-6 mục T2 trích từ 6 transcript bài giảng trong data/vlearn-pack/.
 * Mỗi mục PHẢI ghi mã đoạn ở trường `source`, ví dụ:
 *   source: 'transcript-03-clean.md · đoạn [T03-045]'
 * Chỉ trích ngắn vài dòng — không dán nguyên văn dài (quy định bảo mật §T1-05).
 * ========================================================================== */
