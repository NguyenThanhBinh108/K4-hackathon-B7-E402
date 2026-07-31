#!/usr/bin/env python3
"""
doc_index.py — cau noi toi Knowledge Synthesis (nhanh Hai Dang)

Nap `codebase/backend/knowledge_base.json` — KB MUC TAI LIEU cua Hai Dang:
8 tai lieu (6 transcript + 2 slide), moi cai co title, module, level, so doan,
do tin cay, key_concepts, summary, key_takeaways.

VI SAO GHEP THANG MA KHONG CHAY BACKEND CUA DANG
--------------------------------------------------
Ban cua Dang la FastAPI o localhost:8000 + mot bot Discord rieng goi qua HTTP.
Chay song song hai bot cung mot token dan toi CHINH LOI da gap hom nay: hai bot
cung nghe, cung tra loi, nguoi dung nhan hai cau tra loi trung nhau. Nen:
  - Giu MOT bot duy nhat (BeeBee), MOT lan goi LLM cho moi tin nhan.
  - Doc thang file KB cua Dang, khong copy — ai sua thi ca hai ban deu doi theo.
  - Backend + frontend cua Dang van chay doc lap duoc cho demo web.

BO SUNG GI SO VOI knowledge_index.py
--------------------------------------
knowledge_index tra ve DOAN (703 doan, tra loi "cho nao noi ve X").
doc_index tra ve TAI LIEU (8 tai lieu, tra loi "buoi nao hoc gi", "tai lieu nao
noi ve embedding", "buoi 4 tom tat the nao"). Hai muc do khac nhau, bo tro nhau.
"""

import json
import os
import re
import sys
import unicodedata

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_KB_PATH = os.environ.get("DOC_KB_PATH") or os.path.join(
    BASE_DIR, "..", "backend", "knowledge_base.json"
)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", s)).strip()


_STOP = set(
    "la gi cua o dau khi nao may gio the nay minh moi nguoi co khong voi cho va "
    "nhe vay duoc bao nhieu can phai thi sao tu den trong ban em anh chi cac mot "
    "hay ma nua roi da se nhu ai do di ra vao ve".split()
)


def _toks(s: str) -> set[str]:
    return {t for t in _norm(s).split(" ") if len(t) > 1 and t not in _STOP}


_DOCS: list | None = None


def load_docs() -> list:
    """Doc KB tai lieu. Thieu file -> rong, KHONG lam chet bot."""
    global _DOCS
    if _DOCS is None:
        try:
            with open(DOC_KB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            _DOCS = data.get("documents", []) if isinstance(data, dict) else list(data)
        except Exception as e:
            print(f"[!] Khong nap duoc KB tai lieu ({DOC_KB_PATH}): {e}", file=sys.stderr)
            _DOCS = []
    return _DOCS


def search(query: str, k: int = 3) -> list[dict]:
    """Tim TAI LIEU lien quan. Uu tien khop key_concepts vi day la tu khoa da
    duoc chon loc san, dang tin hon la khop chu trong summary dai."""
    docs = load_docs()
    if not docs:
        return []
    q = _toks(query)
    if not q:
        return []
    out = []
    for d in docs:
        concepts = _toks(" ".join(d.get("key_concepts", []) or []))
        title = _toks(f"{d.get('title','')} {d.get('module','')} {d.get('level','')}")
        body = _toks(f"{d.get('summary','')} {' '.join(d.get('key_takeaways', []) or [])}")
        score = (
            2.0 * len(q & concepts) + 1.5 * len(q & title) + 1.0 * len(q & body)
        ) / len(q)
        if score > 0:
            out.append((score, d))
    out.sort(key=lambda x: -x[0])
    return [d for s, d in out[:k] if s >= 0.30]


def format_for_prompt(items: list[dict]) -> str:
    if not items:
        return "khong tim thay tai lieu nao"
    lines = []
    for d in items:
        seg = d.get("segments")
        lines.append(
            f"- [{d.get('id','?')}] \"{d.get('title','?')}\" ({d.get('type','?')}"
            f"{f' · {seg} doan' if seg else ''} · do tin cay {d.get('reliability','?')}"
            f" · module {d.get('module','?')}) "
            f"KHAI NIEM CHINH: {', '.join(d.get('key_concepts', [])[:8])}. "
            f"TOM TAT: {(d.get('summary') or '')[:280]}"
        )
    return "\n".join(lines)


def by_id(doc_id: str) -> dict | None:
    for d in load_docs():
        if str(d.get("id")) == str(doc_id):
            return d
    return None


def overview() -> list[dict]:
    """Danh sach tai lieu — dung khi nguoi dung hoi 'khoa co nhung tai lieu gi'."""
    return [
        {"id": d.get("id"), "title": d.get("title"), "type": d.get("type"),
         "module": d.get("module"), "segments": d.get("segments"),
         "reliability": d.get("reliability")}
        for d in load_docs()
    ]


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    docs = load_docs()
    print(f"KB tài liệu: {len(docs)} tài liệu · nguồn {os.path.normpath(DOC_KB_PATH)}")
    for d in overview():
        seg = f"{d['segments']} đoạn" if d["segments"] else "—"
        print(f"   {d['id']:<10}{d['type']:<11}{seg:>9} · tin cậy {d['reliability']:<5} · {d['title'][:44]}")
    print()
    for q in sys.argv[1:] or [
        "buổi nào học về transformer và attention",
        "tài liệu nào nói về embedding và token",
        "buổi 2 học gì",
        "trưa nay ăn ở đâu",
    ]:
        hits = search(q)
        print(f"{q!r} -> {[h['id'] for h in hits] or 'không có'}")
