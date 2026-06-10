#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="${CLIMAX_BIN_DIR:-$HOME/.local/bin}"
mkdir -p "$BIN_DIR"

link_one() {
  local name="$1"
  local target="$SCRIPT_DIR/$name"
  if [ ! -e "$target" ]; then
    return 0
  fi
  ln -sf "$target" "$BIN_DIR/$name"
}

link_one ctm
link_one ctmcmd
link_one cj
link_one climax-nlp
link_one climax-codex
link_one climax-send
link_one climax-cmdlog

case ":${PATH}:" in
  *":$BIN_DIR:"*) : ;;
  *)
    echo "Note: add $BIN_DIR to PATH if it is not already present." >&2
    echo "  export PATH=\"$BIN_DIR:$PATH\"" >&2
    ;;
esac

echo "Installed client shims into: $BIN_DIR" >&2
