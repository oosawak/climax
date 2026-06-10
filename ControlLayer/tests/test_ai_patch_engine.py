from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_patch_engine.diff.apply import PatchApplyError, apply_unified_diff
from ai_patch_engine.diff.parser import parse_unified_diff


class TestAiPatchEngine(unittest.TestCase):
    def test_parse_unified_diff(self) -> None:
        diff_text = (
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -1,3 +1,3 @@\n"
            " line1\n"
            "-old\n"
            "+new\n"
        )

        patches = parse_unified_diff(diff_text)

        self.assertEqual(1, len(patches))
        self.assertEqual("app.py", patches[0].file_path)
        self.assertEqual(1, len(patches[0].hunks))
        self.assertEqual([" line1", "-old", "+new"], patches[0].hunks[0].lines)

    def test_apply_unified_diff_updates_file(self) -> None:
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

            result = apply_unified_diff(diff_text, root)

            self.assertTrue(result.success)
            self.assertEqual(["app.py"], result.changed_files)
            self.assertEqual("line1\nnew\nline3\n", target.read_text(encoding="utf-8"))

    def test_apply_unified_diff_dry_run_does_not_write(self) -> None:
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

            result = apply_unified_diff(diff_text, root, dry_run=True)

            self.assertTrue(result.success)
            self.assertEqual(["app.py"], result.changed_files)
            self.assertEqual("line1\nold\nline3\n", target.read_text(encoding="utf-8"))

    def test_apply_unified_diff_raises_on_context_mismatch(self) -> None:
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
            target.write_text("line1\nother\nline3\n", encoding="utf-8")

            with self.assertRaises(PatchApplyError):
                apply_unified_diff(diff_text, root)


if __name__ == "__main__":
    unittest.main()
