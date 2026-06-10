# Climax Control Layer

Minimal Node.js server with MongoDB connectivity, plus a Python AI Patch Engine prototype.

## Setup

```bash
npm install
cp .env.example .env
npm start
```

## AI Patch Engine

The Python prototype lives under `ai_patch_engine/`.

```bash
ai-patch apply --diff patch.diff --root /path/to/project
ai-patch apply --diff patch.diff --root /path/to/project --dry-run
ai-patch apply --diff patch.diff --root /path/to/project --log-file logs/patches.jsonl
ai-patch apply --diff patch.diff --root /path/to/project --snapshot-dir .snapshots
# or
python -m ai_patch_engine.main apply --diff patch.diff --root /path/to/project
```

The engine now creates a rollback snapshot on normal applies and can emit JSONL logs when `--log-file` is set.

## Endpoints

- `GET /health`
- `GET /db/ping`

## Environment

- `PORT`
- `MONGODB_URI`
- `MONGODB_DB`
