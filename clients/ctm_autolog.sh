#!/usr/bin/env bash
# ctm_autolog.sh
# Provides ctmlog_post "<command>" "<exit_code>" "<cwd>" to POST a minimal log to Chronicle.

ctmlog_post(){
  cmd="$1"
  exit_code="$2"
  cwd="$3"

  if [ -z "${CLIMAX_FUNCTIONS_URL:-}" ]; then
    return 0
  fi

  base="${CLIMAX_FUNCTIONS_URL%/}"
  url="${base}/api/log/append"
  if [ -n "${CLIMAX_FUNCTIONS_CODE:-}" ]; then
    url="${url}?code=${CLIMAX_FUNCTIONS_CODE}"
  fi

  server_id="${CLIMAX_SERVER_ID:-$(hostname -s)}"

  session_id=""
  if [ -n "${TMUX:-}" ]; then
    sess=$(tmux display-message -p "#S" 2>/dev/null || true)
    # strip known prefixes (codex-, cmd-, log-)
    session_id="${sess#codex-}"
    session_id="${session_id#cmd-}"
    session_id="${session_id#log-}"
  fi

  topic="${CLIMAX_TOPIC:-default}"

  # sanitize double quotes in fields
  esc(){ echo "$1" | sed 's/"/\\"/g'; }
  server_id_s=$(esc "$server_id")
  session_id_s=$(esc "$session_id")
  topic_s=$(esc "$topic")
  cmd_s=$(esc "$cmd")
  cwd_s=$(esc "$cwd")

  payload=$(printf '{"server_id":"%s","session_id":"%s","topic":"%s","command":"%s","exit_code":%s,"cwd":"%s","log":"%s"}' \
    "$server_id_s" "$session_id_s" "$topic_s" "$cmd_s" "$exit_code" "$cwd_s" "(output not captured)")

  # fire-and-forget POST to avoid blocking the shell prompt
  curl --silent --show-error --fail -X POST -H "Content-Type: application/json" -d "$payload" "$url" >/dev/null 2>&1 &
  return 0
}
