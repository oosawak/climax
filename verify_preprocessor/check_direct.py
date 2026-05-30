#!/usr/bin/env python3
from __future__ import annotations

import argparse

import intent_processor


def main() -> int:
    parser = argparse.ArgumentParser(description='Direct test for intent_processor.py')
    parser.add_argument('--text', required=True)
    args = parser.parse_args()

    prompt = intent_processor.preprocess_for_llm(args.text)
    print(prompt)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
