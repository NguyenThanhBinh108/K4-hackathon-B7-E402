#!/usr/bin/env python3
"""
knowledge_index.py — "Cần bổ sung kiến thức gì, đọc bài nào?"

Nhiem vu: cho mot claim/cau hoi, tim cac DOAN BAI GIANG lien quan trong 6
transcript cua khoa (data/vlearn-pack/transcript/) va tra ve MA DOAN [Txx-NNN]
+ trich ngan, de bot Discord tra loi kieu:

    Nên đọc thêm: buổi "Day 2 sáng — Xác định bài toán kinh doanh cho AI",
    đoạn [T01-004] — "công nghệ sinh ra để giải quyết một vấn đề..."

VI SAO KHONG DUNG EMBEDDING/VECTOR DB
--------------------------------------
~700 doan, chay tren may ca nhan, khong can. Keyword scoring + chuan hoa tieng
Viet khong dau da du va giai thich duoc (quan trong hon cho demo: mo ra la
thay TAI SAO doan do duoc chon). Neu sau nay corpus lon len thi thay dung
ham `search()` — phan con lai khong doi.

LUAT BAO MAT DATA PACK (doc ky truoc khi sua file nay)
-------------------------------------------------------
- Transcript KHONG duoc commit vao repo nop bai. File nay DOC transcript tu
  duong dan ben ngoai luc chay, khong copy noi dung vao repo.
- Moi thu tra ra ngoai (bot Discord, log, ket qua eval) CHI duoc chua MA DOAN
  + trich toi da MAX_QUOTE_CHARS ky tu. Khong bao gio dump ca doan.
- Khong day noi dung transcript vao API ben thu ba ngoai muc toi thieu can
  thiet (guide §3.4 — free tier co the dung data de train).
"""

import os
import re
import sys
import unicodedata

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Trich dan ra ngoai toi da bao nhieu ky tu — GIOI HAN BAO MAT, dung tang.
MAX_QUOTE_CHARS = 220

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# FIX-12: dung `or` chu KHONG dung tham so mac dinh cua os.environ.get().
# File .env co dong `TRANSCRIPT_DIR=` (de trong co y) -> bien TON TAI voi gia
# tri rong -> .get(key, default) tra ve chuoi rong chu khong tra ve default,
# lam tinh nang "nen doc lai bai nao" tat ngam. Dung `or` de chuoi rong cung
# roi ve duong dan mac dinh.
DEFAULT_TRANSCRIPT_DIR = os.environ.get("TRANSCRIPT_DIR") or os.path.join(
    BASE_DIR, "..", "..", "data", "vlearn-pack", "transcript"
)
# FIX-15: data pack CO 2 bo slide bai giang ma truoc day index khong dung.
# Do duoc: 6 transcript chi phu Day 1-Day 2 phan giang noi; nhieu thuat ngu
# hoc vien hoi that (RLHF, temperature, benchmark, RAG) nam o SLIDE chu khong
# nam trong loi giang. Nap them slide => tang do phu, va trich dan duoc theo
# so trang [D1-p07] dung nhu cach khoa quy dinh.
DEFAULT_SLIDE_DIR = os.environ.get("SLIDE_DIR") or os.path.join(
    BASE_DIR, "..", "..", "data", "vlearn-pack", "slides"
)

SEGMENT_RE = re.compile(r"\*\*\[(T\d{2}-\d{3})\]\*\*\s*(.+?)(?=\n\*\*\[T\d{2}-\d{3}\]\*\*|\n##|\Z)", re.S)
HEADING_RE = re.compile(r"^##\s+(.+)$", re.M)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.M)

_STOP = set(
    "la gi cua o dau khi nao may gio the nay minh moi nguoi co khong a oi voi cho va nhe vay "
    "duoc bao nhieu can phai thi sao tu den trong ban em anh chi cac mot hay ma nua roi da se nhu "
    "ai nhi do di ra vao ve tren duoi hoi tra loi ho biet nho cai nhung neu thi con lai rat "
    "cung deu tat ca minh chung ta ban se".split()
)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def toks(s: str) -> list[str]:
    return [t for t in norm(s).split(" ") if len(t) > 2 and t not in _STOP]


