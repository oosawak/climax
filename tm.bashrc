tm() {
  # --- 1. 引数（セッション名/番号）がない場合の処理 ---
  if [ -z "$1" ]; then
    # 起動中の tmux セッションを配列に格納
    local IFS=$'\n'
    local sessions=($(tmux ls -F '#{session_name}' 2>/dev/null))

    # 【修正】セッションが0個でも、この後のメニュー処理へそのまま進むように変更
    echo "=== Current Tmux Sessions ==="
    
    # セッションがある場合のみ一覧を表示
    if [ ${#sessions[@]} -gt 0 ]; then
      local i
      for i in "${!sessions[@]}"; do
        echo "[ $((i + 1)) ] ${sessions[$i]}"
      done
    else
      echo "(No active sessions)"
    fi
    
    echo "[ c ] Create a new session"
    echo "[ q ] Quit"
    echo "----------------------------"

    echo -n "Enter number or choice: "
    read -r choice

    if [ "$choice" = "c" ]; then
      # 数字でも文字でも何でも受け付ける
      echo -n "Enter session name or number (e.g., 2 or 'test'): "
      read -r name
      if [ -n "$name" ]; then
        tm "$name" # 自分自身を引数付きで再帰呼び出し
      else
        echo "Canceled (Empty name)."
      fi
      return
    elif [ "$choice" = "q" ] || [ -z "$choice" ]; then
      echo "Canceled."
      return 0
    elif [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#sessions[@]}" ]; then
      local idx=$((choice - 1))
      tmux attach-session -t "${sessions[$idx]}"
      return 0
    else
      echo "Invalid choice."
      return 1
    fi
  fi

  # --- 2. 引数（セッション名/番号）がある場合の処理 ---
  local target_dir="$HOME/Workspace/$1"

  # 入力が純粋な数字なら「dev+数字」、文字なら「入力された文字」をセッション名にする
  local session_name
  if [[ "$1" =~ ^[0-9]+$ ]]; then
    session_name="dev$1"
  else
    session_name="$1"
  fi

  # 指定されたフォルダがなければ自動作成する
  if [ ! -d "$target_dir" ]; then
    echo "Directory '$target_dir' does not exist. Creating it..."
    mkdir -p "$target_dir"
  fi

  # フォルダへ移動
  cd "$target_dir"

  # セッションがあればアタッチ、なければ新規作成
  tmux a -t "$session_name" 2>/dev/null || tmux new -s "$session_name"
}
