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


def _post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Climax: run a command and append its output as a Chronicle log item.",
    )
    parser.add_argument(
        "--functions-url",
        default=os.getenv("CLIMAX_FUNCTIONS_URL", "http://localhost:7071"),
        help="Azure Functions base URL. Env: CLIMAX_FUNCTIONS_URL",
    )
    parser.add_argument(
        "--functions-code",
        default=os.getenv("CLIMAX_FUNCTIONS_CODE"),
        help="Functions key (code query param). Env: CLIMAX_FUNCTIONS_CODE",
    )
    parser.add_argument(
        "--server-id",
        default=os.getenv("CLIMAX_SERVER_ID") or _default_server_id(),
        help="Server ID (default: hostname). Env: CLIMAX_SERVER_ID",
    )
    parser.add_argument(
        "--session-id",
        required=True,
        help="Session ID (e.g. unity-dev)",
    )
    parser.add_argument(
        "--topic",
        default=os.getenv("CLIMAX_TOPIC") or "default",
        help="Topic/category for grouping logs (default: default). Env: CLIMAX_TOPIC",
    )
    parser.add_argument(
        "--cwd",
        default=None,
        help="Working directory for the command (default: current).",
    )
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to run (after --).")

    args = parser.parse_args()

    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        raise SystemExit("missing command: pass after --, e.g. -- ls -la")

    proc = subprocess.run(cmd, cwd=args.cwd, text=True, capture_output=True)

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    combined = stdout
    if stderr:
        combined = (stdout.rstrip("\n") + "\n\n[stderr]\n" + stderr).lstrip("\n")

    url = _build_url(args.functions_url, "/api/log/append", args.functions_code)
    payload = {
        "server_id": args.server_id,
        "session_id": args.session_id,
        "log": combined.strip() or "(no output)",
        "topic": args.topic,
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "cwd": args.cwd or os.getcwd(),
    }

    result = _post_json(url, payload)
    sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
