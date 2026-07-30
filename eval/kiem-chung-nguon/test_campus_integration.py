#!/usr/bin/env python3
"""
test_campus_integration.py — kiem tra phan TICH HOP Campus Companion vao bot.

DO CAI GI
---------
KHONG do chat luong cua model (cai do can API key va do bang run_golden_set.py
--dim full). File nay do PHAN CODE CUA MINH: cho truoc mot cau tra loi cua LLM,
pipeline co dinh tuyen dung, co chan duoc truong hop bia nguon, va bot co dung
khung hien thi dung khong.

Vi sao tach ra: hai loai loi khac han nhau. Model tra loi sai thi doi prompt/
model; pipeline dinh tuyen sai thi sua code. Tron hai thu vao mot con so thi
khong biet phai sua o dau.

Chay:  python3 test_campus_integration.py     (KHONG can API key, khong ton quota)
"""

import os
import sys
from unittest.mock import patch

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "..", "..", "codebase", "kiem-chung-nguon"))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

import campus_kb                     # noqa: E402
import source_verify as SV           # noqa: E402


def run(text: str, llm_out: dict):
    """Chay verify_message voi mot cau tra loi LLM cho san."""
    with patch.object(SV, "llm_verify_claim", return_value=llm_out):
        return SV.verify_message({"id": "t", "author": "u", "text": text})


CASES = [
    (
        "trả lời được, có nguồn hợp lệ",
        "Trưa nay em ăn ở đâu được?",
        {"intent": "hoi_campus", "campus_decision": "answer",
         "campus_source_id": "campus_lunch_001",
         "answer": "Bạn ăn trưa tại khu campus dining được phép cho học viên.",
         "verdict": "UNVERIFIED_NO_SOURCE", "confidence_llm": 0},
        {"intent": "hoi_campus", "campus_decision": "answer", "co_nguon": True},
    ),
    (
        "BỊA NGUỒN — id không có trong KB thì phải bị hạ xuống chuyển Lab Coach",
        "Trưa nay em ăn ở đâu được?",
        {"intent": "hoi_campus", "campus_decision": "answer",
         "campus_source_id": "campus_KHONG_TON_TAI_999",
         "answer": "Ăn ở căn tin tầng 3, mở cửa 11h-13h.",
         "verdict": "UNVERIFIED_NO_SOURCE", "confidence_llm": 0},
        {"intent": "hoi_campus", "campus_decision": "chuyen_lab_coach", "co_nguon": False},
    ),
    (
        "nói trả lời được nhưng answer rỗng -> chuyển Lab Coach",
        "Gửi xe mất bao nhiêu tiền?",
        {"intent": "hoi_campus", "campus_decision": "answer",
         "campus_source_id": "campus_parking_001", "answer": "",
         "verdict": "UNVERIFIED_NO_SOURCE", "confidence_llm": 0},
        {"intent": "hoi_campus", "campus_decision": "chuyen_lab_coach", "co_nguon": False},
    ),
    (
        "hỏi lại khi câu hỏi mơ hồ",
        "Em nghỉ ở đâu được?",
        {"intent": "hoi_campus", "campus_decision": "hoi_lai",
         "answer": "Bạn hỏi về nghỉ trưa, thư viện hay phòng học?",
         "verdict": "UNVERIFIED_NO_SOURCE", "confidence_llm": 0},
        {"intent": "hoi_campus", "campus_decision": "hoi_lai", "co_nguon": False},
    ),
    (
        "quyết định lạ -> mặc định an toàn là chuyển người",
        "Thư viện mấy giờ đóng?",
        {"intent": "hoi_campus", "campus_decision": "tu_bia_ra_mot_gia_tri",
         "answer": "Mình chưa có giờ chính xác trong nguồn.",
         "verdict": "UNVERIFIED_NO_SOURCE", "confidence_llm": 0},
        {"intent": "hoi_campus", "campus_decision": "chuyen_lab_coach", "co_nguon": False},
    ),
    (
        "câu hỏi kiến thức vẫn đi luồng cũ, không bị campus nuốt",
        "attention trong transformer hoạt động thế nào",
        {"intent": "hoi_kien_thuc", "answer": "Attention cho phép model nhìn cả cụm.",
         "reading_codes": ["T04-038"], "verdict": "UNVERIFIED_NO_SOURCE", "confidence_llm": 0},
        {"intent": "hoi_kien_thuc", "campus_decision": "", "co_nguon": False},
    ),
    (
        "có link vẫn đi luồng kiểm chứng",
        "Paper này: https://arxiv.org/abs/2005.11401",
        {"intent": "kiem_chung", "verdict": "VERIFIED", "confidence_llm": 90,
         "explanation": "ok", "recommended_action": "đọc paper"},
        {"intent": "kiem_chung", "campus_decision": "", "co_nguon": False},
    ),
]


def main() -> int:
    print(f"Campus KB: {len(campus_kb.load_kb())} mục\n")
    print(f"{'':<4}{'intent':<16}{'quyết định':<20}{'nguồn':<8}{'tình huống'}")
    print("-" * 104)
    passed = 0
    for name, text, llm_out, want in CASES:
        r = run(text, llm_out)
        got = {
            "intent": r.intent,
            "campus_decision": r.campus_decision,
            "co_nguon": bool(r.campus_source),
        }
        ok = got == want
        passed += ok
        print(f"{'✓' if ok else '✗':<4}{got['intent']:<16}{got['campus_decision'] or '—':<20}"
              f"{'có' if got['co_nguon'] else '—':<8}{name}")
        if not ok:
            print(f"    mong đợi: {want}")
            print(f"    thực tế : {got}")

    # Khung hien thi cua bot khong test o day: build_embed() phu thuoc vao
    # discord.Client, gia lap no thi test do chinh ban gia lap chu khong do
    # code that. Phan do duoc kiem bang cach chay bot that va bam thu.

    total = len(CASES)
    print("-" * 104)
    print(f"{passed}/{total} đạt ({100*passed/total:.0f}%)")
    print("\nLƯU Ý: đây là test PIPELINE, không phải test chất lượng model.")
    print("Chất lượng model đo bằng: run_golden_set.py --dim full (cần API key còn quota).")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
