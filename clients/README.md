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

## `cj`

Alias of `climax-nlp` (shorter command).

```bash
./clients/cj "unity-devの続きやって"
```

## `climax-nlp`

- Implementation: `clients/climax-nlp.py` (the `clients/climax-nlp` script is a shim).

Save the latest `final_prompt` (no copy/paste).

```bash
export CLIMAX_FUNCTIONS_URL="https://func-api-eedplxgcbbmra.azurewebsites.net"
export CLIMAX_FUNCTIONS_CODE="$(az functionapp keys list -g rg-climax -n func-api-eedplxgcbbmra --query functionKeys.default -o tsv)"

# writes ~/.climax/latest_final_prompt.txt
./clients/climax-nlp "unity-devの続きやって"

# in Codex TUI, paste nothing; just read it:
cat ~/.climax/latest_final_prompt.txt
```

## Team setup (1 page)

Note:
- Most `clients/*` commands auto-read `clients/.env` if present (no manual `set -a`).


This assumes you will use the shared deployed Azure Functions.

### 1) Create your local env file

```bash
cp clients/.env.example clients/.env
```

Edit `clients/.env` and set:

- `CLIMAX_FUNCTIONS_CODE="<配布された function key>"`
- (optional) `CLIMAX_TOPIC="build"`  # default topic for `ctmcmd.py`

### 2) Generate the latest prompt (no copy/paste)

```bash
./clients/cj "unity-devの続きやって"
```

This prints the path to the generated prompt file (default: `~/.climax/latest_final_prompt.txt`).

### 3) Use it

- In Codex TUI: `cat ~/.climax/latest_final_prompt.txt`
- Or launch Codex with the prompt: `./clients/climax-codex "unity-devの続きやって"`

Tip:
- If you use `./clients/ctm cmd <name>` / `./clients/ctm log <name>`, env vars from `clients/.env` are injected automatically on attach.


## Ops (daily workflow)

This is the minimal workflow for session + log management.

### 0) One-time setup

```bash
./clients/setup_clients_env.sh
```

### 1) Start working (no subcommand memorization)

```bash
./clients/ctm
```

In the menu:
- Choose a session
- Use `cmd` for running commands
- Use `log` / `follow` for log viewing

### 2) Log command outputs (command-unit)

Inside the `cmd-<name>` session:

```bash
./clients/ctmcmd.py -- <your command>
```

Tip:
- Set `CLIMAX_TOPIC` in `clients/.env` to avoid passing `--topic` every time.

### 3) Check status / logs quickly

```bash
./clients/ctm status <name> --limit 5
./clients/ctm logs <name> --limit 20
```

### 4) Troubleshoot

```bash
./clients/ctm doctor
```


## `climax-codex`

- Implementation: `clients/climax-codex.py` (the `clients/climax-codex` script is a shim).

Launch Codex with a generated `final_prompt` (Japanese input -> Azure Functions -> Codex prompt).

```bash

# starts: codex sh "<final_prompt>"
./clients/climax-codex "unity-devの続きやって"
```

If you prefer a different Codex subcommand:

```bash
CODEX_SUBCOMMAND=exec ./clients/climax-codex "ログまとめて"
```

## `climax-send` (tmux)

- Implementation: `clients/climax-send.py` (the `clients/climax-send` script is a shim).

Inject the generated `final_prompt` into the currently active tmux pane (and press Enter).

```bash

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

### Subcommands

- In `ctm menu`, you can set `topic` and `limit` interactively; values are remembered under `~/.climax/`.
- In `ctm menu`, choose "Change session" to switch sessions without restarting `ctm`.
- `ctm menu` remembers your last action in `~/.climax/last_action.txt` (press Enter to repeat it).
- `ctm` remembers your last selected session in `~/.climax/last_session.txt` (used as the default in the menu/selection).
- `ctm <name>`: attach to `codex-<name>` (best-effort autosync to Chronicle)
- `ctm cmd <name>`: attach to `cmd-<name>` (env injected)
- `ctm log <name>`: attach to `log-<name>` and show latest logs
- `ctm log <name> --follow --interval 5`: auto-refresh logs
- `ctm logs <name>`: fetch logs from Chronicle (supports `--topic/--limit/--format`)
- `ctm session <name>`: show saved session record (`/api/session/get`)
- `ctm sessions`: list sessions (`/api/sessions`)
- `ctm sync <name>`: push tmux structure to Chronicle (`/api/session/update`)
- `ctm status <name>`: show session + latest logs
- `ctm doctor`: check env + `/api/health`
- `ctm stop <name>`: kill helper sessions (use `--all` to include codex)

Tip:
- Newly created `cmd-<name>` / `log-<name>` sessions auto-source `~/Workspace/climax/clients/.env` (so `ctmcmd.py` can call Azure without manual `set -a`).
- `ctm cmd <name>` / `ctm log <name>` also injects env on attach (works for existing sessions).
- `ctm log <name>` auto-runs `ctm logs <name>` on attach (shows latest logs immediately).

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

# interactive (no need to remember subcommands)
./clients/ctm  # interactive menu (default)
./clients/ctm menu
./clients/ctm log <name> --topic build --limit 20
./clients/ctm log <name> --topic build --limit 50 --follow --interval 5

# fetch latest logs from Chronicle (Cosmos)
./clients/ctm logs <name>
./clients/ctm logs <name> --topic build --limit 5

# stop helper sessions (cleanup)
./clients/ctm stop <name>
./clients/ctm --all stop <name>
./clients/ctm stop --all <name>

# auto-clean cmd/log after you exit Codex
./clients/ctm --cleanup <name>

# custom workspace root
./clients/ctm --workspace ~/Workspace <name>
```

This matches the workflow where you keep Codex, command execution, and log monitoring in separate tmux sessions.

Note:
- `ctm logs` reads `clients/.env` automatically if present (no manual `set -a`).

## `climax-cmdlog`

Run a command and append its output to Chronicle via `POST /api/log/append`.

- Default `server_id` is your hostname (override with `CLIMAX_SERVER_ID`).
- Use `--topic` to group logs by purpose (build/test/deploy/etc.).

Examples:

```bash

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
./clients/ctmcmd.py -- echo hello  # uses CLIMAX_TOPIC or 'default'
```

## `ctmcmd`

Convenience wrapper for command-unit logging from inside tmux.

- Implementation: `clients/ctmcmd.py` (the `clients/ctmcmd` script is a shim).

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
```
