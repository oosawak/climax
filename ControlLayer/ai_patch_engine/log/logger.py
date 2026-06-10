from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class JsonlLogger:
    path: Path

    def write(self, payload: dict[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.write("\n")


def log_event(
    path: str | Path,
    *,
    action: str,
    status: str,
    files: list[str],
    snapshot_id: str | None,
    dry_run: bool,
    details: list[str] | None = None,
    error: str | None = None,
) -> None:
    logger = JsonlLogger(Path(path))
    payload: dict[str, object] = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "action": action,
        "status": status,
        "files": files,
        "snapshot_id": snapshot_id,
        "dry_run": dry_run,
    }
    if details is not None:
        payload["details"] = details
    if error is not None:
        payload["error"] = error
    logger.write(payload)
