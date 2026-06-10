# tmux usage status

This directory contains a small status-line helper for tmux.

## What it shows

- GitHub Copilot monthly premium request usage
- Claude Code monthly token usage from local session logs
- Codex token usage from local session logs
- Gemini CLI token usage from a cached refresh run

## Usage

Run the cache reader directly:

```bash
python3 /home/oosawak/Workspace/climax/tools/tmux_usage_status_bar.py
```

For tmux status bars:

```tmux
set -g status-right "#(python3 /home/oosawak/Workspace/climax/tools/tmux_usage_status_bar.py)"
```

If your `tm` launcher already sets up tmux, source this file from that path:

```tmux
source-file /home/oosawak/Workspace/climax/tools/tmux_usage_status_bar.tmux
```

## Refresh job

Run the updater on a timer and let the bar read the cached JSON:

```bash
python3 /home/oosawak/Workspace/climax/tools/tmux_usage_refresh.py
```

Example cron entry every 5 minutes:

```cron
*/5 * * * * /usr/bin/python3 /home/oosawak/Workspace/climax/tools/tmux_usage_refresh.py >/dev/null 2>&1
```

The cache defaults to `/tmp/climax-tmux-usage.json`. Override it with `TMUX_USAGE_CACHE_PATH` if you want to store it elsewhere.

## Auth variables

- GitHub Copilot: `GH_TOKEN`, `GITHUB_TOKEN`, or `COPILOT_GITHUB_TOKEN`
- GitHub user/org lookup: `GITHUB_USER`, `GH_USER`, `GITHUB_ORG`, `GITHUB_ORGANIZATION`
- Claude Code: `ANTHROPIC_ADMIN_KEY`
- Codex/OpenAI: `OPENAI_ADMIN_KEY`, optionally `OPENAI_PROJECT_ID`

## Notes

- GitHub Copilot usage is read from the Copilot CLI if available.
- Claude usage is read from `claude -p '/stats'` and does not call the model for the `/stats` command.
- Codex usage is read from local session JSONL files under `~/.codex/sessions`.
- Gemini usage is refreshed by a background command and cached for tmux display.
