#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


def _replace_bash_function(text: str, func_name: str, replacement_body: str) -> str:
    pattern = re.compile(
        rf"(^[	 ]*{re.escape(func_name)}\s*\(\)\s*\{{)(.*?)(^[	 ]*\}}\s*$)",
        re.M | re.S,
    )
    m = pattern.search(text)
    if not m:
        raise SystemExit(f"function not found: {func_name}")

    head, tail = m.group(1), m.group(3)
    body = replacement_body
    if not body.endswith("\n"):
        body += "\n"

    return text[: m.start()] + head + "\n" + body + tail + text[m.end() :]


def main() -> int:
    ap = argparse.ArgumentParser(description="Replace a bash function definition in-place.")
    ap.add_argument("--file", required=True, help="Target bash script path")
    ap.add_argument("--func", required=True, help="Function name to replace")
    ap.add_argument(
        "--replacement",
        required=True,
        help="Path to text file containing replacement function body (inside braces)",
    )
    args = ap.parse_args()

    target = Path(args.file)
    rep = Path(args.replacement)

    src = target.read_text(encoding="utf-8")
    body = rep.read_text(encoding="utf-8")

    out = _replace_bash_function(src, args.func, body)
    target.write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
