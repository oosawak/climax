---
title: "Climax Chronicle: GitHub Pagesでセッション/ログ管理画面を動かす（Function Key運用）"
emoji: "🧭"
type: "tech"
topics: ["github", "azure", "functions", "tmux", "cli"]
published: false
---

Climax Chronicle の主目的は **セッション管理** と **ログ管理**。

この記事では、その閲覧・確認を “ブラウザから” できるようにするために、
**GitHub Pages** で管理画面を公開し、**Azure Functions の Function Key** で API を保護する運用をまとめます。

前提:

- 「ログイン不要で、鍵（Function Key）を知ってる人だけが使える」運用でOK
- Azure Static Web Apps（SWA）は将来使うかもしれないので、GitHub Pages 版は `docs/` に分離して置く

> 画面URLとスクリーンショットは、あとで差し替えできるようにプレースホルダにしています。

## 全体像

```text
tmux（cmd/log/codex セッション）
  ↓（コマンド実行単位ログ）
clients/ctmcmd.py
  ↓  POST https://<functionapp>.azurewebsites.net/api/log/append?code=...
Azure Functions (Chronicle API)
  ↓（永続化）
Cosmos DB
  ↑  GET /api/sessions, /api/logs, /api/logs/recent など
GitHub Pages（管理画面: docs/admin）
```

ポイント:

- **GitHub Pages は静的サイト**なので、ブラウザから Azure Functions を呼びます
- ブラウザ呼び出しには **CORS 設定**が必要です（後述）
- API は Function Key で保護します（`CLIMAX_FUNCTIONS_CODE`）

## 公開するファイル（GitHub Pages用）

このリポジトリでは GitHub Pages 用の管理画面を `docs/` に置きます。

- `docs/index.html`（`docs/admin/` へリダイレクト）
- `docs/admin/index.html`（UI）
- `docs/admin/main.js`（API呼び出し）
- `docs/admin/style.css`

## GitHub Pages の設定

GitHub のリポジトリ設定で Pages を有効にします。

1. Repo Settings → Pages
2. Source: “Deploy from a branch”
3. Branch: `main`
4. Folder: `/docs`

公開URL（例）:

- `https://<yourname>.github.io/<repo>/`
- 管理画面: `https://<yourname>.github.io/<repo>/admin/`

> TODO: 実際のURLをここに記入  
> TODO: 画面スクリーンショットをここに貼る

## 管理画面の入力（ここが重要）

管理画面（`/admin/`）を開いたら、まず Connection セクションを埋めます。

### API base

Azure Functions の URL を入れます。

- 推奨: `https://<functionapp>.azurewebsites.net`
  - GitHub Pages から使う場合は **絶対URL** を入れます（`/api` のような相対パスは不可）
  - 末尾の `/api` は **省略OK**（画面側で自動補完）
- 明示するなら: `https://<functionapp>.azurewebsites.net/api`

### Function code

Function Key を入れます（Function 側が `AuthLevel.FUNCTION` の場合）。

- `CLIMAX_FUNCTIONS_CODE` の値（`?code=` の中身）を入れる
- あるいは `?code=...` の形でもOK（画面側で処理します）

この値はブラウザの `localStorage` に保存されます（サーバには保存しません）。

### server_id

ログやセッションの “送信元識別子” です。

- 例: `i9`
- 迷ったらホスト名相当で固定（運用で一貫させるのがおすすめ）

## 画面でできること（セッション/ログ）

画面の主機能は、今のところこの2つです。

### セッション

- `Load sessions`: セッション一覧を取得
- `session/get`: セッション詳細を取得（必要なら `session_id (manual)` でもOK）

### ログ

- `Recent logs`: 最新ログから server/session の候補を作る（選ぶと入力が埋まる）
- `Load logs`: `server_id + session_id` でログ一覧取得
- `Follow`: 5秒ごとに再取得
- `Stop`: 停止

補助:

- `Copy: ctm <session>` / `ctm cmd` / `ctm log`: 端末で貼り付けて起動するためのコマンドをコピー

> “ブラウザから tmux を起動” はできないので、コピーしてターミナルに貼る運用にします。

## CORS 設定（ブラウザから Functions を叩くため）

GitHub Pages（`https://<yourname>.github.io`）から Azure Functions を呼ぶには、
Functions 側に CORS で “許可するオリジン” を登録する必要があります。

このリポジトリには設定用スクリプトを用意しています。

```bash
cd ~/Workspace/climax
AZ_RESOURCE_GROUP=rg-climax \
AZ_FUNCTION_APP=func-api-eedplxgcbbmra \
bash scripts/az_set_functions_cors.sh
```

環境に合わせて:

- `AZ_RESOURCE_GROUP`（例: `rg-climax`）
- `AZ_FUNCTION_APP`（例: `func-api-eedplxgcbbmra`）

を変更してください。

## Codex から実際に使う最小手順（初心者向け）

### 0) クライアント設定（初回）

```bash
./clients/setup_clients_env.sh
```

生成される `clients/.env` に、少なくとも以下を入れます（例）:

```bash
CLIMAX_FUNCTIONS_URL="https://func-api-eedplxgcbbmra.azurewebsites.net"
CLIMAX_FUNCTIONS_CODE="<配布された function key>"
```

### 1) セッション開始（覚えない）

```bash
./clients/ctm
```

メニューから `start` / `cmd` / `log` を選んで運用します。

### 2) ログを残す（コマンド実行単位）

```bash
./clients/ctmcmd.py -- <your command>
```

例:

```bash
./clients/ctmcmd.py -- echo hello
```

topic を固定したければ `clients/.env` に:

```bash
CLIMAX_TOPIC="build"
```

### 3) ブラウザで確認

GitHub Pages の管理画面を開いて:

- `API base`（Functions URL）
- `Function code`（Function Key）
- `server_id`

を入れてから、`Recent logs` → `Load logs` で確認します。

