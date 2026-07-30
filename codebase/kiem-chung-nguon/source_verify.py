#!/usr/bin/env python3
"""
source_verify.py — Prototype "Kiem Chung Nguon" (Source Verification Assistant)
Vibecode Kit / K4 Hackathon — Huong B (Tro ly Hoc vien, Discord)

MUC TIEU
--------
Input: 1 tin nhan chia se kien thuc (text, co the kem link).
Output: verdict kiem chung + do tin cay + trich dan + giai thich, theo dung
        thiet ke trong spec-draft-kiem-chung-nguon.md (§4-§6).

TRANG THAI DATA (quan trong)
-----------------------------
Nhom KHONG co quyen truy cap Discord API / bot token cho kenh that cua khoa,
va theo luat hackathon KHONG duoc dung du lieu that cua nguoi that ngoai
data pack duoc cap. Vi vay script nay doc tin nhan tu file JSON gia lap
(`eval/mock-messages.json`) thay vi goi Discord API. Ham `load_messages()`
la diem duy nhat can thay the khi nhom co bot token that (xem ghi chu
trong ham do) — phan pipeline ben duoi khong phu thuoc vao nguon input.

AI CALL THAT (bat buoc theo luat hackathon — muc do nao cung phai co >=1)
--------------------------------------------------------------------------
Buoc `llm_verify_claim()` goi mot LLM that qua OpenRouter (uu tien, model
mac dinh nvidia/nemotron-3-super-120b-a12b:free qua OPENROUTER_API_KEY),
hoac fallback Gemini (GEMINI_API_KEY) / Claude (ANTHROPIC_API_KEY) de: tach
claim, danh gia claim co can nguon ngoai khong, va sinh verdict + giai
thich. NEU CHUA CO API KEY NAO (vd dang chay thu trong sandbox truoc khi
nhom cam key that), script tu dong chuyen sang MOCK MODE — dung heuristic
don gian de pipeline van chay end-to-end, va IN RO CANH BAO do khong phai
la AI that. Truoc khi nop/demo, nhom BAT BUOC phai export mot trong 3 key
tren de day la loi goi AI that dung nhu luat.

Chay thu:
    python3 source_verify.py                          # mock mode neu chua co key
    OPENROUTER_API_KEY=xxx python3 source_verify.py    # AI that qua OpenRouter (uu tien)
    GEMINI_API_KEY=xxx python3 source_verify.py        # AI that qua Gemini
    ANTHROPIC_API_KEY=xxx python3 source_verify.py     # AI that qua Claude
"""

import json
import os
import re
import sys
import time
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    requests = None

try:
    import trafilatura
except ImportError:
    trafilatura = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

from risk_patterns import scan_risk_patterns

# FIX-01: console Windows mac dinh dung codepage cp1252, in tieng Viet co dau
# la UnicodeEncodeError -> crash ngay tin nhan dau tien. Ep stdout/stderr sang
# UTF-8 truoc khi in bat cu thu gi. (Python 3.7+; khong anh huong macOS/Linux.)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Gioi han ky tu noi dung trich xuat dua vao prompt LLM — du de doi chieu
# claim voi doan mo dau/abstract, khong lam prompt qua dai (ton token, de
# vuot context window cua model free tier qua OpenRouter).
MAX_EXTRACT_CHARS = 1500
FETCH_TIMEOUT_SECONDS = 8


def fetch_source_content(url: str) -> tuple[str | None, str]:
    """Tai va trich xuat noi dung CHINH (bo boilerplate menu/quang cao) tu 1 URL,
    de LLM doi chieu claim voi noi dung THAT thay vi chi doan theo domain tier.

    Ho tro:
      - Trang HTML thuong (paper abstract page, GitHub README, doc site) qua trafilatura.
      - File PDF truc tiep (vd link arxiv.org/pdf/...) qua pypdf, doc vai trang dau.

    FIX-04: tra ve (noi_dung | None, LY_DO). Truoc day chi tra None nen khi
    THIEU THU VIEN (chua pip install trafilatura) san pham van bao "chua trich
    xuat duoc noi dung that (PDF anh/JS-required/bi chan)" — do loi SAI nguyen
    nhan, nguoi xem tuong link co van de. Gio phan biet ro:
        "ok"                 — trich xuat duoc
        "thieu-thu-vien"     — chua cai trafilatura/pypdf/requests
        "khong-trich-xuat"   — link that su khong doc duoc (PDF anh, chan bot, JS, timeout)
    Caller PHAI fallback ve danh gia theo domain-tier, KHONG duoc crash pipeline.
    """
    if requests is None:
        return None, "thieu-thu-vien"
    try:
        is_pdf_url = url.lower().split("?")[0].endswith(".pdf")

        if is_pdf_url:
            if PdfReader is None:
                return None, "thieu-thu-vien"
            resp = requests.get(url, timeout=FETCH_TIMEOUT_SECONDS, allow_redirects=True)
            resp.raise_for_status()
            ctype = resp.headers.get("content-type", "")
            if "pdf" not in ctype and "pdf" not in url.lower():
                return None, "khong-trich-xuat"
            from io import BytesIO
            reader = PdfReader(BytesIO(resp.content))
            text_parts = []
            for page in reader.pages[:3]:  # vai trang dau du cho abstract/intro
                text_parts.append(page.extract_text() or "")
            text = "\n".join(text_parts).strip()
        else:
            if trafilatura is None:
                return None, "thieu-thu-vien"
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None, "khong-trich-xuat"
            text = trafilatura.extract(downloaded) or ""
            text = text.strip()

        if not text:
            return None, "khong-trich-xuat"
        return text[:MAX_EXTRACT_CHARS], "ok"
    except Exception:
        # Bat moi loi (timeout, 403, PDF scan anh khong co text layer, HTML
        # loi ma hoa, v.v.) — day la best-effort, khong phai buoc bat buoc.
        return None, "khong-trich-xuat"


