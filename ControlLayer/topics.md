# Topics

This file tracks the active work topics in a human-readable format.

## Current Topics

### 1. AI Patch Engine
- `id`: `ai-patch-engine`
- `status`: `in_progress`
- `priority`: `high`
- `owner`: `codex`
- `summary`: Python-based patch application layer for unified diff, rollback, and structured edits.
- `current_work`:
  - Unified diff parsing and local application
  - Snapshot-based rollback
  - JSONL change logging
  - CLI entrypoint `ai-patch`
- `next_action`:
  - Harden multi-file patch handling
  - Improve new-file and delete-file coverage
  - Add AST-based edit path for Python

### 2. Topic Management
- `id`: `topic-management`
- `status`: `in_progress`
- `priority`: `medium`
- `owner`: `codex`
- `summary`: Keep an editable topic list for ongoing work in this repository.
- `current_work`:
  - Introduce a lightweight manual topic register
- `next_action`:
  - Decide whether to add status conventions and update rules
  - Optionally mirror this file into a machine-readable format later

## Update Rules

- Add a new topic when work becomes substantial enough to track separately.
- Keep `status` to one of:
  - `planned`
  - `in_progress`
  - `blocked`
  - `done`
- Update `current_work` and `next_action` when the active focus changes.
- Keep entries short and concrete.

## Recent Completion

- Added the initial `ai_patch_engine/` package.
- Added rollback and JSONL logging support.
- Added unit tests for parsing, applying, rollback, and logging.
