#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'MSG'
Usage:
  climax-send <Japanese text...>
  echo <Japanese text> | climax-send

Description:
  Converts Japanese text to `final_prompt` via /api/nlp/analyze, then sends it to
  the currently active tmux pane (and presses Enter).

Requirements:
  - tmux
  - CLIMAX_FUNCTIONS_URL / CLIMAX_FUNCTIONS_CODE env vars (or load from clients/.env)

Notes:
  - This does not "hook" Codex internals; it injects keystrokes into the active pane.
  - Run this from a different pane than the Codex TUI pane (otherwise you'll type into yourself).
MSG
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if ! command -v tmux >/dev/null 2>&1; then
  echo "Missing tmux." >&2
  exit 1
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

final_prompt="$(python "$(dirname "$0")/climax_preprocess_client.py" \
  --functions-url "$CLIMAX_FUNCTIONS_URL" \
  --functions-code "$CLIMAX_FUNCTIONS_CODE" \
  --text "$text" \
  --format final_prompt)"

# Send to active pane.
# -l sends the string literally.
tmux send-keys -l -- "$final_prompt"
tmux send-keys Enter
