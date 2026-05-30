#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$DIR/lib.sh"

session_id=""
file=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --session-id) session_id="${2:-}"; shift 2;;
    --file) file="${2:-}"; shift 2;;
    *) die "unknown arg: $1";;
  esac
done

[[ -n "$session_id" ]] || die "--session-id required"
[[ -n "$file" ]] || die "--file required"

url="$(chronicle_url "/api/log/append")"

tail -n 0 -F "$file" | while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  python3 - "$session_id" "$(server_id)" "$line" | curl -fsS -X POST -H "Content-Type: application/json" --data-binary @- "$url" >/dev/null
done

PYTHON_CODE='
import json, sys
from datetime import datetime, timezone
session_id=sys.argv[1]
server_id=sys.argv[2]
line=sys.argv[3]
payload={
  "server_id": server_id,
  "session_id": session_id,
  "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
  "log": line,
}
print(json.dumps(payload, ensure_ascii=False))
'

python3 -c "$PYTHON_CODE"

