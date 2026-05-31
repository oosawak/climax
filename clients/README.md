# Clients

## `climax_preprocess_client.py`

Japanese command -> `/api/nlp/analyze` -> print prompts.

### Usage

```bash
# final_prompt only (default)
python clients/climax_preprocess_client.py --text "昨日の続きやって"

# from stdin
echo "昨日の続きやって" | python clients/climax_preprocess_client.py

# print english prompt
python clients/climax_preprocess_client.py --text "昨日の続きやって" --format english_prompt

# print full JSON
python clients/climax_preprocess_client.py --text "昨日の続きやって" --format json

# if your Functions is not localhost
python clients/climax_preprocess_client.py --functions-url http://127.0.0.1:7071 --text "昨日の続きやって"

# deployed Azure Functions (requires function key)
KEYFUNC="$(az functionapp keys list -g rg-climax -n func-api-eedplxgcbbmra --query functionKeys.default -o tsv)"
python clients/climax_preprocess_client.py \
  --functions-url https://func-api-eedplxgcbbmra.azurewebsites.net \
  --functions-code "$KEYFUNC" \
  --text "unity-devの続きやって"

# or via env vars
export CLIMAX_FUNCTIONS_URL="https://func-api-eedplxgcbbmra.azurewebsites.net"
export CLIMAX_FUNCTIONS_CODE="$KEYFUNC"
python clients/climax_preprocess_client.py --text "ログまとめて"
```

### Notes

- Requires `/api/nlp/analyze` endpoint available (local or deployed).
- If Azure AI Language is not configured on the server, it falls back to heuristics.

## `climax-nlp`

Save the latest `final_prompt` (no copy/paste).

```bash
export CLIMAX_FUNCTIONS_URL="https://func-api-eedplxgcbbmra.azurewebsites.net"
export CLIMAX_FUNCTIONS_CODE="$(az functionapp keys list -g rg-climax -n func-api-eedplxgcbbmra --query functionKeys.default -o tsv)"

# writes ~/.climax/latest_final_prompt.txt
./clients/climax-nlp "unity-devの続きやって"

# in Codex TUI, paste nothing; just read it:
cat ~/.climax/latest_final_prompt.txt
```

### `climax-nlp` backends

- Local only (default):

```bash
export CLIMAX_FUNCTIONS_URL="https://func-api-eedplxgcbbmra.azurewebsites.net"
export CLIMAX_FUNCTIONS_CODE="$(az functionapp keys list -g rg-climax -n func-api-eedplxgcbbmra --query functionKeys.default -o tsv)"

./clients/climax-nlp "unity-devの続きやって"
cat ~/.climax/latest_final_prompt.txt
```

- Blob (optional):

```bash
export CLIMAX_BACKEND=blob
export CLIMAX_BLOB_ACCOUNT="<storageAccountName>"
export CLIMAX_BLOB_CONTAINER="<containerName>"
# export CLIMAX_BLOB_NAME="latest_final_prompt.txt"  # optional

# upload
./clients/climax-nlp "ログまとめて"

# download into ~/.climax/latest_final_prompt.txt
./clients/climax-nlp --pull --backend blob
```

## Team setup (1 page)

This assumes you will use the shared deployed Azure Functions.

### 1) Create your local env file

```bash
cp clients/.env.example clients/.env
```

Edit `clients/.env` and set:

- `CLIMAX_FUNCTIONS_CODE="<配布された function key>"`

### 2) Load env vars for your shell

```bash
set -a
. clients/.env
set +a
```

### 3) Generate the latest prompt (no copy/paste)

```bash
./clients/climax-nlp "unity-devの続きやって"
```

This writes the latest prompt to:

- `~/.climax/latest_final_prompt.txt`

### 4) Use it in Codex

In Codex TUI, read the file:

```bash
cat ~/.climax/latest_final_prompt.txt
```

## `climax-codex`

Launch Codex with a generated `final_prompt` (Japanese input -> Azure Functions -> Codex prompt).

```bash
set -a
. clients/.env
set +a

# starts: codex sh "<final_prompt>"
./clients/climax-codex "unity-devの続きやって"
```

If you prefer a different Codex subcommand:

```bash
CODEX_SUBCOMMAND=exec ./clients/climax-codex "ログまとめて"
```

## `climax-send` (tmux)

Inject the generated `final_prompt` into the currently active tmux pane (and press Enter).

```bash
set -a
. clients/.env
set +a

# In one pane: run Codex TUI
# In another pane: send an instruction into the active pane
./clients/climax-send "unity-devの続きやって"
```

Tip:
- Run `climax-send` from a different pane than the Codex pane.
- Make the Codex pane active (focus it), then run `climax-send` in the other pane.

### Working directory note

For ongoing development and deployment of the Azure Functions + infra template, keep the repo checked out under your workspace (example):

- `~/Workspace/climax/functions-climax`

Avoid working from `/tmp/...` because it may be wiped and is not meant for persistent checkouts.

## `ctm`

Start (or reuse) tmux sessions per workspace directory.

Tip:
- Newly created `cmd-<name>` / `log-<name>` sessions auto-source `~/Workspace/climax/clients/.env` (so `ctmcmd.py` can call Azure without manual `set -a`).

Sessions:

- `codex-<name>`: runs `codex sh`
- `cmd-<name>`: shell for commands
- `log-<name>`: shell reserved for log tail/senders

Usage:

```bash
# choose from ~/Workspace (number prompt)
./clients/ctm

# start/attach by name (開始/復帰)
./clients/ctm <name>

# attach to cmd or log sessions
./clients/ctm cmd <name>
./clients/ctm log <name>

# stop helper sessions (cleanup)
./clients/ctm stop <name>
./clients/ctm stop --all <name>

# auto-clean cmd/log after you exit Codex
./clients/ctm --cleanup <name>

# custom workspace root
./clients/ctm --workspace ~/Workspace <name>
```

This matches the workflow where you keep Codex, command execution, and log monitoring in separate tmux sessions.

## `climax-cmdlog`

Run a command and append its output to Chronicle via `POST /api/log/append`.

- Default `server_id` is your hostname (override with `CLIMAX_SERVER_ID`).
- Use `--topic` to group logs by purpose (build/test/deploy/etc.).

Examples:

```bash
set -a
. clients/.env
set +a

# run a command and store its stdout/stderr as one log item
./clients/climax-cmdlog --session-id unity-dev --topic build -- cargo build

# custom server id (optional)
CLIMAX_SERVER_ID=ubuntu-01 ./clients/climax-cmdlog --session-id unity-dev --topic test -- cargo test
```

## `ctmcmd.py`

Python implementation of command-unit logging (more reliable than editing bash scripts in some environments).

```bash
# recommended
./clients/ctmcmd.py --topic build -- echo hello
```

## `ctmcmd`

Convenience wrapper for command-unit logging from inside tmux.

- Infers `session_id` from the current tmux session name (`cmd-<name>` -> `<name>`).
- Sends stdout/stderr + metadata to `POST /api/log/append` via `climax-cmdlog`.

Example:

```bash
# inside: ./clients/ctm cmd unity-dev
./clients/ctmcmd build -- cargo build
./clients/ctmcmd test  -- cargo test
```

## Setup (no copy-paste)

Create/update `clients/.env` automatically (fetches the Function key via Azure CLI):

```bash
./clients/setup_clients_env.sh
set -a; . clients/.env; set +a
```
