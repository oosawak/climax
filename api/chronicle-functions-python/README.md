# Azure Functions（Python）: Chronicle API

## 目的

tmux/zellij から収集した以下を受け取り、Cosmos DB（または暫定のローカル永続）へ保存する。

- セッション構造（pane/tab）
- ログ（時系列 append）
- アーティファクト参照（GitHub の repo/path/commit）

## ローカル実行（参考）

Azure Functions Core Tools を利用する前提。

```bash
cd api/chronicle-functions-python
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



## エンドポイント（抜粋）

- `GET /api/health`
- `GET /api/sessions`
- `POST /api/session/update`
- `POST /api/log/append`
- `POST /api/nlp/analyze`（日本語命令の前処理: intent抽出→英語プロンプト→日本語応答指示プロンプト）


## 環境変数（追加: Azure AI Language）

`/api/nlp/analyze` で Azure AI Language（Conversation / CLU）を使う場合に設定する。
未設定の場合は、簡易ヒューリスティックにフォールバックする。

- `LANGUAGE_ENDPOINT`
- `LANGUAGE_KEY`
- `LANGUAGE_PROJECT`
- `LANGUAGE_DEPLOYMENT`


## クライアント（例）

Functions を起動した状態で、前処理（`/api/nlp/analyze`）だけ叩いて `final_prompt` を得る。

- `clients/climax_preprocess_client.py`

```bash
python clients/climax_preprocess_client.py --text "昨日の続きやって"
```

出力された `final_prompt` を、任意の LLM（ローカル/クラウド）に渡す。


## Notes (NLP module)

- `api/chronicle-functions-python/chronicle_nlp.py` is a thin wrapper that imports the canonical preprocessor at repo root: `intent_processor.py`.
