# verify_preprocessor

Codex（このリポジトリの作業エージェント）から、前処理レイヤーの動作を**最短で確認**するためのフォルダー。

## 何を確認する？

- `intent_processor.py` が日本語入力から `final_prompt` を生成できる
- Functions 側ラッパー（`api/chronicle-functions-python/chronicle_nlp.py`）が `intent_processor.py` を参照して動く
- （任意）HTTP（`/api/nlp/analyze`）経由でも同じ情報が取れる

## 1) 直呼びチェック（最短）

```bash
python verify_preprocessor/check_direct.py --text "昨日の続きやって"
```

## 2) Functions ラッパーチェック（HTTPなし）

```bash
python verify_preprocessor/check_wrapper.py --text "昨日の続きやって"
```

## 3) HTTPチェック（Functions起動が必要）

### 3.1 Functions起動

```bash
cd api/chronicle-functions-python
cp local.settings.json.example local.settings.json
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
func start
```

### 3.2 別ターミナルで呼ぶ

```bash
python verify_preprocessor/check_http.py --text "昨日の続きやって" --format json
```

## Azure AI Language を実際に使う（任意）

`api/chronicle-functions-python/local.settings.json` に以下を設定してから 3) を実行。

- `LANGUAGE_ENDPOINT`
- `LANGUAGE_KEY`
- `LANGUAGE_PROJECT`
- `LANGUAGE_DEPLOYMENT`

未設定の場合はヒューリスティックにフォールバックする。
