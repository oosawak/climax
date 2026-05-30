---
title: "Climax Chronicle: Codexで日本語コマンドを使う（前処理→投入の運用パターン）"
emoji: "🧪"
type: "tech"
topics: ["codex", "azure", "nlp", "tmux", "workflow"]
published: false
---

Climax Chronicle では、日本語で打ったコマンドをそのまま LLM に渡すのではなく、
Azure Functions + Azure AI Language（CLU）で

- intent / entities を抽出し
- 英語の `english_prompt` を組み立て
- 日本語回答を強制した `final_prompt` にする

…という「前処理」を挟む。

この記事では、その `final_prompt` を **Codex（TUI）で実際に使う**ための運用パターンを整理する。

## 前提

- Azure Functions 側に `/api/nlp/analyze` がある
- 端末側に `clients/climax_preprocess_client.py` がある
- 共有運用の場合、Functions の `URL` と `function key` を配布する

## セットアップ（チーム共有）

### 1) `.env` を作る

```bash
cp clients/.env.example clients/.env
```

`clients/.env` の `CLIMAX_FUNCTIONS_CODE` を配布キーに置き換える。

### 2) 環境変数を読み込む

```bash
set -a
. clients/.env
set +a
```

## 運用パターン（おすすめ順）

### パターンA: ファイル保存して読む（堅い）

1) 日本語 → `final_prompt` を生成して保存

```bash
./clients/climax-nlp "unity-devの続きやって"
```

2) Codex 側で読む

```bash
cat ~/.climax/latest_final_prompt.txt
```

特徴:

- コピペ無し（固定ファイル）
- 失敗しにくい
- どのターミナル/ツールでも同じ運用ができる

### パターンB: tmux に自動投入（体験が良い）

tmux を使っている場合、`final_prompt` をアクティブペインへ自動投入できる。

1) tmux でペインを2つ用意

- ペインA: Codex TUI（投入先）
- ペインB: 送信コマンド実行用

2) Codex ペインをアクティブにしておく

3) 別ペインから送る

```bash
./clients/climax-send "ログまとめて"
```

特徴:

- 変換→投入→Enter まで一発
- 「入力フック」ではなく tmux の `send-keys` を使うため、構成依存が少ない

注意:

- `climax-send` は **tmux のアクティブペイン**に送る。
- 実行前に、投入先（Codexのペイン）を一度アクティブにしておく。

### パターンC: Codex を起動するときに渡す（開始の1発に便利）

`final_prompt` を作って `codex sh` に渡して起動する。

```bash
./clients/climax-codex "unity-devの続きやって"
```

特徴:

- 起動の1発目が楽
- 既に起動しているCodexに「差し込む」用途には向かない

## どれを使うべきか

- 安定性最優先: パターンA
- tmux で普段から開発している: パターンB
- 開始の一発目だけ楽にしたい: パターンC

## まとめ

- Codex TUI の「入力を送信前に自動変換」よりも、
  **変換結果を固定ファイルに保存/ tmux で投入**の方が運用しやすい
- `final_prompt` を介すことで「英語で推論・日本語で回答」を安定させられる
