from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..log.logger import log_event
from .parser import FilePatch, Hunk, parse_unified_diff
from .rollback import SnapshotManager


@dataclass(slots=True)
class ApplyResult:
    success: bool
    root: str
    changed_files: list[str] = field(default_factory=list)
    dry_run: bool = False
    snapshot_id: str | None = None
    details: list[str] = field(default_factory=list)
    preview_contents: dict[str, str] = field(default_factory=dict)


class PatchApplyError(RuntimeError):
    pass


def apply_unified_diff(
    diff_input: str | Path,
    root: str | Path,
    *,
    dry_run: bool = False,
    log_file: str | Path | None = None,
    snapshot_dir: str | Path | None = None,
) -> ApplyResult:
    patches = parse_unified_diff(diff_input)
    return apply_file_patches(patches, root, dry_run=dry_run, log_file=log_file, snapshot_dir=snapshot_dir)


def apply_file_patches(
    patches: list[FilePatch],
    root: str | Path,
    *,
    dry_run: bool = False,
    log_file: str | Path | None = None,
    snapshot_dir: str | Path | None = None,
) -> ApplyResult:
    root_path = Path(root)
    changed_files: list[str] = []
    details: list[str] = []
    preview_contents: dict[str, str] = {}
    snapshot_id: str | None = None
    snapshot_manager: SnapshotManager | None = None

    target_files = [_patch_target_path(patch) for patch in patches]
    target_files = [path for path in target_files if path]

    if not dry_run:
        snapshot_manager = SnapshotManager(root_path, snapshot_dir=snapshot_dir)
        snapshot_id = snapshot_manager.create_snapshot(target_files)

    try:
        for patch in patches:
            relative_path = _patch_target_path(patch)
            if not relative_path:
                raise PatchApplyError('Patch does not specify a target file path')

            target_path = root_path / relative_path

            if patch.is_deleted_file:
                if not target_path.exists():
                    raise PatchApplyError(f'Cannot delete missing file: {relative_path}')
                if dry_run:
                    changed_files.append(relative_path)
                    details.append(f'delete:{relative_path}')
                    preview_contents[relative_path] = ''
                    continue
                target_path.unlink()
                changed_files.append(relative_path)
                details.append(f'delete:{relative_path}')
                continue

            original_lines = _read_lines(target_path)
            new_lines = original_lines[:]

            if patch.is_new_file and not target_path.exists():
                new_lines = []

            for hunk in patch.hunks:
                new_lines = _apply_hunk(new_lines, hunk, relative_path)

            rendered = _render_lines(new_lines)
            if dry_run:
                changed_files.append(relative_path)
                details.append(f'dry_run:{relative_path}')
                preview_contents[relative_path] = rendered
                continue

            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(rendered, encoding='utf-8')
            changed_files.append(relative_path)
            details.append(f'write:{relative_path}')

        result = ApplyResult(
            success=True,
            root=str(root_path),
            changed_files=changed_files,
            dry_run=dry_run,
            snapshot_id=snapshot_id,
            details=details,
            preview_contents=preview_contents,
        )
        _log_success(log_file, result)
        return result
    except Exception as exc:
        if snapshot_manager is not None and snapshot_id is not None:
            snapshot_manager.rollback(snapshot_id)
        _log_failure(log_file, root_path, changed_files, dry_run, snapshot_id, details, exc)
        raise


def _log_success(log_file: str | Path | None, result: ApplyResult) -> None:
    if log_file is None:
        return
    log_event(
        log_file,
        action='apply_diff',
        status='success',
        files=result.changed_files,
        snapshot_id=result.snapshot_id,
        dry_run=result.dry_run,
        details=result.details,
    )


def _log_failure(
    log_file: str | Path | None,
    root_path: Path,
    changed_files: list[str],
    dry_run: bool,
    snapshot_id: str | None,
    details: list[str],
    exc: Exception,
) -> None:
    if log_file is None:
        return
    log_event(
        log_file,
        action='apply_diff',
        status='failure',
        files=changed_files,
        snapshot_id=snapshot_id,
        dry_run=dry_run,
        details=details,
        error=f'{exc.__class__.__name__}: {exc}',
    )


def _patch_target_path(patch: FilePatch) -> str:
    if patch.new_file_path and patch.new_file_path != '/dev/null':
        return patch.new_file_path.removeprefix('b/').removeprefix('a/')
    if patch.old_file_path and patch.old_file_path != '/dev/null':
        return patch.old_file_path.removeprefix('b/').removeprefix('a/')
    return patch.file_path.removeprefix('b/').removeprefix('a/')


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding='utf-8').splitlines()


def _render_lines(lines: list[str]) -> str:
    return "\n".join(lines) + ("\n" if lines else "")



def _apply_hunk(lines: list[str], hunk: Hunk, file_path: str) -> list[str]:
    old_chunk = [line[1:] for line in hunk.lines if line[:1] in {' ', '-'}]
    new_chunk = [line[1:] for line in hunk.lines if line[:1] in {' ', '+'}]

    start_index = max(hunk.old_start - 1, 0)
    if _matches_at(lines, start_index, old_chunk):
        return _replace_at(lines, start_index, len(old_chunk), new_chunk)

    match_index = _find_chunk(lines, old_chunk, max(0, start_index - 3), min(len(lines), start_index + 4))
    if match_index is not None:
        return _replace_at(lines, match_index, len(old_chunk), new_chunk)

    raise PatchApplyError(
        f'Failed to apply hunk in {file_path}: expected old chunk not found near line {hunk.old_start}'
    )


def _matches_at(lines: list[str], index: int, chunk: list[str]) -> bool:
    return lines[index : index + len(chunk)] == chunk


def _find_chunk(lines: list[str], chunk: list[str], start: int, end: int) -> int | None:
    if not chunk:
        return start
    search_end = max(end - len(chunk) + 1, start)
    for index in range(start, search_end + 1):
        if lines[index : index + len(chunk)] == chunk:
            return index
    return None


def _replace_at(lines: list[str], index: int, remove_count: int, insert_lines: list[str]) -> list[str]:
    return lines[:index] + insert_lines + lines[index + remove_count :]
