# Sender（tmux/zellij → Chronicle API）

ここは「Chrono Chamber（tmux/zellij）」から Chronicle API に情報を送るための最小ツール置き場。

## 前提（環境変数）

- `CHRONICLE_BASE_URL` 例: `https://<func-app>.azurewebsites.net`
- `CHRONICLE_FUNCTION_KEY`（Functions の場合）例: `...?code=...` 用
- `CLIMAX_SERVER_ID` 例: `ubuntu-01`

## 使い方（例）

```bash
export CHRONICLE_BASE_URL="http://localhost:7071"
export CLIMAX_SERVER_ID="ubuntu-01"

./send_session_update.sh --session-id unity-dev
./tail_and_send_log.sh --session-id unity-dev --file /tmp/unity-dev.log
```

