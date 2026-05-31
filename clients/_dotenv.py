from __future__ import annotations

import os
from pathlib import Path


def parse_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            continue
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
            v = v[1:-1]
        out[k] = v
    return out


def load_dotenv(path: Path, *, override: bool = False) -> dict[str, str]:
    vals = parse_dotenv(path)
    for k, v in vals.items():
        if override or (k not in os.environ):
            os.environ[k] = v
    return vals

