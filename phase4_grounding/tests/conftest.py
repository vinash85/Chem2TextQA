"""Shared fixtures for phase4_grounding tests.

Notes:
- `tiny_dataset_path` returns the path to the hand-crafted JSONL.
- `tiny_dataset_records` returns the parsed dataset as a list of dicts.
- `fake_openrouter_client` returns a scriptable async client that never hits the network.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from pathlib import Path

import pytest

# Make the project root importable so `from phase4_grounding.grounding... import` works
# regardless of how pytest is invoked.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from phase4_grounding.grounding.models import ChatResult  # noqa: E402


@pytest.fixture
def tiny_dataset_path() -> Path:
    return Path(__file__).parent / "data" / "tiny_dataset.jsonl"


@pytest.fixture
def tiny_dataset_records(tiny_dataset_path: Path) -> list[dict]:
    with tiny_dataset_path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


@pytest.fixture
def tmp_out_dir(tmp_path: Path) -> Path:
    out = tmp_path / "outputs"
    out.mkdir()
    return out


class FakeOpenRouterClient:
    """Scriptable async stand-in for OpenRouterClient.

    Construct with a list of responses; each call to `chat` pops the next.
    A response can be a ChatResult (success) or an Exception instance (raised).
    """

    def __init__(self, responses: Iterable[ChatResult | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    async def chat(self, *, model: str, prompt: str, **kwargs) -> ChatResult:
        self.calls.append({"model": model, "prompt": prompt, "kwargs": kwargs})
        if not self._responses:
            raise AssertionError("FakeOpenRouterClient ran out of scripted responses")
        nxt = self._responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


@pytest.fixture
def fake_openrouter_client():
    def _factory(responses: Iterable[ChatResult | Exception]) -> FakeOpenRouterClient:
        return FakeOpenRouterClient(responses)

    return _factory
