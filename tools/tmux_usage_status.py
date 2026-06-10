#!/usr/bin/env python3
"""Render a compact usage status line for tmux.

The script is intentionally best-effort:
- GitHub Copilot: monthly premium request usage from GitHub's billing API
- Claude Code: Anthropic usage report from the Admin API
- Codex/OpenAI: monthly cost usage from the OpenAI organization costs API

Each provider can be used with no extra config if the relevant auth token is
available in the environment. Optional budget variables let the script compute
"remaining" values for the status line.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple


UTC = dt.timezone.utc


@dataclass
class StatusItem:
    label: str
    text: str
    ok: bool = True


def now_utc() -> dt.datetime:
    return dt.datetime.now(tz=UTC)


def month_bounds_utc(moment: Optional[dt.datetime] = None) -> Tuple[dt.datetime, dt.datetime]:
    moment = moment or now_utc()
    start = dt.datetime(moment.year, moment.month, 1, tzinfo=UTC)
    if moment.month == 12:
        end = dt.datetime(moment.year + 1, 1, 1, tzinfo=UTC)
    else:
        end = dt.datetime(moment.year, moment.month + 1, 1, tzinfo=UTC)
    return start, end


def fmt_int(n: Optional[int]) -> str:
    if n is None:
        return "?"
    return f"{n:,}"


def fmt_float(n: Optional[float]) -> str:
    if n is None:
        return "?"
    return f"{n:,.2f}"


def fmt_tokens(n: Optional[int]) -> str:
    if n is None:
        return "?"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def parse_int_env(*names: str) -> Optional[int]:
    for name in names:
        raw = os.getenv(name)
        if not raw:
            continue
        try:
            return int(raw)
        except ValueError:
            return None
    return None


def parse_float_env(*names: str) -> Optional[float]:
    for name in names:
        raw = os.getenv(name)
        if not raw:
            continue
        try:
            return float(raw)
        except ValueError:
            return None
    return None


def env(*names: str) -> Optional[str]:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def run_command(args: Iterable[str], timeout: int = 10) -> Tuple[int, str, str]:
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


def http_json(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 15,
) -> Any:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
        return json.loads(payload)


def github_user_name() -> Optional[str]:
    value = env("GITHUB_USER", "GH_USER")
    if value:
        return value

    if not shutil_which("gh"):
        return None

    code, stdout, _ = run_command(["gh", "api", "user", "--jq", ".login"])
    if code == 0 and stdout:
        return stdout
    return None


def github_token() -> Optional[str]:
    value = env("GH_TOKEN", "GITHUB_TOKEN", "COPILOT_GITHUB_TOKEN")
    if value:
        return value

    if not shutil_which("gh"):
        return None

    code, stdout, _ = run_command(["gh", "auth", "token"])
    if code == 0 and stdout:
        return stdout
    return None


def github_copilot_status(now: dt.datetime) -> StatusItem:
    username = github_user_name()
    token = github_token()
    if not username or not token:
        return StatusItem("copilot", "auth?", ok=False)

    scope = env("COPILOT_USAGE_SCOPE") or "user"
    start, _ = month_bounds_utc(now)
    params = {
        "year": str(now.year),
        "month": str(now.month),
    }
    if scope == "org":
        org = env("GITHUB_ORG", "GITHUB_ORGANIZATION")
        if not org:
            return StatusItem("copilot", "org?", ok=False)
        endpoint = f"https://api.github.com/organizations/{urllib.parse.quote(org)}/settings/billing/premium_request/usage"
    else:
        endpoint = f"https://api.github.com/users/{urllib.parse.quote(username)}/settings/billing/premium_request/usage"

    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "climax-tmux-usage-status",
    }
    try:
        data = http_json(url, headers=headers)
    except Exception:
        return StatusItem("copilot", "err", ok=False)

    used = 0
    for item in data.get("usageItems", []):
        if str(item.get("product", "")).lower() != "copilot":
            continue
        used += int(item.get("netQuantity") or 0)

    allowance = parse_int_env("COPILOT_MONTHLY_ALLOWANCE", "GITHUB_COPILOT_MONTHLY_ALLOWANCE")
    if allowance is not None:
        remaining = max(allowance - used, 0)
        return StatusItem("copilot", f"{fmt_int(remaining)}pr left")
    return StatusItem("copilot", f"{fmt_int(used)}pr used")


def anthropic_usage_status(now: dt.datetime) -> StatusItem:
    admin_key = env("ANTHROPIC_ADMIN_KEY")
    if not admin_key:
        return StatusItem("claude", "auth?", ok=False)

    start, end = month_bounds_utc(now)
    params = {
        "starting_at": start.isoformat().replace("+00:00", "Z"),
        "ending_at": end.isoformat().replace("+00:00", "Z"),
        "limit": "31",
        "bucket_width": "1d",
    }
    url = "https://api.anthropic.com/v1/organizations/usage_report/messages?" + urllib.parse.urlencode(params)
    headers = {
        "x-api-key": admin_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    try:
        data = http_json(url, headers=headers)
    except Exception:
        return StatusItem("claude", "err", ok=False)

    input_tokens = 0
    output_tokens = 0
    for bucket in data.get("data", []):
        for result in bucket.get("results", []):
            input_tokens += int(result.get("uncached_input_tokens") or 0)
            input_tokens += int(result.get("cache_read_input_tokens") or 0)
            cache_creation = result.get("cache_creation") or {}
            input_tokens += int(cache_creation.get("ephemeral_1h_input_tokens") or 0)
            input_tokens += int(cache_creation.get("ephemeral_5m_input_tokens") or 0)
            output_tokens += int(result.get("output_tokens") or 0)

    total_tokens = input_tokens + output_tokens
    budget = parse_int_env("CLAUDE_MONTHLY_TOKEN_BUDGET", "ANTHROPIC_MONTHLY_TOKEN_BUDGET")
    if budget is not None:
        remaining = max(budget - total_tokens, 0)
        return StatusItem("claude", f"{fmt_tokens(remaining)}tok left")
    return StatusItem("claude", f"{fmt_tokens(total_tokens)}tok used")


def openai_cost_status(now: dt.datetime) -> StatusItem:
    admin_key = env("OPENAI_ADMIN_KEY")
    if not admin_key:
        return StatusItem("codex", "auth?", ok=False)

    start, end = month_bounds_utc(now)
    params = {
        "start_time": str(int(start.timestamp())),
        "end_time": str(int(end.timestamp())),
        "bucket_width": "1d",
        "limit": "31",
    }
    project_id = env("OPENAI_PROJECT_ID")
    if project_id:
        params["project_ids"] = project_id
    url = "https://api.openai.com/v1/organization/costs?" + urllib.parse.urlencode(params, doseq=True)
    headers = {
        "Authorization": f"Bearer {admin_key}",
        "Content-Type": "application/json",
    }
    try:
        data = http_json(url, headers=headers)
    except Exception:
        return StatusItem("codex", "err", ok=False)

    spent = 0.0
    for bucket in data.get("data", []):
        for result in bucket.get("results", []):
            amount = result.get("amount") or {}
            spent += float(amount.get("value") or 0.0)

    budget = parse_float_env("OPENAI_MONTHLY_BUDGET_USD", "OPENAI_COST_BUDGET_USD")
    if budget is not None:
        remaining = max(budget - spent, 0.0)
        return StatusItem("codex", f"${fmt_float(remaining)} left")
    return StatusItem("codex", f"${fmt_float(spent)} spent")


def shutil_which(name: str) -> Optional[str]:
    from shutil import which

    return which(name)


def render(items: Iterable[StatusItem], separator: str = " | ") -> str:
    parts = []
    for item in items:
        parts.append(f"{item.label} {item.text}")
    return separator.join(parts)


def to_json(items: Iterable[StatusItem]) -> str:
    payload = {
        item.label: {
            "text": item.text,
            "ok": item.ok,
        }
        for item in items
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a tmux-friendly usage status line.")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a flat status line")
    args = parser.parse_args()

    now = now_utc()
    items = [
        github_copilot_status(now),
        anthropic_usage_status(now),
        openai_cost_status(now),
    ]

    if args.json:
        print(to_json(items))
    else:
        print(render(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
