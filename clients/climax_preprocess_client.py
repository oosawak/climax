#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def _read_text(args: argparse.Namespace) -> str:
    if args.text is not None:
        text = args.text.strip()
        if not text:
            raise SystemExit('--text is empty')
        return text

    stdin = sys.stdin.read()
    text = (stdin or '').strip()
    if not text:
        raise SystemExit('no input: pass --text or pipe via stdin')
    return text


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


def _build_analyze_url(base_url: str, functions_code: str | None) -> str:
    base = base_url.rstrip('/')
    url = f'{base}/api/nlp/analyze'
    if not functions_code:
        return url

    code = functions_code.strip()
    if not code:
        return url

    q = urllib.parse.urlencode({'code': code})
    return f'{url}?{q}'


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Climax: Japanese command -> intent -> English prompt -> final prompt (Japanese response)',
    )
    parser.add_argument(
        '--functions-url',
        default=os.getenv('CLIMAX_FUNCTIONS_URL', 'http://localhost:7071'),
        help='Azure Functions base URL (default: http://localhost:7071). Env: CLIMAX_FUNCTIONS_URL',
    )
    parser.add_argument(
        '--functions-code',
        default=os.getenv('CLIMAX_FUNCTIONS_CODE'),
        help='Functions key ("code" query param). Required for deployed Azure unless auth is anonymous. Env: CLIMAX_FUNCTIONS_CODE',
    )
    parser.add_argument('--text', help='Japanese command text. If omitted, reads stdin.')
    parser.add_argument(
        '--format',
        choices=['final_prompt', 'english_prompt', 'json'],
        default='final_prompt',
        help='Output format (default: final_prompt)',
    )

    args = parser.parse_args()

    text = _read_text(args)
    url = _build_analyze_url(args.functions_url, args.functions_code)

    result = _post_json(url, {'text': text})

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