def missing_optional_libs() -> list[str]:
    """FIX-04: liet ke thu vien tuy chon con thieu, de canh bao RO o dau moi
    lan chay thay vi de tinh nang trich xuat noi dung tat am tham."""
    missing = []
    if requests is None:
        missing.append("requests")
    if trafilatura is None:
        missing.append("trafilatura")
    if PdfReader is None:
        missing.append("pypdf")
    return missing


def _load_dotenv(path: str | None = None) -> None:
    """Doc file .env don gian (KEY=VALUE moi dong), khong can cai python-dotenv.

    Chi set bien moi truong neu CHUA duoc set san (os.environ.setdefault) —
    de bien export thu cong trong shell van uu tien hon file .env.
    Mac dinh tim file .env nam CUNG THU MUC voi source_verify.py. File nay
    da nam trong .gitignore (*.env) nen khong lo bi commit nham.
    """
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()

            # FIX-11: cat chu thich cung dong. Truoc day dong
            #     AUTO_MIN_LEN=80          # bo qua tin ngan hon bay nhieu ky tu
            # cho ra gia tri '80          # bo qua...' -> int() nem ValueError
            # va bot chet ngay luc khoi dong. Chu thich trong ngoac kep thi giu.
            if value[:1] in ('"', "'"):
                quote = value[0]
                end = value.find(quote, 1)
                value = value[1:end] if end > 0 else value[1:]
            else:
                value = re.split(r"\s+#", value, maxsplit=1)[0].strip()

            if key:
                os.environ.setdefault(key, value)


_load_dotenv()


# ---------------------------------------------------------------------------
# 1. DOMAIN TRUST TIER — heuristic ranh gioi cho nguon (khong can AI cho buoc nay)
# ---------------------------------------------------------------------------

DOMAIN_TIERS = {
    # tier: (nhan, diem_co_so 0-100)
    "paper": (
        ["arxiv.org", "aclanthology.org", "dl.acm.org", "openreview.net",
         "pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov", "semanticscholar.org"],
        90,
    ),
    "official-doc": (
        ["docs.claude.com", "docs.anthropic.com", "ai.google.dev",
         "platform.openai.com", "docs.python.org", "developer.mozilla.org",
         "pytorch.org", "huggingface.co/docs", "modelcontextprotocol.io"],
        88,
    ),
    "github": (["github.com", "gitlab.com"], 70),
    "reputable-blog": (
        ["openai.com/blog", "anthropic.com/news", "ai.googleblog.com",
         "research.google", "deepmind.google"],
        75,
    ),
}

# TLD/domain danh rieng cho tai lieu/kiem thu (IANA reserved) -> khong phai nguon that
RESERVED_TEST_DOMAINS_SUFFIX = (".example", ".test", ".invalid", ".localhost")


def classify_domain(url: str) -> tuple[str, int]:
    """Tra ve (tier_label, base_score) cho mot URL, khong goi AI — chi tra cuu bang."""
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return ("unparseable", 5)

    if host.endswith(RESERVED_TEST_DOMAINS_SUFFIX) or any(
        host.endswith(suf) for suf in RESERVED_TEST_DOMAINS_SUFFIX
    ):
        return ("reserved-test-domain-not-real", 5)

    for tier, (domains, score) in DOMAIN_TIERS.items():
        if any(host == d or host.endswith("." + d) or d in host for d in domains):
            return (tier, score)

    return ("unknown-domain", 30)


