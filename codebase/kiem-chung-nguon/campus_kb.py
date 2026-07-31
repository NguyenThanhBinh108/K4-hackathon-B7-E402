#!/usr/bin/env python3
"""
campus_kb.py — cau noi toi Campus Companion (nhanh Linh & Liem)

Nap `campus-companion/knowledge_base.json` de bot Discord tra loi duoc cau hoi
sinh hoat campus / quy dinh khoa: an trua, nghi trua, thu vien, gui xe, wifi,
ra vao campus, diem danh, kenh Discord, tai lieu...

VI SAO PORT SANG PYTHON MA KHONG GOI SERVER NODE
--------------------------------------------------
Ban Node (`campus-companion/server.mjs`) chay tot, nhung ghep vao bot Discord
theo kieu goi HTTP thi luc demo phai bat HAI tien trinh, quan ly hai cong,
va hai lan goi LLM cho mot tin nhan. Ghep thang: mot tien trinh, MOT lan goi
LLM, va KB van la MOT ban goc duy nhat — file JSON cua Linh & Liem, khong copy.

Doi ai sua KB thi ca hai ban (web Node va bot Discord) deu doi theo.
"""

import json
import os
import re
import sys
import unicodedata

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_PATH = os.environ.get("CAMPUS_KB_PATH") or os.path.join(
    BASE_DIR, "..", "..", "campus-companion", "knowledge_base.json"
)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", s)).strip()


_STOP = set(
    "la gi cua o dau khi nao may gio the nay minh moi nguoi co khong voi cho va "
    "nhe vay duoc bao nhieu can phai thi sao tu den trong ban em anh chi cac mot "
    "hay ma nua roi da se nhu ai do di ra vao ve tren duoi thi".split()
)


def _toks(s: str) -> set[str]:
    return {t for t in _norm(s).split(" ") if len(t) > 1 and t not in _STOP}


_KB: list | None = None


def load_kb() -> list:
    """Doc KB. Thieu file -> tra ve rong, KHONG lam chet bot (tinh nang campus
    tat, cac tinh nang khac van chay)."""
    global _KB
    if _KB is None:
        try:
            with open(KB_PATH, "r", encoding="utf-8") as f:
                _KB = json.load(f)
        except Exception as e:
            print(f"[!] Khong nap duoc Campus KB ({KB_PATH}): {e}", file=sys.stderr)
            _KB = []
    return _KB


def search(query: str, k: int = 4) -> list[dict]:
    """Tim muc KB lien quan. Nguong THAP co y — quyet dinh cuoi la cua LLM,
    giong nhu voi bai giang: tu khoa lo do phu, LLM lo do chinh xac."""
    kb = load_kb()
    if not kb:
        return []
    q = _toks(query)
    if not q:
        return []
    scored = []
    for item in kb:
        hay = _toks(
            f"{item.get('topic','')} {item.get('content','')} {item.get('source_title','')}"
        )
        hit = len(q & hay)
        if hit:
            scored.append((hit / len(q), hit, item))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return [it for score, _h, it in scored[:k] if score >= 0.12]


def format_for_prompt(items: list[dict]) -> str:
    if not items:
        return "khong tim thay muc nao"
    out = []
    for it in items:
        out.append(
            f"- [{it.get('id','?')}] (chu de: {it.get('topic','?')} · nguon: "
            f"{it.get('source_title','?')} — {it.get('source_location','?')} · "
            f"cap nhat {it.get('last_updated','?')}) {it.get('content','')[:320]}"
        )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# FAQ — "cau nay da co nguoi hoi roi"
# Dung chung co che tim kiem voi Campus KB nen de o day, khong tao them module.
# ---------------------------------------------------------------------------

_FAQ: list | None = None
FAQ_PATH = os.environ.get("FAQ_PATH") or os.path.join(BASE_DIR, "faq.json")


def load_faq() -> list:
    global _FAQ
    if _FAQ is None:
        try:
            with open(FAQ_PATH, "r", encoding="utf-8") as f:
                _FAQ = json.load(f)
        except Exception as e:
            print(f"[!] Khong nap duoc FAQ ({FAQ_PATH}): {e}", file=sys.stderr)
            _FAQ = []
    return _FAQ


def search_faq(query: str, k: int = 3) -> list[dict]:
    """Tim cau da tra loi truoc do. Tinh diem tren cau hoi + cac cach hoi khac
    + tu khoa chu de; cong nhe theo so luot da duoc hoi that (chu de hot thi
    kha nang la no hon)."""
    faq = load_faq()
    if not faq:
        return []
    q = _toks(query)
    if not q:
        return []
    out = []
    for item in faq:
        hay = _toks(" ".join([item.get("question", ""), item.get("topic_key", "")]
                             + list(item.get("variants", []))))
        hit = len(q & hay)
        if not hit:
            continue
        score = hit / len(q) + min(item.get("asked_count", 0), 100) / 1000.0
        out.append((score, item))
    out.sort(key=lambda x: -x[0])
    return [it for s, it in out[:k] if s >= 0.20]


def format_faq_for_prompt(items: list[dict]) -> str:
    if not items:
        return "khong co cau nao khop"
    lines = []
    for it in items:
        src = ", ".join(s["code"] for s in it.get("sources", [])) or "chua co nguon trong tai lieu khoa"
        lines.append(
            f"- [{it['id']}] (da co {it.get('asked_count',0)} hoc vien hoi · nguon: {src}"
            f"{' · CHU DE CHUA CO TRONG TAI LIEU KHOA' if it.get('gap') else ''}) "
            f"HOI: {it['question']} | DAP: {it['answer'][:300]}"
        )
    return "\n".join(lines)


def faq_by_id(faq_id: str) -> dict | None:
    for it in load_faq():
        if it.get("id") == faq_id:
            return it
    return None


def by_id(kb_id: str) -> dict | None:
    for it in load_kb():
        if it.get("id") == kb_id:
            return it
    return None


def topics() -> list[str]:
    """Cac chu de campus bot tra loi duoc — dung khi goi y cho nguoi dung."""
    seen, out = set(), []
    for it in load_kb():
        t = (it.get("topic") or "").strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    kb = load_kb()
    print(f"Campus KB: {len(kb)} mục · nguồn {os.path.normpath(KB_PATH)}")
    print("Chủ đề:", ", ".join(topics()))
    for q in sys.argv[1:] or [
        "trưa nay em ăn ở đâu được",
        "mang cơm từ nhà thì ngồi ăn chỗ nào",
        "thư viện mấy giờ đóng cửa",
        "gợi ý quán ăn ngon gần trường",
        "attention trong transformer là gì",
    ]:
        hits = search(q)
        print(f"\n{q!r} -> {len(hits)} mục")
        for h in hits:
            print(f"   [{h['id']}] {h['topic']} · {h['source_title']}")
