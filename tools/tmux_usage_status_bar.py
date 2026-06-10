#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_CACHE_PATH = Path(os.getenv("TMUX_USAGE_CACHE_PATH", "/tmp/climax-tmux-usage.json"))
STALE_AFTER_SECONDS = int(os.getenv("TMUX_USAGE_CACHE_STALE_AFTER", "1800"))


@dataclass
class StatusItem:
    label: str
    text: str
    ok: bool = True


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: str) -> Optional[datetime]:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except Exception:
        return None


def _fmt_age(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m"
    return f"{int(seconds // 3600)}h"


def _load_cache(path: Path) -> dict:
    if not path.exists():
        return {"generated_at": None, "items": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"generated_at": None, "items": []}


def _items_from_payload(payload: dict) -> list[StatusItem]:
    items: list[StatusItem] = []
    for raw in payload.get("items", []):
        label = str(raw.get("label", "?"))
        text = str(raw.get("text", "n/a"))
        ok = bool(raw.get("ok", True))
        items.append(StatusItem(label=label, text=text, ok=ok))
    return items


def _render(items: Iterable[StatusItem], separator: str = " | ") -> str:
    return separator.join(f"{item.label} {item.text}" for item in items)


def _render_json(items: Iterable[StatusItem]) -> str:
    payload = {
        item.label: {"text": item.text, "ok": item.ok}
        for item in items
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Render cached usage status for tmux.")
    parser.add_argument("--cache", default=str(DEFAULT_CACHE_PATH), help="path to the cache JSON file")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a flat status line")
    args = parser.parse_args()

    cache_path = Path(args.cache)
    payload = _load_cache(cache_path)
    items = _items_from_payload(payload)
    generated_at = payload.get("generated_at")
    if generated_at:
        ts = _parse_timestamp(str(generated_at))
        if ts is not None:
            age = (_now() - ts).total_seconds()
            if age > STALE_AFTER_SECONDS:
                items.append(StatusItem("cache", f"stale {_fmt_age(age)}", ok=False))

    if not items:
        items = [StatusItem("cache", "missing", ok=False)]

    print(_render_json(items) if args.json else _render(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
