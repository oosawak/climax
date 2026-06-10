title: "Climax Chronicle: 実際に使う手順まとめ"
emoji: "🧭"
type: "tech"
topics: ["azure", "tmux", "cli", "devops", "github"]
published: true
---

Climax Chronicle を実運用で使うための手順を、初心者向けに1本へまとめる。

この記事の目的は、機能説明ではなく **実際にどう使うか** を迷わない形にすること。

## 何をする仕組みか

Climax Chronicle は次の2つを扱う。

- **セッション管理**: `tmux` の作業セッションを一覧化して復帰しやすくする
- **ログ管理**: コマンド実行単位のログを残して、あとから確認しやすくする

### 全体像

```text
┌──────────────────────┐
│  tmux / codex / cmd  │
│  log セッション       │
└──────────┬───────────┘
           │
           │  ctm / ctmcmd
           ▼
┌──────────────────────┐
│ Azure Functions       │
│ - /api/session/update │
│ - /api/log/append     │
│ - /api/session/get    │
│ - /api/sessions       │
│ - /api/nlp/analyze    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Cosmos DB             │
│ - session             │
│ - log                 │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 管理画面              │
│ GitHub Pages / docs   │
│ Azure Static Web Apps  │
└──────────────────────┘
```


## いま実装してあるもの

この章は「最近がんばったこと」ではなく、**実際に動くように入れたもの**をまとめる。
利用者が Cosmos や API の細部を意識しなくてよい状態へ寄せた。

### 1. Azure Functions の API を固めた

現状の Chronicle API は次のルートを使う。

- `GET /api/health`
- `GET /api/sessions`
- `GET /api/session/get`
- `POST /api/session/update`
- `GET /api/logs`
- `GET /api/logs/recent`
- `POST /api/log/append`
- `POST /api/logs/backfill_nlp`
- `POST /api/nlp/analyze`
- `GET /api/artifacts`

役割の分担はこうしている。

- `session/update` と `session/get` で tmux / codex / cmd / log の構造を保存する
- `logs` でコマンド単位の履歴を見る
- `logs/recent` で最近動いたセッション候補を取る
- `backfill_nlp` で過去ログに NLP の結果を後から付ける
- `nlp/analyze` で日本語入力を intent / entities / 英語プロンプトに変換する
- `artifacts` で関連ファイルや GitHub の成果物を一覧化する

これで、セッション一覧・詳細・ログ・NLP 前処理・成果物参照までをひと通り扱える。

### 2. `ctm` を “入口” にした

`ctm` は単なる tmux ラッパーではなく、Chronicle 操作の入口にした。

```bash
cd ~/Workspace/climax
./clients/setup_clients_env.sh
```

この1回で次が揃う。

- `clients/.env` を作る
- `CLIMAX_FUNCTIONS_URL` と `CLIMAX_FUNCTIONS_CODE` を入れる
- `ctm` / `ctmcmd` / `cj` / `climax-*` を PATH で使えるようにする

### 3. `ctm init <name>` で新規作成を1本化した

利用者が保存先や Cosmos を知らなくていいように、`ctm init` で次をまとめて実行する。

- `~/Workspace/<name>` を作る
- `codex-<name>` / `cmd-<name>` / `log-<name>` を作る
- 可能なら Chronicle に同期する
- `codex-<name>` に attach する

### 4. `ctm status` は session + logs を一緒に見せる

`status` は単に JSON を返すのではなく、次を同時に見せる。

- `session/get` の結果
- `logs` の直近結果
- `directory` と `panes` の意味

### 5. `ctmcmd` でコマンド単位ログを送る

`cmd-<name>` セッション内では `ctmcmd` を使う。

- `echo hello` のような単位で送る
- `topic` で `build` / `test` / `deploy` などに分類する
- 後で一覧や要約に使える

### 6. 管理画面は GitHub Pages 版と Azure Static Web Apps 版の2系統にした

管理画面は2つの入口を用意している。

- **GitHub Pages 版**: Function Key を知っている人がすぐ使える
- **Azure Static Web Apps 版**: 将来的な認証付き運用に寄せやすい
- どちらの UI も、裏では Azure Functions の HTTP API を呼ぶ

