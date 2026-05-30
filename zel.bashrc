zel() {
  _zellij_enter() {
    local target="$1"
    if [ -n "$ZELLIJ" ]; then
      zellij action switch-session "$target"
    else
      zellij attach "$target"
    fi
  }

  if [ -z "$1" ]; then
    # 色コード除去 → 最初の単語だけ抽出（1行に綺麗に修正）
    local sessions
    sessions=$(zellij list-sessions \
      | sed -r 's/\x1B\[[0-9;]*m//g' \
      | sed 's/ .*//')

    local list="(new) Create new session"
    [ -n "$sessions" ] && list="$list"$'\n'"$sessions"

    local choice
    choice=$(echo "$list" | fzf --prompt="zellij > " --height=40% --reverse)

    [ -z "$choice" ] && return

    if [[ "$choice" == "(new) Create new session" ]]; then
      read -r -p "Enter new session name: " newname
      [ -n "$newname" ] && zel "$newname"
      return
    fi

    _zellij_enter "$choice"
    return
  fi

  local arg="$1"
  local session_name="$arg"

  local target_dir="$HOME/Workspace/$arg"
  [ ! -d "$target_dir" ] && mkdir -p "$target_dir"
  cd "$target_dir" || return 1

  # こちらの条件分岐内の sed も1行に修正
  if zellij list-sessions \
      | sed -r 's/\x1B\[[0-9;]*m//g' \
      | sed 's/ .*//' \
      | grep -q "^$session_name$"; then
    _zellij_enter "$session_name"
  else
    zellij --session "$session_name"
  fi
}