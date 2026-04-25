"""Async OpenRouter chat client with retries, backoff, and a USD budget cap.

Public surface:
- `OpenRouterClient(api_key, concurrency, max_usd)` — instantiate once per run.
- `await client.chat(model=..., prompt=...) -> ChatResult` — single completion.
- `client.spend_usd` — cumulative cost so far (for periodic logging).
- `BudgetExceeded` — raised on the call **after** cumulative spend crosses
  `max_usd`. The result of the call that pushed spend over the line is still
  returned, so the runner can persist it before aborting.

Behavior:
- Single shared `httpx.AsyncClient`; retries on `429` and `5xx` with
  exponential backoff (`backoff_base * 2**attempt`). When the response
  carries a `Retry-After` header, that value is honored verbatim.
- Concurrency is bounded by an `asyncio.Semaphore`.
- `pricing` is per-million-token USD; unknown models cost zero. Override via
  the `pricing` constructor argument when invoking real models so the budget
  check is meaningful.

The HTTP transport and sleep function are injectable so unit tests can run
without network or wall-clock waits.
"""
from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx

from .models import ChatResult


class BudgetExceeded(Exception):
    """Raised when cumulative spend exceeds the configured `max_usd` cap."""


@dataclass(frozen=True)
class ModelPricing:
    """Per-million-token USD prices."""

    prompt_per_mtok: float
    completion_per_mtok: float


DEFAULT_PRICING: dict[str, ModelPricing] = {
    "anthropic/claude-sonnet-4.6": ModelPricing(prompt_per_mtok=3.0, completion_per_mtok=15.0),
    "google/gemini-2.5-pro": ModelPricing(prompt_per_mtok=1.25, completion_per_mtok=10.0),
}


class OpenRouterClient:
    """Async OpenRouter completions client with retries and a budget cap."""

    def __init__(
        self,
        api_key: str,
        concurrency: int = 5,
        max_usd: float = 15.0,
        pricing: dict[str, ModelPricing] | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
        max_retries: int = 5,
        backoff_base: float = 1.0,
        timeout_s: float = 60.0,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.max_usd = float(max_usd)
        self.pricing = dict(pricing) if pricing is not None else dict(DEFAULT_PRICING)
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._sleep = sleep
        self._sem = asyncio.Semaphore(concurrency)
        self._client = httpx.AsyncClient(
            base_url=base_url,
            transport=transport,
            timeout=httpx.Timeout(timeout_s),
        )
        self.spend_usd: float = 0.0
        self.calls: int = 0

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "OpenRouterClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        p = self.pricing.get(model)
        if p is None:
            return 0.0
        return (
            prompt_tokens * p.prompt_per_mtok / 1_000_000.0
            + completion_tokens * p.completion_per_mtok / 1_000_000.0
        )

    async def chat(
        self,
        *,
        model: str,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        **kw: Any,
    ) -> ChatResult:
        if self.spend_usd > self.max_usd:
            raise BudgetExceeded(
                f"cumulative spend ${self.spend_usd:.4f} exceeded budget ${self.max_usd:.2f}"
            )
        async with self._sem:
            return await self._chat_with_retries(model, prompt, temperature, max_tokens, kw)

    async def _chat_with_retries(
        self,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int | None,
        kw: dict[str, Any],
    ) -> ChatResult:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            **kw,
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens

        attempt = 0
        while True:
            t0 = time.monotonic()
            response = await self._client.post("/chat/completions", headers=headers, json=body)

            if response.status_code == 429 or 500 <= response.status_code < 600:
                if attempt >= self.max_retries:
                    response.raise_for_status()
                delay = self._compute_backoff(response, attempt)
                await self._sleep(delay)
                attempt += 1
                continue

            response.raise_for_status()
            data = response.json()
            return self._record_and_build(model, data, t0)

    def _compute_backoff(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return self.backoff_base * (2 ** attempt)

    def _record_and_build(self, model: str, data: dict, t0: float) -> ChatResult:
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"unexpected OpenRouter response shape: {exc}") from exc
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        latency_ms = int((time.monotonic() - t0) * 1000)

        self.spend_usd += self.estimate_cost(model, prompt_tokens, completion_tokens)
        self.calls += 1

        return ChatResult(
            text=text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
        )
