#!/usr/bin/env bash
set -euo pipefail

die() { echo "error: $*" >&2; exit 1; }

require_env() {
  local name="$1"
  [[ -n "${!name:-}" ]] || die "missing env: $name"
}

chronicle_url() {
  require_env CHRONICLE_BASE_URL
  local path="$1"
  local base="${CHRONICLE_BASE_URL%/}"
  local key="${CHRONICLE_FUNCTION_KEY:-}"
  if [[ -n "$key" ]]; then
    if [[ "$key" == \?code=* ]]; then
      echo "${base}${path}${key}"
    else
      echo "${base}${path}?code=${key}"
    fi
  else
    echo "${base}${path}"
  fi
}

server_id() {
  echo "${CLIMAX_SERVER_ID:-$(hostname -s)}"
}

