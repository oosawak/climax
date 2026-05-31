#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from _dotenv import load_dotenv


def _read_text_from_args_or_stdin(args: list[str]) -> str:
    if args:
        text = " ".join(args)
    else:
        text = sys.stdin.read()
    return text.strip()


def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise SystemExit(f"Missing {name}")
    return val


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="climax-send",
        description="Japanese -> /api/nlp/analyze -> final_prompt -> inject into active tmux pane.",
    )
    ap.add_argument("text", nargs="*", help="Japanese input text. If omitted, reads stdin.")
    ns = ap.parse_args(argv)
    load_dotenv(Path(__file__).resolve().parent / ".env")


    if subprocess.run(["which", "tmux"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        raise SystemExit("Missing tmux.")

    text = _read_text_from_args_or_stdin(ns.text)
    if not text:
        raise SystemExit("No input text.")

    functions_url = _require_env("CLIMAX_FUNCTIONS_URL")
    functions_code = _require_env("CLIMAX_FUNCTIONS_CODE")

    clients_dir = Path(__file__).resolve().parent
    preprocess = clients_dir / "climax_preprocess_client.py"
    if not preprocess.exists():
        raise SystemExit(f"Missing preprocess client: {preprocess}")

    proc = subprocess.run(
        [
            sys.executable,
            str(preprocess),
            "--functions-url",
            functions_url,
            "--functions-code",
            functions_code,
            "--text",
            text,
            "--format",
            "final_prompt",
        ],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or "")
        raise SystemExit(proc.returncode)
    final_prompt = (proc.stdout or "").rstrip("\n")
    if not final_prompt.strip():
        raise SystemExit("Empty final_prompt returned.")

    # Send to active pane.
    subprocess.run(["tmux", "send-keys", "-l", "--", final_prompt], check=True)
    subprocess.run(["tmux", "send-keys", "Enter"], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

