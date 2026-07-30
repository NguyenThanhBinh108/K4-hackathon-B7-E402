#!/usr/bin/env python3
"""
message_type.py — TIP-06
Phan loai rule-based LOAI TIN NHAN truoc khi goi LLM, cho pipeline Kiem Chung Nguon.

Van de thuc te (phat hien tu test bot that voi nguoi dung, xem
manual-claude-verification-run.md): model free qua OpenRouter co xu huong
mac dinh verdict UNVERIFIED_NO_SOURCE cho hau het tin nhan khong co link,
ke ca khi:
  (a) tin nhan la chia se KINH NGHIEM/QUAN SAT CA NHAN — khong phai mot
      claim khach quan dung/sai, ma la "co the dung voi nguoi viet nhung
      khong chac dung pho quat";
  (b) tin nhan la MOT CODE TIP/TRICK ma AI hoan toan co the tu danh gia
      dung/sai bang kien thuc nen tang cua minh, khong bat buoc phai co
      link nguon moi danh gia duoc.

Thiet ke: giong risk_patterns.py — DUNG rule-based (keyword/regex) chay
TRUOC LLM, dua ket qua vao prompt nhu context co san, de LLM khong phai
tu doan loai tin nhan tu dau (da chung minh voi risk_patterns.py rang
prompt instruction don thuan khong du de model free tuan theo nhat quan).
LLM van la nguoi ra verdict cuoi cung — day chi la GOI Y phan loai, khong
tu dong ghi de verdict.
"""

import re

PERSONAL_EXPERIENCE_RE = re.compile(
    r"(theo kinh nghiệm|theo kinh nghiem|kinh nghiệm cá nhân|kinh nghiem ca nhan|"
    r"cá nhân mình|ca nhan minh|theo mình|theo minh|mình thấy|minh thay|"
    r"mình đã thử|minh da thu|trải nghiệm cá nhân|trai nghiem ca nhan|"
    r"riêng mình|rieng minh|\bimo\b)",
    re.IGNORECASE,
)

# Dau hieu tin nhan dang noi ve mot ky thuat/meo code cu the (khong phai
# claim tong quat kieu "model X tot hon model Y").
CODE_TIP_HINT_RE = re.compile(
    r"(```|`[^`]+`|\bcode\b|snippet|function|hàm |ham |\bbug\b|debug|"
    r"\bconfig\b|syntax|import |\btrick\b|mẹo|meo |\btip\b|refactor|"
    r"optimize|tối ưu|toi uu)",
    re.IGNORECASE,
)


def classify_message_type(text: str, urls: list) -> tuple[list[str], list[str]]:
    """Tra ve (tags, notes).

    tags co the gom "personal_experience" va/hoac "code_tip_no_source".
    Mot tin nhan co the vua la ca hai (vd "theo kinh nghiem minh thi debug
    kieu nay nhanh hon" ma khong kem link).
    """
    tags: list[str] = []
    notes: list[str] = []

    if PERSONAL_EXPERIENCE_RE.search(text):
        tags.append("personal_experience")
        notes.append(
            "Có dấu hiệu đây là chia sẻ kinh nghiệm/quan sát cá nhân, không "
            "phải khẳng định khách quan — có thể đúng với người viết nhưng "
            "không chắc đúng phổ quát."
        )

    if not urls and CODE_TIP_HINT_RE.search(text):
        tags.append("code_tip_no_source")
        notes.append(
            "Có vẻ là một mẹo/kỹ thuật code không kèm link nguồn — nếu đủ tự "
            "tin, nên dùng kiến thức nền tảng để đánh giá đúng/sai thay vì "
            "mặc định 'chưa xác minh được' chỉ vì thiếu link."
        )

    return tags, notes


if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    samples = [
        ("Theo kinh nghiệm mình dùng thì prompt ngắn hơn cho kết quả tốt hơn.", []),
        ("Mẹo debug: dùng `console.log` trước khi crash để trace nhanh hơn.", []),
        ("Paper mới ra nói về scaling laws.", ["https://arxiv.org/abs/1234.5678"]),
    ]
    for text, urls in samples:
        tags, notes = classify_message_type(text, urls)
        print(text)
        print("  tags:", tags)
        for n in notes:
            print("  -", n)
        print()
