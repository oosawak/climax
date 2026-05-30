#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$DIR/lib.sh"

session_id=""
directory="${PWD}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --session-id) session_id="${2:-}"; shift 2;;
    --directory) directory="${2:-}"; shift 2;;
    *) die "unknown arg: $1";;
  esac
done

[[ -n "$session_id" ]] || die "--session-id required"

payload="$(mktemp)"

zellij_json="$("$DIR/dump_zellij_session_json.sh" || true)"

python3 - "$session_id" "$directory" "$(server_id)" "$zellij_json" >"$payload" <<'PY'
import json
import sys
from datetime import datetime, timezone

session_id = sys.argv[1]
directory = sys.argv[2]
server_id = sys.argv[3]
zellij_json = sys.argv[4]

try:
    z = json.loads(zellij_json) if zellij_json.strip() else {}
except Exception:
    z = {}

panes = []
if isinstance(z, dict):
    # Keep the raw structure as a pane entry for now; refine later.
    if z:
        panes.append({"source": "zellij", "dump": z})

payload = {
    "server_id": server_id,
    "session_id": session_id,
    "directory": directory,
    "panes": panes,
    "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
}
print(json.dumps(payload, ensure_ascii=False))
PY

url="$(chronicle_url "/api/session/update")"
curl -fsS -X POST -H "Content-Type: application/json" --data-binary @"$payload" "$url" >/dev/null
echo "sent session update: ${session_id}"

