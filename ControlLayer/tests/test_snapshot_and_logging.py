from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_patch_engine.diff.apply import apply_unified_diff
from ai_patch_engine.diff.rollback import SnapshotManager
from ai_patch_engine.log.logger import log_event


class TestSnapshotAndLogging(unittest.TestCase):
    def test_snapshot_manager_rolls_back_modified_new_and_deleted_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "app.py"
            target.write_text("original\n", encoding="utf-8")
            created = root / "created.txt"

            manager = SnapshotManager(root)
            snapshot_id = manager.create_snapshot(["app.py", "created.txt"])

            target.write_text("changed\n", encoding="utf-8")
            created.write_text("temp\n", encoding="utf-8")

            manager.rollback(snapshot_id)

            self.assertEqual("original\n", target.read_text(encoding="utf-8"))
            self.assertFalse(created.exists())

    def test_log_event_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "logs" / "patches.jsonl"

            log_event(
                log_path,
                action="apply_diff",
                status="success",
                files=["app.py"],
                snapshot_id="ccl-123",
                dry_run=False,
                details=["write:app.py"],
            )

            record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual("apply_diff", record["action"])
            self.assertEqual("success", record["status"])
            self.assertEqual(["app.py"], record["files"])
            self.assertEqual("ccl-123", record["snapshot_id"])
            self.assertEqual(False, record["dry_run"])

    def test_apply_unified_diff_emits_snapshot_and_log(self) -> None:
        diff_text = (
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -1,3 +1,3 @@\n"
            " line1\n"
            "-old\n"
            "+new\n"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "app.py"
            target.write_text("line1\nold\nline3\n", encoding="utf-8")
            log_path = root / "logs" / "patches.jsonl"

            result = apply_unified_diff(diff_text, root, log_file=log_path)

            self.assertTrue(result.snapshot_id)
            self.assertTrue(log_path.exists())
            log_record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual("success", log_record["status"])
            self.assertEqual(result.snapshot_id, log_record["snapshot_id"])
            self.assertEqual(["app.py"], result.changed_files)
            self.assertEqual("line1\nnew\nline3\n", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
