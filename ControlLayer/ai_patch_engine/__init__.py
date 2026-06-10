"""AI Patch Engine package."""

from .diff.apply import ApplyResult, PatchApplyError, apply_file_patches, apply_unified_diff
from .diff.parser import FilePatch, Hunk, parse_unified_diff
from .diff.rollback import SnapshotManager, SnapshotError

__all__ = [
    'ApplyResult',
    'FilePatch',
    'Hunk',
    'PatchApplyError',
    'SnapshotError',
    'SnapshotManager',
    'apply_file_patches',
    'apply_unified_diff',
    'parse_unified_diff',
]
