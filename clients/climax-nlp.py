#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from _dotenv import load_dotenv


def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise SystemExit(f"Missing {name}")
    return val


def _read_text_from_args_or_stdin(args: list[str]) -> str:
    if args:
        text = " ".join(args)
    else:
        text = sys.stdin.read()
    return text.strip()


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _az_blob_download(account: str, container: str, name: str, file_path: Path) -> None:
    args = [
        "az",
        "storage",
        "blob",
        "download",
        "--account-name",
        account,
        "--container-name",
        container,
        "--name",
        name,
        "--file",
        str(file_path),
    ]
    conn = os.getenv("CLIMAX_BLOB_CONNECTION_STRING", "").strip()
    if conn:
        args += ["--connection-string", conn]
    else:
        args += ["--auth-mode", "login"]
    p = subprocess.run(args, text=True, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr or p.stdout or "")
        raise SystemExit(p.returncode)


def _az_blob_upload(account: str, container: str, name: str, file_path: Path) -> None:
    args = [
        "az",
        "storage",
        "blob",
        "upload",
        "--account-name",
        account,
        "--container-name",
        container,
        "--name",
        name,
        "--file",
        str(file_path),
        "--overwrite",
    ]
    conn = os.getenv("CLIMAX_BLOB_CONNECTION_STRING", "").strip()
    if conn:
        args += ["--connection-string", conn]
    else:
        args += ["--auth-mode", "login"]
    p = subprocess.run(args, text=True, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr or p.stdout or "")
        raise SystemExit(p.returncode)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="cj",
        description="Japanese command -> /api/nlp/analyze -> save final_prompt (local or blob).",
    )
    ap.add_argument("--backend", choices=["local", "blob"], default=os.getenv("CLIMAX_BACKEND", "local"))
    ap.add_argument("--pull", action="store_true", help="Download from blob into local file.")
    ap.add_argument("text", nargs="*", help="Japanese input text. If omitted, reads stdin.")
    ns = ap.parse_args(argv)
    load_dotenv(Path(__file__).resolve().parent / ".env")


    functions_url = _require_env("CLIMAX_FUNCTIONS_URL")
    functions_code = _require_env("CLIMAX_FUNCTIONS_CODE")

    prompt_dir = Path(os.path.expanduser(os.getenv("CLIMAX_PROMPT_DIR", str(Path.home() / ".climax"))))
    _ensure_dir(prompt_dir)
    out_path = prompt_dir / "latest_final_prompt.txt"
    json_path = prompt_dir / "latest_nlp.json"

    blob_account = os.getenv("CLIMAX_BLOB_ACCOUNT", "").strip()
    blob_container = os.getenv("CLIMAX_BLOB_CONTAINER", "").strip()
    blob_name = os.getenv("CLIMAX_BLOB_NAME", "latest_final_prompt.txt").strip() or "latest_final_prompt.txt"

    if ns.backend == "blob" or ns.pull:
        if not blob_account or not blob_container:
            raise SystemExit("Missing blob settings. Set CLIMAX_BLOB_ACCOUNT and CLIMAX_BLOB_CONTAINER.")
        if subprocess.run(["which", "az"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
            raise SystemExit("Missing Azure CLI: az")

    if ns.pull:
        if ns.backend != "blob":
            raise SystemExit("--pull requires --backend blob")
        _az_blob_download(blob_account, blob_container, blob_name, out_path)
        sys.stdout.write(str(out_path) + "\n")
        return 0

    text = _read_text_from_args_or_stdin(ns.text)
    if not text:
        raise SystemExit("No input text.")

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
            "json",
        ],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or "")
        raise SystemExit(proc.returncode)

    raw = proc.stdout or ""
    json_path.write_text(raw, encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise SystemExit("server returned non-JSON response")

    final_prompt = str(data.get("final_prompt") or "")
    out_path.write_text(final_prompt, encoding="utf-8")

    if ns.backend == "blob":
        _az_blob_upload(blob_account, blob_container, blob_name, out_path)

    sys.stdout.write(str(out_path) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

