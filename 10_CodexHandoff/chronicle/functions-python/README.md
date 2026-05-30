# Azure Functions（Python）: Chronicle API

## 目的

tmux/zellij から収集した以下を受け取り、Cosmos DB（または暫定のローカル永続）へ保存する。

- セッション構造（pane/tab）
- ログ（時系列 append）
- アーティファクト参照（GitHub の repo/path/commit）

## ローカル実行（参考）

Azure Functions Core Tools を利用する前提。

```bash
cd 10_CodexHandoff/chronicle/functions-python
cp local.settings.json.example local.settings.json
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
func start
```

## 環境変数

- `CHRONICLE_STORAGE`:
  - `file`（デフォルト）: `./.data/chronicle.jsonl` に JSONL で追記
  - `cosmos`: Cosmos DB を使用
- `COSMOS_ENDPOINT`, `COSMOS_KEY`, `COSMOS_DATABASE`, `COSMOS_CONTAINER`

