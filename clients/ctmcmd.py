#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


def _default_server_id() -> str:
    host = socket.gethostname().split(".")[0]
    return host or "unknown-host"


def _infer_session_id_from_tmux() -> str | None:
    if not os.getenv("TMUX"):
        return None
    try:
        out = subprocess.check_output(["tmux", "display-message", "-p", "#S"], text=True).strip()
    except Exception:
        return None
    for prefix in ("cmd-", "codex-", "log-"):
        if out.startswith(prefix):
            out = out[len(prefix):]
            break
    return out or None


def _build_url(base_url: str, path: str, functions_code: str | None) -> str:
    base = base_url.rstrip("/")
    url = f"{base}{path}"
    if not functions_code:
        return url
    code = functions_code.strip()
    if not code:
        return url
    q = urllib.parse.urlencode({"code": code})
    return f"{url}?{q}"


def _post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            raw = res.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        details = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTPError {e.code}: {details}")
    except urllib.error.URLError as e:
        raise SystemExit(f"URLError: {e.reason}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise SystemExit("server returned non-JSON response")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a command and append its output to Chronicle (/api/log/append).")
    ap.add_argument("--functions-url", default=os.getenv("CLIMAX_FUNCTIONS_URL", "http://localhost:7071"))
    ap.add_argument("--functions-code", default=os.getenv("CLIMAX_FUNCTIONS_CODE"))
    ap.add_argument("--server-id", default=os.getenv("CLIMAX_SERVER_ID") or _default_server_id())
    ap.add_argument("--session-id", default=os.getenv("CLIMAX_SESSION_ID"))
    ap.add_argument("--topic", required=True)
    ap.add_argument("--cwd", default=None)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        raise SystemExit("missing command: pass after --, e.g. -- echo hello")

    session_id = args.session_id or _infer_session_id_from_tmux()
    if not session_id:
        session_id = os.path.basename(os.path.abspath(args.cwd or os.getcwd()))

    proc = subprocess.run(cmd, cwd=args.cwd, text=True, capture_output=True)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    combined = stdout
    if stderr:
        combined = (stdout.rstrip("\n") + "\n\n[stderr]\n" + stderr).lstrip("\n")

    url = _build_url(args.functions_url, "/api/log/append", args.functions_code)
    payload = {
        "server_id": args.server_id,
        "session_id": session_id,
        "topic": args.topic,
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "cwd": args.cwd or os.getcwd(),
        "log": combined.strip() or "(no output)",
    }

    result = _post_json(url, payload)
    sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
