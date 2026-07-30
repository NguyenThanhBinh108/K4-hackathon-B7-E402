#!/usr/bin/env python3
"""
update_demo_ui.py — nap lai du lieu cho demo-discord-ui.html tu file ket qua.

VI SAO CAN FILE NAY
-------------------
`demo-discord-ui.html` nhung thang du lieu vao trong `const DATA = [...]` (bat
buoc phai vay: mo bang file:// thi fetch() bi CORS chan). Nhung do la mot BAN
CHUP tai mot thoi diem — chay lai pipeline thi UI khong tu doi, hai ben lech
nhau luc nao khong biet, va luc demo se noi mot dang trong khi eval/ noi mot dang.

Script nay ghi de dung dong `const DATA = ...` bang noi dung moi nhat cua file
ket qua, giu nguyen toan bo HTML/CSS/JS con lai.

Cach dung (chay sau moi lan chay source_verify.py voi API that):
    python3 update_demo_ui.py
    python3 update_demo_ui.py ../../eval/kiem-chung-nguon/last-run-results.json
"""

import json
import os
import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RESULTS = os.path.join(
    BASE_DIR, "..", "..", "eval", "kiem-chung-nguon", "last-run-results.json"
)
UI_PATH = os.path.join(BASE_DIR, "demo-discord-ui.html")

DATA_LINE_RE = re.compile(r"^const DATA = .*;$", re.MULTILINE)


def main() -> None:
    results_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RESULTS

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    modes = {r.get("mode") for r in results}
    if "MOCK" in modes:
        print(
            "⚠️  File ket qua nay co case MOCK MODE (khong phai AI that).\n"
            "   Demo UI se hien du lieu mock — chi lam vay khi dang test, "
            "dung dung ban nay de demo/nop bai.",
            file=sys.stderr,
        )

    with open(UI_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    if not DATA_LINE_RE.search(html):
        print("Khong tim thay dong 'const DATA = ...;' trong demo-discord-ui.html", file=sys.stderr)
        sys.exit(1)

    new_line = "const DATA = " + json.dumps(results, ensure_ascii=False) + ";"
    html = DATA_LINE_RE.sub(lambda _: new_line, html, count=1)

    # Cap nhat luon so hien tren nut "Tat ca (N)" cho khop so case
    html = re.sub(
        r'(<button id="btn-all"[^>]*>)Tất cả \(\d+\)</button>',
        rf"\g<1>Tất cả ({len(results)})</button>",
        html,
    )

    with open(UI_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(
        f"Da nap {len(results)} case tu {os.path.normpath(results_path)}\n"
        f"vao {os.path.normpath(UI_PATH)} (mode: {', '.join(sorted(m for m in modes if m))})"
    )


if __name__ == "__main__":
    main()
