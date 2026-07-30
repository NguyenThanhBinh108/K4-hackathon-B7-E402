#!/usr/bin/env python3
"""
rescore_results.py — tinh lai `final_credibility_score` cho mot file ket qua
DA CHAY, bang cong thuc `aggregate_score()` hien tai trong source_verify.py.

VI SAO CAN FILE NAY
-------------------
Cong thuc diem tin cay da duoc sua (xem ghi chu FIX-01 trong source_verify.py):
truoc day diem = 0.4*domain + 0.6*llm_confidence, khien mot claim DA BI KET LUAN
LA SAI (CONTRADICTED) van duoc 54/100. Cac file ket qua chay truoc do dang giu
diem tinh theo cong thuc cu.

Chay lai toan bo 17 case voi API that thi ton quota va thoi gian, trong khi
verdict/explanation cua AI KHONG doi — chi cong thuc gop diem doi. Script nay
tinh lai DUNG truong `final_credibility_score` tu cac truong da luu san
(verdict, domain_score, url_reachable, content_extracted, risk_flag), giu
nguyen moi thu khac.

DAY KHONG PHAI LA SUA SO LIEU: verdict, explanation, llm_confidence, moi thu
AI that tra ve deu duoc giu nguyen. Chi cong thuc gop cuoi duoc ap lai. File
goc luon duoc backup thanh *.bak truoc khi ghi de.

Cach dung:
    python3 rescore_results.py ../../eval/kiem-chung-nguon/last-run-results.json
    python3 rescore_results.py <file> --dry-run     # chi xem, khong ghi
"""

import json
import os
import shutil
import sys

from source_verify import aggregate_score, NOT_SCORABLE_VERDICTS

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def rescore(path: str, dry_run: bool = False) -> int:
    with open(path, "r", encoding="utf-8") as f:
        results = json.load(f)

    changed = 0
    print(f"{'id':<6}{'verdict':<38}{'cu':>5}{'moi':>6}")
    print("-" * 55)
    for r in results:
        old = r.get("final_credibility_score")
        new = aggregate_score(
            r.get("verdict", "UNVERIFIED_NO_SOURCE"),
            r.get("domain_score", 0),
            r.get("url_reachable"),
            bool(r.get("content_extracted")),
        )
        # Rui ro cao van bi ha tran nhu trong verify_message()
        if r.get("risk_flag"):
            new = min(new, 15)

        r["final_credibility_score"] = new
        r["score_applicable"] = r.get("verdict") not in NOT_SCORABLE_VERDICTS
        r.setdefault("extract_reason", "ok" if r.get("content_extracted") else "")

        mark = "" if old == new else "  <-- doi"
        if old != new:
            changed += 1
        print(f"{r['message_id']:<6}{r['verdict']:<38}{old:>5}{new:>6}{mark}")

    print("-" * 55)
    print(f"{changed}/{len(results)} case doi diem")

    if dry_run:
        print("(--dry-run: khong ghi file)")
        return changed

    backup = path + ".bak"
    shutil.copyfile(path, backup)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Da ghi {path}\nBan cu giu tai {os.path.basename(backup)}")
    return changed


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("Dung: python3 rescore_results.py <duong-dan-file-ket-qua.json> [--dry-run]")
        sys.exit(1)
    rescore(args[0], dry_run="--dry-run" in sys.argv)
