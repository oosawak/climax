#!/usr/bin/env bash
set -euo pipefail

# Tries to dump current zellij session as JSON.
# This script is defensive about CLI differences across zellij versions.

try() {
  if "$@" >/tmp/zellij-dump.json 2>/tmp/zellij-dump.err; then
    cat /tmp/zellij-dump.json
    return 0
  fi
  return 1
}

command -v zellij >/dev/null 2>&1 || { echo "{}"; exit 0; }

# Candidate invocations (best-effort; first working one wins)
try zellij action dump-session --output-format json && exit 0
try zellij action dump-session --format json && exit 0
try zellij action dump-session --json && exit 0
try zellij action dump-session && exit 0

echo "{}"