def toks_dau(s: str) -> set[str]:
    """Token GIU NGUYEN DAU tieng Viet — dung de chan nham lan sau khi bo dau.
    Vi du: 'phở' va 'phổ' deu ve 'pho' khi bo dau; giu ban co dau de phan biet.
    """
    s = re.sub(r"[^\w\s]", " ", (s or "").lower(), flags=re.UNICODE)
    return {t for t in s.split() if len(t) > 2}


def _has_dau(s: str) -> bool:
    """Nguoi dung co go dau khong? Neu go khong dau (rat pho bien tren Discord)
    thi KHONG duoc phat diem vi 'khong khop dau'."""
    return any(unicodedata.category(c) == "Mn" for c in unicodedata.normalize("NFD", s or ""))


class Segment:
    __slots__ = ("code", "text", "heading", "lecture", "file", "_tokens", "_tokens_dau")

    def __init__(self, code, text, heading, lecture, file):
        self.code = code
        self.text = text
        self.heading = heading
        self.lecture = lecture
        self.file = file
        self._tokens = set(toks(text + " " + heading))
        self._tokens_dau = toks_dau(text + " " + heading)

    def quote(self) -> str:
        """Trich ngan DUNG GIOI HAN BAO MAT — day la thu duy nhat duoc ra ngoai."""
        t = re.sub(r"\s+", " ", self.text).strip()
        return t if len(t) <= MAX_QUOTE_CHARS else t[:MAX_QUOTE_CHARS].rsplit(" ", 1)[0] + "…"

    def cite(self) -> str:
        return f"[{self.code}] {self.lecture}"


def build_index(transcript_dir: str = DEFAULT_TRANSCRIPT_DIR) -> list[Segment]:
    """Doc 6 file transcript, tach thanh cac doan co ma [Txx-NNN]."""
    if not os.path.isdir(transcript_dir):
        raise FileNotFoundError(
            f"Khong thay thu muc transcript: {transcript_dir}\n"
            "Dat bien moi truong TRANSCRIPT_DIR tro toi data/vlearn-pack/transcript/"
        )

    segments: list[Segment] = []
    for name in sorted(os.listdir(transcript_dir)):
        if not name.startswith("transcript-") or not name.endswith(".md"):
            continue
        path = os.path.join(transcript_dir, name)
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        title_m = TITLE_RE.search(raw)
        lecture = title_m.group(1).replace("Transcript bài giảng (bản sạch) — ", "").strip() if title_m else name

        # Ghi nho heading gan nhat truoc moi doan, de biet doan do thuoc muc nao
        heading_at: list[tuple[int, str]] = [(m.start(), m.group(1).strip()) for m in HEADING_RE.finditer(raw)]

        for m in SEGMENT_RE.finditer(raw):
            code, text = m.group(1), m.group(2).strip()
            if text.startswith("[Hoạt động lớp"):
                continue  # phan hanh chinh, khong phai kien thuc
            heading = ""
            for pos, h in heading_at:
                if pos < m.start():
                    heading = h
                else:
                    break
            segments.append(Segment(code, text, heading, lecture, name))
    return segments


def build_slide_index(slide_dir: str = DEFAULT_SLIDE_DIR) -> list[Segment]:
    """Nap 2 bo slide bai giang — moi TRANG la mot doan, ma trich dan [D1-p07].

    Best-effort: thieu pypdf hoac thieu file thi tra ve rong, KHONG lam chet
    ca index (transcript van dung duoc). Trang gan nhu khong co text (slide
    toan anh) bi bo qua.
    """
    if not os.path.isdir(slide_dir):
        return []
    try:
        from pypdf import PdfReader
    except ImportError:
        print("[!] Chua cai pypdf -> khong nap duoc slide vao index", file=sys.stderr)
        return []

    segs: list[Segment] = []
    for name in sorted(os.listdir(slide_dir)):
        if not name.lower().endswith(".pdf"):
            continue
        day = "D1" if name.lower().startswith("d1") else "D2" if name.lower().startswith("d2") else name[:2].upper()
        lecture = f"Slide bài giảng {'Day 1' if day == 'D1' else 'Day 2' if day == 'D2' else day}"
        try:
            reader = PdfReader(os.path.join(slide_dir, name))
        except Exception as e:
            print(f"[!] Khong doc duoc {name}: {e}", file=sys.stderr)
            continue
        for i, page in enumerate(reader.pages, start=1):
            try:
                text = (page.extract_text() or "").strip()
            except Exception:
                continue
            if len(text) < 40:
                continue  # trang toan anh / trang bia
            first_line = re.split(r"[\n\r]", text, maxsplit=1)[0].strip()[:80]
            segs.append(Segment(f"{day}-p{i:02d}", re.sub(r"\s+", " ", text),
                                first_line, lecture, name))
    return segs