def check_url_reachable(url: str, timeout: int = 6) -> bool | None:
    """Kiem tra URL co that/con truy cap duoc khong. None = khong kiem tra duoc (offline/lib thieu)."""
    if requests is None:
        return None
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code >= 400:
            resp = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
        return resp.status_code < 400
    except Exception:
        return False


URL_RE = re.compile(r"https?://[^\s)>\]]+")

# FIX-08: dau cau dinh o CUOI url khi nguoi ta viet "... https://abc.com, ..."
# truoc day bi bat vao url -> sinh ra url rac kieu "https://agentrouter.org,"
# (thay trong M15). Cat cac ky tu nay o cuoi, KHONG cat o giua url.
_TRAILING_PUNCT = ".,;:!?\"'"


def extract_urls(text: str) -> list[str]:
    urls = []
    for raw in URL_RE.findall(text):
        cleaned = raw.rstrip(_TRAILING_PUNCT)
        if cleaned and cleaned not in urls:
            urls.append(cleaned)
    return urls


# ---------------------------------------------------------------------------
# 2. LLM CALL THAT — day la buoc "AI chay that" theo luat hackathon
# ---------------------------------------------------------------------------

VERIFY_PROMPT_TEMPLATE = """Ban la AI kiem chung nguon cho kenh chia se kien thuc AI cua mot khoa hoc (~1000 hoc vien).
Nhiem vu: doc mot tin nhan, tach claim chinh, va danh gia CO CAN THAN TRONG — khong duoc doan lieu.

Tin nhan: "{text}"
Link kem theo (neu co): {urls}
Loai nguon cua link (da tra cuu truoc, khong can AI doan lai): {domain_info}
Noi dung THAT trich xuat tu link (neu trich xuat duoc, da cat con {max_chars} ky tu dau): {extracted_content}
Rui ro da phat hien truoc boi rule-based scan (neu co, KHONG duoc tu y bo qua hay ha thap muc do nghiem trong cua nhung dieu nay): {risk_reasons}

Tra loi CHINH XAC theo dinh dang JSON sau, khong them chu gi khac:
{{
  "claim": "cau claim chinh duoc trich ra",
  "verdict": "VERIFIED | PARTIALLY_VERIFIED | UNVERIFIED_NO_SOURCE | CONTRADICTED | OPINION_NOT_APPLICABLE | PARTIALLY_CORRECT | VERIFIED_SELF_PUBLISHED_TRANSPARENT | OUT_OF_SCOPE_POLICY_QUESTION",
  "confidence_llm": <so 0-100, muc do AI tu tin vao verdict nay>,
  "explanation": "giai thich ngan gon, gan voi hanh dong tiep theo cho nguoi doc",
  "risk_class": "mot hoac nhieu trong ①②③④, cach nhau bang dau phay",
  "recommended_action": "nguoi doc nen lam gi tiep theo"
}}

QUY TAC BAT BUOC:
- Tat ca gia tri text (claim, explanation, recommended_action) PHAI viet HOAN TOAN bang tieng Viet. KHONG duoc chen tu tieng Anh/Trung/Nga/Y hay ngon ngu khac vao giua cau (tru ten rieng/thuat ngu ky thuat khong co ban dich, vd "gradient checkpointing").
- Neu khong co link VA ban khong chac chan claim nay dung/sai tu kien thuc nen tang cua minh -> verdict PHAI la UNVERIFIED_NO_SOURCE, KHONG duoc doan.
- Neu day la y kien chu quan (vd so sanh "cai nay nhanh hon cai kia" khong co benchmark) -> verdict PHAI la OPINION_NOT_APPLICABLE, khong phan xu dung/sai.
- Neu day la cau hoi ve chinh sach/thẩm quyen nen tang (vd co duoc phep dung mot ky thuat/cach lam nao do theo dieu khoan nen tang khong) chu khong phai mot claim kien thuc dung/sai -> verdict PHAI la OUT_OF_SCOPE_POLICY_QUESTION, khong tu phan xu "duoc" hay "khong duoc".
- Neu day la nguon tu xuat ban nhung minh bach ve tac gia (khong gia danh to chuc khac) -> co the dung VERIFIED_SELF_PUBLISHED_TRANSPARENT thay vi VERIFIED thuong.
- Neu "Rui ro da phat hien truoc" KHONG rong -> giai thich PHAI nhac lai it nhat 1 ly do rui ro do, va recommended_action PHAI uu tien canh bao rui ro nay truoc khi noi ve do tin cay noi dung thong thuong.
- Neu "Noi dung THAT trich xuat tu link" CO gia tri (khong phai "khong trich xuat duoc") -> BAT BUOC doi chieu claim voi noi dung nay truoc tien. Neu claim KHOP voi noi dung -> co the dung VERIFIED (khong chi PARTIALLY_VERIFIED). Neu claim MAU THUAN voi noi dung trich xuat -> verdict PHAI la CONTRADICTED du domain co uy tin the nao.
- Neu "Noi dung THAT trich xuat tu link" la "khong trich xuat duoc" (vd PDF anh, trang chan bot, het thoi gian) -> KHONG duoc coi day la dau hieu xau, chi danh gia lui ve domain-tier nhu binh thuong, va PHAI ghi ro trong explanation la "chua doi chieu duoc noi dung that, chi danh gia theo do uy tin domain".
- KHONG duoc tu bia ra mot URL/nguon khong co trong "Link kem theo" de lam bang chung.
"""


