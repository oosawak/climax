"""Unified diff parsing and application."""

from .apply import ApplyResult, PatchApplyError, apply_file_patches, apply_unified_diff
from .parser import FilePatch, Hunk, parse_unified_diff
from .rollback import SnapshotManager, SnapshotError

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
