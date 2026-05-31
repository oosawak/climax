---
title: "Climax Chronicle: tmuxセッション/コマンドログをCosmosに貯めて見返す（運用メモ）"
emoji: "🗃️"
type: "tech"
topics: ["azure", "python", "tmux", "devops", "cli"]
published: false
---

Climax Chronicle の主目的は **セッション管理** と **ログ管理**。

- セッション: 「どの作業（プロジェクト）を、どのディレクトリでやっているか」を記録して一覧/復帰しやすくする
- ログ: 「何を実行したか」をコマンド単位で残して、あとから検索/要約/棚卸しできるようにする

このメモは、CLI 運用を “迷わない最小手順” に落とし込むためのもの。

## 全体像

```text
tmux（cmd/log/codex セッション）
  ↓ （コマンド実行単位ログ）
clients/ctmcmd.py
  ↓  POST /api/log/append
Azure Functions (Chronicle API)
  ↓
Cosmos DB（永続化）
  ↓  GET /api/logs など
clients/ctm（menu / logs / status）
```

ポイント:

- Azure Functions の `file` 保存は永続性が弱いので、**本番は Cosmos** を前提にする
- ログは “ターミナル全文” ではなく、まずは **コマンド実行単位**で十分（topicで分類）

## 日常運用（最小）

### 0) 初回セットアップ（チームでも個人でも同じ）

```bash
./clients/setup_clients_env.sh
```

これで `clients/.env` が作られ、以後 `clients/*` は基本的に自動で読み込む。

### 1) 作業開始（覚えない）

```bash
./clients/ctm
```

`ctm` はデフォルトで `menu` を開く。

### 2) コマンドログを残す（cmd セッション内）

```bash
./clients/ctmcmd.py -- <your command>
```

topic を固定したい場合は `clients/.env` に:

```bash
CLIMAX_TOPIC="build"
```

### 3) ログを見る（log セッション）

menu から:

- `log`（最新を1回表示）
- `follow`（自動更新で追う）

### 4) すぐ確認したい（API直叩き相当）

```bash
./clients/ctm status <name> --limit 5
./clients/ctm logs <name> --limit 20 --topic build
./clients/ctm sessions
```

### 5) こけた時

```bash
./clients/ctm doctor
```

## topic の運用（おすすめ）

迷わないために、まずは固定セットだけ使う。

- `build`
- `test`
- `deploy`
- `run`
- `default`

## どこまでを“セッション”として扱うか

現状は tmux の命名規約で揃えるだけで十分。

- `codex-<name>`
- `cmd-<name>`
- `log-<name>`

`<name>` は基本的に `~/Workspace/<name>` のディレクトリ名と一致させる。

## 次の段階（Web 管理画面）

最終的には Web で見たい。

最小 UI（最初に作るならこれ）:

- セッション一覧（server/session/directory/updated）
- セッション詳細（pane情報）
- ログ一覧（topic/limit/自動更新）

チーム利用する場合は、Function key をブラウザに出さない設計（認証）を後で入れる。

