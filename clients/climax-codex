#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'MSG'
Usage:
  climax-codex <Japanese text...>
  echo <Japanese text> | climax-codex

Description:
  Converts Japanese text to `final_prompt` via /api/nlp/analyze, then launches Codex
  with that prompt as the initial message.

Env:
  CLIMAX_FUNCTIONS_URL   (required)
  CLIMAX_FUNCTIONS_CODE  (required)

Optional:
  CODEX_BIN              (default: codex)
  CODEX_SUBCOMMAND       (default: sh)

Examples:
  climax-codex "unity-devの続きやって"
  echo "ログまとめて" | climax-codex

Notes:
  Codex CLI supports passing an initial prompt as a positional argument in many versions.
  If your Codex build doesn't accept this, run `codex --help` and adjust CODEX_SUBCOMMAND.
MSG
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
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

: "${CLIMAX_FUNCTIONS_URL:?Missing CLIMAX_FUNCTIONS_URL}"
: "${CLIMAX_FUNCTIONS_CODE:?Missing CLIMAX_FUNCTIONS_CODE}"

CODEX_BIN="${CODEX_BIN:-codex}"
CODEX_SUBCOMMAND="${CODEX_SUBCOMMAND:-sh}"

if ! command -v "$CODEX_BIN" >/dev/null 2>&1; then
  echo "Missing codex binary: $CODEX_BIN" >&2
  exit 1
fi

final_prompt="$(python "$(dirname "$0")/climax_preprocess_client.py" \
  --functions-url "$CLIMAX_FUNCTIONS_URL" \
  --functions-code "$CLIMAX_FUNCTIONS_CODE" \
  --text "$text" \
  --format final_prompt)"

# Launch codex with the generated prompt.
exec "$CODEX_BIN" "$CODEX_SUBCOMMAND" "$final_prompt"
