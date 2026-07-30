#!/usr/bin/env python3
"""
risk_patterns.py — TIP-01
Bang pattern rui ro rule-based cho pipeline Kiem Chung Nguon.

Muc dich: phat hien SOM (truoc khi goi LLM) cac dau hieu rui ro tai chinh/
bao mat trong mot tin nhan chia se kien thuc — vd tin nhan M14 trong golden
set (huong dan dung proxy ben thu ba khong chinh thuc de "dung Claude Code
mien phi", co link affiliate, yeu cau dan API token vao BASE_URL la).

Thiet ke: DUNG rule-based (regex/keyword), KHONG dung LLM cho buoc nay —
ly do: day la loai rui ro can phat hien 100% nhat quan, khong nen phu
thuoc vao LLM co the bo sot do "nghe co ve hop ly". LLM chi dung
risk_reasons o day de DIEN GIAI them, khong tu quyet dinh risk_flag tu dau
(xem source_verify.py::llm_verify_claim).
"""

import re

# Moi pattern: (ten_pattern, regex, muc_do_nghiem_trong 1-3, giai_thich)
RISK_PATTERNS = [
    (
        "affiliate_referral_link",
        re.compile(r"[?&](aff|ref|referral|via)=", re.IGNORECASE),
        2,
        "Link dang ky co gan ma gioi thieu/affiliate — nguoi chia se co dong "
        "co tai chinh (hoa hong/tin dung) khi co nguoi dang ky qua link nay, "
        "can duoc cong khai ro rang.",
    ),
    (
        "paste_api_key_to_third_party",
        re.compile(
            r"(dán|dan|paste).{0,40}(api[\s_-]?key|token|auth[\s_-]?token)"
            r".{0,60}(base[\s_-]?url|proxy|bên thứ ba|ben thu ba|domain)",
            re.IGNORECASE,
        ),
        3,
        "Yêu cầu dán API key/token cá nhân vào một dịch vụ/domain bên thứ ba "
        "không phải nhà cung cấp chính thức — rủi ro lộ thông tin xác thực, "
        "vi phạm điều khoản dịch vụ gốc.",
    ),
    (
        "change_base_url_to_unofficial_domain",
        re.compile(
            r"(anthropic_base_url|base[_\s]?url).{0,60}(đổi|doi|trỏ|tro|thay)",
            re.IGNORECASE,
        ),
        3,
        "Hướng dẫn đổi endpoint gốc (BASE_URL) của một dịch vụ AI sang domain "
        "khác — đây là dấu hiệu định tuyến traffic qua bên thứ ba không được "
        "nhà cung cấp xác nhận.",
    ),
    (
        "daily_login_farming_reward",
        re.compile(
            r"(mỗi ngày|moi ngay|hàng ngày|hang ngay).{0,60}"
            r"(đăng xuất|dang xuat|đăng nhập|dang nhap).{0,60}"
            r"(nhận|nhan|được|duoc).{0,30}(tín dụng|tin dung|\$|credit|thưởng|thuong)",
            re.IGNORECASE,
        ),
        2,
        "Mô tả cơ chế lặp lại hằng ngày để nhận thêm tín dụng/tiền thưởng — "
        "dấu hiệu điển hình của referral/growth-hacking scheme, không phải "
        "chính sách chính thức thông thường của nhà cung cấp dịch vụ.",
    ),
]

# Ten brand -> danh sach domain chinh thuc tuong ung. Dung de kiem tra
# "nhac ten brand nhung KHONG kem bat ky domain chinh thuc nao trong URL
# thuc su co trong tin nhan" — kiem tra bang logic Python (khong dung regex
# khoang cach, vi cach do KHONG DANG TIN: dot 1 dau chay thu cho thay no bao
# false positive tren ca case hop le nhu M06 vi ky tu unicode/khoang cach
# lam sai lech do dai match).
BRAND_OFFICIAL_DOMAINS = {
    "anthropic": ["anthropic.com", "docs.claude.com", "docs.anthropic.com", "claude.com"],
    "claude": ["anthropic.com", "docs.claude.com", "docs.anthropic.com", "claude.com"],
    "openai": ["openai.com", "platform.openai.com"],
    "gpt": ["openai.com", "platform.openai.com"],
    "google": ["google.com", "ai.google.dev", "google.dev", "research.google"],
    "gemini": ["ai.google.dev", "google.com"],
}
BRAND_KEYWORD_RE = re.compile(
    r"\b(" + "|".join(BRAND_OFFICIAL_DOMAINS.keys()) + r")\b", re.IGNORECASE
)



