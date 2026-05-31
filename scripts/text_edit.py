#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReplaceResult:
    changed: bool
    count: int


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def replace_literal(text: str, old: str, new: str, *, count: int = 1) -> ReplaceResult:
    out = text.replace(old, new, count)
    applied = min(text.count(old), max(0, count))
    return ReplaceResult(changed=out != text, count=applied)


def replace_regex(text: str, pattern: str, repl: str, *, count: int = 1, flags: int = 0) -> tuple[str, ReplaceResult]:
    rx = re.compile(pattern, flags)
    out, n = rx.subn(repl, text, count=count)
    return out, ReplaceResult(changed=out != text, count=n)


def insert_after(text: str, needle: str, insert: str, *, count: int = 1) -> tuple[str, ReplaceResult]:
    if needle not in text:
        return text, ReplaceResult(changed=False, count=0)
    parts = text.split(needle)
    occ = len(parts) - 1
    use = min(occ, max(0, count))
    if use <= 0:
        return text, ReplaceResult(changed=False, count=0)

    out: list[str] = []
    remaining = use
    for part in parts[:-1]:
        out.append(part)
        out.append(needle)
        if remaining > 0:
            out.append(insert)
            remaining -= 1
    out.append(parts[-1])
    return "".join(out), ReplaceResult(changed=True, count=use)


def insert_before(text: str, needle: str, insert: str, *, count: int = 1) -> tuple[str, ReplaceResult]:
    out, r = insert_after(text, needle, insert + needle, count=count)
    return out, r


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="text_edit.py",
        description="Small, dependency-free text editing helper (replace/insert).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("replace", help="literal replace")
    p.add_argument("--file", required=True)
    p.add_argument("--old", required=True)
    p.add_argument("--new", required=True)
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--check", action="store_true", help="do not write, only report")

    p = sub.add_parser("re", help="regex replace")
    p.add_argument("--file", required=True)
    p.add_argument("--pattern", required=True)
    p.add_argument("--repl", required=True)
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--multiline", action="store_true")
    p.add_argument("--dotall", action="store_true")
    p.add_argument("--check", action="store_true")

    p = sub.add_parser("insert-after", help="insert text after a needle")
    p.add_argument("--file", required=True)
    p.add_argument("--needle", required=True)
    p.add_argument("--insert", required=True)
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--check", action="store_true")

    p = sub.add_parser("insert-before", help="insert text before a needle")
    p.add_argument("--file", required=True)
    p.add_argument("--needle", required=True)
    p.add_argument("--insert", required=True)
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--check", action="store_true")

    p = sub.add_parser("show", help="print file")
    p.add_argument("--file", required=True)

    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        sys.stderr.write(f"ERR: file not found: {path}\n")
        return 2

    if args.cmd == "show":
        sys.stdout.write(_read_text(path))
        return 0

    text = _read_text(path)
    out = text
    result = ReplaceResult(changed=False, count=0)

    if args.cmd == "replace":
        out = text.replace(args.old, args.new, args.count)
        result = replace_literal(text, args.old, args.new, count=args.count)

    elif args.cmd == "re":
        flags = 0
        if args.multiline:
            flags |= re.M
        if args.dotall:
            flags |= re.S
        out, result = replace_regex(text, args.pattern, args.repl, count=args.count, flags=flags)

    elif args.cmd == "insert-after":
        out, result = insert_after(text, args.needle, args.insert, count=args.count)

    elif args.cmd == "insert-before":
        out, result = insert_before(text, args.needle, args.insert, count=args.count)

    else:
        sys.stderr.write("ERR: unknown cmd\n")
        return 2

    if not result.changed:
        sys.stderr.write("NOOP\n")
        return 1

    if getattr(args, "check", False):
        sys.stderr.write(f"CHANGED count={result.count}\n")
        return 0

    _write_text(path, out)
    sys.stderr.write(f"UPDATED count={result.count}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
