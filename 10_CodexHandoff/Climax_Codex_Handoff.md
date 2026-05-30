# Climax 詠唱環境：Codex 引き継ぎ書（完全版）
蒼穹の記憶庫（Azure） × Chrono Chamber（tmux/zellij） × GitHub

この文書は、Climax 詠唱環境の構築を Codex に引き継ぐための仕様書である。  
Azure・tmux/zellij・GitHub・Android 司令塔を統合し、  
**「儀式（セッション）を蒼穹に記録し続ける環境」** を構築する。

---

# 1. 世界観（Climax Lore）

- **現世の神殿**：Ubuntu / Linux
- **Chrono Chamber**：tmux または zellij
- **記録の使い魔**：Azure Functions
- **蒼穹の記憶庫**：Cosmos DB
- **蒼穹の写本庫**：GitHub Repos
- **記憶閲覧の祭壇**：GitHub Pages
- **詠唱器**：Android（音声操作）

目的：  
**儀式（セッション）・精霊の言葉（ログ）・成果物（ファイル）を蒼穹（Azure/GitHub）に永続化し、後から参照できる体系を作る。**

---

# 2. 全体アーキテクチャ

```text
Ubuntu（tmux/zellij）
   ↓ JSON 送信
Azure Functions（記録の使い魔）
   ↓
Cosmos DB（蒼穹の記憶庫）
   ↓
GitHub Pages（記憶閲覧の祭壇）
   ↓
GitHub Repos（蒼穹の写本庫）
```

---

# 3. 必要な機能一覧（Codex が実装すべき項目）

## 3-1. セッション管理（tmux または zellij）
- セッション一覧取得
- セッション構造（pane/tab）の取得
- 作業ディレクトリの取得
- セッション開始/終了時のフック
- Azure Functions へ JSON 送信

### zellij を使う場合の利点
- `zellij action dump-session --json` で構造が丸ごと取れる
- ネスト問題が少ない

---

## 3-2. ログ管理
- pane のログ取得
- AI CLI のログ取得
- 時系列ログの送信
- Azure Functions の `/api/log/append` に POST
- Cosmos DB に保存
- 後で AI 要約可能な形式にする

---

## 3-3. Azure Functions（API）
必要なエンドポイント：

```text
GET  /api/sessions        # セッション一覧取得
POST /api/session/update  # セッション構造更新
POST /api/log/append      # ログ追加
GET  /api/artifacts       # GitHub アーティファクト情報
```

---

## 3-4. Cosmos DB（データ構造）

### セッション情報
```json
{
  "id": "session-unity-dev",
  "type": "session",
  "server_id": "ubuntu-01",
  "session_id": "unity-dev",
  "directory": "/home/user/unity",
  "panes": [
    { "pane_id": 0, "command": "nvim" },
    { "pane_id": 1, "command": "ai-cli" }
  ],
  "updated_at": "2026-05-27T22:00:00Z"
}
```

### ログ情報
```json
{
  "id": "log-unity-dev-20260527-220100",
  "type": "log",
  "server_id": "ubuntu-01",
  "session_id": "unity-dev",
  "timestamp": "2026-05-27T22:01:00Z",
  "log": "Build completed successfully"
}
```

### サーバー情報
```json
{
  "id": "server-ubuntu-01",
  "type": "server",
  "server_id": "ubuntu-01",
  "hostname": "dev-machine-01",
  "last_seen": "2026-05-27T22:05:00Z"
}
```

### GitHub アーティファクト情報
```json
{
  "id": "artifact-unity-dev",
  "type": "artifact",
  "session_id": "unity-dev",
  "repo": "github.com/koushirou/unity-dev",
  "path": "Assets/Scripts/Player.cs",
  "commit": "a1b2c3d4"
}
```

---

# 4. JSON 仕様（Azure Functions に送る形式）

## セッション更新
```json
{
  "server_id": "ubuntu-01",
  "session_id": "unity-dev",
  "directory": "/home/user/unity",
  "panes": [
    { "id": 1, "command": "nvim" },
    { "id": 2, "command": "ai-cli" }
  ],
  "updated_at": "2026-05-27T22:00:00Z"
}
```

## ログ送信
```json
{
  "server_id": "ubuntu-01",
  "session_id": "unity-dev",
  "timestamp": "2026-05-27T22:01:00Z",
  "log": "User executed: cargo build"
}
```

---

# 5. tmux/zellij 側で必要な実装

## 5-1. セッション情報取得
- tmux: `tmux list-panes -F ...`
- zellij: `zellij action dump-session --json`（推奨）

## 5-2. ログ取得
- pane の出力をファイルに保存
- `tail -f` で Azure にストリーミング
- または zellij プラグインで直接送信

## 5-3. Azure Functions への送信
- `curl -X POST -H "Content-Type: application/json"`
- JSON を送る関数を作る

---

# 6. GitHub Pages（UI）
- セッション一覧
- セッション詳細
- ログビューア
- GitHub ファイル参照
- タイムライン
- AI 要約（後で追加）

---

# 7. Android 司令塔（音声操作）
- 音声 → tmux/zellij 起動
- 音声 → Azure Functions 呼び出し
- 音声 → GitHub push

---

# 8. Codex に求めること（実装タスク）

1. **Azure Functions に送る JSON 仕様の確定**
2. **zellij（または tmux）からセッション情報を JSON で取得する関数の作成**
3. **ログ送信の仕組みの実装**
4. **Azure Functions の API 実装**
5. **Cosmos DB の保存処理**
6. **GitHub Pages の UI の基盤作成**

---

# 9. 最終目的

**Climax 詠唱環境を完成させる。  
儀式（セッション）・精霊の言葉（ログ）・写本（ファイル）を蒼穹（Azure/GitHub）に永続化し、  
いつでも参照できる世界を作る。**
