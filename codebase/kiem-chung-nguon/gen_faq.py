#!/usr/bin/env python3
"""
gen_faq.py — sinh faq.json: "cau nay da co nguoi hoi roi"

VI SAO CAN
----------
Luong kiem chung dang thieu mot thu ma nguoi dung mong doi: neu cau hoi DA
DUOC TRA LOI truoc do thi tra loi ngay, kem nguon. Hien tai bot phai suy tu
703 doan bai giang moi lan, va voi chu de bi hoi di hoi lai thi vua cham vua
khong nhat quan.

FAQ giai quyet ca hai: cau tra loi chot san, nguon chot san, va con so THAT
"bao nhieu hoc vien da hoi" lay tu chatlog.

BA NGUON DU LIEU, KHONG BIA CAI NAO
------------------------------------
1. `asked_count` — DEM THAT tren 1.261 tin nhan hoc vien trong chatlog VLearn.
2. `sources`     — MA DOAN THAT do knowledge_index tra ve, kiem lai duoc.
3. `answer`      — nhom tu viet, DUA TREN cac doan da trich dan o tren.

Chu de nao khong co trong tai lieu khoa thi ghi thang `"gap": true` va cau
tra loi noi ro la chua co — KHONG bia mot doan bai giang khong ton tai.

Chay:
    python3 gen_faq.py            # ghi faq.json
    python3 gen_faq.py --check    # chi kiem tra
"""

import csv
import json
import os
import re
import sys
import unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "faq.json")
CHATLOG = os.path.join(BASE, "..", "..", "data", "vlearn-pack", "chatlog",
                       "chat_history_anonymized_for_hackathon.csv")

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", s)).strip()


