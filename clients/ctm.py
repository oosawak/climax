#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from _dotenv import load_dotenv
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CLIENTS_DIR = Path(__file__).resolve().parent
CLIENTS_ENV_PATH = CLIENTS_DIR / ".env"
STATE_DIR = Path.home() / ".climax"
LAST_SESSION_PATH = STATE_DIR / "last_session.txt"
LAST_ACTION_PATH = STATE_DIR / "last_action.txt"
LAST_TOPIC_PATH = STATE_DIR / "last_topic.txt"
LAST_LIMIT_PATH = STATE_DIR / "last_limit.txt"
LAST_FORMAT_PATH = STATE_DIR / "last_format.txt"


def _env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def _default_server_id() -> str:
    return (os.uname().nodename.split(".")[0] or "unknown-host").strip()


def _chronicle_available() -> bool:
    return bool(_env("CLIMAX_FUNCTIONS_URL") and _env("CLIMAX_FUNCTIONS_CODE"))


def _build_url(base_url: str, path: str, params: dict[str, str]) -> str:
    base = base_url.rstrip("/")
    qs = urlencode(params)
    return f"{base}{path}?{qs}" if qs else f"{base}{path}"


def _get_json(url: str) -> dict:
    req = Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=30) as res:
            raw = res.read().decode("utf-8")
    except HTTPError as e:
        details = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTPError {e.code}: {details}")
    except URLError as e:
        raise SystemExit(f"URLError: {e.reason}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise SystemExit("server returned non-JSON response")


def _post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=30) as res:
            raw = res.read().decode("utf-8")
    except HTTPError as e:
        details = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTPError {e.code}: {details}")
    except URLError as e:
        raise SystemExit(f"URLError: {e.reason}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise SystemExit("server returned non-JSON response")


def run_tmux(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["tmux", *args], check=check, text=True)


def require_tmux() -> None:
    if subprocess.run(["which", "tmux"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        raise SystemExit("Missing tmux.")


def has_session(name: str) -> bool:
    p = subprocess.run(
        ["tmux", "has-session", "-t", name],
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return p.returncode == 0


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def pick_workspace_dir(workspace: Path) -> str:
    candidates = sorted([p for p in workspace.iterdir() if p.is_dir()])
    if not candidates:
        raise SystemExit(f"No directories found under {workspace}")
    print(f"Select a workspace directory under: {workspace}", file=sys.stderr)
    for idx, p in enumerate(candidates, 1):
        print(f"{idx:2d}) {p.name}", file=sys.stderr)
    sel = input("Enter number: ").strip()
    if not sel.isdigit():
        raise SystemExit("Invalid selection.")
    n = int(sel)
    if n < 1 or n > len(candidates):
        raise SystemExit("Out of range.")
    return candidates[n - 1].name




def _read_state(path: Path) -> str | None:
    try:
        val = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except Exception:
        return None
    return val or None


def _write_state(path: Path, value: str) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(value + "\n", encoding="utf-8")
    except Exception:
        return


def _read_last_session() -> str | None:
    return _read_state(LAST_SESSION_PATH)


def _write_last_session(name: str) -> None:
    _write_state(LAST_SESSION_PATH, name)


def _read_last_action() -> str | None:
    return _read_state(LAST_ACTION_PATH)


def _write_last_action(action: str) -> None:
    _write_state(LAST_ACTION_PATH, action)
def fetch_sessions() -> list[dict[str, Any]]:
    base_url = _env("CLIMAX_FUNCTIONS_URL")
    code = _env("CLIMAX_FUNCTIONS_CODE")
    server_id = _env("CLIMAX_SERVER_ID") or _default_server_id()
    data = _get_json(_build_url(base_url, "/api/sessions", {"server_id": server_id, "code": code}))
    items = data.get("items") or data.get("sessions") or []
    if not isinstance(items, list):
        return []
    return [x for x in items if isinstance(x, dict)]

def _read_last_topic() -> str | None:
    try:
        return _read_state(LAST_TOPIC_PATH)
    except Exception:
        return None


def _write_last_topic(topic: str) -> None:
    _write_state(LAST_TOPIC_PATH, topic)


def _read_last_limit() -> int | None:
    try:
        val = _read_state(LAST_LIMIT_PATH)
        return int(val) if val else None
    except Exception:
        return None


def _write_last_limit(limit: int) -> None:
    _write_state(LAST_LIMIT_PATH, str(int(limit)))

def _read_last_format() -> str | None:
    try:
        val = _read_state(LAST_FORMAT_PATH)
        return val if val in ("json", "text") else None
    except Exception:
        return None


def _write_last_format(fmt: str) -> None:
    if fmt in ("json", "text"):
        _write_state(LAST_FORMAT_PATH, fmt)




def pick_session_from_chronicle_or_workspace(workspace: Path) -> str:
    default = _read_last_session()
    if _chronicle_available():
        try:
            items = fetch_sessions()
        except Exception:
            items = []
        if items:
            names: list[str] = []
            print("Select a session from Chronicle:", file=sys.stderr)
            for idx, it in enumerate(items, 1):
                sid = (it.get("session_id") or it.get("id") or "").strip()
                if not sid:
                    continue
                names.append(sid)
                cwd = (it.get("directory") or it.get("cwd") or "").strip()
                suffix = f"  {cwd}" if cwd else ""
                print(f"{idx:2d}) {sid}{suffix}", file=sys.stderr)
            if names:
                sel = input("Enter number: ").strip()
                if sel.isdigit():
                    n = int(sel)
                    if 1 <= n <= len(names):
                        return names[n - 1]
    return pick_workspace_dir(workspace)


def inject_clients_env(session: str) -> None:
    cmd = "set -a; [ -f ~/Workspace/climax/clients/.env ] && . ~/Workspace/climax/clients/.env; set +a"
    run_tmux(["send-keys", "-t", session, cmd, "Enter"], check=False)


def ensure_sessions(name: str, workspace: Path, *, with_cmd: bool, with_log: bool) -> None:
    workdir = workspace / name
    ensure_dir(workdir)

    codex_sess = f"codex-{name}"
    cmd_sess = f"cmd-{name}"
    log_sess = f"log-{name}"

    if not has_session(codex_sess):
        run_tmux(["new-session", "-d", "-s", codex_sess, "-c", str(workdir), "codex sh"])

    if with_cmd and not has_session(cmd_sess):
        run_tmux(
            [
                "new-session",
                "-d",
                "-s",
                cmd_sess,
                "-c",
                str(workdir),
                'bash -lc "set -a; [ -f ~/Workspace/climax/clients/.env ] && . ~/Workspace/climax/clients/.env; set +a; exec bash"',
            ]
        )

    if with_log and not has_session(log_sess):
        run_tmux(
            [
                "new-session",
                "-d",
                "-s",
                log_sess,
                "-c",
                str(workdir),
                'bash -lc "set -a; [ -f ~/Workspace/climax/clients/.env ] && . ~/Workspace/climax/clients/.env; set +a; exec bash"',
            ]
        )
        run_tmux(["send-keys", "-t", log_sess, "echo 'log session: add tail/senders here'", "Enter"], check=False)


def kill_sessions(name: str, *, stop_all: bool) -> None:
    for sess in (f"cmd-{name}", f"log-{name}"):
        if has_session(sess):
            run_tmux(["kill-session", "-t", sess], check=False)
    if stop_all:
        sess = f"codex-{name}"
        if has_session(sess):
            run_tmux(["kill-session", "-t", sess], check=False)


def _print_logs_text(items: list[dict[str, Any]]) -> None:
    for it in items:
        ts = it.get("timestamp") or ""
        topic = it.get("topic") or ""
        exit_code = it.get("exit_code")
        cmd = it.get("command") or ""
        line = it.get("log") or ""
        head = f"[{ts}]"
        if topic:
            head += f" [{topic}]"
        if exit_code is not None:
            head += f" (exit={exit_code})"
        if cmd:
            head += f" {cmd}"
        sys.stdout.write(head + "\n")
        if line:
            sys.stdout.write(str(line).rstrip("\n") + "\n")
        sys.stdout.write("\n")


def show_latest_logs_in_log_session(
    name: str,
    log_sess: str,
    *,
    limit: int,
    topic: str | None,
    out_format: str,
    follow: bool,
    interval: int,
) -> None:
    base = f"~/Workspace/climax/clients/ctm logs {name} --limit {limit} --format {out_format}"
    if topic:
        base += f" --topic {topic}"
    if follow:
        sec = max(1, int(interval))
        cmd = f"while true; do clear; {base}; sleep {sec}; done"
    else:
        cmd = f"clear; {base}"
    run_tmux(["send-keys", "-t", log_sess, cmd, "Enter"], check=False)


def do_doctor() -> int:
    ok = True
    if not CLIENTS_ENV_PATH.exists():
        sys.stderr.write(f"WARN: missing {CLIENTS_ENV_PATH} (run: ./clients/setup_clients_env.sh)\n")
        ok = False

    base_url = _env("CLIMAX_FUNCTIONS_URL")
    code = _env("CLIMAX_FUNCTIONS_CODE")
    if not base_url:
        sys.stderr.write("ERR: Missing CLIMAX_FUNCTIONS_URL\n")
        ok = False
    if not code:
        sys.stderr.write("ERR: Missing CLIMAX_FUNCTIONS_CODE\n")
        ok = False

    if base_url:
        url = _build_url(base_url, "/api/health", {"code": code} if code else {})
        try:
            data = _get_json(url)
            sys.stdout.write("health: ok\n")
            if os.getenv("CTM_DOCTOR_JSON") == "1":
                sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
        except SystemExit as e:
            sys.stderr.write(f"health: fail ({e})\n")
            ok = False
    return 0 if ok else 1


def do_sessions(out_format: str) -> int:
    data = {"items": fetch_sessions()}
    if out_format == "json":
        sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
        return 0
    for it in data["items"]:
        sid = (it.get("session_id") or it.get("id") or "").strip()
        cwd = (it.get("cwd") or it.get("directory") or "").strip()
        line = sid
        if cwd:
            line += f"  {cwd}"
        if line:
            sys.stdout.write(line + "\n")
    return 0


def do_backfill(*, limit: int, topic: str | None, dry_run: bool, out_format: str) -> int:
    base_url = _env("CLIMAX_FUNCTIONS_URL")
    code = _env("CLIMAX_FUNCTIONS_CODE")
    url = _build_url(base_url, "/api/logs/backfill_nlp", {"code": code})
    payload: dict[str, object] = {"limit": max(1, int(limit)), "dry_run": bool(dry_run)}
    if topic:
        payload["topic"] = topic
    data = _post_json(url, payload)
    if out_format == "json":
        sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
        return 0
    sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return 0


def do_logs(name: str, *, limit: int, topic: str | None, out_format: str) -> int:
    base_url = _env("CLIMAX_FUNCTIONS_URL")
    code = _env("CLIMAX_FUNCTIONS_CODE")
    server_id = _env("CLIMAX_SERVER_ID") or _default_server_id()
    params: dict[str, str] = {"server_id": server_id, "session_id": name, "limit": str(max(1, int(limit))), "code": code}
    if topic:
        params["topic"] = topic
    data = _get_json(_build_url(base_url, "/api/logs", params))
    if out_format == "json":
        sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
        return 0
    items = data.get("items") or []
    if isinstance(items, list):
        _print_logs_text([x for x in items if isinstance(x, dict)])
    return 0


def do_status(name: str, *, limit: int, topic: str | None) -> int:
    base_url = _env("CLIMAX_FUNCTIONS_URL")
    code = _env("CLIMAX_FUNCTIONS_CODE")
    server_id = _env("CLIMAX_SERVER_ID") or _default_server_id()
    sess = _get_json(_build_url(base_url, "/api/session/get", {"server_id": server_id, "session_id": name, "code": code}))
    item = sess.get("item") if isinstance(sess, dict) else None
    if not isinstance(item, dict):
        item = sess if isinstance(sess, dict) else {}
    sys.stdout.write(f"session: {name}\n")
    directory = item.get("directory") or item.get("cwd") or ""
    updated = item.get("updated_at") or ""
    if directory:
        sys.stdout.write(f"  dir: {directory}\n")
    if updated:
        sys.stdout.write(f"  updated_at: {updated}\n")
    sys.stdout.write("\n")
    do_logs(name, limit=limit, topic=topic, out_format="text")
    return 0


def collect_tmux_panes(name: str) -> tuple[list[dict[str, Any]], str]:
    codex_sess = f"codex-{name}"
    cmd_sess = f"cmd-{name}"
    log_sess = f"log-{name}"
    panes: list[dict[str, Any]] = []
    directory = ""
    for sess in (cmd_sess, codex_sess, log_sess):
        if not has_session(sess):
            continue
        try:
            out = subprocess.check_output(
                ["tmux", "list-panes", "-t", sess, "-F", "#{pane_index}\t#{pane_current_path}\t#{pane_current_command}"],
                text=True,
            )
        except Exception:
            continue
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            idx_s, cwd, cmd = parts
            try:
                idx = int(idx_s)
            except ValueError:
                continue
            panes.append({"session": sess, "pane": idx, "cwd": cwd, "command": cmd})
            if sess == codex_sess and idx == 0 and cwd:
                directory = cwd
    return panes, directory


def do_sync(name: str, workspace: Path, *, with_cmd: bool, with_log: bool) -> int:
    base_url = _env("CLIMAX_FUNCTIONS_URL")
    code = _env("CLIMAX_FUNCTIONS_CODE")
    server_id = _env("CLIMAX_SERVER_ID") or _default_server_id()
    require_tmux()
    ensure_sessions(name, workspace, with_cmd=with_cmd, with_log=with_log)
    panes, directory = collect_tmux_panes(name)
    if not directory:
        directory = str((workspace / name).resolve())
    url = _build_url(base_url, "/api/session/update", {"code": code})
    data = _post_json(url, {"server_id": server_id, "session_id": name, "directory": directory, "panes": panes})
    sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
    return 0


def do_menu(ns: argparse.Namespace, workspace: Path) -> int:
    name = ns.name or pick_session_from_chronicle_or_workspace(workspace)
    _write_last_session(name)
    print(f"Selected: {name}", file=sys.stderr)

    actions = [
        ("change", "Change session"),
        ("codex", "Attach codex session"),
        ("cmd", "Attach cmd session"),
        ("log", "Attach log session (show latest)"),
        ("follow", "Attach log session (auto-refresh)"),
        ("topic", "Set topic filter"),
        ("limit", "Set log limit"),
        ("format", "Toggle output format (text/json)"),
        ("status", "Show status (session + logs)"),
        ("logs", "Fetch logs (print)"),
        ("sync", "Sync tmux -> Chronicle"),
        ("session", "Show session record"),
        ("sessions", "List sessions"),
        ("doctor", "Doctor (env + /api/health)"),
        ("stop", "Stop cmd/log sessions"),
    ]

    last_action = _read_last_action()

    last_topic = _read_last_topic()
    last_limit = _read_last_limit()
    last_format = _read_last_format()
    if last_format and ns.format == "text":
        ns.format = last_format
    if last_topic and not ns.topic:
        ns.topic = last_topic
    if last_limit and ns.limit == 20:
        ns.limit = last_limit

    while True:
        cur_topic = ns.topic or "(none)"
        print(f"settings: session={name} topic={cur_topic} limit={ns.limit} format={ns.format}", file=sys.stderr)
        for i, (_, label) in enumerate(actions, 1):
            print(f"{i:2d}) {label}", file=sys.stderr)
        print(" 0) Quit", file=sys.stderr)

        default_index: int | None = None
        if last_action:
            for i, (a, _) in enumerate(actions, 1):
                if a == last_action:
                    default_index = i
                    break

        prompt = "Select action"
        if default_index:
            prompt += f" (default: {default_index})"
        prompt += ": "

        sel = input(prompt).strip()
        if not sel and default_index:
            action = actions[default_index - 1][0]
        else:
            if not sel.isdigit():
                return 0
            n = int(sel)
            if n == 0 or not (1 <= n <= len(actions)):
                return 0
            action = actions[n - 1][0]

        _write_last_action(action)
        last_action = action

        if action == "change":
            name = pick_session_from_chronicle_or_workspace(workspace)
            _write_last_session(name)
            print(f"Selected: {name}", file=sys.stderr)
            continue

        if action == "topic":
            cur = ns.topic or ""
            val = input(f"Topic (empty to clear) [{cur}]: ").strip()
            ns.topic = val or None
            if ns.topic is not None:
                _write_last_topic(ns.topic)
            continue

        if action == "limit":
            cur = str(ns.limit)
            val = input(f"Limit [{cur}]: ").strip()
            if val.isdigit():
                ns.limit = max(1, int(val))
                _write_last_limit(ns.limit)
            continue

        if action == "format":
            ns.format = "json" if ns.format == "text" else "text"
            _write_last_format(ns.format)
            print(f"format: {ns.format}", file=sys.stderr)
            continue

        if action == "doctor":
            do_doctor()
            continue
        if action == "sessions":
            if not _chronicle_available():
                raise SystemExit("Missing CLIMAX_FUNCTIONS_URL/CLIMAX_FUNCTIONS_CODE")
            do_sessions(ns.format)
            continue
        if action in ("session", "logs", "status", "sync"):
            if not _chronicle_available():
                raise SystemExit("Missing CLIMAX_FUNCTIONS_URL/CLIMAX_FUNCTIONS_CODE")
            if action == "session":
                do_session(name, ns.format)
                continue
            if action == "logs":
                do_logs(name, limit=ns.limit, topic=ns.topic, out_format=ns.format)
                continue
            if action == "status":
                do_status(name, limit=ns.limit, topic=ns.topic)
                continue
            if action == "sync":
                do_sync(name, workspace, with_cmd=not ns.no_cmd, with_log=not ns.no_log)
                continue

        require_tmux()
        ensure_sessions(name, workspace, with_cmd=not ns.no_cmd, with_log=not ns.no_log)
        codex_sess = f"codex-{name}"
        cmd_sess = f"cmd-{name}"
        log_sess = f"log-{name}"

        if action == "stop":
            kill_sessions(name, stop_all=ns.stop_all)
            continue
        if action == "cmd":
            inject_clients_env(cmd_sess)
            os.execvp("tmux", ["tmux", "attach", "-t", cmd_sess])
        if action == "log":
            inject_clients_env(log_sess)
            show_latest_logs_in_log_session(
                name,
                log_sess,
                limit=max(1, int(ns.limit)),
                topic=ns.topic,
                out_format=ns.format,
                follow=False,
                interval=int(ns.interval),
            )
            os.execvp("tmux", ["tmux", "attach", "-t", log_sess])
        if action == "follow":
            inject_clients_env(log_sess)
            show_latest_logs_in_log_session(
                name,
                log_sess,
                limit=max(1, int(ns.limit)),
                topic=ns.topic,
                out_format=ns.format,
                follow=True,
                interval=int(ns.interval),
            )
            os.execvp("tmux", ["tmux", "attach", "-t", log_sess])

        os.execvp("tmux", ["tmux", "attach", "-t", codex_sess])


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="ctm", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--workspace", default=str(Path.home() / "Workspace"))
    parser.add_argument("--no-cmd", action="store_true")
    parser.add_argument("--no-log", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--all", dest="stop_all", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--topic", default=os.getenv("CLIMAX_TOPIC"))
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--follow", action="store_true")
    parser.add_argument("--interval", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "subcmd",
        nargs="?",
        choices=["cmd", "log", "logs", "menu", "session", "sessions", "sync", "status", "doctor", "stop", "backfill"],
        default=None,
    )
    parser.add_argument("name", nargs="?")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    ns = parse_args(argv)
    load_dotenv(CLIENTS_ENV_PATH)

    workspace = Path(os.path.expanduser(ns.workspace)).resolve()
    if not workspace.is_dir():
        raise SystemExit(f"Workspace not found: {workspace}")

    if ns.subcmd == "menu":
        return do_menu(ns, workspace)

    if ns.subcmd is None and ns.name is None:
        # default: interactive menu (no need to remember subcommands)
        return do_menu(ns, workspace)


    if ns.subcmd == "doctor":
        return do_doctor()

    if ns.subcmd == "sessions":
        if not _chronicle_available():
            raise SystemExit("Missing CLIMAX_FUNCTIONS_URL/CLIMAX_FUNCTIONS_CODE")
        return do_sessions(ns.format)

    if ns.subcmd == "backfill":
        if not _chronicle_available():
            raise SystemExit("Missing CLIMAX_FUNCTIONS_URL/CLIMAX_FUNCTIONS_CODE")
        return do_backfill(limit=ns.limit, topic=ns.topic, dry_run=bool(ns.dry_run), out_format=ns.format)

    # Name required for most subcommands.
    if ns.subcmd in ("cmd", "log", "logs", "session", "sync", "status", "stop"):
        if not ns.name:
            raise SystemExit(f"Missing name for: {ns.subcmd}")
        name = ns.name
    else:
        name = ns.name or pick_workspace_dir(workspace)

    if ns.subcmd in ("logs", "session", "sync", "status") and not _chronicle_available():
        raise SystemExit("Missing CLIMAX_FUNCTIONS_URL/CLIMAX_FUNCTIONS_CODE")

    if ns.subcmd == "session":
        return do_session(name, ns.format)
    if ns.subcmd == "logs":
        return do_logs(name, limit=ns.limit, topic=ns.topic, out_format=ns.format)
    if ns.subcmd == "status":
        return do_status(name, limit=ns.limit, topic=ns.topic)
    if ns.subcmd == "sync":
        return do_sync(name, workspace, with_cmd=not ns.no_cmd, with_log=not ns.no_log)

    codex_sess = f"codex-{name}"
    cmd_sess = f"cmd-{name}"
    log_sess = f"log-{name}"

    if ns.subcmd == "stop":
        require_tmux()
        kill_sessions(name, stop_all=ns.stop_all)
        return 0

    require_tmux()
    ensure_sessions(name, workspace, with_cmd=not ns.no_cmd, with_log=not ns.no_log)

    if ns.subcmd == "cmd":
        inject_clients_env(cmd_sess)
        os.execvp("tmux", ["tmux", "attach", "-t", cmd_sess])

    if ns.subcmd == "log":
        inject_clients_env(log_sess)
        show_latest_logs_in_log_session(
            name,
            log_sess,
            limit=max(1, int(ns.limit)),
            topic=ns.topic,
            out_format=ns.format,
            follow=bool(ns.follow),
            interval=int(ns.interval),
        )
        os.execvp("tmux", ["tmux", "attach", "-t", log_sess])

    # default: codex attach with best-effort autosync
    if os.getenv("CTM_AUTOSYNC", "1") != "0" and _chronicle_available():
        try:
            base_url = _env("CLIMAX_FUNCTIONS_URL")
            code = _env("CLIMAX_FUNCTIONS_CODE")
            server_id = _env("CLIMAX_SERVER_ID") or _default_server_id()
            panes, directory = collect_tmux_panes(name)
            if not directory:
                directory = str((workspace / name).resolve())
            url = _build_url(base_url, "/api/session/update", {"code": code})
            _post_json(url, {"server_id": server_id, "session_id": name, "directory": directory, "panes": panes})
        except Exception:
            pass

    p = subprocess.run(["tmux", "attach", "-t", codex_sess])
    if ns.cleanup:
        kill_sessions(name, stop_all=False)
    return p.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

