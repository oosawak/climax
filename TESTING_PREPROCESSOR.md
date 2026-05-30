# Preprocessor / NLP Testing (Climax)

This document shows how to verify the **Codex preprocessor layer** locally.

## 0) Prerequisites

- Python is available (`python` command works)
- (Optional) Azure Functions Core Tools (`func`) for HTTP testing

## 1) Quick syntax check (repo root)

```bash
python -m py_compile intent_processor.py
```

## 2) Direct call test (repo root)

Generate the LLM prompt from Japanese input.

```bash
python -c "import intent_processor as p; print(p.preprocess_for_llm('昨日の続きやって'))"
```

## 3) Wrapper test (Functions project, no HTTP)

`api/chronicle-functions-python/chronicle_nlp.py` is a thin wrapper around `intent_processor.py`.

```bash
cd api/chronicle-functions-python
python -c "import chronicle_nlp as n; print(n.analyze_command('昨日の続きやって').to_payload())"
```

## 4) HTTP test (client -> Azure Functions)

### 4.1 Start Functions

```bash
cd api/chronicle-functions-python
cp local.settings.json.example local.settings.json
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
func start
```

### 4.2 Call `/api/nlp/analyze`

In another terminal (repo root):

```bash
python clients/climax_preprocess_client.py --text "昨日の続きやって" --format json
```

You should see keys like:

- `nlp.intent`
- `english_prompt`
- `final_prompt`

## 5) Azure AI Language (optional)

To test the real Azure AI Language call, set these in `api/chronicle-functions-python/local.settings.json`:

- `LANGUAGE_ENDPOINT`
- `LANGUAGE_KEY`
- `LANGUAGE_PROJECT`
- `LANGUAGE_DEPLOYMENT`

Then repeat **4) HTTP test**.

If these are not set (or Azure call fails), the server falls back to heuristics.
