#!/usr/bin/env python3
"""
run_golden_set.py — chay golden-set.csv va in bang ket qua co %.

HAI CHIEU CHAT LUONG, chay rieng duoc vi gia khac han nhau:

  --dim goiy   (mac dinh, MIEN PHI)  Do LOP TU KHOA THO, truoc khi LLM loc.
               Lop nay CO Y de nguong thap de an do phu — con so o day KHONG
               phai chat luong san pham, no la dau vao cho buoc loc. Dung de
               theo doi do phu: neu tut xuong thi tu khoa dang bo sot.

  --dim full   (TON QUOTA AI)        Do SAN PHAM THAT: verdict + goi y sau khi
               LLM da loc ung vien. Day moi la con so dua vao spec §7.
               31 case ~ 31 luot goi LLM, moi luot 10-40 giay.

Chay:
    python3 run_golden_set.py                  # chieu goi y, mien phi
    python3 run_golden_set.py --dim full       # co AI that
    python3 run_golden_set.py --dim full --only G01,M05
"""

import argparse
import csv
import os
import re
import sys
import time
from collections import Counter

# ---------------------------------------------------------------------------
# CHIEU C5 — DUNG NGON NGU (them 30/07 sau khi do duoc loi tai lap)
#
# Prompt ghi ro "PHAI viet HOAN TOAN bang tieng Viet", nhung model free
# nemotron lien tuc chen chu Trung/Nhat/Han/Tay Ban Nha vao giua cau tieng
# Viet. Da thay qua nhieu luot chay doc lap: 决定論 (M05), 官方 (M14),
# 발표 (M03). Day KHONG phai ngau nhien.
#
# Dinh nghia kiem chung duoc (nguoi ngoai nhom cham ra cung ket qua):
#   FAIL neu output chua BAT KY ky tu nao thuoc bang chu KHONG PHAI Latin
#   (Han/Nhat/Han Quoc/Kirin/Thai/A Rap).
#
# Gioi han da biet: khong bat duoc lan tieng Anh/Tay Ban Nha ('khôngofficial',
# 'crédito') vi chung dung chung bang chu Latin. Chieu nay do PHAN DO DUOC,
# khong tu nhan la do het.
# ---------------------------------------------------------------------------
NON_LATIN = re.compile(
    "["
    "一-鿿"      # Han (Trung/Nhat kanji)
    "぀-ヿ"      # Hiragana + Katakana
    "가-힯"      # Hangul
    "Ѐ-ӿ"      # Kirin
    "฀-๿"      # Thai
    "؀-ۿ"      # A Rap
    "]"
)


def check_language(*texts) -> tuple[bool, str]:
    """Tra ve (dat, ky_tu_vi_pham). dat=True nghia la khong lan chu ngoai."""
    bad = []
    for t in texts:
        bad += NON_LATIN.findall(t or "")
    return (not bad), "".join(dict.fromkeys(bad))[:20]

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "..", "..", "codebase", "kiem-chung-nguon"))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

GOLDEN = os.path.join(BASE, "golden-set.csv")


def load_cases(only=None):
    rows = list(csv.DictReader(open(GOLDEN, encoding="utf-8")))
    if only:
        want = {x.strip() for x in only.split(",")}
        rows = [r for r in rows if r["id"] in want]
    return rows


def dim_goiy(rows):
    """Chieu C4 — goi y bai giang. Ky vong 'co' / 'khong' / 'co|khong' (chap nhan ca hai)."""
    import knowledge_index as K

    print(f"{'id':<6}{'lớp':<20}{'mong đợi':<12}{'thực tế':<10}{'đoạn gợi ý'}")
    print("-" * 104)
    passed = fails = 0
    for r in rows:
        exp = r["ky_vong_goi_y_bai_giang"].strip()
        out = K.suggest_reading(r["input"])
        got = "co" if out["found"] else "khong"
        ok = got in {x.strip() for x in exp.split("|")}
        passed += ok
        fails += (not ok)
        codes = ", ".join(f"{i['code']}" for i in out["items"]) or "—"
        print(f"{r['id']:<6}{r['lop']:<20}{exp:<12}{got:<10}{'✓ ' if ok else '✗ '}{codes}")
    total = len(rows)
    print("-" * 104)
    print(f"C4 · gợi ý bài giảng: {passed}/{total} đạt ({100*passed/total:.1f}%)")
    return passed, total


