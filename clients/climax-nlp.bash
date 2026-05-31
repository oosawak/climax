#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'MSG'
Usage:
  cj <Japanese text...>
  echo <Japanese text> | cj

  # optional
  cj --backend local|blob
  cj --pull --backend blob

Converts Japanese command into `final_prompt` via /api/nlp/analyze.

Backends:
- local (default): writes to ~/.climax/latest_final_prompt.txt
- blob: uploads to Azure Blob Storage (also keeps local copy)

Env vars (recommended):
  CLIMAX_FUNCTIONS_URL   (e.g. https://func-api-eedplxgcbbmra.azurewebsites.net)
  CLIMAX_FUNCTIONS_CODE  (function key; required for deployed Azure)

Optional:
  CLIMAX_PROMPT_DIR      (default: ~/.climax)
  CLIMAX_BACKEND         (default: local)

Blob backend env vars:
  CLIMAX_BLOB_ACCOUNT    (storage account name)
  CLIMAX_BLOB_CONTAINER  (container name)
  CLIMAX_BLOB_NAME       (default: latest_final_prompt.txt)

Auth for blob upload/download:
- Prefer: Azure CLI login (uses: --auth-mode login)
- Or: set CLIMAX_BLOB_CONNECTION_STRING (uses: --connection-string)
MSG
}

backend="${CLIMAX_BACKEND:-local}"
pull=0

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --backend) backend="$2"; shift 2 ;;
    --pull) pull=1; shift 1 ;;
    --) shift; break ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) break ;;
  esac
done

case "$backend" in
  local|blob) ;;
  *) echo "Invalid backend: $backend (expected local|blob)" >&2; exit 2 ;;
esac

: "${CLIMAX_FUNCTIONS_URL:?Missing CLIMAX_FUNCTIONS_URL}"
: "${CLIMAX_FUNCTIONS_CODE:?Missing CLIMAX_FUNCTIONS_CODE}"

PROMPT_DIR="${CLIMAX_PROMPT_DIR:-$HOME/.climax}"
mkdir -p "$PROMPT_DIR"

out="$PROMPT_DIR/latest_final_prompt.txt"
json_out="$PROMPT_DIR/latest_nlp.json"

blob_account="${CLIMAX_BLOB_ACCOUNT:-}"
blob_container="${CLIMAX_BLOB_CONTAINER:-}"
blob_name="${CLIMAX_BLOB_NAME:-latest_final_prompt.txt}"
blob_conn="${CLIMAX_BLOB_CONNECTION_STRING:-}"

blob_args=()
if [ -n "$blob_conn" ]; then
  blob_args+=(--connection-string "$blob_conn")
else
  blob_args+=(--auth-mode login)
fi

if [ "$backend" = "blob" ] || [ $pull -eq 1 ]; then
  if [ -z "$blob_account" ] || [ -z "$blob_container" ]; then
    echo "Missing blob settings. Set CLIMAX_BLOB_ACCOUNT and CLIMAX_BLOB_CONTAINER." >&2
    exit 1
  fi
fi

if [ $pull -eq 1 ]; then
  if [ "$backend" != "blob" ]; then
    echo "--pull requires --backend blob" >&2
    exit 2
  fi

  az storage blob download \
    --account-name "$blob_account" \
    --container-name "$blob_container" \
    --name "$blob_name" \
    --file "$out" \
    "${blob_args[@]}" \
    >/dev/null

  printf '%s\n' "$out"
  exit 0
fi

text=""
if [ $# -gt 0 ]; then
  text="$*"
else
  text="$(cat)"
fi
text="$(printf '%s' "$text" | sed -e 's/^ *//' -e 's/ *$//')"
if [ -z "$text" ]; then
  echo "No input text." >&2
  exit 1
fi

python "$(dirname "$0")/climax_preprocess_client.py" \
  --functions-url "$CLIMAX_FUNCTIONS_URL" \
  --functions-code "$CLIMAX_FUNCTIONS_CODE" \
  --text "$text" \
  --format json \
  >"$json_out"

python - <<PY
import json
from pathlib import Path

data = json.loads(Path("$json_out").read_text(encoding="utf-8"))
final_prompt = str(data.get("final_prompt") or "")
Path("$out").write_text(final_prompt, encoding="utf-8")
PY

if [ "$backend" = "blob" ]; then
  az storage blob upload \
    --account-name "$blob_account" \
    --container-name "$blob_container" \
    --name "$blob_name" \
    --file "$out" \
    --overwrite \
    "${blob_args[@]}" \
    >/dev/null
fi

printf '%s\n' "$out"