# Chi coi la "mismatch dang ngo" khi tin nhan CUNG luc am chi mot kenh
# thay the/khong chinh thuc — tranh false positive tren cac tin nhan chi
# don thuan NHAC TEN brand (vd "dung Claude Code de build", "skill cho
# Claude Code") ma khong claim gi ve viec truy cap/uu dai tu brand do.
ALTERNATIVE_ACCESS_HINTS = re.compile(
    r"(miễn phí|mien phi|free|thay thế|thay the|không chính thức|khong chinh thuc|"
    r"giá rẻ|gia re|unofficial|proxy|qua nền tảng|qua nen tang|qua dịch vụ|qua dich vu|"
    r"bên thứ ba|ben thu ba)",
    re.IGNORECASE,
)


def _check_brand_domain_mismatch(text: str, urls: list) -> str | None:
    """Chi bao rui ro khi: (a) tin nhan nhac ten mot brand AI lon, VA
    (b) tin nhan CO it nhat 1 URL, VA (c) KHONG co URL nao thuoc domain
    chinh thuc cua brand do duoc nhac, VA (d) tin nhan co dau hieu am chi
    mot kenh truy cap thay the/khong chinh thuc (xem ALTERNATIVE_ACCESS_HINTS).

    Dieu kien (d) quan trong de tranh false positive: chi nhac ten brand
    khi gioi thieu mot cong cu tuong thich (vd "skill cho Claude Code")
    KHONG nen bi coi la rui ro — khac voi tin nhan claim "dung X mien phi
    qua kenh khac" (vd M14).
    """
    brands_mentioned = set(m.lower() for m in BRAND_KEYWORD_RE.findall(text))
    if not brands_mentioned or not urls:
        return None
    if not ALTERNATIVE_ACCESS_HINTS.search(text):
        return None

    url_hosts = [u.lower() for u in urls]
    for brand in brands_mentioned:
        official = BRAND_OFFICIAL_DOMAINS.get(brand, [])
        if any(any(dom in host for dom in official) for host in url_hosts):
            continue  # brand nay co it nhat 1 URL khop domain chinh thuc -> ok
        return (
            f"Tin nhắn nhắc tới '{brand}' nhưng URL đính kèm không thuộc domain "
            f"chính thức của {brand} ({', '.join(official)}) — kiểm tra kỹ trước "
            "khi tin đây là thông tin/chương trình chính thức."
        )
    return None


def scan_risk_patterns(text: str, urls: list) -> tuple[bool, list]:
    """Quet rule-based tren text + urls.

    Tra ve (risk_flag: bool, risk_reasons: list[str]).
    Chi bat risk_flag=True cho pattern muc nghiem trong >=2, hoac khi phat
    hien brand/domain mismatch (xem _check_brand_domain_mismatch).
    """
    reasons = []
    high_severity_hit = False

    for name, pattern, severity, explanation in RISK_PATTERNS:
        if pattern.search(text):
            reasons.append(f"[{name}] {explanation}")
            if severity >= 2:
                high_severity_hit = True

    mismatch = _check_brand_domain_mismatch(text, urls)
    if mismatch:
        reasons.append(f"[brand_domain_mismatch] {mismatch}")
        high_severity_hit = True

    return high_severity_hit, reasons


if __name__ == "__main__":
    # FIX-01: console Windows (cp1252) khong in duoc tieng Viet co dau -> self-test
    # nay tung crash bang UnicodeEncodeError ngay dong ly do dau tien.
    import sys

    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    # Self-test nhanh voi case M14 tu golden set
    sample = (
        "Hướng dẫn dùng Claude Code với Claude Opus 5 miễn phí qua nền tảng "
        "bên thứ ba Agent Router (https://agentrouter.org/register?aff=0qYW): "
        "đăng ký bằng GitHub nhận $100 tín dụng, mỗi ngày đăng xuất-đăng nhập "
        "lại nhận thêm $25 miễn phí, dán vào VSCode settings, đổi "
        "ANTHROPIC_BASE_URL trỏ sang domain của bên thứ ba đó."
    )
    flag, reasons = scan_risk_patterns(sample, [])
    print("risk_flag:", flag)
    for r in reasons:
        print(" -", r)
