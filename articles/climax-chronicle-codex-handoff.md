---
title: "Climax詠唱環境: Codexに渡す引き継ぎ書（世界観×技術仕様×実装タスク）"
emoji: "📜"
type: "tech"
topics: ["codex", "azure", "zellij", "cosmosdb", "zenn"]
published: false
---

Climax 詠唱環境を AI（Codex）に継続開発させるときに、**毎回の説明コストをゼロに近づける**ための「正式な引き継ぎ書」を用意した。

このドキュメントは **世界観（用語）× 技術仕様（構成/データ/API）× 実装タスク（優先順位）** を一枚にまとめ、Codex に貼るだけで作業を再開できる状態を目指す。

## 1) 置き場所（リポジトリ内の正式版）

引き継ぎ書の本体はこのファイル：

- `10_CodexHandoff/Climax_Codex_Handoff.md`

Zenn 記事本文では全量を貼らず、使い方と要点をまとめる（＝更新は Markdown 側を正とする）。

## 2) Codex に渡すときの使い方

### 最小手順

1. `10_CodexHandoff/Climax_Codex_Handoff.md` を開く
2. 内容を Codex に貼る
3. その直後に「今回やりたいタスク」を 1〜3 個だけ書く

### 依頼テンプレ

```text
このリポジトリの `10_CodexHandoff/Climax_Codex_Handoff.md` が仕様です。
まず内容を前提として理解してから、次を進めてください：

- タスク1:
- タスク2:
- タスク3:

制約:
- 変更は最小限
- 既存の世界観用語は維持
- 作業はZenn記事も更新対象（必要なら）
```

## 3) 引き継ぎ書の中身（何が“一目で”わかるか）

- 世界観（Climax Lore）: 用語と対応する技術要素
- 全体アーキテクチャ: Ubuntu → Functions → Cosmos → Pages/Repos
- 必要機能: セッション/ログ/Functions API/UI/Android
- JSON 仕様: `session/update` と `log/append` の形
- Cosmos DB のドキュメント例: session/log/server/artifact
- 実装タスク: まず何から作るべきか

## 4) 次の一手（おすすめ）

引き継ぎ書が揃ったので、次は “動く最小ループ” を作る。

- `zellij action dump-session --json` を叩いて JSON を取得
- `curl` で `/api/session/update` に投げる（Functions 側は仮でもOK）
- Cosmos DB へ保存して、`GET /api/sessions` で一覧が返る

この最小ループが通ると、以降の拡張（ログ、UI、Android）が迷わない。
