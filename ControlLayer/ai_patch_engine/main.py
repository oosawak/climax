from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .diff.apply import PatchApplyError, apply_unified_diff


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='ai-patch')
    subparsers = parser.add_subparsers(dest='command', required=True)

    apply_parser = subparsers.add_parser('apply', help='Apply a unified diff to a root directory')
    apply_parser.add_argument('--diff', required=True, help='Path to a unified diff file')
    apply_parser.add_argument('--root', required=True, help='Project root to patch')
    apply_parser.add_argument('--dry-run', action='store_true', help='Do not write changes')
    apply_parser.add_argument('--log-file', help='Write JSONL change logs to this file')
    apply_parser.add_argument('--snapshot-dir', help='Override snapshot directory root')

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == 'apply':
        try:
            result = apply_unified_diff(
                Path(args.diff),
                Path(args.root),
                dry_run=args.dry_run,
                log_file=args.log_file,
                snapshot_dir=args.snapshot_dir,
            )
        except PatchApplyError as exc:
            print(json.dumps({'success': False, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
            return 1

        print(
            json.dumps(
                {
                    'success': result.success,
                    'root': result.root,
                    'changed_files': result.changed_files,
                    'dry_run': result.dry_run,
                    'snapshot_id': result.snapshot_id,
                    'details': result.details,
                    'preview_contents': result.preview_contents,
                },
                ensure_ascii=False,
            )
        )
        return 0

    return 2


if __name__ == '__main__':
    raise SystemExit(main())
