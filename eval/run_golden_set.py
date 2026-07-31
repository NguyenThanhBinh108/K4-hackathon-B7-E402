#!/usr/bin/env python3
"""
run_golden_set.py — chay eval/golden-set.csv qua san pham THAT, in bang ket qua.

Cham the nao (de nguoi ngoai nhom cham ra cung ket qua):
  - Cot `ky_vong` la intent (hoi_kien_thuc / hoi_campus / hoi_tai_lieu /
    ngoai_pham_vi / hoi_tai_lieu) HOAC verdict (VERIFIED / CONTRADICTED / ...)
    HOAC `risk_flag` (phai bi gan co rui ro).
  - DAT khi truong tuong ung cua san pham khop.
  - Rieng cac case "khong co trong tai lieu": DAT khi san pham NOI RO khong
    biet HOAC tra ve ngoai_pham_vi — tuc la khong bia.

Chay:
    python run_golden_set.py            # chay het
    python run_golden_set.py --limit 8  # chay thu 8 case dau
"""
import csv, json, os, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "..", "codebase", "kiem-chung-nguon"))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from source_verify import verify_message  # noqa: E402

CSV_IN = os.path.join(BASE, "golden-set.csv")
OUT = os.path.join(BASE, "ket-qua-luot-1.json")

INTENTS = {"hoi_kien_thuc", "hoi_campus", "hoi_tai_lieu", "ngoai_pham_vi", "kiem_chung"}


def cham(row, r) -> tuple[bool, str]:
    ky = (row["ky_vong"] or "").strip()
    if ky == "risk_flag":
        return bool(r.risk_flag), f"risk_flag={r.risk_flag}"
    if ky in INTENTS:
        # Khong bia = van tinh dat voi nhom "khong co trong tai lieu"
        if ky == "ngoai_pham_vi" and r.intent == "ngoai_pham_vi":
            return True, f"intent={r.intent}"
        return r.intent == ky, f"intent={r.intent}"
    return r.verdict == ky, f"verdict={r.verdict}"


def main() -> int:
    lim = None
    if "--limit" in sys.argv:
        lim = int(sys.argv[sys.argv.index("--limit") + 1])
    rows = list(csv.DictReader(open(CSV_IN, encoding="utf-8")))
    if lim:
        rows = rows[:lim]

    ket_qua, dat = [], 0
    print(f"{'ID':<5}{'KIỂU':<28}{'':<3}CHI TIẾT")
    print("-" * 88)
    for row in rows:
        try:
            r = verify_message({"id": row["id"], "author": "eval", "text": row["dau_vao"]})
            ok, chi_tiet = cham(row, r)
            mode = r.mode
        except Exception as e:
            ok, chi_tiet, mode = False, f"LỖI {type(e).__name__}: {e}", "ERROR"
        dat += ok
        ket_qua.append({
            "id": row["id"], "nguon": row["nguon"], "kieu_kho": row["kieu_kho"],
            "ky_vong": row["ky_vong"], "thuc_te": chi_tiet, "dat": ok, "mode": mode,
        })
        print(f"{row['id']:<5}{row['kieu_kho']:<28}{'✓' if ok else '✗'}  {chi_tiet} [{mode}]")
        time.sleep(0.2)          # tranh dinh rate limit cua nha cung cap

    n = len(rows)
    print("-" * 88)
    print(f"KẾT QUẢ: {dat}/{n} = {dat*100//n if n else 0}%")
    live = sum(1 for k in ket_qua if k["mode"] == "LIVE_AI")
    print(f"AI thật: {live}/{n} lượt  (MOCK/LỖI không tính là bằng chứng)")
    json.dump({"tong": n, "dat": dat, "live_ai": live, "chi_tiet": ket_qua},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Đã ghi {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
