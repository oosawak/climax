---
title: "Climax詠唱環境 構築ログ(1): zellijをビルド導入し、Azure CLIをpipxで入れてAzure準備を整える"
emoji: "🧙"
type: "tech"
topics: ["zellij", "azure", "pipx", "ubuntu", "zenn"]
published: false
---

Climax 詠唱環境（Chrono Chamber × Azure）を作っていくための、作業ログ 1 本目。

この回はまず「セッションを保持する器（zellij）」と「Azure を触る手（Azure CLI）」を揃えて、Azure 側の最小準備（Resource Group 作成）まで進める。

## 目的（ざっくり）

- tmux/zellij の「儀式（セッション）」を保持し、後で取り出せるようにする
- セッション情報・ログを Azure Functions へ送って Cosmos DB に蓄積する（次回以降）
- GitHub Pages で閲覧できるようにする（次回以降）

## 1) zellij のインストール（ソースビルド）

今回は fork を clone してビルドした。

```bash
git clone https://github.com/oosawak/zellij.git
cd zellij

rustup target add wasm32-wasip1
cargo build --release --target wasm32-wasip1 -p zellij-utils
cargo build --release

sudo cp target/release/zellij /usr/local/bin/
```

動作確認（任意）：

```bash
zellij --version
```

## 2) Azure CLI のインストール（pipx）

システム Python と分離して `az` を管理したいので `pipx` を使用。

```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
pipx install azure-cli
```

動作確認（任意）：

```bash
az --version
```

ログイン：

```bash
az login
az account show -o table
```

## 3) Zenn CLI のインストール（記事管理）

このリポジトリの `articles/` を Zenn 形式で管理・プレビューするために、Zenn CLI を入れる。

（Node.js が必要。`node -v` / `npm -v` が通る状態にしておく）

```bash
npm i -D zenn-cli
```

初回セットアップ（未初期化の場合のみ）：

```bash
npx zenn init
```

ローカルプレビュー（任意）：

```bash
npx zenn preview
```

## 4) Azure の最小準備（Resource Group 作成）

`Climax` という Resource Group を `japaneast` に作成。

```bash
az group create --name "Climax" --location "japaneast" -o table
az group list -o table
az group show -n Climax -o table
```

## 5) Codex 引き継ぎ書（世界観 × 技術仕様 × 実装タスク）

この段階では実装より先に、AI に渡す「引き継ぎ書」を整備して、以降の指示のブレを減らす。

リポジトリ内の例：

- `10_CodexHandoff/Climax_Codex_Handoff.md`

## 次にやること

- Azure Functions（HTTP API）をスキャフォールド化（`/api/session/update`, `/api/log/append` など）
- tmux/zellij からセッション構造・ログを送る最小スクリプト作成
- Cosmos DB 作成と保存処理の接続
- GitHub Pages 側の最小 UI（セッション一覧/ログビューア）
