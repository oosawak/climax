# AGENTS.md — Work Guide + Planned Agent Architecture (Climax)

This file is a **practical work guide for AI agents** editing this repository.
It also documents the **planned agent/module split** so future code can converge on stable names.

If there is a conflict between **Existing** and **Planned**, treat **Existing** as source of truth until the planned modules are created.

## Repository map (where to change things)

- Docs (Zenn)
  - `articles/`: Zenn articles (Markdown)
  - Rule: frontmatter `topics` must be **<= 5**
- Canonical spec
  - `10_CodexHandoff/Climax_Codex_Handoff.md`: canonical handoff/spec for ongoing work
- Azure Functions (Chronicle API)
  - `api/chronicle-functions-python/function_app.py`: HTTP routes
  - `api/chronicle-functions-python/chronicle_models.py`: request validation/models
  - `api/chronicle-functions-python/chronicle_storage.py`: storage backends (file/cosmos)
  - `api/chronicle-functions-python/chronicle_nlp.py`: NLP preprocessor (Azure AI Language optional)
- Client utilities
  - `clients/climax_preprocess_client.py`: calls `/api/nlp/analyze` and prints prompts
  - `clients/README.md`: usage

## Existing API surface (Chronicle)

Routes are defined in `api/chronicle-functions-python/function_app.py`.

- `GET /api/health`
- `GET /api/sessions`
- `POST /api/session/update`
- `POST /api/log/append`
- `POST /api/nlp/analyze` (Japanese command -> intent/entities -> English prompt -> final prompt)

## Local run (Functions)

```bash
cd api/chronicle-functions-python
cp local.settings.json.example local.settings.json
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
func start
```

## Local run (Zenn)

```bash
npx zenn preview
```

## Client usage (preprocess)

With Functions running:

```bash
python clients/climax_preprocess_client.py --text "昨日の続きやって"
```

## Environment variables

- Storage
  - `CHRONICLE_STORAGE` = `file` (default) or `cosmos`
  - `CHRONICLE_FILE_PATH`
  - `COSMOS_ENDPOINT`, `COSMOS_KEY`, `COSMOS_DATABASE`, `COSMOS_CONTAINER`
- Azure AI Language (optional; if unset, server falls back to heuristics)
  - `LANGUAGE_ENDPOINT`, `LANGUAGE_KEY`, `LANGUAGE_PROJECT`, `LANGUAGE_DEPLOYMENT`

## Planned agent/module split (names we want to converge on)

These names match the “Spirits” described in the lore. Some modules do **not** exist yet.

### 1) Interpretation Spirit (Intent/Entities extraction)

- Existing implementation
  - `api/chronicle-functions-python/chronicle_nlp.py`
    - `analyze_command(text)`
    - Azure AI Language call is optional; otherwise heuristic fallback
- Planned implementation (to be created)
  - `intent_processor.py`
    - `interpret_with_azure_language()`
    - `interpret_with_heuristics()`

### 2) Prompt Builder (Intent -> English task)

- Existing implementation
  - `api/chronicle-functions-python/chronicle_nlp.py`
    - `build_english_prompt(intent, entities)`
    - `build_final_prompt(english_prompt)`
- Planned implementation (to be created)
  - `intent_processor.py`
    - `build_english_prompt()`
    - `build_final_prompt_for_llm()`

### 3) LLM Spirit (English reasoning -> Japanese response)

- Existing implementation
  - Not implemented in this repo yet (only the `final_prompt` is produced)
- Planned implementation (to be created)
  - `llm_client.py`
    - adapters for at least one backend (e.g., Ollama / llama.cpp / OpenAI)
    - input: `final_prompt`
    - output: Japanese response text

### 4) Memory Spirit (Sessions/Logs persistence)

- Existing implementation
  - `api/chronicle-functions-python/chronicle_storage.py`
  - `api/chronicle-functions-python/chronicle_models.py`
- Planned implementation (to be created)
  - `memory_client.py` (higher-level read/write helpers + schema evolution)

### 5) Execution Spirit (tmux/zellij/SSH/shell execution)

- Existing implementation
  - Not implemented as a unified module yet
- Planned implementation (to be created)
  - `executor.py`
    - run commands safely
    - session selection and lifecycle

## Change policy (keep work safe)

- Make **minimal, scoped** changes.
- Do **not** commit secrets (keys, tokens).
- When behavior changes, update the canonical spec in `10_CodexHandoff/Climax_Codex_Handoff.md`.
- For docs, prefer adding a new file in `articles/` rather than rewriting unrelated content.
