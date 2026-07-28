---
title: "Climax Control Layer 技術仕様書 v1.0"
emoji: "⚙️"
type: "tech"
topics: ["codex", "nodejs", "mongodb", "zellij", "zenn"]
published: false
---

了解、Koushirou。  
では **Climax Control Layer（CCL）正式仕様書 v1.0** を、  
**技術者にそのまま渡して開発を開始できるレベル**でまとめる。

以下は **完全な技術仕様書**。  
Markdown 形式なので、そのまま GitHub の README や Notion に貼れる。

---

# 📘 **Climax Control Layer — 技術仕様書 v1.0（技術者向け）**

## 1. 概要

**Climax Control Layer（CCL）** は、  
複数ホストのセッション管理（tmux / Zellij）、  
AI 使用量管理（Claude / OpenAI / Copilot）、  
Topic DB（知識ベース）、  
リアルタイムログストリーム、  
Lo‑Fi UI（GUI / CLI）  
を統合する **常駐型オーケストレーションレイヤー**。

目的は：

- 分散したホスト・AI・セッションを **1つの統合レイヤーで制御**する  
- VS Code / Web / CLI / Android から **同じ情報にアクセス**できる  
- AI による **topic 自動生成・自動更新**  
- tmux / Zellij の **横断セッション管理**  
- AI 使用量の **統合ダッシュボード**  
- Lo‑Fi UI による **世界観の統一**

---

## 2. 全体アーキテクチャ

```
                   ┌──────────────────────────┐
                   │      VS Code (GUI)       │
                   │  - Lo-Fi Dashboard       │
                   │  - Topic Viewer          │
                   └──────────┬───────────────┘
                              │ WebSocket
                   ┌──────────┴───────────────┐
                   │   Climax Control Layer    │
                   │        (Node.js)          │
                   │                            │
                   │  ┌──────────────────────┐  │
                   │  │ SSH Manager          │  │
                   │  │ - 複数ホスト接続     │  │
                   │  │ - tmux/Zellij RPC    │  │
                   │  └──────────────────────┘  │
                   │  ┌──────────────────────┐  │
                   │  │ Session Manager      │  │
                   │  │ - セッション一覧     │  │
                   │  │ - attach/detach      │  │
                   │  └──────────────────────┘  │
                   │  ┌──────────────────────┐  │
                   │  │ Log Streamer         │  │
                   │  │ - リアルタイムログ   │  │
                   │  └──────────────────────┘  │
                   │  ┌──────────────────────┐  │
                   │  │ AI Usage Collector   │  │
                   │  │ - Claude/OpenAI/     │  │
                   │  │   Copilot 使用量     │  │
                   │  └──────────────────────┘  │
                   │  ┌──────────────────────┐  │
                   │  │ Topic DB Manager     │  │
                   │  │ - AI 自動生成/更新   │  │
                   │  └──────────────────────┘  │
                   └──────────┬───────────────┘
                              │ MongoDB
                   ┌──────────┴───────────────┐
                   │        MongoDB            │
                   │  - topics                 │
                   │  - sessions               │
                   │  - logs                   │
                   │  - ai_usage               │
                   └──────────────────────────┘
```

---

## 3. 技術スタック

| 機能 | 技術 |
|------|------|
| Core Server | Node.js（常駐） |
| DB | MongoDB |
| SSH | ssh2 / node-ssh |
| tmux | child_process 経由で RPC |
| Zellij | `zellij action` CLI |
| Web UI | WebSocket + HTML/Canvas |
| VS Code UI | WebView Extension |
| CLI UI | Zellij / ANSI Renderer |
| AI API | Claude / OpenAI / Copilot |

---

## 4. コンポーネント仕様

### 4.1 SSH Manager
- 複数ホストへ常時 SSH 接続  
- tmux / Zellij のセッション一覧取得  
- ログストリーム取得  
- コマンド実行  

**要件：**
- 接続維持（自動再接続）  
- ホストごとに設定ファイル（YAML/JSON）  
- タイムアウト・エラー処理  

---

### 4.2 Session Manager
- tmux / Zellij のセッション一覧を統合  
- attach/detach の実行  
- セッション状態を MongoDB に保存  
- セッションの “現在状態” を WebSocket で配信  

**要件：**
- tmux: `tmux ls`, `tmux attach -t <name>`  
- Zellij: `zellij list-sessions`, `zellij attach <name>`  
- セッション名の正規化  

---

### 4.3 Log Streamer
- tmux / Zellij のログをリアルタイム取得  
- WebSocket で UI に配信  
- MongoDB にバッチ保存（1秒〜5秒間隔）  

**要件：**
- ストリーム処理  
- バックプレッシャー対応  
- ログの圧縮・要約（AI 連携）  

---

### 4.4 AI Usage Collector
- Claude / OpenAI / Copilot の使用量 API を定期取得  
- 日次・月次集計  
- Topic DB と紐づけ  

**要件：**
- cron（5分〜15分間隔）  
- provider ごとに collector 実装  
- コスト計算ロジック  

---

### 4.5 Topic DB Manager
- AI による topic 自動生成  
- AI による topic 自動更新  
- embeddings の生成  
- プロジェクト横断検索  

**要件：**
- Claude / OpenAI の embeddings API  
- topic の差分更新  
- 関連ファイルの自動抽出  

---

## 5. MongoDB スキーマ

### 5.1 topics

```json
{
  "title": "ログ監視",
  "summary": "ログ監視の仕組みと改善点",
  "related_files": ["src/log/index.ts"],
  "embeddings": [...],
  "host": "server-a",
  "project": "pos-system",
  "ai_usage": {
    "claude": 1234,
    "openai": 5678,
    "copilot": 910
  },
  "updated_at": "2026-06-03T12:00:00Z"
}
```

---

### 5.2 sessions

```json
{
  "host": "server-a",
  "type": "zellij",
  "name": "dev",
  "status": "attached",
  "updated_at": "2026-06-03T12:00:00Z"
}
```

---

### 5.3 logs

```json
{
  "host": "server-a",
  "session": "dev",
  "timestamp": 1717392000,
  "line": "Server started on port 3000"
}
```

---

### 5.4 ai_usage

```json
{
  "provider": "claude",
  "tokens_in": 12345,
  "tokens_out": 67890,
  "cost": 0.12,
  "timestamp": 1717392000
}
```

---

## 6. API 設計（Node.js）

### GET /sessions  
複数ホストのセッション一覧。

### POST /sessions/attach  
tmux / Zellij に attach。

### GET /topics  
topic 一覧。

### POST /topics/generate  
AI による topic 自動生成。

### GET /logs/stream  
WebSocket によるログストリーム。

### GET /ai/usage  
AI 使用量の統合データ。

---

## 7. VS Code 拡張仕様

- WebView で Lo‑Fi ダッシュボード表示  
- WebSocket でリアルタイム更新  
- topic / session / usage を表示  
- コマンドパレットから操作可能  

---

## 8. CLI UI（Zellij）

- ASCII Lo‑Fi UI  
- セッション一覧  
- topic 一覧  
- AI 使用量  
- ログストリーム  

---

## 9. 実装方針

- Node.js サーバーは常駐（systemd）  
- SSH 接続は永続  
- ログはストリーム処理  
- AI 使用量は cron で定期取得  
- topic は AI による自動更新  
- UI は WebSocket でリアルタイム同期  

---

## 10. 運用方針

- MongoDB はローカル or Atlas  
- Node.js サーバーは systemd で常駐  
- ホスト情報は .env / config.json  
- AI API キーは Vault or .env  
- ログは 30 日でローテーション  

---
