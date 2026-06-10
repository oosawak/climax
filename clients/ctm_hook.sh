#!/usr/bin/env bash
# ctm_hook.sh
# Source this in interactive shells to enable PROMPT_COMMAND-based auto-logging.

CLIENTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "${CLIENTS_DIR}/ctm_autolog.sh" ]; then
  . "${CLIENTS_DIR}/ctm_autolog.sh"
fi

# Only enable for interactive bash shells
if [ -n "${BASH_VERSION:-}" ] && [ -n "${PS1:-}" ]; then
  export PROMPT_COMMAND='\
    ec=$?;\
    cmd=$(history 1 | sed "s/^[ ]*[0-9]\+[ ]*//");\
    cwd=$(pwd);\
    if [ -n """$cmd""" ]; then ctmlog_post "$cmd" "$ec" "$cwd" &; fi\
  '
fi
