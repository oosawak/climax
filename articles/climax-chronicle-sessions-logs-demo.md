---
title: "Climax Chronicle: demo - ローカルでコマンド実行→Azure Functions 風エンドポイントへ送るデモ"
emoji: "🎞️"
type: "tech"
topics: ["chronicle","tmux","ctm","demo"]
published: false
---

目的: ctm/ctmcmd クライアントが Chronicle API にログを送る動作をローカルでデモし、動画収録できるようにする。

準備

- このリポジトリをクローンしておく
- Python3 が必要
- 録画する場合は asciinema を推奨（インストール方法は環境依存）

スクリプト

- scripts/ctm_local_server.py
  - Chronicle の最小エミュレータ（/api/log/append, /api/logs, /api/nlp/analyze, /api/health）
  - 受信データは JSONL で /tmp/ctm_test_db.jsonl に保存される

- scripts/test_ctmcmd.sh
  - 上のサーバを起動
  - clients/ctmcmd.py を使って "echo hello-world" を実行し /api/log/append に送信
  - /api/logs を問い合わせて送信結果を表示
  - サーバを停止する

実行例

```
# 実行権限を付ける（必要なら）
chmod +x scripts/test_ctmcmd.sh
./scripts/test_ctmcmd.sh
```

動画収録例（asciinema を使う）

```
# 録画を開始し、スクリプトを実行して終了する
asciinema rec demo.cast -c "./scripts/test_ctmcmd.sh"
# demo.cast を再生
asciinema play demo.cast
```

拡張案

- 本番の Azure Functions と接続して実行するための .env サンプルを作成
- PROMPT_COMMAND ベースの自動ログフックを codex セッションに注入して、自動でコマンド実行ログを送る
- stdout/stderr を丸ごと収集するためのラッパー(shell DEBUG trap)を実装

問題があればこのデモスクリプトを実行して出力を貼ってください。