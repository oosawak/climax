#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional
from shutil import which


DEFAULT_CACHE_PATH = Path(os.getenv("TMUX_USAGE_CACHE_PATH", "/tmp/climax-tmux-usage.json"))
CODex_SESSION_ROOT = Path(os.path.expanduser("~/.codex/sessions"))


@dataclass
class StatusItem:
    label: str
    text: str
    ok: bool = True


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def run_command(args: Iterable[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", "command not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"


def format_tokens(value: Optional[int]) -> str:
    if value is None:
        return "?"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def parse_json_lines(path: Path) -> list[dict[str, Any]]:
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except Exception:
        return []


def find_latest_file(root: Path, pattern: str) -> Optional[Path]:
    if not root.exists():
        return None
    candidates = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def collect_claude() -> StatusItem:
    code, stdout, stderr = run_command(
        [
            "claude",
            "-p",
            "/stats",
            "--output-format",
            "json",
            "--dangerously-skip-permissions",
        ],
        timeout=30,
    )
    if code != 0:
        msg = (stderr or stdout).lower()
        if "auth" in msg or "login" in msg:
            return StatusItem("claude", "auth?", ok=False)
        return StatusItem("claude", "err", ok=False)

    try:
        payload = json.loads(stdout)
    except Exception:
        text = stdout.strip() or "ok"
        return StatusItem("claude", text[:48], ok=True)

    usage = payload.get("usage") or {}
    total = int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0)
    if total > 0:
        return StatusItem("claude", f"{format_tokens(total)} tok", ok=True)

    result = str(payload.get("result") or "").strip()
    if result:
        if "subscription" in result.lower():
            return StatusItem("claude", "sub", ok=True)
        return StatusItem("claude", result[:48], ok=True)
    return StatusItem("claude", "ok", ok=True)


def collect_codex() -> StatusItem:
    session = find_latest_file(CODex_SESSION_ROOT, "**/*.jsonl")
    if not session:
        return StatusItem("codex", "missing", ok=False)

    records = parse_json_lines(session)
    token_record = next((r for r in reversed(records) if r.get("type") == "token_count"), None)
    if token_record:
        usage = token_record.get("info", {}).get("total_token_usage", {})
        total = int(usage.get("total_tokens") or 0)
        if total > 0:
            return StatusItem("codex", f"{format_tokens(total)} tok", ok=True)

    completed = next(
        (r for r in reversed(records) if r.get("type") == "event_msg" and r.get("payload", {}).get("type") == "task_complete"),
        None,
    )
    if completed:
        return StatusItem("codex", "ok", ok=True)
    return StatusItem("codex", "unknown", ok=False)


def collect_gemini() -> StatusItem:
    code, stdout, stderr = run_command(
        [
            "gemini",
            "--output-format",
            "json",
            "--prompt",
            "say hello",
            "--skip-trust",
            "--yolo",
        ],
        timeout=90,
    )

    if code != 0 and not stdout:
        msg = (stderr or "").lower()
        if "auth" in msg or "authentication" in msg:
            return StatusItem("gemini", "auth?", ok=False)
        return StatusItem("gemini", "err", ok=False)

    try:
        payload = json.loads(stdout)
    except Exception:
        text = stdout.strip() or stderr.strip() or "ok"
        return StatusItem("gemini", text[:48], ok=code == 0)

    stats = payload.get("stats") or {}
    models = stats.get("models") or {}
    total = 0
    for model in models.values():
        tokens = (model or {}).get("tokens") or {}
        total += int(tokens.get("total") or 0)
    if total > 0:
        return StatusItem("gemini", f"{format_tokens(total)} tok", ok=True)

    response = str(payload.get("response") or "").strip()
    if response:
        return StatusItem("gemini", response[:48], ok=True)
    return StatusItem("gemini", "ok", ok=True)


def collect_copilot() -> StatusItem:
    if which("gh") is None:
        return StatusItem("copilot", "gh?", ok=False)

    code, stdout, stderr = run_command(["gh", "copilot", "--", "-p", "/usage", "-s"], timeout=30)
    text = (stdout or stderr).strip()
    if code != 0 and not text:
        return StatusItem("copilot", "err", ok=False)
    if "Install GitHub Copilot CLI" in text:
        return StatusItem("copilot", "install?", ok=False)

    match = re.search(r"(\d[\d,]*)", text.replace(",", ""))
    if "premium request" in text.lower() and match:
        return StatusItem("copilot", f"{match.group(1)} req", ok=True)
    if text:
        return StatusItem("copilot", text.replace("\n", " ")[:48], ok=code == 0)
    return StatusItem("copilot", "ok", ok=True)


def write_cache(path: Path, items: list[StatusItem]) -> None:
    payload = {
        "generated_at": utc_now().isoformat().replace("+00:00", "Z"),
        "items": [
            {"label": item.label, "text": item.text, "ok": item.ok}
            for item in items
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh cached CLI usage for tmux.")
    parser.add_argument("--cache", default=str(DEFAULT_CACHE_PATH), help="path to the cache JSON file")
    args = parser.parse_args()

    items = [collect_copilot(), collect_claude(), collect_codex(), collect_gemini()]
    write_cache(Path(args.cache), items)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
