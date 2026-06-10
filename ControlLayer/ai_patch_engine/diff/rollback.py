from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


@dataclass(slots=True)
class SnapshotEntry:
    path: str
    existed: bool


class SnapshotError(RuntimeError):
    pass


class SnapshotManager:
    def __init__(self, root: str | Path, snapshot_dir: str | Path | None = None) -> None:
        self.root = Path(root)
        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir is not None else self.root / ".ai_patch_engine" / "snapshots"

    def create_snapshot(self, target_files: list[str]) -> str:
        snapshot_id = self._build_snapshot_id()
        snapshot_root = self._snapshot_root(snapshot_id)
        files_root = snapshot_root / "files"
        files_root.mkdir(parents=True, exist_ok=True)

        entries: list[SnapshotEntry] = []
        for relative_path in sorted(set(target_files)):
            source_path = self.root / relative_path
            existed = source_path.exists()
            entries.append(SnapshotEntry(path=relative_path, existed=existed))
            if existed and source_path.is_file():
                destination_path = files_root / relative_path
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, destination_path)

        manifest = {
            "snapshot_id": snapshot_id,
            "created_at": self._timestamp(),
            "root": str(self.root),
            "entries": [{"path": entry.path, "existed": entry.existed} for entry in entries],
        }
        snapshot_root.mkdir(parents=True, exist_ok=True)
        (snapshot_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return snapshot_id

    def rollback(self, snapshot_id: str) -> None:
        snapshot_root = self._snapshot_root(snapshot_id)
        manifest_path = snapshot_root / "manifest.json"
        if not manifest_path.exists():
            raise SnapshotError(f"Snapshot not found: {snapshot_id}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = manifest.get("entries", [])
        files_root = snapshot_root / "files"

        for raw_entry in entries:
            relative_path = raw_entry["path"]
            existed = bool(raw_entry["existed"])
            target_path = self.root / relative_path
            backup_path = files_root / relative_path

            if existed:
                if not backup_path.exists():
                    raise SnapshotError(f"Missing backup for {relative_path} in snapshot {snapshot_id}")
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_path, target_path)
            elif target_path.exists():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()

    def _snapshot_root(self, snapshot_id: str) -> Path:
        return self.snapshot_dir / snapshot_id

    def _build_snapshot_id(self) -> str:
        return f"ccl-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
