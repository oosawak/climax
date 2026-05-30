---
title: "Climax詠唱環境 メモ: zellijの最低限の使い方（セッション運用編）"
emoji: "🧭"
type: "tech"
topics: ["zellij", "tmux", "terminal", "linux", "ubuntu"]
published: false
---

Climax の運用では「セッションを落とさず保持して、あとで戻る」が最重要。
ここでは zellij を“コマンドだけ”で回す最小セットをまとめる。

## よく使う流れ

### 1) セッションを作って入る

```bash
zellij attach -c Climax
```

- `-c` は、無ければ作って入る（create）
- 以後はこのセッションを「時間の間」として使い回す

### 2) いま動いているセッション一覧

```bash
zellij list-sessions
```

### 3) 既存セッションに戻る（アタッチ）

```bash
zellij attach Climax
```

### 4) いったん抜ける（デタッチ）

セッションを維持したまま抜けたいときは、zellij 内でデタッチする。
（キー操作は環境・設定で変わりやすいので、ここでは省略）

戻るときはまた：

```bash
zellij attach Climax
```

### 5) セッションを終了（要注意）

セッションごと消す（＝中のプロセスも止まる）ので注意。

```bash
zellij kill-session Climax
```

## 運用のコツ

- 名前を固定する: `Climax`, `ComfyUI`, `Unity`, `Rust` など用途別に
- 常駐系は zellij に入れる: `npm run dev`, `func start`, `cargo watch` など
- 迷ったら一覧: `zellij list-sessions`

## 次に書く予定

- レイアウト（起動時に分割状態を作る）
- セッションに“役割”を持たせる命名規則