_INDEX: list[Segment] | None = None
_IDF: dict[str, float] | None = None


def get_index(transcript_dir: str = DEFAULT_TRANSCRIPT_DIR) -> list[Segment]:
    global _INDEX
    if _INDEX is None:
        _INDEX = build_index(transcript_dir) + build_slide_index()
    return _INDEX


def get_idf() -> dict[str, float]:
    """IDF tren 645 doan. Ly do can: tu pho bien kieu 'cach', 'lam', 'viec'
    xuat hien o gan nhu moi doan nen khop chung KHONG chung minh dieu gi;
    neu dem token nhu nhau thi mot cau hoi ngoai pham vi van dat diem cao
    (do duoc: 'cách nấu phở bò' tung an 0.767 vi 'cach' + 'pho'<-'phổ').
    """
    global _IDF
    if _IDF is None:
        import math

        segs = get_index()
        df: dict[str, int] = {}
        for s in segs:
            for t in s._tokens:
                df[t] = df.get(t, 0) + 1
        n = len(segs)
        _IDF = {t: math.log(n / (1 + c)) + 0.1 for t, c in df.items()}
    return _IDF


# Nguong "khoi luong IDF" toi thieu de mot doan duoc coi la ung vien.
#
# LICH SU CHINH NGUONG NAY — ghi lai de dung tu chinh nua ma khong co du lieu:
# Da thu BA cach chan cau hoi ngoai pham vi bang tu khoa, deu do tren du lieu
# that va deu that bai:
#   1. Ty le khop IDF        -> 'giá vàng hôm nay' dat 0.70 (khop toan tu pho bien)
#   2. Khoi luong IDF >= 6.0 -> chan duoc cau rac, nhung chan luon 'benchmark la gi'
#                               (4.71) va 'ReAct... trong Agent' (5.62) — hoi dung
#                               chu de cot loi ma bi im lang
#   3. Max-IDF               -> 'cách nấu phở bò' co max 5.96 (tu 'nau' hiem),
#                               CAO HON ca 'benchmark' 4.71 -> khong phan tach duoc
#   4. Tu vung >=2 file nguon-> 940 tu, van dinh 'phở'<-'phổ biến', 'vàng', 'mai'
#
# Ket luan: bag-of-words tren tieng Viet bo dau KHONG the phan biet "thuat ngu
# cua khoa" voi "tu tieng Viet thong thuong". Nen doi kien truc: tu khoa lo
# DO PHU (nguong thap), LLM lo DO CHINH XAC (loc lai trong llm_verify_claim).
MIN_IDF_MASS = 3.0


