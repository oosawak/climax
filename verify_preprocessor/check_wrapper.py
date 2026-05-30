#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='Wrapper test for api/chronicle-functions-python/chronicle_nlp.py')
    parser.add_argument('--text', required=True)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    fn_dir = repo_root / 'api' / 'chronicle-functions-python'
    sys.path.insert(0, str(fn_dir))

    import chronicle_nlp  # noqa: E402

    result = chronicle_nlp.analyze_command(args.text)
    print(result.to_payload())
    print('---')
    english = chronicle_nlp.build_english_prompt(result.intent, result.entities)
    print(english)
    print('---')
    print(chronicle_nlp.build_final_prompt(english))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
