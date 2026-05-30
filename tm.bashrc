tm() {
  # --- 0. Utility: attach or switch depending on environment ---
  _tmux_enter() {
    local target="$1"
    if [ -n "$TMUX" ]; then
      tmux switch-client -t "$target"
    else
      tmux attach-session -t "$target"
    fi
  }

  # --- 1. No argument: fzf launcher ---
  if [ -z "$1" ]; then
    local sessions
    sessions=$(tmux ls -F '#{session_name}' 2>/dev/null)

    # fzf input list
    local list="(new) Create new session"
    if [ -n "$sessions" ]; then
      list="$list"$'\n'"$sessions"
    fi

    local choice
    choice=$(echo "$list" | fzf --prompt="tmux > " --height=40% --reverse)

    # Cancel
    [ -z "$choice" ] && return

    # New session
    if [[ "$choice" == "(new) Create new session" ]]; then
      read -p "Enter new session name or number: " newname
      [ -n "$newname" ] && tm "$newname"
      return
    fi

    # Existing session
    _tmux_enter "$choice"
    return
  fi

  # --- 2. Argument given: create or attach ---
  local arg="$1"
  local session_name

  if [[ "$arg" =~ ^[0-9]+$ ]]; then
    session_name="dev$arg"
  else
    session_name="$arg"
  fi

  local target_dir="$HOME/Workspace/$arg"

  if [ ! -d "$target_dir" ]; then
    echo "Creating directory: $target_dir"
    mkdir -p "$target_dir"
  fi

  cd "$target_dir" || return 1

  if tmux has-session -t "$session_name" 2>/dev/null; then
    _tmux_enter "$session_name"
  else
    tmux new -s "$session_name"
  fi
}