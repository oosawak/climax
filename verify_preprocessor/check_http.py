#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def _post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        method='POST',
        headers={'Content-Type': 'application/json'},
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            raw = res.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        details = e.read().decode('utf-8', errors='replace')
        raise SystemExit(f'HTTPError {e.code}: {details}')
    except urllib.error.URLError as e:
        raise SystemExit(f'URLError: {e.reason}')

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise SystemExit('server returned non-JSON response')


def main() -> int:
    parser = argparse.ArgumentParser(description='HTTP test for /api/nlp/analyze')
    parser.add_argument('--functions-url', default='http://localhost:7071')
    parser.add_argument('--text', required=True)
    parser.add_argument('--format', choices=['final_prompt', 'english_prompt', 'json'], default='final_prompt')
    args = parser.parse_args()

    base = args.functions_url.rstrip('/')
    url = f'{base}/api/nlp/analyze'
    result = _post_json(url, {'text': args.text})

    if args.format == 'json':
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        return 0

    if args.format == 'english_prompt':
        sys.stdout.write(str(result.get('english_prompt', '')) + '\n')
        return 0

    sys.stdout.write(str(result.get('final_prompt', '')) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