GitHub Pages の管理画面では、

- `API base`
- `Function code`
- `server_id`

だけを入れればよい。

管理画面は Cosmos DB を直接読まない。ブラウザは Azure Functions の HTTP API を叩くだけで、
実データの読み書きは Functions 側が Cosmos DB に対して行う。
Function code はブラウザの `localStorage` に保存し、サーバには残さない。

### 7. `Recent logs` はいったん無効化した

今の運用では `Load sessions` / `session/get` / `status` の方が分かりやすい。
中途半端に `Recent logs` を残すより、誤解しない状態に寄せた。

## プロンプトの工夫

Climax では、**日本語で命令して、AI 側で英語に整理し、返答は日本語に戻す** という流れを採っている。

```text
日本語の入力
  ↓
Azure AI Language で intent / entities を抽出
  ↓
英語の task prompt を生成
  ↓
LLM 用の final prompt にする
  ↓
「返答は必ず日本語」を強制
```

### 具体的な狙い

- 音声入力や自然な日本語のまま命令できる
- AI の内部処理は英語の方が安定しやすい
- 返答は日本語のままにして、利用者の体験を崩さない

### 例

```text
日本語: 昨日の続きやって
↓
intent: continue_previous_task
↓
English prompt: Continue the previous development work from the latest context.
↓
final prompt: You must understand the task in English, but your final answer MUST be in Japanese.
```

この層分けがあると、

- 前処理の変更
- LLM の差し替え
- セッション管理ロジックの拡張

を独立して進めやすい。

## NLP を見せる

NLP は「前処理として本当に使っている」ことが見えた方が伝わる。
そのため、動画や記事では 1 回だけではなく複数の日本語入力を流して、意図の分岐が見えるようにする。

### 例

```text
昨日の続きやって
→ continue_previous_task
→ Continue the previous development work from the latest context.

ログまとめて
→ summarize_logs
→ Summarize the following logs in a concise way.

unity-devを開いて
→ open_unity_session
→ Open the Unity development session named 'unity-dev'.

こんにちは
→ unknown
→ 意図が曖昧なので確認質問を返す
```

### 何が伝わるか

- 日本語で入れているのに、内部で intent / entities を抽出している
- その結果が英語のタスクに変換される
- 最後に「必ず日本語で返答する」制約を付けている
- つまり、単なるログ管理ではなく、**前処理としての NLP が実際に動いている**ことが見える

### API 実験スクリプト

動画収録の前に、Azure Functions の API 一覧と NLP の複数例をまとめて確認するスクリプトも用意した。

```bash
scripts/test_chronicle_api_surface.sh
```

このスクリプトは次を順に試す。

- `/api/health`
- `/api/sessions`
- `/api/session/update`
- `/api/session/get`
- `/api/log/append`
- `/api/logs`
- `/api/logs/recent`
- `/api/logs/backfill_nlp`
- `/api/nlp/analyze`
- `/api/artifacts`

さらに NLP は複数の入力を流して、意図の分岐をその場で確認できる。

## 使い方の最小手順

### 1. 初回セットアップ

```bash
cd ~/Workspace/climax
./clients/setup_clients_env.sh
```

### 2. 新しい作業を始める

```bash
ctm init my-project
```

### 3. ログを残す

```bash
ctmcmd -- echo hello
```

### 4. 一覧を見る

```bash
ctm sessions
```

### 5. 詳細を見る

```bash
ctm session my-project
ctm status my-project --limit 5
```

## CORS 設定

GitHub Pages から Azure Functions を呼ぶので、Functions 側で CORS を許可する。

```bash
cd ~/Workspace/climax
AZ_RESOURCE_GROUP=rg-climax AZ_FUNCTION_APP=func-api-eedplxgcbbmra bash scripts/az_set_functions_cors.sh
```

## まとめ

この運用のポイントは、**ユーザーが Cosmos や API の実装細部を意識しなくてよいこと**。

- 入口は `ctm`
- ログは `ctmcmd`
- 確認は `ctm sessions` / `ctm session` / `ctm status`
- Web では GitHub Pages の管理画面で見る

この形に揃えておくと、Codex からも人間からも使いやすい。