# (khoa_dem, cau_hoi_chuan, cac_cach_hoi_khac, truy_van_tim_nguon, cau_tra_loi)
FAQ = [
 ("agent", "Agent là gì, khác gì workflow?",
  ["agent la gi", "agent khac workflow the nao", "khi nao dung agent"],
  "agent workflow rule based ba cấp độ",
  "Khoá phân ba cấp độ: rule-based (luật cứng, đoán trước được), workflow (chuỗi bước cố định do người thiết kế), và agent (tự chọn bước tiếp theo dựa trên kết quả trung gian). Càng lên cao càng linh hoạt nhưng càng khó đoán và khó kiểm thử. Chọn mức thấp nhất giải quyết được bài toán, đừng mặc định dùng agent."),

 ("llm", "LLM hoạt động thế nào?",
  ["llm la gi", "mo hinh ngon ngu lon hoat dong ra sao"],
  "LLM dự đoán token hoạt động",
  "Bản chất LLM dự đoán token tiếp theo dựa trên toàn bộ ngữ cảnh đang có, lặp lại nhiều lần để sinh ra câu trả lời. Nó không tra cứu sự thật mà sinh chuỗi có xác suất cao — nên có thể phát biểu rất trôi chảy một điều sai."),

 ("prompt", "Prompt engineering là gì? Có phải train lại model không?",
  ["prompt engineering la gi", "prompt co phai train lai model khong"],
  "prompt engineering system prompt",
  "Không phải train lại. Prompt engineering là điều chỉnh phần đầu vào — bối cảnh, ví dụ, ràng buộc, định dạng đầu ra — để dẫn model tới câu trả lời mong muốn. Trọng số model không đổi. Fine-tuning mới là thứ đổi trọng số, và tốn kém hơn nhiều."),

 ("token", "Token và context window là gì?",
  ["token la gi", "context window la gi", "gioi han context"],
  "token context window giới hạn",
  "Token là đơn vị model cắt văn bản ra để xử lý, một từ tiếng Việt có thể thành nhiều token. Context window là số token tối đa model nhìn được trong một lượt, gồm cả prompt lẫn câu trả lời. Vượt quá thì phần cũ nhất bị cắt — đó là lý do hội thoại dài hay bị 'quên' đoạn đầu."),

 ("transformer", "Transformer và attention hoạt động ra sao?",
  ["attention la gi", "transformer hoat dong the nao"],
  "transformer attention",
  "Trước Transformer, model đọc tuần tự từng từ. Transformer đọc cả cụm cùng lúc và dùng attention để quyết định từ nào liên quan tới từ nào — nhờ vậy giữ được quan hệ ở xa và tính song song được. Bài báo gốc là 'Attention Is All You Need' (2017)."),

 ("rag", "RAG là gì? Khi nào dùng RAG thay vì fine-tuning?",
  ["rag la gi", "rag hay fine tuning", "khi nao fine tune"],
  "RAG fine-tuning chọn cái nào",
  "RAG là truy hồi tài liệu liên quan rồi đưa vào prompt để model trả lời dựa trên đó. Ưu tiên RAG khi kiến thức hay thay đổi và cần trích nguồn. Fine-tuning đòi dữ liệu chất lượng, kinh nghiệm huấn luyện và chi phí lặp lại mỗi lần dữ liệu đổi — thường không phải lựa chọn đầu tiên."),

 ("hallucin", "Hallucination là gì? Đặt temperature=0 có hết không?",
  ["hallucination la gi", "temperature 0 co het hallucinate khong"],
  "hallucination temperature",
  "Hallucination là model phát biểu điều nghe hợp lý nhưng không có căn cứ. temperature=0 chỉ làm đầu ra ổn định hơn giữa các lần chạy, KHÔNG loại bỏ hallucination — model vẫn sinh chuỗi có xác suất cao, và chuỗi đó vẫn có thể sai. Cách giảm thật sự là bắt model trả lời dựa trên nguồn và kiểm tra được nguồn."),

 ("automation", "Khi nào augment, khi nào automate?",
  ["augmentation hay automation", "muc do tu dong hoa"],
  "automation augmentation mức tự động hoá",
  "Chọn theo cost-of-error: sai thì ai chịu hậu quả, sửa đắt hay rẻ. Sai đắt và khó sửa thì để người quyết (augment). Đa số case lành, số ít hiểm thì để máy làm phần chắc và chuyển người phần mơ hồ (conditional). Sai rẻ, user tự thấy và sửa được thì automate. Thường bắt đầu từ augment rồi mới tăng dần."),

 ("benchmark", "Benchmark là gì? Có phải tự tạo cho mỗi bài toán không?",
  ["benchmark la gi", "moi de bai phai tu tao benchmark dung khong"],
  "benchmark đánh giá golden set",
  "Benchmark công khai đo năng lực chung của model, không đo được sản phẩm của bạn giải đúng bài toán của bạn hay chưa. Nên với mỗi bài toán cụ thể vẫn cần bộ case riêng, có nhãn đúng do nhóm tự định nghĩa và kiểm chứng được."),

 ("guardrail", "Guardrail là gì?",
  ["guardrail la gi", "chan model tra loi bay"],
  "guardrail an toàn giới hạn",
  "Guardrail là các lớp chặn đặt quanh model để nó không làm điều không được phép: chặn đầu vào độc hại, giới hạn phạm vi trả lời, kiểm tra đầu ra trước khi hiển thị, và có đường lui khi không chắc. Guardrail bằng luật cứng kiểm chứng được dễ hơn guardrail nhờ nhắc nhở trong prompt."),

 ("rlhf", "RLHF là gì?",
  ["rlhf la gi", "huan luyen theo phan hoi con nguoi"],
  "RLHF huấn luyện phản hồi",
  "RLHF là bước huấn luyện dùng phản hồi của con người để biến một model chỉ biết đoán token thành trợ lý biết làm theo yêu cầu: model sinh nhiều câu trả lời, người xếp hạng, rồi model được tối ưu theo xếp hạng đó."),

 ("cost of error", "Cost-of-error nghĩa là gì trong thiết kế sản phẩm AI?",
  ["cost of error la gi", "chi phi sai"],
  "cost of error sai thì ai chịu",
  "Là câu hỏi: khi AI sai thì ai gánh hậu quả, phát hiện được ngay không, và sửa đắt hay rẻ. Đây là căn cứ để chọn mức tự động hoá và để đặt ngưỡng — không phải chọn theo cảm giác tiện hay không tiện."),

 ("api", "Gọi API của LLM cần chú ý gì?",
  ["goi api llm", "system prompt la gi"],
  "API system prompt tham số",
  "Một lượt gọi gồm nhiều lớp: system prompt đặt vai trò và ràng buộc, phần ngữ cảnh, rồi câu hỏi của người dùng. System prompt nằm đầu nên có ảnh hưởng mạnh nhất. Ngoài ra còn các tham số như temperature và giới hạn token đầu ra."),

 ("workflow", "Các workflow pattern thường dùng?",
  ["workflow pattern", "chaining routing parallel"],
  "workflow pattern chaining routing parallel",
  "Bốn dạng hay gặp: chaining (nối các bước theo thứ tự), routing (phân loại rồi đưa vào nhánh phù hợp), parallel (chạy nhiều nhánh cùng lúc rồi gộp), và agent (tự quyết bước tiếp theo). Ba dạng đầu đoán trước được nên dễ kiểm thử hơn dạng cuối."),

 # --- Chu de KHONG CO trong tai lieu khoa: khai bao thang, khong bia ---
 ("react", "ReAct là gì?",
  ["react la gi", "react khac langgraph the nao"],
  None,
  "Chủ đề này chưa có trong tài liệu và transcript được cấp của khoá — 6 transcript hiện chỉ phủ nội dung Day 1 và Day 2. Trợ lý không tự giải thích để tránh nói sai. Hỏi Lab Coach hoặc đọc tài liệu chính thức của framework tương ứng."),

 ("zero shot", "Zero-shot, one-shot, few-shot, CoT khác nhau thế nào?",
  ["zero shot one shot few shot", "cot la gi"],
  None,
  "Phần này xuất hiện trên slide bài giảng nhưng chưa có đoạn giảng chi tiết trong transcript được cấp. Trợ lý chỉ nêu tên các khái niệm, không tự diễn giải sâu. Hỏi Lab Coach để được giải thích đầy đủ."),

 # ===== Bo sung dot 2 — chon theo so luot hoi THAT trong chatlog =====
 ("chatbot", "Làm chatbot cho doanh nghiệp thì bắt đầu từ đâu?",
  ["lam chatbot bat dau tu dau", "xay dung ai chatbot support"],
  "chatbot support bài toán mơ hồ",
  "Bắt đầu từ việc xác định chatbot giải bài toán gì, cho ai, thay thế cách làm nào — không bắt đầu từ công nghệ. Yêu cầu kiểu 'làm một AI chatbot support' là đề bài mơ hồ; phải bóc ra thành công việc cụ thể của một vai cụ thể thì mới triển khai và đo được."),

 ("tool", "Tool calling là gì? Khi nào cho model gọi tool?",
  ["tool calling la gi", "function calling la gi", "cho model goi tool khi nao"],
  "tool agent gọi công cụ",
  "Tool calling là cho model quyền gọi một hàm/API bên ngoài thay vì tự bịa kết quả — ví dụ tra cơ sở dữ liệu, tính toán, gửi truy vấn. Dùng khi câu trả lời cần dữ liệu model không có sẵn hoặc cần độ chính xác mà sinh chữ không đảm bảo. Mỗi tool thêm vào là thêm một chỗ có thể hỏng, nên chỉ thêm khi thật cần."),

 ("eval", "Đánh giá một sản phẩm AI thì đo bằng gì?",
  ["eval la gi", "danh gia san pham ai", "do chat luong ai"],
  "đánh giá quality bar golden set",
  "Không đo bằng cảm giác. Cách làm: chạy tay 10-20 đầu vào, đọc từng đầu ra, đặt tên cho từng loại lỗi thấy được, biến mỗi loại thành một tiêu chí kiểm chứng được (người ngoài chấm ra cùng kết quả), rồi mới xây bộ case và chốt ngưỡng đạt bằng con số trước khi đo."),

 ("guard", "Làm sao chặn model trả lời bậy hoặc ra ngoài phạm vi?",
  ["chan model tra loi bay", "gioi han pham vi tra loi"],
  "guardrail giới hạn phạm vi an toàn",
  "Ba lớp: chặn ở đầu vào (loại yêu cầu ngoài phạm vi trước khi gọi model), ràng buộc trong prompt (nêu rõ được làm gì, không được làm gì), và kiểm ở đầu ra (đối chiếu với nguồn, từ chối khi không có căn cứ). Lớp bằng luật cứng kiểm chứng dễ hơn lớp chỉ dựa vào nhắc nhở trong prompt."),

 ("memory", "Memory trong agent là gì?",
  ["memory la gi", "agent nho hoi thoai truoc"],
  "memory ngữ cảnh hội thoại",
  "Model không tự nhớ giữa các lượt gọi — mọi thứ nó 'nhớ' đều phải được đưa lại vào ngữ cảnh. Memory là cơ chế lưu và chọn lại phần đáng nhớ để nhét vào lượt sau. Vì context window có hạn nên phải chọn lọc, không thể nhét toàn bộ lịch sử."),

 ("latency", "Làm sao giảm độ trễ khi gọi LLM?",
  ["giam latency", "goi llm cham qua"],
  "độ trễ tốc độ phản hồi",
  "Vài hướng thường dùng: chọn model nhỏ hơn cho bước dễ, rút ngắn prompt và phần ngữ cảnh đưa vào, chạy song song các bước độc lập, hiển thị dần kết quả thay vì chờ trọn câu trả lời, và lưu lại kết quả cho câu hỏi lặp. Đo trước khi tối ưu để biết chỗ nào thật sự chậm."),

 ("routing", "Routing là gì trong thiết kế workflow?",
  ["routing la gi", "phan loai roi chuyen nhanh"],
  "routing phân loại nhánh workflow",
  "Routing là bước phân loại đầu vào rồi đưa vào nhánh xử lý phù hợp, thay vì dùng một đường chung cho mọi loại. Ưu điểm là mỗi nhánh tối ưu riêng được và đoán trước được hành vi; nhược điểm là phân loại sai thì cả nhánh sau sai theo, nên bước phân loại phải được đo riêng."),

 ("structured output", "Làm sao bắt model trả về JSON đúng định dạng?",
  ["structured output", "bat model tra ve json", "schema dau ra"],
  "định dạng đầu ra JSON schema",
  "Nêu rõ schema trong prompt kèm ví dụ, và dùng chế độ ép định dạng của nhà cung cấp nếu có. Quan trọng không kém: phía code phải chịu được đầu ra hỏng — model có thể trả JSON bị cắt giữa chừng hoặc kèm chữ thừa, nên luôn bọc bước phân tích trong xử lý lỗi và thử lại, đừng để một câu trả lời hỏng làm chết cả luồng."),

 ("fallback", "Khi AI không chắc thì nên làm gì?",
  ["khi ai khong chac", "fallback la gi", "chuyen nguoi that"],
  "không chắc thu hẹp phạm vi",
  "Không đoán liều. Ba đường lui theo mức độ: hỏi lại một câu để làm rõ, trả lời kèm giới hạn và nói rõ chỗ chưa chắc, hoặc từ chối và chuyển cho người có thẩm quyền. Chọn đường nào phụ thuộc cost-of-error — sai càng đắt thì càng phải nghiêng về chuyển người."),

 ("cost", "Chi phí gọi LLM tính thế nào, làm sao giảm?",
  ["chi phi goi llm", "token cost", "giam chi phi ai"],
  "chi phí token",
  "Chi phí tính theo token vào và token ra, nên prompt dài và câu trả lời dài đều tốn. Cách giảm: cắt phần ngữ cảnh không cần, dùng model nhỏ cho bước đơn giản, lưu lại kết quả câu hỏi lặp, và giới hạn độ dài đầu ra. Đo lượng token thật trước khi tối ưu."),

 ("mvp", "MVP trong sản phẩm AI nên gồm những gì?",
  ["mvp la gi", "lam mvp the nao"],
  "MVP lát cắt nhỏ nhất",
  "Một lát cắt đủ hẹp để chạy hết từ đầu đến cuối: một người dùng, một công việc, một quyết định AI, một kết quả. Đủ để đo xem quyết định AI đó có đúng không. Không phải bản rút gọn của toàn bộ sản phẩm, mà là một đường xuyên suốt mỏng nhất còn tạo ra giá trị."),

 ("intent", "Nhận diện intent để làm gì?",
  ["intent la gi", "phan loai y dinh nguoi dung"],
  "intent phân loại ý định",
  "Để trả lời đúng cỡ và đúng kiểu. Cùng một khung trả lời cho mọi loại câu hỏi sẽ sai với phần lớn: người chào hỏi, người hỏi bài, người hỏi thủ tục cần ba cách đáp khác nhau. Phân loại sai thì mọi bước sau sai theo, nên bước này phải có bộ case đo riêng."),

 ("privacy", "Đưa dữ liệu người dùng vào API AI có vấn đề gì?",
  ["gui data nguoi dung cho ai", "privacy khi dung api"],
  "bảo mật dữ liệu quy định",
  "Có ba thứ phải cân: nhà cung cấp có dùng dữ liệu để huấn luyện không (free tier thường có), dữ liệu có chứa thông tin cá nhân không, và người bị thu thập có biết không. Nguyên tắc an toàn: chỉ gửi phần tối thiểu cần cho việc đang làm, và không gửi dữ liệu thật của người thật khi chưa được phép."),

 ("monitoring", "Sau khi đưa sản phẩm AI vào dùng thì theo dõi gì?",
  ["theo doi san pham ai", "monitoring sau khi deploy"],
  "theo dõi đo lường sau triển khai",
  "Theo dõi tỷ lệ từ chối và chuyển người, tỷ lệ người dùng phản hồi tiêu cực, các câu hỏi hệ thống không trả lời được (đây là nguồn để mở rộng), độ trễ và chi phí. Quan trọng nhất là giữ được đường đi từ một câu trả lời tệ ngược về đúng nguồn và bước đã sinh ra nó."),

 ("bias", "Model có thiên lệch không? Xử lý thế nào?",
  ["bias trong model", "thien lech du lieu"],
  "thiên lệch dữ liệu huấn luyện",
  "Model học từ dữ liệu nên mang theo thiên lệch của dữ liệu đó. Không có cách xoá sạch; cách làm thực tế là biết mình đang dùng nó cho ai, kiểm thử riêng trên các nhóm dễ bị thiệt, và không dùng model một mình cho quyết định ảnh hưởng trực tiếp tới quyền lợi con người."),

 ("dataset", "Cần bao nhiêu dữ liệu để làm sản phẩm AI?",
  ["can bao nhieu du lieu", "dataset bao nhieu la du"],
  "dữ liệu chất lượng số lượng",
  "Với sản phẩm dựa trên model có sẵn, thứ cần không phải khối lượng dữ liệu huấn luyện mà là một bộ case đủ tốt để đo — vài chục case có nhãn đúng và phủ được các tình huống khó còn giá trị hơn hàng nghìn case dễ. Chỉ khi fine-tune mới cần dữ liệu quy mô lớn và chất lượng đồng đều."),

 ("stakeholder", "Sếp giao đề bài mơ hồ thì làm sao?",
  ["sep giao de bai mo ho", "yeu cau chung chung"],
  "yêu cầu mơ hồ bóc tách bài toán",
  "Đừng nhảy thẳng vào giải pháp. Hỏi lại để biết ai dùng, dùng lúc nào, hiện đang làm bằng cách gì và chỗ nào đang hỏng. Nếu người giao đề chưa rõ thì thử đưa một bản cụ thể để họ phản biện — thường phản biện trên một bản nháp cụ thể dễ hơn nhiều so với mô tả trừu tượng."),

 ("kpi", "Chọn chỉ số thành công cho sản phẩm AI thế nào?",
  ["chi so thanh cong", "kpi cho san pham ai"],
  "chỉ số thành công đo lường",
  "Chỉ số phải gắn với công việc của người dùng, không gắn với hoạt động của model. 'Số câu AI trả lời' không nói lên gì; 'tỷ lệ câu người dùng không phải hỏi lại người thật' thì có. Chọn chỉ số mà khi nó tăng, người dùng thật sự đỡ vất vả hơn."),

 ("mcp", "MCP là gì?",
  ["mcp la gi", "model context protocol"],
  None,
  "Chủ đề này chưa có trong tài liệu và transcript được cấp của khoá. Trợ lý không tự giải thích để tránh nói sai — đây cũng là loại claim học viên hay nhầm nguồn gốc. Hỏi Lab Coach hoặc đọc tài liệu chính thức của giao thức."),

 ("prompt injection", "Prompt injection là gì? Chặn thế nào?",
  ["prompt injection", "jailbreak", "bi lua lo system prompt"],
  None,
  "Chủ đề này chưa có đoạn giảng trong tài liệu được cấp. Nguyên tắc chung mà sản phẩm này đang áp dụng: không bao giờ hiển thị hoặc sửa system prompt, khoá kiến thức, khoá cấu hình theo yêu cầu người dùng, và mọi yêu cầu kiểu đó đều chuyển người phụ trách. Chi tiết sâu hơn hỏi Lab Coach."),
]


