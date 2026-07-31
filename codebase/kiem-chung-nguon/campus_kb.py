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


def _chuan_hoa(item: dict) -> dict:
    """FIX-26: doc duoc CA HAI luoc do.

    Ban cua Linh & Lieu (lay tu So tay hoc vien VinUni PDF chinh thuc) dung
    khoa tieng Viet: tieu_de / noi_dung / nguon / do_tin_cay / loai_du_lieu.
    Ban mo phong cu cua minh dung: topic / content / source_title.
    Chuan hoa ve mot dang de phan con lai khong phai biet su khac biet nay.
    """
    if "noi_dung" in item or "tieu_de" in item:
        return {
            "id": item.get("id", "?"),
            "topic": item.get("danh_muc") or item.get("tieu_de") or "?",
            "content": item.get("noi_dung", ""),
            "source_title": item.get("nguon", "?"),
            "source_location": item.get("url_nguon") or item.get("pham_vi_ap_dung", ""),
            "do_tin_cay": item.get("do_tin_cay", "?"),
            "loai_du_lieu": item.get("loai_du_lieu", "?"),
            "tham_quyen": item.get("tham_quyen", ""),
            "_raw": item,
        }
    return {
        "id": item.get("id", "?"),
        "topic": item.get("topic", "?"),
        "content": item.get("content", ""),
        "source_title": item.get("source_title", "?"),
        "source_location": item.get("source_location", ""),
        "do_tin_cay": "C",
        "loai_du_lieu": item.get("data_type", "mo_phong").upper(),
        "tham_quyen": "",
        "_raw": item,
    }


def load_kb() -> list:
    """Doc KB. Thieu file -> tra ve rong, KHONG lam chet bot (tinh nang campus
    tat, cac tinh nang khac van chay)."""
    global _KB
    if _KB is None:
        try:
            with open(KB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw = data.get("kb", []) if isinstance(data, dict) else list(data)
            _KB = [_chuan_hoa(x) for x in raw]
        except Exception as e:
            print(f"[!] Khong nap duoc Campus KB ({KB_PATH}): {e}", file=sys.stderr)
            _KB = []
    return _KB


# Uu tien khi hai muc cung khop: du lieu THAT tu So tay chinh thuc phai thang
# du lieu mo phong cua nhom. CHUA_CO xep duoi cung nhung KHONG bo — no chinh
# la cau tra loi dung cho nhung cau khoa chua co thong tin.
#
# He so phai NHO. Do lan dau voi 2.0: cau "trua nay toi muon di an" tra ve
# CT-07 (thoi luong chuong trinh) thay vi muc an uong, va "vang may buoi thi bi
# loai" bo qua 7 muc Chuyen can THAT. Boost manh khong phai uu tien nguon —
# no la lam hong do lien quan. 1.15 chi du de pha hoa khi diem xap xi nhau.
_UU_TIEN = {"THAT": 1.15, "MO_PHONG": 1.0, "CHUA_CO": 0.95}


# FIX-27: dong nghia tieng Viet — do duoc, khong doan.
# Cau "vang may buoi thi bi loai" KHONG khop 7 muc Chuyen can (THAT) vi So tay
# viet la "nghi" chu khong phai "vang", nen no roi xuong muc An uong mo phong.
# Day dung la lo hong bag-of-words da ghi nhan trong knowledge_index. Chi map
# nhung cap THAT SU gap trong data, khong bia them cho du.
_DONG_NGHIA = {
    "vang": ["nghi"], "nghi": ["vang"],
    "hoc bong": ["tro cap"], "tro cap": ["hoc bong", "sinh hoat phi"],
    "hoc phi": ["chi phi", "tro cap"],
    "diem danh": ["chuyen can", "nghi"], "chuyen can": ["diem danh", "nghi"],
    "duoi hoc": ["loai", "khong hoan thanh"], "loai": ["duoi hoc"],
    "an": ["cang tin", "an uong"], "cang tin": ["an uong"],
    "do xe": ["gui xe", "bai xe"], "gui xe": ["do xe", "bai xe"],
    "mang": ["wifi"], "wifi": ["mang"],
    "nop bai": ["deadline", "han nop"], "han nop": ["nop bai", "deadline"],
}


def _mo_rong(q: set[str]) -> set[str]:
    """Them tu dong nghia vao tap tu khoa truy van (khong thay the)."""
    out = set(q)
    for t in q:
        out.update(_DONG_NGHIA.get(t, []))
    joined = " ".join(sorted(q))
    for cum, dn in _DONG_NGHIA.items():
        if " " in cum and cum in joined:
            out.update(dn)
    return {w for x in out for w in x.split()}


def search(query: str, k: int = 4) -> list[dict]:
    """Tim muc KB lien quan. Nguong THAP co y — quyet dinh cuoi la cua LLM,
    giong nhu voi bai giang: tu khoa lo do phu, LLM lo do chinh xac."""
    kb = load_kb()
    if not kb:
        return []
    q = _mo_rong(_toks(query))
    if not q:
        return []
    scored = []
    for item in kb:
        hay = _toks(f"{item['topic']} {item['content']} {item['source_title']}")
        hit = len(q & hay)
        if hit:
            base = hit / len(q)
            scored.append((base * _UU_TIEN.get(item["loai_du_lieu"], 1.0), hit, item))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return [it for score, _h, it in scored[:k] if score >= 0.12]


def format_for_prompt(items: list[dict]) -> str:
    if not items:
        return "khong tim thay muc nao"
    out = []
    for it in items:
        loai = it.get("loai_du_lieu", "?")
        canh_bao = ""
        if loai == "MO_PHONG":
            canh_bao = " ⚠ DU LIEU MO PHONG, chua doi chieu phong hanh chinh"
        elif loai == "CHUA_CO":
            canh_bao = " ⚠ KHOA CHUA CO THONG TIN NAY — phai noi ro va chuyen nguoi phu trach"
        out.append(
            f"- [{it.get('id','?')}] (chu de: {it.get('topic','?')} · nguon: "
            f"{it.get('source_title','?')} · do tin cay {it.get('do_tin_cay','?')}"
            f"{canh_bao}) {it.get('content','')[:320]}"
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
