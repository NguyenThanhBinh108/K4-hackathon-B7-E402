#!/usr/bin/env python3
"""
test_knowledge_index.py — do LOP TU KHOA THO cua module "đọc bài nào".

DOC KY PHAN NAY TRUOC KHI DOC CON SO
-------------------------------------
Ban dau lop tu khoa vua lo do phu vua lo do chinh xac, va bo test nay do ca hai
(dat 12/13 = 92%). Sau khi do tren du lieu that, ba cach chan cau ngoai pham vi
bang tu khoa deu that bai — bag-of-words tren tieng Viet bo dau khong phan biet
duoc "thuat ngu cua khoa" voi "tu thong thuong" ('phở' -> 'pho' <- 'phổ biến').
Xem BAO-CAO-KIEM-CHUNG-DATA.md muc 3.

Nen kien truc da doi: tu khoa lo DO PHU (nguong ha xuong), LLM lo DO CHINH XAC
(loc lai trong llm_verify_claim). Vi vay bo test nay gio do DUNG MOT THU:

    DO PHU — cau hoi dung chu de khoa hoc thi PHAI ra duoc ung vien.

Phan "nen im lang" van chay va van in ra, nhung la SO THAM KHAO: o kien truc
moi, viec loai ung vien rac la nhiem vu cua buoc LLM, do bang
`run_golden_set.py --dim full`. Con so tut tu 92% xuong la HE QUA CO Y cua viec
doi kien truc, khong phai chat luong giam — do full pipeline thi 6 case kho
tang tu 2/6 len 4/6.

Chay:  python3 test_knowledge_index.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                                "codebase", "kiem-chung-nguon"))

import knowledge_index as K  # noqa: E402

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# (cau hoi, co nen goi y khong, ly do xep loai)
CASES = [
    # --- NEN goi y: dung chu de bai giang cua khoa ---
    ("cost of error là gì khi nào augment khi nào automate", True, "khái niệm lõi buổi 2"),
    ("attention trong transformer hoạt động thế nào", True, "buổi foundation"),
    ("prompt engineering co phai la train lai model khong", True, "gõ KHÔNG DẤU — phải vẫn hiểu"),
    ("fine-tuning hay RAG thì chọn cái nào", True, "có trong buổi 3"),
    ("làm sao xác định bài toán từ yêu cầu mơ hồ của sếp", True, "chủ đề mở đầu buổi 1"),
    ("token va context window la gi", True, "không dấu + thuật ngữ"),
    ("hallucination là gì, temperature=0 có hết hallucinate không", True, "claim sai ở M05"),
    ("double diamond là gì", True, "có mục riêng trong transcript"),
    # --- KHONG nen goi y: ngoai pham vi bai giang ---
    ("cách nấu phở bò", False, "bẫy bỏ dấu: phở→pho trùng phổ"),
    ("giá vàng hôm nay bao nhiêu", False, "toàn từ phổ biến, không đặc trưng"),
    ("mai đi đá bóng không mọi người", False, "tin nhắn tán gẫu"),
    ("hii", False, "tin cụt"),
    ("thời tiết Hà Nội ngày mai thế nào", False, "ngoài phạm vi hoàn toàn"),
]


def main() -> int:
    idx = K.get_index()
    n_slide = sum(1 for s in idx if s.code[0] == "D")
    print(f"Index: {len(idx)} đoạn ({len(idx)-n_slide} từ transcript + {n_slide} từ slide)\n")
    print(f"{'':<4}{'mong đợi':<10}{'thực tế':<10}{'câu hỏi':<52}{'đoạn đầu'}")
    print("-" * 100)

    pos = [c for c in CASES if c[1]]
    neg = [c for c in CASES if not c[1]]
    pos_ok = neg_ok = 0
    for query, expect, why in CASES:
        out = K.suggest_reading(query)
        got = out["found"]
        top = out["items"][0] if out["items"] else None
        ok = got == expect
        if expect and ok:
            pos_ok += 1
        elif not expect and ok:
            neg_ok += 1
        mark = "✓" if ok else ("✗" if expect else "·")
        top_s = "{} ({})".format(top["code"], top["score"]) if top else "—"
        exp_s = "gợi ý" if expect else "im lặng"
        got_s = "gợi ý" if got else "im lặng"
        print(f"{mark:<4}{exp_s:<10}{got_s:<10}{query[:50]:<52}{top_s}")

    print("-" * 100)
    print(f"ĐỘ PHỦ (tiêu chí đạt/không đạt): {pos_ok}/{len(pos)} câu đúng chủ đề ra được ứng viên "
          f"({100*pos_ok/len(pos):.0f}%)")
    print(f"Tham khảo — im lặng đúng ở lớp thô: {neg_ok}/{len(neg)}. "
          f"Lọc ứng viên rác là việc của bước LLM, đo bằng: run_golden_set.py --dim full")

    miss = [c for c in pos if not K.suggest_reading(c[0])["found"]]
    if miss:
        print("\nCâu đúng chủ đề mà KHÔNG ra ứng viên (lỗi độ phủ — phải sửa):")
        for q, _, why in miss:
            print(f"  · {q!r} — {why}")

    return 0 if pos_ok == len(pos) else 1


if __name__ == "__main__":
    sys.exit(main())
