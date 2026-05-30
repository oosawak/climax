from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# This Functions project lives at: api/chronicle-functions-python/
# The repo root is two levels up from this file.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Canonical preprocessor lives at repo root (planned module name).
from intent_processor import (  # noqa: E402
    build_english_prompt as _build_english_prompt,
    build_final_prompt_for_llm as _build_final_prompt_for_llm,
    interpret_with_azure_language as _interpret_with_azure_language,
    interpret_with_heuristics as _interpret_with_heuristics,
)


@dataclass(frozen=True)
class NlpResult:
    intent: str
    entities: dict[str, Any]
    provider: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "entities": self.entities,
            "provider": self.provider,
        }


def analyze_command(text: str) -> NlpResult:
    """Analyze a Japanese command.

    Uses Azure AI Language if configured; otherwise falls back to heuristics.
    """

    try:
        result = _interpret_with_azure_language(text)
    except Exception:
        result = _interpret_with_heuristics(text)

    return NlpResult(intent=result.intent, entities=result.entities, provider=result.provider)


def build_english_prompt(intent: str, entities: dict[str, Any]) -> str:
    return _build_english_prompt(type("_IR", (), {"intent": intent, "entities": entities})())


def build_final_prompt(english_prompt: str) -> str:
    return _build_final_prompt_for_llm(english_prompt)
