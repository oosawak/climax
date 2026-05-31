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

---

## 動作環境メモ（ビット幅 / バージョン）

「ローカルで動くか」の切り分けで迷いやすいので、検証時に見えていた前提をメモしておく。

- Azure Functions Core Tools: 4.x（64-bit）
- Python Worker: 3.12（Linux x64）
- Functions Runtime: 4.x

この前提が崩れている場合（例: Python 3.11、Core Tools が古い、ARM 環境など）は、同じ手順でも挙動が変わる可能性がある。


## なぜ CLU の学習データ（utterances）が必要なのか

Climax Chronicle の前処理は、ユーザーの日本語コマンドをそのまま LLM に投げず、
Azure AI Language（Conversation / CLU）で

- intent（何をしたいか）
- entities（対象やパラメータ：セッション名、検索語、ファイルパスなど）

を抽出してから、英語プロンプト（`english_prompt`）→最終プロンプト（`final_prompt`）を作る。

ここで重要なのは、CLU は「辞書」ではなく **プロジェクトに定義した intent/entity を学習して推定する**仕組みだという点。
つまり intent を増やしたい場合は、その intent に対応する「例文（utterances）」が必要になる。

学習データが少ない（または無い）と、運用上はだいたい次のどれかが起きる。

- intent が `unknown` に寄りやすい（分類できない）
- entity が抽出できない（`session` が空になる等）
- entity が「文末語込み」で抽出される（例: `unity-devを開いて` が丸ごと `session` になる）
- 表現ゆれ（「探して」「検索して」「見つけて」など）に弱い

だからこそ、最初に「最小の学習データ」を用意し、使いながら増やしていく運用が現実的。

## 何を学習させるべきか（最小セット）

開発で効く順に、まずは intent を少数に絞るのがおすすめ。

例:

- `continue_previous_task`
- `summarize_logs`
- `open_unity_session`
- `search_in_repo`
- `open_file`
- `run_checks`
- `summarize_diff`
- `unknown`

entity はまずこれだけで十分。

- `session`（例: `unity-dev`）
- `query`（例: `intent_processor.py`）
- `path`（例: `api/chronicle-functions-python/function_app.py`）

## Language Studio が使えない環境での運用

Language Studio（Web UI）が使えなくても、Authoring API で

- import（プロジェクト作成/更新）
- train（学習）
- deploy（デプロイ）

を自動化できる。

このリポジトリでは、Authoring API の呼び出しを `provision_clu_and_configure_functions.sh` にまとめている。

- intent/entity 定義
- utterances（例文）
- train / deploy

までを一括で実行する。

## 注意: entity の offset/length について

Conversation/CLU の学習データでは、entity を「どの部分か」指定するために `offset` / `length` を使う。

このリポジトリのスクリプトは `Utf16CodeUnit` 前提なので、日本語が混ざると数え方がズレやすい。
そのため、まずは `unity-dev` のような ASCII 文字列を entity 例にして、ラベル付けが壊れにくい形から始めるのがおすすめ。

それでも抽出結果が「文末語込み」になる場合があるため、サーバー側で `entities.session` などを正規化して実用性を担保している。

## 学習データは「固定」ではなく「運用で増やす」

学習データは一度作って終わりではなく、実際に使ってみて

- `unknown` が多い
- entity が抜ける
- 表現ゆれに弱い

が見えてきた時に utterance を少しずつ足して再 train/deploy するのが一番コスパが良い。

## Zenn 向け：学習データ（utterances）が必要な理由の書き方（テンプレ）

文章にするときは、次の順で説明すると伝わりやすい。

1. **やりたいこと**: 日本語の雑な指示（例: 「unity-devの続きやって」）を、開発ツールが扱える「構造化された命令」に変換したい。
2. **なぜ LLM 直投げじゃないか**: 
   - 毎回プロンプトを工夫しないと安定しない
   - ちょっとした表現ゆれで意図がブレる
   - セッション名/ファイルパスなどの「パラメータ」を確実に抜き出しにくい
3. **CLU を挟む理由**: intent/entities を先に確定させ、英語タスク（`english_prompt`）の生成を安定させる。
4. **そのために学習データが必要**: CLU は「こちらが定義した intent/entity の分類器」なので、
   - intent ごとの代表的な言い回し（utterances）
   - entity を含む例（どこが `session` / `path` / `query` か）

   が無いと、分類・抽出の根拠が作れない。
5. **運用上のメリット**: 
   - intent が増えても「追加するのは例文」なので、仕様変更が追いやすい（= インターフェースとして管理できる）
   - unknown が増えたら utterance を足して改善できる（プロンプト調整より再現性が高い）
   - entity を正規化して後段処理（ログ保存/セッション操作/コマンド実行）に渡しやすい

最後に「Language Studio が使えなくても Authoring API で import/train/deploy できる」ことを添えると、個人環境でも再現できる記事になる。