class LLMUnavailable(Exception):
    pass


def llm_verify_claim(
    text: str,
    urls: list[str],
    domain_info: str,
    risk_reasons: list[str] | None = None,
    extracted_content: str | None = None,
) -> dict:
    """Goi LLM that (OpenRouter uu tien, fallback Gemini/Anthropic).
    Neu khong co API key -> raise LLMUnavailable de caller chuyen sang mock mode.
    """
    prompt = VERIFY_PROMPT_TEMPLATE.format(
        text=text,
        urls=urls or "khong co",
        domain_info=domain_info,
        max_chars=MAX_EXTRACT_CHARS,
        extracted_content=(extracted_content if extracted_content else "khong trich xuat duoc"),
        risk_reasons=("; ".join(risk_reasons) if risk_reasons else "khong co"),
    )

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if openrouter_key and requests is not None:
        # OpenRouter — dung chung 1 endpoint OpenAI-compatible cho nhieu model,
        # uu tien truoc Gemini/Anthropic neu co OPENROUTER_API_KEY.
        model_name = os.environ.get(
            "OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free"
        )
        max_retries = 4
        backoff_seconds = 8
        last_error = None
        for attempt in range(max_retries):
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            if resp.status_code == 429:
                last_error = f"429 Too Many Requests (lan thu {attempt + 1}/{max_retries})"
                print(f"  [rate-limit] {last_error} -> cho {backoff_seconds}s roi thu lai...", file=sys.stderr)
                time.sleep(backoff_seconds)
                backoff_seconds *= 2
                continue

            # OpenRouter doi khi tra ve HTTP 200 nhung body khong co "choices"
            # ma la {"error": {...}} — vd model free dang qua tai, khong co
            # provider nao rang, hoac noi dung bi content-filter. Truoc day
            # code doc thang data["choices"] -> KeyError lam crash toan bo
            # script giua chung 17 message. Gio bat loi nay giong 429: log
            # ro rang, thu lai vai lan, khong crash ca pipeline vi 1 message.
            try:
                data = resp.json()
            except ValueError:
                data = {}

            if resp.status_code >= 400 or "choices" not in data:
                err_msg = data.get("error", {}).get("message") if isinstance(data.get("error"), dict) else data.get("error")
                last_error = f"HTTP {resp.status_code}, body error: {err_msg or data}"
                print(f"  [openrouter-error] lan thu {attempt + 1}/{max_retries}: {last_error} -> cho {backoff_seconds}s roi thu lai...", file=sys.stderr)
                time.sleep(backoff_seconds)
                backoff_seconds *= 2
                continue

            raw = data["choices"][0]["message"]["content"]
            return _parse_llm_json(raw)
        raise LLMUnavailable(f"OpenRouter loi sau {max_retries} lan thu: {last_error}")

    if gemini_key and requests is not None:
        # Goi Gemini REST API truc tiep (khong can cai SDK rieng)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={gemini_key}"
        )
        # Retry voi backoff cho 429 (Too Many Requests) — free tier Gemini
        # gioi han so request/phut, goi 14 message lien tiep rat de dinh rate
        # limit. KHONG coi 429 la "khong co key" — day la loi tam thoi, retry
        # duoc, khac voi LLMUnavailable (thieu key hoan toan).
        max_retries = 4
        backoff_seconds = 8
        last_error = None
        for attempt in range(max_retries):
            resp = requests.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30,
            )
            if resp.status_code == 429:
                last_error = f"429 Too Many Requests (lan thu {attempt + 1}/{max_retries})"
                print(f"  [rate-limit] {last_error} -> cho {backoff_seconds}s roi thu lai...", file=sys.stderr)
                time.sleep(backoff_seconds)
                backoff_seconds *= 2
                continue
            resp.raise_for_status()
            data = resp.json()
            raw = data["candidates"][0]["content"]["parts"][0]["text"]
            return _parse_llm_json(raw)
        raise LLMUnavailable(f"Gemini bi rate-limit sau {max_retries} lan thu: {last_error}")

    if anthropic_key and requests is not None:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-5",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = data["content"][0]["text"]
        return _parse_llm_json(raw)

    raise LLMUnavailable(
        "Chua tim thay OPENROUTER_API_KEY, GEMINI_API_KEY hay ANTHROPIC_API_KEY "
        "trong bien moi truong (hoac trong file .env cung thu muc)."
    )


