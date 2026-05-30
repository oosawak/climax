---
title: "Climax: Azure AI Languageを前処理（意図抽出）に使う詠唱フロー（日本語→英語推論→日本語返答）"
emoji: "📱"
type: "tech"
topics: ["azure", "ai", "nlp", "python", "codex"]
published: false
---

スマホ（Android）から AI に命令すると、自然に日本語になる。

一方で、推論は英語の方が安定する場面がある。

そこで Climax では、Azure を「生成AI」ではなく **前処理（意図抽出）だけ**に使う。

- 命令: 日本語
- 前処理: Azure AI Language（intent / entities）
- 推論: Codex等/LLM/ConfiUI（英語プロンプト）
- 返答: 日本語（翻訳サービスは使わない）

## アーキテクチャ

```text
日本語の命令
  ↓
Azure AI Language（意図抽出）
  ↓
英語プロンプト生成
  ↓
LLM（英語で推論）
  ↓
LLMが日本語で返答（プロンプトで指定）
```

ポイントは2つ。

- Azure は軽量な前処理だけ
- 返答は「日本語で返せ」と LLM に命令するだけ

## Climax の実装（最小）

このリポジトリでは Azure Functions（Python）に前処理エンドポイントを用意した。

- `POST /api/nlp/analyze`

入力：

```json
{ "text": "昨日の続きやって" }
```

出力（例）：

- `nlp.intent` / `nlp.entities`
- `english_prompt`
- `final_prompt`（日本語返答指定込み）

実装: `api/chronicle-functions-python/function_app.py`

## ローカル実行（Functions）

```bash
cd api/chronicle-functions-python
cp local.settings.json.example local.settings.json
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
func start
```

## Azure AI Language の設定（任意）

`local.settings.json` に以下を入れる（未設定ならヒューリスティックにフォールバックする）。

- `LANGUAGE_ENDPOINT`
- `LANGUAGE_KEY`
- `LANGUAGE_PROJECT`
- `LANGUAGE_DEPLOYMENT`

## 呼び出し例（クライアント側）

```python
import requests

r = requests.post(
    "http://localhost:7071/api/nlp/analyze",
    json={"text": "昨日の続きやって"},
)
r.raise_for_status()
body = r.json()

final_prompt = body["final_prompt"]
# ここから先は、AzureではなくLLMに投げる（ローカル/任意の実行環境）
```

## まとめ

- 日本語で命令できる
- 前処理で intent / entities を取り、英語プロンプトに組み立てる
- Codex等/LLM/ComfyUI には英語で考えさせつつ、日本語で返させる
- Azure は「前処理だけ」にすると軽い