def count_asked() -> dict:
    """Dem THAT so luot hoc vien hoi tung chu de trong chatlog."""
    if not os.path.exists(CHATLOG):
        print(f"[!] Khong thay chatlog: {CHATLOG} -> asked_count = 0", file=sys.stderr)
        return {}
    rows = list(csv.DictReader(open(CHATLOG, encoding="utf-8")))
    cnt = {}
    for r in rows:
        if r.get("role") != "student":
            continue
        blob = _norm(r.get("content", ""))
        for key, *_ in FAQ:
            if key in blob:
                cnt[key] = cnt.get(key, 0) + 1
    return cnt


def build() -> list[dict]:
    counts = count_asked()
    try:
        import knowledge_index as K
    except Exception as e:
        print(f"[!] Khong nap duoc knowledge_index: {e}", file=sys.stderr)
        K = None

    faq = []
    for i, (key, q, variants, src_query, answer) in enumerate(FAQ, start=1):
        sources, gap = [], src_query is None
        if K is not None and src_query:
            for it in K.suggest_reading(src_query, top_k=2)["items"]:
                sources.append({
                    "code": it["code"],
                    "lecture": it["lecture"],
                    "heading": it["heading"],
                    "quote": it["quote"],
                })
            if not sources:
                gap = True
        faq.append({
            "id": f"faq_{i:03d}",
            "topic_key": key,
            "question": q,
            "variants": variants,
            "answer": answer,
            "sources": sources,
            "gap": gap,                       # True = chua co trong tai lieu khoa
            "asked_count": counts.get(key, 0),  # dem that tren chatlog
            "data_type": "tong_hop_tu_tai_lieu_khoa",
        })
    faq.sort(key=lambda x: -x["asked_count"])
    return faq


if __name__ == "__main__":
    faq = build()
    n_gap = sum(1 for f in faq if f["gap"])
    n_src = sum(len(f["sources"]) for f in faq)
    print(f"Sinh {len(faq)} câu FAQ · {n_src} trích dẫn có mã đoạn thật · {n_gap} chủ đề chưa có trong tài liệu")
    print(f"\n{'chủ đề':<16}{'đã hỏi':>8}  nguồn")
    for f in faq:
        codes = ", ".join(s["code"] for s in f["sources"]) or ("⚠️ CHƯA CÓ TRONG TÀI LIỆU" if f["gap"] else "—")
        print(f"  {f['topic_key']:<16}{f['asked_count']:>6} lượt  {codes}")

    if "--check" in sys.argv:
        bad = [f["id"] for f in faq if not f["gap"] and not f["sources"]]
        print(f"\nKiểm tra: {'ĐẠT' if not bad else 'LỖI — câu không gap mà thiếu nguồn: ' + str(bad)}")
        sys.exit(0 if not bad else 1)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(faq, f, ensure_ascii=False, indent=2)
    print(f"\nĐã ghi {OUT}")
