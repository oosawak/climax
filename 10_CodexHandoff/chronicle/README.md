# Chronicle（蒼穹の記憶庫）スキャフォールド

Climax の「セッション構造」「ログ」「アーティファクト参照」を蓄積・閲覧するための最小構成。

## 構成

- `functions-python/`: Azure Functions（HTTP API）スキャフォールド
- `sender/`: tmux/zellij 側から API に送るためのスクリプト（次ステップで追加）
- `pages/`: GitHub Pages 用の静的 UI 雛形（次ステップで追加）

## API（予定）

- `GET  /api/sessions`
- `POST /api/session/update`
- `POST /api/log/append`
- `GET  /api/artifacts`

