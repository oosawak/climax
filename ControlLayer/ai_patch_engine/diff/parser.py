from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Hunk:
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FilePatch:
    file_path: str
    new_file_path: str | None = None
    old_file_path: str | None = None
    hunks: list[Hunk] = field(default_factory=list)
    is_new_file: bool = False
    is_deleted_file: bool = False


def _read_input(diff_input: str | Path) -> str:
    path = Path(diff_input)
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8")
    return str(diff_input)


def parse_unified_diff(diff_input: str | Path) -> list[FilePatch]:
    text = _read_input(diff_input)
    lines = text.splitlines()

    patches: list[FilePatch] = []
    current_patch: FilePatch | None = None
    current_hunk: Hunk | None = None

    for raw_line in lines:
        line = raw_line.rstrip("\n")

        if line.startswith("diff --git "):
            current_patch = None
            current_hunk = None
            continue

        if line.startswith("--- "):
            old_file = line[4:].strip()
            if current_patch is None:
                current_patch = FilePatch(file_path=old_file)
                patches.append(current_patch)
            current_patch.old_file_path = old_file
            if old_file == "/dev/null":
                current_patch.is_new_file = True
            continue

        if line.startswith("+++ "):
            new_file = line[4:].strip()
            if current_patch is None:
                current_patch = FilePatch(file_path=new_file)
                patches.append(current_patch)
            current_patch.new_file_path = new_file
            current_patch.file_path = _normalize_patch_path(new_file)
            if new_file == "/dev/null":
                current_patch.is_deleted_file = True
            continue

        if line.startswith("@@ "):
            header = line[3:]
            old_range, new_range = header.split(" @@")[0].split(" ", 1)
            old_start, old_lines = _parse_range(old_range)
            new_start, new_lines = _parse_range(new_range)
            current_hunk = Hunk(
                old_start=old_start,
                old_lines=old_lines,
                new_start=new_start,
                new_lines=new_lines,
            )
            if current_patch is None:
                current_patch = FilePatch(file_path="")
                patches.append(current_patch)
            current_patch.hunks.append(current_hunk)
            continue

        if current_hunk is not None and line[:1] in {"+", "-", " "}:
            current_hunk.lines.append(line)

    return patches


def _parse_range(range_text: str) -> tuple[int, int]:
    range_text = range_text.strip()
    if not range_text.startswith(("-", "+")):
        raise ValueError(f"Invalid hunk range: {range_text}")
    range_text = range_text[1:]
    if "," in range_text:
        start, length = range_text.split(",", 1)
        return int(start), int(length)
    return int(range_text), 1


def _normalize_patch_path(path_text: str) -> str:
    normalized = path_text.strip()
    if normalized.startswith("a/") or normalized.startswith("b/"):
        return normalized[2:]
    return normalized