def _parse_llm_json(raw: str) -> dict:
    """Tach JSON tu cau tra loi cua LLM.

    FIX-10: model reasoning (vd nemotron qua OpenRouter) hay viet mot doan suy
    nghi truoc roi moi ra JSON — kieu "Okay, the user wants me to... {json}".
    Ban cu goi thang json.loads() nen gap truong hop do la nem JSONDecodeError,
    ma loi nay KHONG duoc bat o verify_message() (chi bat LLMUnavailable) ->
    chet ca luot chay giua chung. Gio: bo rao ```json, roi neu van khong parse
    duoc thi cat lay khoi { ... } ngoai cung.
    """
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(json)?", "", raw).rstrip("`").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Thu parse tu TUNG dau '{' — raw_decode tu biet doan JSON ket thuc o dau,
    # nen chiu duoc ca truong hop model viet mot dau '{' hong o doan suy nghi
    # phia truoc roi moi ra JSON that.
    decoder = json.JSONDecoder()
    for i, ch in enumerate(raw):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(raw, i)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj:
            return obj
    raise ValueError(f"Khong tach duoc JSON tu cau tra loi cua LLM: {raw[:200]!r}")


def mock_llm_verify_claim(
    text: str, urls: list[str], domain_info: str, risk_reasons: list[str] | None = None
) -> dict:
    """MOCK MODE — chi dung khi khong co API key, de chung minh pipeline chay
    end-to-end. Day KHONG PHAI AI that — chi la heuristic tu-khoa don gian.
    BAT BUOC thay bang llm_verify_claim() that truoc khi demo/nop bai.
    """
    if risk_reasons:
        return {
            "claim": text[:120],
            "verdict": "UNVERIFIED_NO_SOURCE",
            "confidence_llm": 10,
            "explanation": (
                "[MOCK MODE] Rule-based scan da phat hien rui ro: "
                + "; ".join(risk_reasons[:2])
            ),
            "risk_class": "④,①",
            "recommended_action": "CANH BAO: khong nen lam theo huong dan nay cho den khi tu kiem chung doc lap.",
        }

    lower = text.lower()
    if urls and "paper" in domain_info:
        verdict, conf = "VERIFIED", 85
    elif urls and ("official-doc" in domain_info or "github" in domain_info):
        verdict, conf = "PARTIALLY_VERIFIED", 65
    elif urls and "reserved-test-domain" in domain_info:
        verdict, conf = "UNVERIFIED_NO_SOURCE", 10
    elif "không chắc" in lower or "ai xác nhận" in lower or "nghe nói" in lower:
        verdict, conf = "UNVERIFIED_NO_SOURCE", 20
    elif "có ai" in lower and "không" in lower:
        verdict, conf = "OPINION_NOT_APPLICABLE", 0
    else:
        verdict, conf = "UNVERIFIED_NO_SOURCE", 30

    return {
        "claim": text[:120],
        "verdict": verdict,
        "confidence_llm": conf,
        "explanation": "[MOCK MODE — chua co API key that, day la heuristic don gian de test pipeline]",
        "risk_class": "①",
        "recommended_action": "Cam OPENROUTER_API_KEY (hoac GEMINI_API_KEY / ANTHROPIC_API_KEY) de co verdict AI that.",
    }


# ---------------------------------------------------------------------------
# 3. AGGREGATE — gop domain tier + LLM verdict thanh 1 diem tin cay cuoi
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    message_id: str
    author: str
    text: str
    urls: list
    domain_tier: str
    domain_score: int
    url_reachable: object
    claim: str
    verdict: str
    llm_confidence: int
    final_credibility_score: int
    explanation: str
    risk_class: str
    recommended_action: str
    mode: str  # "LIVE_AI" hoac "MOCK"
    risk_flag: bool = False          # TIP-02 — rui ro tai chinh/bao mat, tach khoi credibility
    risk_reasons: list = None        # TIP-02 — ly do cu the (tu rule-based scan_risk_patterns)
    content_extracted: bool = False  # TIP-05 — co trich xuat duoc noi dung that tu link khong
    extract_reason: str = ""         # FIX-04 — ok | thieu-thu-vien | khong-trich-xuat
    score_applicable: bool = True    # FIX-01 — False voi y kien ca nhan / cau hoi chinh sach


# ---------------------------------------------------------------------------
# FIX-01 — LOI NGHIEM TRONG NHAT DA SUA: diem tin cay tung tinh NGUOC HUONG.
#
# Cong thuc cu:  0.4 * domain_score + 0.6 * llm_confidence
# Van de: prompt dinh nghia `confidence_llm` la "muc do AI TU TIN VAO VERDICT",
# khong phai "muc do claim dang tin". Nen AI cang chac chan rang "cai nay SAI"
# thi diem tin cay cang CAO. Hau qua do duoc tren lươt chay that:
#     M05 CONTRADICTED (claim sai su that)  -> 54/100
#     M02 UNVERIFIED_NO_SOURCE              -> 79/100  (thanh mau XANH tren UI)
# Voi mot san pham ve NIEM TIN thi day la loi chet nguoi.
#
# Cong thuc moi: VERDICT quyet dinh DAI DIEM, chat luong bang chung (domain_score
# + co doi chieu duoc noi dung that khong) quyet dinh VI TRI TRONG DAI.
# `llm_confidence` KHONG con duoc cong vao diem tin cay nua — no chi con y nghia
# la do tin cua AI vao phan quyet, van duoc luu lai trong ket qua de tra cuu.
# ---------------------------------------------------------------------------

VERDICT_BANDS = {
    # Tran 95 chu khong phai 100 la co y: mot san pham kiem chung nguon khong
    # nen bao gio tuyen bo chac chan tuyet doi (HAX G2 — dat ky vong thap hon
    # kha nang mot chut, dung nguoc lai).
    "VERIFIED":                            (70, 95),
    "VERIFIED_SELF_PUBLISHED_TRANSPARENT": (60, 90),
    "PARTIALLY_VERIFIED":                  (40, 70),
    "PARTIALLY_CORRECT":                   (35, 65),
    "UNVERIFIED_NO_SOURCE":                (0, 35),
    "CONTRADICTED":                        (0, 10),
    # Hai verdict duoi day KHONG phai phan xu dung/sai -> khong co "do tin cay"
    "OPINION_NOT_APPLICABLE":              (0, 0),
    "OUT_OF_SCOPE_POLICY_QUESTION":        (0, 0),
}

NOT_SCORABLE_VERDICTS = {"OPINION_NOT_APPLICABLE", "OUT_OF_SCOPE_POLICY_QUESTION"}


def aggregate_score(
    verdict: str,
    domain_score: int,
    url_reachable,
    content_extracted: bool = False,
) -> int:
    """Diem tin cay 0-100. Dai diem do VERDICT quyet dinh; vi tri trong dai do
    CHAT LUONG BANG CHUNG quyet dinh. Khong dung llm_confidence (xem ghi chu tren).
    """
    low, high = VERDICT_BANDS.get(verdict, VERDICT_BANDS["UNVERIFIED_NO_SOURCE"])
    if high == low:
        return low

    # Suc manh bang chung 0..1: domain_score la chinh, doi chieu duoc noi dung
    # that thi cong them (day la dung y cua TIP-05 — noi dung that > doan theo domain).
    evidence = domain_score / 100.0
    if content_extracted:
        evidence = min(1.0, evidence + 0.15)

    score = low + (high - low) * evidence

    # Link chet/khong truy cap duoc -> tru thang, nhung khong tut khoi day dai.
    if url_reachable is False:
        score = max(low, score - 20)

    return int(round(score))


def verify_message(msg: dict) -> VerificationResult:
    text = msg["text"]
    urls = extract_urls(text)

    if urls:
        tier, score = classify_domain(urls[0])
        reachable = check_url_reachable(urls[0])
        # TIP-05: thu trich xuat noi dung THAT tu link dau tien de doi chieu
        # claim, thay vi chi doan theo domain-tier. Best-effort — None neu
        # khong trich xuat duoc (PDF scan anh, trang chan bot, JS-required...).
        extracted_content, extract_reason = fetch_source_content(urls[0])
    else:
        tier, score, reachable = "no-url", 0, None
        extracted_content, extract_reason = None, "khong-co-link"

    domain_info = f"{tier} (diem co so {score})" if urls else "khong co link"

    # TIP-01/02: rule-based risk scan CHAY TRUOC LLM — LLM chi duoc dien giai
    # them, khong tu quyet risk_flag tu dau (tranh bo sot vi "nghe hop ly")
    risk_flag, risk_reasons = scan_risk_patterns(text, urls)

    mode = "LIVE_AI"
    try:
        llm_out = llm_verify_claim(text, urls, domain_info, risk_reasons, extracted_content)
    except LLMUnavailable as e:
        print(f"  [!] {e} -> chuyen sang MOCK MODE cho message {msg['id']}", file=sys.stderr)
        llm_out = mock_llm_verify_claim(text, urls, domain_info, risk_reasons)
        mode = "MOCK"

    verdict = llm_out.get("verdict", "UNVERIFIED_NO_SOURCE")
    final_score = aggregate_score(verdict, score, reachable, bool(extracted_content))
    if risk_flag:
        # Case rui ro cao khong nen doc theo thang tin cay thong thuong —
        # ha ran credibility de khong bao gio hien nhu "kha tin" trong danh
        # sach thuong, nhung gia tri thuc su nam o risk_flag/risk_reasons
        final_score = min(final_score, 15)

    return VerificationResult(
        message_id=msg["id"],
        author=msg.get("author", "?"),
        text=text,
        urls=urls,
        domain_tier=tier,
        domain_score=score,
        url_reachable=reachable,
        claim=llm_out.get("claim", text[:120]),
        verdict=verdict,
        llm_confidence=int(llm_out.get("confidence_llm", 0)),
        final_credibility_score=final_score,
        explanation=llm_out.get("explanation", ""),
        risk_class=llm_out.get("risk_class", ""),
        recommended_action=llm_out.get("recommended_action", ""),
        mode=mode,
        risk_flag=risk_flag,
        risk_reasons=risk_reasons,
        content_extracted=bool(extracted_content),
        extract_reason=extract_reason,
        score_applicable=verdict not in NOT_SCORABLE_VERDICTS,
    )


# ---------------------------------------------------------------------------
# 4. INPUT LOADER — DIEM DUY NHAT CAN THAY BANG DISCORD API THAT SAU NAY
# ---------------------------------------------------------------------------

def load_messages(path: str) -> list:
    """Doc tin nhan tu file JSON gia lap.

    Khi nhom co bot token that cho kenh Discord cua khoa, thay ham nay bang
    vd. discord.py on_message listener goi verify_message() cho tung tin
    nhan moi trong kenh #chia-se-kien-thuc. Phan con lai cua pipeline
    (classify_domain, llm_verify_claim, aggregate_score) khong doi.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_discord_reply(r: VerificationResult) -> str:
    verdict_emoji = {
        "VERIFIED": "✅",
        "VERIFIED_SELF_PUBLISHED_TRANSPARENT": "✅",
        "PARTIALLY_VERIFIED": "🟡",
        "UNVERIFIED_NO_SOURCE": "❔",
        "CONTRADICTED": "❌",
        "OPINION_NOT_APPLICABLE": "💬",
        "PARTIALLY_CORRECT": "🟡",
        "OUT_OF_SCOPE_POLICY_QUESTION": "🔒",
    }.get(r.verdict, "❔")

    lines = []

    # TIP-03: risk_flag=True -> canh bao PHAI dung dau tien, dung dong voi
    # verdict/credibility thuong, khong bi lan/de bi luot qua (theo Blueprint
    # §DESIGN SYSTEM — quyet dinh D-003 cua Chu nha)
    if r.risk_flag:
        lines.append("🚨 **CẢNH BÁO RỦI RO CAO — đọc trước khi tin theo nội dung này** 🚨")
        for reason in (r.risk_reasons or []):
            lines.append(f"  ⚠️ {reason}")
        lines.append("")  # dong trong tach biet canh bao voi phan verdict thuong

    # FIX-01: y kien ca nhan / cau hoi chinh sach khong phai phan xu dung-sai
    # -> khong hien thang diem tin cay (hien 0/100 se bi doc nham la "rat khong dang tin")
    score_text = (
        f"độ tin cậy {r.final_credibility_score}/100"
        if r.score_applicable
        else "không chấm độ tin cậy (đây không phải claim đúng/sai)"
    )
    lines.append(
        f"{verdict_emoji} **Kiểm chứng nguồn** — {score_text}"
        f" {'(⚠️ MOCK MODE — chưa phải AI thật)' if r.mode == 'MOCK' else ''}"
    )
    lines.append(f"Claim: {r.claim}")
    lines.append(f"Verdict: {r.verdict}")
    if r.urls:
        lines.append(f"Nguồn: {r.urls[0]} (loại: {r.domain_tier}, reachable={r.url_reachable})")
        if len(r.urls) > 1:
            lines.append(f"  (+{len(r.urls) - 1} link khác trong tin nhắn — xem ghi chú kỹ thuật §multi-URL)")
        # FIX-04: nói ĐÚNG nguyên nhân, không đổ hết cho link
        if r.content_extracted:
            lines.append("  ✅ Đã đối chiếu với nội dung thật trích xuất từ link")
        elif r.extract_reason == "thieu-thu-vien":
            lines.append(
                "  ⛔ CHƯA CÀI THƯ VIỆN trích xuất (trafilatura/pypdf) — tính năng đối chiếu"
                " nội dung thật đang TẮT, chỉ đánh giá theo độ uy tín domain."
                " Chạy: pip install -r requirements.txt"
            )
        else:
            lines.append(
                "  ⚠️ Không trích xuất được nội dung thật (PDF ảnh/JS-required/bị chặn/timeout)"
                " — chỉ đánh giá theo độ uy tín domain"
            )
    else:
        lines.append("Nguồn: không có link đính kèm")
    lines.append(f"Giải thích: {r.explanation}")
    lines.append(f"Lớp chỗ khó: {r.risk_class}")
    lines.append(f"Gợi ý tiếp theo: {r.recommended_action}")
    return "\n".join(lines)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Cau truc repo: codebase/kiem-chung-nguon/source_verify.py
    #            va: eval/kiem-chung-nguon/mock-messages.json
    # => phai len 2 cap (ve repo root) roi vao eval/kiem-chung-nguon/
    repo_root = os.path.join(base_dir, "..", "..")
    data_path = os.path.join(repo_root, "eval", "kiem-chung-nguon", "mock-messages.json")
    out_path = os.path.join(repo_root, "eval", "kiem-chung-nguon", "last-run-results.json")

    messages = load_messages(data_path)

    # Cho phep chi chay mot tap con tin nhan (vd chi test 3 bai moi them),
    # thay vi phai chay lai toan bo — tranh ton API quota/thoi gian khi chi
    # muon kiem tra case moi. Cach dung: python3 source_verify.py M15 M16 M17
    only_ids = sys.argv[1:]
    if only_ids:
        wanted = set(only_ids)
        messages = [m for m in messages if m["id"] in wanted]
        missing = wanted - {m["id"] for m in messages}
        if missing:
            print(f"[!] Khong tim thay id: {sorted(missing)}", file=sys.stderr)
        # Chay tap con -> ghi ra file rieng, khong de ghi de len
        # last-run-results.json day du (14 case cu) neu chi test vai case moi.
        out_path = os.path.join(
            repo_root, "eval", "kiem-chung-nguon", "last-run-results-subset.json"
        )

    results = []
    has_real_key = bool(
        os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
    )

    # FIX-04: canh bao NGAY TU DAU neu thieu thu vien trich xuat, thay vi de
    # tinh nang tat am tham roi bao "khong trich xuat duoc noi dung".
    missing = missing_optional_libs()
    if missing:
        print(
            f"⛔ THIEU THU VIEN: {', '.join(missing)} — tinh nang doi chieu noi dung that\n"
            f"   (TIP-05) dang TAT, ket qua se chi danh gia theo domain-tier.\n"
            f"   Chay: pip install -r requirements.txt\n",
            file=sys.stderr,
        )
    if not has_real_key:
        print(
            "⚠️  Chua co API key -> se chay MOCK MODE (khong phai AI that).\n"
            "   Ket qua se ghi ra file rieng, KHONG ghi de len ket qua LIVE_AI.\n",
            file=sys.stderr,
        )

    print(f"Dang xu ly {len(messages)} tin nhan tu {data_path}\n" + "=" * 60)
    for i, msg in enumerate(messages):
        r = verify_message(msg)
        results.append(asdict(r))
        print(f"\n--- {r.message_id} ({r.author}) ---")
        print(format_discord_reply(r))
        # Nghi giua cac lan goi AI that de tranh dinh rate limit free tier
        # (Gemini free tier gioi han so request/phut) — khong can nghi o
        # mock mode vi khong co goi mang that.
        if has_real_key and i < len(messages) - 1:
            time.sleep(10)

    # FIX-03: lươt chay co bat ky case MOCK nao thi KHONG duoc ghi de len file
    # ket qua LIVE_AI — day la artifact bang chung cho R4. Truoc day chay thu
    # khi chua cam key se xoa sach 17 ket qua AI that ma khong canh bao gi.
    mock_count = sum(1 for r in results if r["mode"] == "MOCK")
    if mock_count:
        root, ext = os.path.splitext(out_path)
        out_path = f"{root}-MOCK{ext}"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n" + "=" * 60)
    print(f"Da luu {len(results)} ket qua vao {os.path.normpath(out_path)}")

    if mock_count:
        print(
            f"\n⚠️  {mock_count}/{len(results)} case chay o MOCK MODE (chua co API key that).\n"
            "   Ket qua da ghi ra file *-MOCK.json — file ket qua LIVE_AI KHONG bi dong den.\n"
            "   Truoc khi demo/nop bai: export OPENROUTER_API_KEY=... (hoac GEMINI_API_KEY=...,\n"
            "   ANTHROPIC_API_KEY=...) de day la loi goi AI that, dung theo luat hackathon."
        )


if __name__ == "__main__":
    main()