def dim_full(rows):
    """Do san pham that: C2 verdict + C4 goi y sau khi LLM loc. GOI AI THAT."""
    from source_verify import verify_message

    print(f"{'id':<6}{'lớp':<20}{'verdict thực tế':<38}{'điểm':<6}{'gợi ý':<22}{'ngôn ngữ'}")
    print("-" * 122)
    p_verdict = p_goiy = p_lang = 0
    results = []
    for i, r in enumerate(rows):
        try:
            res = verify_message({"id": r["id"], "author": "golden", "text": r["input"]})
        except Exception as e:
            print(f"{r['id']:<6}{r['lop']:<20}LỖI {type(e).__name__}: {str(e)[:60]}")
            continue

        ok_v = res.verdict in {x.strip() for x in r["ky_vong_verdict"].split("|")}
        got_g = "co" if res.reading else "khong"
        ok_g = got_g in {x.strip() for x in r["ky_vong_goi_y_bai_giang"].split("|")}
        ok_l, bad = check_language(res.explanation, res.recommended_action, res.claim)
        p_verdict += ok_v
        p_goiy += ok_g
        p_lang += ok_l
        results.append((r, res, ok_v, ok_g, ok_l, bad))

        codes = ",".join(c["code"] for c in (res.reading or [])) or "—"
        print(f"{r['id']:<6}{r['lop']:<20}"
              f"{('✓ ' if ok_v else '✗ ') + res.verdict:<38}"
              f"{res.final_credibility_score:<6}"
              f"{('✓ ' if ok_g else '✗ ') + codes:<22}"
              f"{'✓' if ok_l else '✗ lẫn: ' + bad}")
        # Nghi giua cac luot de khong dinh rate limit free tier
        if i < len(rows) - 1:
            time.sleep(3)

    total = len(results) or 1
    print("-" * 122)
    print(f"C2 · định tuyến/verdict : {p_verdict}/{total} đạt ({100*p_verdict/total:.1f}%)")
    print(f"C4 · gợi ý bài giảng    : {p_goiy}/{total} đạt ({100*p_goiy/total:.1f}%)")
    print(f"C5 · đúng ngôn ngữ      : {p_lang}/{total} đạt ({100*p_lang/total:.1f}%)")
    cand = sum(x[1].reading_candidates for x in results)
    kept = sum(len(x[1].reading or []) for x in results)
    print(f"     (LLM giữ {kept}/{cand} đoạn từ khoá đề xuất — phần bị loại là giá trị của bước lọc)")

    hard = [x for x in results if x[0]["lop"].startswith("①")]
    bad_hard = [x[0]["id"] for x in hard if not x[2]]
    print(f"\nĐiều kiện cứng — lớp ① không được trả lời khẳng định khi không có căn cứ: "
          f"{'ĐẠT' if not bad_hard else 'KHÔNG ĐẠT ' + str(bad_hard)}")

    lang_fail = [(x[0]["id"], x[5]) for x in results if not x[4]]
    if lang_fail:
        print(f"\nCase lẫn chữ nước ngoài ({len(lang_fail)}): " +
              ", ".join(f"{i} ({b})" for i, b in lang_fail))

    modes = Counter(x[1].mode for x in results)
    print(f"\nChế độ chạy: {dict(modes)}")
    if modes.get("MOCK"):
        print("⚠️  Có case chạy MOCK — số này KHÔNG dùng làm bằng chứng AI thật.")
    return p_verdict, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dim", choices=["goiy", "full"], default="goiy")
    ap.add_argument("--only", help="chỉ chạy vài case, vd G01,M05")
    args = ap.parse_args()

    rows = load_cases(args.only)
    print(f"Golden set: {len(rows)} case · nguồn: "
          f"{dict(Counter('chatlog thật' if r['nguon'].startswith('chatlog') else 'tự soạn' for r in rows))}")
    print(f"Phân bố lớp: {dict(Counter(r['lop'] for r in rows))}\n")

    if args.dim == "goiy":
        p, t = dim_goiy(rows)
    else:
        p, t = dim_full(rows)

    print("\nQuality bar trong spec: ≥80% pass C1+C2, C3 trung bình ≥3,5, "
          "và 0 case lớp ① trả lời khẳng định khi không có căn cứ.")
    print("Ghi kết quả này vào spec §7 — kể cả khi chưa đạt bar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
