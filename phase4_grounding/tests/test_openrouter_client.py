"""Tests for grounding.openrouter_client.OpenRouterClient.

The HTTP layer is faked with `httpx.MockTransport` and `asyncio.sleep` is
replaced with a recorder so backoff tests are wall-clock free.
"""
from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest

from phase4_grounding.grounding.models import ChatResult
from phase4_grounding.grounding.openrouter_client import (
    DEFAULT_PRICING,
    BudgetExceeded,
    ModelPricing,
    OpenRouterClient,
)


def _ok_response(text: str = "hello", prompt_tokens: int = 100, completion_tokens: int = 50) -> dict:
    return {
        "choices": [{"message": {"content": text}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


def _make_transport(responses: list[httpx.Response]) -> tuple[httpx.MockTransport, list[httpx.Request]]:
    """Build a MockTransport that returns the given responses in order.
    Returns the transport and a list that records each received request."""
    received: list[httpx.Request] = []
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        received.append(request)
        if not queue:
            raise AssertionError("transport ran out of scripted responses")
        return queue.pop(0)

    return httpx.MockTransport(handler), received


def _make_recording_sleep() -> tuple[Callable, list[float]]:
    durations: list[float] = []

    async def sleep(d: float) -> None:
        durations.append(d)

    return sleep, durations


@pytest.mark.asyncio
async def test_cost_tracker_arithmetic_uses_per_million_pricing():
    pricing = {"test/model": ModelPricing(prompt_per_mtok=2.0, completion_per_mtok=4.0)}
    transport, _ = _make_transport(
        [httpx.Response(200, json=_ok_response(prompt_tokens=1_000_000, completion_tokens=500_000))]
    )
    sleep, _ = _make_recording_sleep()
    async with OpenRouterClient(
        api_key="x", pricing=pricing, transport=transport, sleep=sleep
    ) as client:
        await client.chat(model="test/model", prompt="hi")
    # 1M prompt @ $2 + 0.5M completion @ $4 = $2 + $2 = $4
    assert client.spend_usd == pytest.approx(4.0)
    assert client.calls == 1


@pytest.mark.asyncio
async def test_unknown_model_costs_zero():
    transport, _ = _make_transport(
        [httpx.Response(200, json=_ok_response(prompt_tokens=1_000, completion_tokens=1_000))]
    )
    sleep, _ = _make_recording_sleep()
    async with OpenRouterClient(api_key="x", transport=transport, sleep=sleep) as client:
        await client.chat(model="some/unknown-model", prompt="hi")
    assert client.spend_usd == 0.0


@pytest.mark.asyncio
async def test_budget_exceeded_raised_on_call_after_overspend():
    """Spend may exceed the cap by one call; the next call raises so the
    runner can persist the result of the call that pushed over."""
    pricing = {"m": ModelPricing(prompt_per_mtok=10.0, completion_per_mtok=10.0)}
    transport, _ = _make_transport(
        [
            httpx.Response(200, json=_ok_response(prompt_tokens=1_000_000, completion_tokens=0)),
            httpx.Response(200, json=_ok_response()),
        ]
    )
    sleep, _ = _make_recording_sleep()
    async with OpenRouterClient(
        api_key="x", pricing=pricing, max_usd=5.0, transport=transport, sleep=sleep
    ) as client:
        # First call: cost = $10, exceeds cap, but result still returned.
        result = await client.chat(model="m", prompt="hi")
        assert isinstance(result, ChatResult)
        assert client.spend_usd == pytest.approx(10.0)
        # Second call: refuses before issuing the request.
        with pytest.raises(BudgetExceeded):
            await client.chat(model="m", prompt="hi again")


@pytest.mark.asyncio
async def test_retry_after_header_is_honored_verbatim():
    transport, _ = _make_transport(
        [
            httpx.Response(429, headers={"Retry-After": "7"}, json={"error": "rate limited"}),
            httpx.Response(200, json=_ok_response()),
        ]
    )
    sleep, sleeps = _make_recording_sleep()
    async with OpenRouterClient(
        api_key="x", transport=transport, sleep=sleep, backoff_base=99.0
    ) as client:
        await client.chat(model="anthropic/claude-sonnet-4.6", prompt="hi")
    assert sleeps == [7.0]


@pytest.mark.asyncio
async def test_exponential_backoff_when_no_retry_after():
    transport, _ = _make_transport(
        [
            httpx.Response(500, json={"error": "boom"}),
            httpx.Response(503, json={"error": "boom"}),
            httpx.Response(200, json=_ok_response()),
        ]
    )
    sleep, sleeps = _make_recording_sleep()
    async with OpenRouterClient(
        api_key="x", transport=transport, sleep=sleep, backoff_base=2.0
    ) as client:
        await client.chat(model="anthropic/claude-sonnet-4.6", prompt="hi")
    # base * 2^0 = 2, base * 2^1 = 4
    assert sleeps == [2.0, 4.0]


@pytest.mark.asyncio
async def test_retries_exhausted_raises_http_error():
    responses = [httpx.Response(500, json={"error": "boom"}) for _ in range(6)]
    transport, _ = _make_transport(responses)
    sleep, _ = _make_recording_sleep()
    async with OpenRouterClient(
        api_key="x", transport=transport, sleep=sleep, max_retries=3, backoff_base=0.1
    ) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.chat(model="anthropic/claude-sonnet-4.6", prompt="hi")


@pytest.mark.asyncio
async def test_4xx_other_than_429_does_not_retry():
    transport, received = _make_transport(
        [httpx.Response(400, json={"error": "bad request"})]
    )
    sleep, sleeps = _make_recording_sleep()
    async with OpenRouterClient(api_key="x", transport=transport, sleep=sleep) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.chat(model="anthropic/claude-sonnet-4.6", prompt="hi")
    # exactly one HTTP attempt, no sleeps
    assert len(received) == 1
    assert sleeps == []


@pytest.mark.asyncio
async def test_authorization_header_sent():
    transport, received = _make_transport([httpx.Response(200, json=_ok_response())])
    sleep, _ = _make_recording_sleep()
    async with OpenRouterClient(api_key="my-secret-key", transport=transport, sleep=sleep) as client:
        await client.chat(model="anthropic/claude-sonnet-4.6", prompt="hi")
    assert received[0].headers["Authorization"] == "Bearer my-secret-key"


@pytest.mark.asyncio
async def test_request_body_carries_model_and_prompt():
    transport, received = _make_transport([httpx.Response(200, json=_ok_response())])
    sleep, _ = _make_recording_sleep()
    async with OpenRouterClient(api_key="x", transport=transport, sleep=sleep) as client:
        await client.chat(
            model="anthropic/claude-sonnet-4.6",
            prompt="decompose this answer",
            temperature=0.0,
            max_tokens=512,
        )
    body = json.loads(received[0].content)
    assert body["model"] == "anthropic/claude-sonnet-4.6"
    assert body["messages"] == [{"role": "user", "content": "decompose this answer"}]
    assert body["temperature"] == 0.0
    assert body["max_tokens"] == 512


@pytest.mark.asyncio
async def test_chat_returns_token_usage_in_chat_result():
    transport, _ = _make_transport(
        [httpx.Response(200, json=_ok_response(prompt_tokens=42, completion_tokens=17))]
    )
    sleep, _ = _make_recording_sleep()
    async with OpenRouterClient(api_key="x", transport=transport, sleep=sleep) as client:
        result = await client.chat(model="anthropic/claude-sonnet-4.6", prompt="hi")
    assert result.prompt_tokens == 42
    assert result.completion_tokens == 17
    assert result.text == "hello"
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_default_pricing_includes_audit_models():
    """Sanity: DEFAULT_PRICING has both models named in PLAN.md so the budget
    cap is meaningful out of the box."""
    assert "anthropic/claude-sonnet-4.6" in DEFAULT_PRICING
    assert "google/gemini-2.5-pro" in DEFAULT_PRICING
    for p in DEFAULT_PRICING.values():
        assert p.prompt_per_mtok > 0
        assert p.completion_per_mtok > 0


@pytest.mark.asyncio
async def test_invalid_retry_after_falls_back_to_exponential():
    transport, _ = _make_transport(
        [
            httpx.Response(429, headers={"Retry-After": "garbage"}, json={"error": "x"}),
            httpx.Response(200, json=_ok_response()),
        ]
    )
    sleep, sleeps = _make_recording_sleep()
    async with OpenRouterClient(
        api_key="x", transport=transport, sleep=sleep, backoff_base=3.0
    ) as client:
        await client.chat(model="anthropic/claude-sonnet-4.6", prompt="hi")
    # falls back to backoff_base * 2^0
    assert sleeps == [3.0]
