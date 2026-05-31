#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'MSG'
Usage:
  ctm                  # pick a workspace dir, attach to codex-<name>
  ctm <name>           # create/reuse sessions, attach to codex-<name>
  ctm cmd <name>       # attach to cmd-<name>
  ctm log <name>       # attach to log-<name>
  ctm stop <name>      # kill cmd-<name> and log-<name>
  ctm --all stop <name># kill codex/cmd/log sessions

Options:
  --workspace <dir>    (default: ~/Workspace)
  --no-cmd             do not create cmd-<name>
  --no-log             do not create log-<name>
  --cleanup            after codex session ends, kill cmd/log sessions

Creates (or reuses) three tmux sessions per workspace directory:
  - codex-<name>: runs `codex sh` in <workspace>/<name>
  - cmd-<name>:   shell in <workspace>/<name>
  - log-<name>:   shell in <workspace>/<name> (reserved for log tail/senders)
MSG
}

workspace="$HOME/Workspace"
with_cmd=1
with_log=1
cleanup=0
stop_all=0

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --workspace) workspace="$2"; shift 2 ;;
    --no-cmd) with_cmd=0; shift 1 ;;
    --no-log) with_log=0; shift 1 ;;
    --cleanup) cleanup=1; shift 1 ;;
    --all) stop_all=1; shift 1 ;;
    --) shift; break ;;
    *) break ;;
  esac
done

if ! command -v tmux >/dev/null 2>&1; then
  echo "Missing tmux." >&2
  exit 1
fi

workspace="${workspace%/}"
if [ ! -d "$workspace" ]; then
  echo "Workspace not found: $workspace" >&2
  exit 1
fi

pick_name() {
  local d
  echo "Select a workspace directory under: $workspace" >&2
  local i=1
  local -a names=()
  while IFS= read -r d; do
    d="$(basename "$d")"
    names+=("$d")
    printf '%2d) %s\n' "$i" "$d" >&2
    i=$((i+1))
  done < <(find "$workspace" -maxdepth 1 -mindepth 1 -type d -printf '%p\n' | sort)

  if [ ${#names[@]} -eq 0 ]; then
    echo "No directories found under $workspace" >&2
    exit 1
  fi

  local sel
  read -r -p "Enter number: " sel >&2
  if ! [[ "$sel" =~ ^[0-9]+$ ]]; then
    echo "Invalid selection." >&2
    exit 1
  fi
  if [ "$sel" -lt 1 ] || [ "$sel" -gt ${#names[@]} ]; then
    echo "Out of range." >&2
    exit 1
  fi
  echo "${names[$((sel-1))]}"
}

subcmd=""
name=""

case "${1:-}" in
  cmd|log|stop)
    subcmd="$1"
    name="${2:-}"
    if [ -z "$name" ]; then
      echo "Missing name for: $subcmd" >&2
      usage >&2
      exit 2
    fi
    ;;
  "")
    name="$(pick_name)"
    ;;
  *)
    name="$1"
    ;;
esac

codex_sess="codex-$name"
cmd_sess="cmd-$name"
log_sess="log-$name"

if [ "$subcmd" = "stop" ]; then
  if tmux has-session -t "$cmd_sess" 2>/dev/null; then
    tmux kill-session -t "$cmd_sess"
  fi
  if tmux has-session -t "$log_sess" 2>/dev/null; then
    tmux kill-session -t "$log_sess"
  fi
  if [ $stop_all -eq 1 ]; then
    if tmux has-session -t "$codex_sess" 2>/dev/null; then
      tmux kill-session -t "$codex_sess"
    fi
  fi
  exit 0
fi

workdir="$workspace/$name"
if [ ! -d "$workdir" ]; then
  echo "Workspace dir not found: $workdir" >&2
  exit 1
fi

# Ensure codex session exists (always)
if ! tmux has-session -t "$codex_sess" 2>/dev/null; then
  tmux new-session -d -s "$codex_sess" -c "$workdir" "codex sh"
fi

if [ $with_cmd -eq 1 ]; then
  if ! tmux has-session -t "$cmd_sess" 2>/dev/null; then
    tmux new-session -d -s "$cmd_sess" -c "$workdir" "bash -lc \"set -a; [ -f ~/Workspace/climax/clients/.env ] && . ~/Workspace/climax/clients/.env; set +a; exec bash\""
  fi
fi

if [ $with_log -eq 1 ]; then
  if ! tmux has-session -t "$log_sess" 2>/dev/null; then
    tmux new-session -d -s "$log_sess" -c "$workdir" "bash -lc \"set -a; [ -f ~/Workspace/climax/clients/.env ] && . ~/Workspace/climax/clients/.env; set +a; exec bash\""
    tmux send-keys -t "$log_sess" "echo 'log session: add tail/senders here'" Enter
  fi
fi


inject_clients_env() {
  local sess="$1"
  tmux send-keys -t "$sess" "set -a; [ -f ~/Workspace/climax/clients/.env ] && . ~/Workspace/climax/clients/.env; set +a" Enter
}

case "$subcmd" in
  cmd)
    inject_clients_env "$cmd_sess"
    exec tmux attach -t "$cmd_sess"
    ;;
  log)
    inject_clients_env "$log_sess"
    exec tmux attach -t "$log_sess"
    ;;
  *)
    tmux attach -t "$codex_sess"
    if [ $cleanup -eq 1 ]; then
      if tmux has-session -t "$cmd_sess" 2>/dev/null; then
        tmux kill-session -t "$cmd_sess"
      fi
      if tmux has-session -t "$log_sess" 2>/dev/null; then
        tmux kill-session -t "$log_sess"
      fi
    fi
    ;;
esac

