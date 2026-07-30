#!/usr/bin/env python3
"""
test_knowledge_index.py — bo case cho module "cần bổ sung kiến thức gì, đọc bài nào".

Do DUNG mot chieu chat luong duy nhat, kiem chung duoc: voi mot cau hoi, module
CO nen goi y doan bai giang hay KHONG. Nguoi ngoai nhom chay lai se ra cung ket qua.

Vi sao chieu nay quan trong hon "goi y co dung doan khong": goi y sai mot doan
bai giang lam hoc vien doc nham, con te hon la khong goi y gi. Nen bar dat o
cho "biet khi nao NEN IM LANG".

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
    print(f"Index: {len(idx)} đoạn từ 6 transcript\n")
    print(f"{'':<4}{'mong đợi':<10}{'thực tế':<10}{'câu hỏi':<52}{'đoạn đầu'}")
    print("-" * 100)

    passed = 0
    fails = []
    for query, expect, why in CASES:
        out = K.suggest_reading(query)
        got = out["found"]
        top = out["items"][0] if out["items"] else None
        mark = "✓" if got == expect else "✗"
        if got == expect:
            passed += 1
        else:
            fails.append((query, expect, got, why))
        exp_s = "gợi ý" if expect else "im lặng"
        got_s = "gợi ý" if got else "im lặng"
        top_s = f"{top['code']} ({top['score']})" if top else "—"
        print(f"{mark:<4}{exp_s:<10}{got_s:<10}{query[:50]:<52}{top_s}")

    pct = 100 * passed / len(CASES)
    print("-" * 100)
    print(f"{passed}/{len(CASES)} đạt ({pct:.0f}%)")

    if fails:
        print("\nCase chưa đạt — ghi nhận trung thực, không chỉnh ngưỡng cho vừa:")
        for q, e, g, why in fails:
            print(f"  · {q!r}\n    mong {'gợi ý' if e else 'im lặng'}, thực tế {'gợi ý' if g else 'im lặng'} — {why}")

    return 0 if pct >= 80 else 1


if __name__ == "__main__":
    sys.exit(main())
