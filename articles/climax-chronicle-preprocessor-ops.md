---
title: "Climax Chronicle: 日本語コマンド→Azure AI Language(CLU)→Codex用プロンプト（運用メモ）"
emoji: "🧩"
type: "tech"
topics: ["azure", "codex", "nlp", "python", "devops"]
published: false
---

Climax Chronicle の「前処理レイヤー（日本語コマンド→意図/エンティティ→英語プロンプト→最終プロンプト）」を、**ローカル/Azure の両方で動かす**ための整理メモ。

- 入力: 日本語（例: `unity-devの続きやって`）
- 前処理: Azure AI Language (Conversation / CLU)
- 出力: `final_prompt`（LLM に「日本語で回答せよ」を強制した英語タスク）

## 全体像

```text
日本語コマンド
  ↓
Azure Functions (Python): /api/nlp/analyze
  ↓
Azure AI Language (CLU) で intent/entities 抽出（失敗時は heuristic fallback）
  ↓
intent/entities → english_prompt
  ↓
english_prompt → final_prompt（日本語回答を強制する指示込み）
```

ポイント:

- **推論は英語**（安定しやすい）
- **返答は日本語**（プロンプトで強制）
- Azure は「生成」ではなく **意図抽出（NLP）**として使う

## 実装コンポーネント

- Azure Functions (Python)
  - `POST /api/nlp/analyze`
  - `POST /api/log/append`（ログ保存）
  - `POST /api/session/update`（セッション保存）
- NLP コア（前処理の本体）
  - `intent_processor.py`
- 端末側ツール
  - `clients/climax_preprocess_client.py`（`final_prompt` を取得）
  - `clients/climax-nlp`（`final_prompt` を `~/.climax/latest_final_prompt.txt` に保存。Codex 側で `cat` して読む）

## エンドポイント（Functions）

入力:

```json
{ "text": "昨日の続きやって" }
```

出力（例）:

- `nlp.intent` / `nlp.entities` / `nlp.provider`
- `english_prompt`
- `final_prompt`

## 必要な環境変数

### Azure AI Language（CLU）

Functions 側（Application settings）に設定:

- `LANGUAGE_ENDPOINT`
- `LANGUAGE_KEY`
- `LANGUAGE_PROJECT`
- `LANGUAGE_DEPLOYMENT`

補足:

- `LANGUAGE_PROJECT` / `LANGUAGE_DEPLOYMENT` は **CLUのプロジェクト名/デプロイ名**。
- ここが揃わない場合、サーバーは `heuristic` にフォールバックする。

### Chronicle の保存（暫定）

- `CHRONICLE_STORAGE=file`
- `CHRONICLE_FILE_PATH=./.data/chronicle.jsonl`

注意:

- Azure Functions 上の `file` 保存は **永続保証が弱い**（再起動/スケールで消える前提）。
- 本番で保持したいなら Cosmos などに寄せる。

## Language Studio が使えない環境で CLU を作る

Language Studio（Web UI）が使えなくても、**Authoring API** で以下を自動化できる:

- プロジェクト import
- train
- deploy

このリポジトリでは `codex_preprocessor_workspace/provision_clu_and_configure_functions.sh` で一括実行する。

```bash
cd codex_preprocessor_workspace
bash provision_clu_and_configure_functions.sh
```

このスクリプトは:

- `continue_previous_task`
- `summarize_logs`
- `open_unity_session`

などの intent と、`session` entity の最低限の学習データを含むプロジェクトを作成する。

## Azure 上の動作確認（ワンコマンド）

`codex_preprocessor_workspace/check_azure_nlp.sh` を使うと、代表ケースをまとめて叩ける。

```bash
cd codex_preprocessor_workspace
bash check_azure_nlp.sh
```

期待:

- `ログまとめて` → `summarize_logs`
- `unity-devを開いて` → `open_unity_session` + `entities.session=unity-dev`
- `こんにちは` → `unknown`

## Codex で使う（コピペ無し運用）

Codex TUI は「入力フックで自動変換」みたいな形がやりづらいので、
**変換結果を固定ファイルに保存して読ませる**方式にする。

### 1) 端末側で `climax-nlp` を使う

（初回だけ）Functions の URL/キーを環境変数に入れる:

```bash
export CLIMAX_FUNCTIONS_URL="https://func-api-eedplxgcbbmra.azurewebsites.net"
export CLIMAX_FUNCTIONS_CODE="$(az functionapp keys list -g rg-climax -n func-api-eedplxgcbbmra --query functionKeys.default -o tsv)"
```

変換して保存:

```bash
./clients/climax-nlp "unity-devの続きやって"
```

### 2) Codex 側で読む

Codex TUI 内で:

```bash
cat ~/.climax/latest_final_prompt.txt
```

この内容（= `final_prompt`）をそのまま Codex に渡して作業を進める。

## unknown の扱い

unknown intent のときは、いきなり作業を進めず:

- 「次に何をしたいか」日本語で確認質問を1つ返す

…という英語プロンプト（`final_prompt`）を返すようにしている。

## まとめ

- 日本語入力を Azure Functions に投げて `final_prompt` を得る
- Azure AI Language（CLU）で intent/entities を抽出
- UIなしでも Authoring API でプロジェクト作成→train→deploy できる
- Codex には `final_prompt` を渡す（固定ファイル保存でコピペ無し運用も可能）