def search(query: str, top_k: int = 3, min_score: float = 0.25) -> list[tuple[Segment, float]]:
    """Tim doan bai giang lien quan nhat toi query.

    Hai dieu kien PHAI thoa dong thoi:
      1. Ty le khop  = IDF(token khop) / IDF(token cua cau hoi CO trong bai giang)
                       >= min_score        -> doan nay noi dung y cau hoi
      2. Khoi luong  = IDF(token khop) >= MIN_IDF_MASS
                       -> nhung tu khop la tu DAC TRUNG, khong phai tu pho bien

    Vi sao tach lam hai: chi dung ty le thi 'giá vàng hôm nay bao nhiêu' van
    dat 0.7 (khop het tu pho bien); chi dung khoi luong thi cau dai lan man
    cung dat nguong. Do duoc tren 645 doan that.

    Token khong co trong bai giang (vd 'cost', 'error') bi loai khoi mau so
    thay vi bi phat — neu khong thi cau hoi dung tu tieng Anh se bi chan oan.
    """
    q = toks(query)
    if not q:
        return []
    qset = set(q)
    idf = get_idf()

    known = {t for t in qset if t in idf}
    # Khop theo TIEN TO cho tu dai: 'augment' -> 'augmentation',
    # 'automate' -> 'automation', 'transform' -> 'transformer'. Khong lam voi
    # tu ngan vi de dinh nham ('ban' -> 'bang', 'banh'...).
    for t in qset - known:
        if len(t) >= 5:
            known |= {v for v in idf if v.startswith(t) or t.startswith(v) and len(v) >= 5}
    if not known:
        return []
    denom = sum(idf[t] for t in known)

    q_dau = toks_dau(query)
    query_co_dau = _has_dau(query)

    scored = []
    for seg in get_index():
        matched = known & seg._tokens
        if not matched:
            continue
        mass = sum(idf[t] for t in matched)

        # He so khop dau: chi ap dung khi nguoi dung CO go dau. Token khop sau
        # khi bo dau nhung ban co dau khong xuat hien trong doan -> nghi ngo
        # nham (phở/phổ, mua/mưa, ban/bận...).
        if query_co_dau:
            agree = len(q_dau & seg._tokens_dau)
            mass *= 0.45 + 0.55 * min(1.0, agree / len(matched))

        if mass < MIN_IDF_MASS:
            continue

        score = mass / denom
        if qset & set(toks(seg.heading)):
            score += 0.08
        if score >= min_score:
            scored.append((seg, round(score, 3)))

    scored.sort(key=lambda x: -x[1])
    return scored[:top_k]


def suggest_reading(claim: str, top_k: int = 3, per_lecture: int = 1) -> dict:
    """Dau ra dung cho bot Discord.

    Tra ve dict:
      {"found": bool, "items": [{"code","lecture","heading","quote","score"}]}
    Khong tim thay -> found=False, va bot PHAI noi ro "khong thay trong bai
    giang cua khoa" thay vi bia ra mot buoi hoc nao do.

    FIX-13 (`per_lecture`): do tren 40 cau hoi that lay tu chatlog, **25/34
    truong hop top-k tra ve nhieu doan CUNG MOT BUOI** — nguoi doc phai doc hai
    lan gan nhu cung mot chuyen, va mat co hoi biet buoi khac cung noi ve no.
    Gio moi buoi chi lay doan diem cao nhat; muon nhieu doan cung buoi thi tang
    `per_lecture`.
    """
    # Lay du roi moi loc, de sau khi bo trung van con du top_k
    hits = search(claim, top_k=top_k * 4)

    picked: list[tuple[Segment, float]] = []
    seen_per_lecture: dict[str, int] = {}
    for seg, sc in hits:
        n = seen_per_lecture.get(seg.lecture, 0)
        if n >= per_lecture:
            continue
        seen_per_lecture[seg.lecture] = n + 1
        picked.append((seg, sc))
        if len(picked) >= top_k:
            break

    return {
        "found": bool(picked),
        "items": [
            {
                "code": s.code,
                "lecture": s.lecture,
                "heading": s.heading,
                "quote": s.quote(),
                "score": sc,
            }
            for s, sc in picked
        ],
    }


if __name__ == "__main__":
    idx = get_index()
    print(f"Da nap {len(idx)} doan tu {os.path.normpath(DEFAULT_TRANSCRIPT_DIR)}")
    by_file: dict[str, int] = {}
    for s in idx:
        by_file[s.file] = by_file.get(s.file, 0) + 1
    for f, n in sorted(by_file.items()):
        print(f"  {f}: {n} doan")

    demos = sys.argv[1:] or [
        "cost of error là gì, khi nào thì augment khi nào automate",
        "làm sao xác định bài toán từ yêu cầu mơ hồ của sếp",
        "attention trong transformer hoạt động thế nào",
        "cách nấu phở bò",  # phai tra RONG
    ]
    for q in demos:
        print(f"\n--- {q!r}")
        out = suggest_reading(q)
        if not out["found"]:
            print("  (không thấy đoạn nào liên quan trong bài giảng — đúng như mong đợi nếu câu hỏi ngoài phạm vi)")
        for it in out["items"]:
            print(f"  [{it['code']}] score={it['score']} · {it['lecture']}")
            print(f"      mục: {it['heading']}")
            print(f"      “{it['quote']}”")
