"""End-to-end judging of a single Q&A: prompt → model call → parse.

The orchestration logic is intentionally tiny: it composes already-tested
modules (prompt builder, OpenRouter client, parser) and adds the one-shot
retry on parse failure.

`ClaimJudge.judge(row, model) -> JudgedQA` is the public surface.

On the second consecutive parse failure the judge raises `JudgeError` with
the raw response on it; the runner script catches this and writes a row to
`claims_per_qa.errors.jsonl` (per PLAN §Step 3).
"""
from __future__ import annotations

from typing import Protocol

from .models import ChatResult, JudgedQA, ParseResult, SampleRow
from .parser import ClaimParser
from .prompt import PromptBuilder

_RETRY_INSTRUCTION = (
    "\n\nYour previous output was not valid JSON. Return only the JSON object — "
    "no markdown fences, no commentary."
)


class JudgeError(Exception):
    """Raised when both judging attempts fail to produce parseable output."""

    def __init__(
        self,
        message: str,
        *,
        cid: int,
        qa_index: int,
        model: str,
        raw: str,
        first_error: str | None,
        second_error: str | None,
    ) -> None:
        super().__init__(message)
        self.cid = cid
        self.qa_index = qa_index
        self.model = model
        self.raw = raw
        self.first_error = first_error
        self.second_error = second_error


class _ChatClient(Protocol):
    async def chat(self, *, model: str, prompt: str, **kwargs: object) -> ChatResult: ...


class ClaimJudge:
    """Compose prompt + client + parser; one retry on parse failure."""

    def __init__(
        self,
        client: _ChatClient,
        prompt_builder: PromptBuilder,
        parser: ClaimParser | None = None,
    ) -> None:
        self.client = client
        self.prompt_builder = prompt_builder
        self.parser = parser or ClaimParser()

    async def judge(self, row: SampleRow, model: str) -> JudgedQA:
        prompt = self.prompt_builder.build(row)
        attached_ids = {e.id for e in row.evidence_attached}

        first = await self.client.chat(model=model, prompt=prompt)
        first_parsed = self.parser.parse(first.text, attached_ids)
        if first_parsed.ok:
            return self._judged_qa(row, model, first_parsed, [first])

        retry_prompt = prompt + _RETRY_INSTRUCTION
        second = await self.client.chat(model=model, prompt=retry_prompt)
        second_parsed = self.parser.parse(second.text, attached_ids)
        if second_parsed.ok:
            return self._judged_qa(row, model, second_parsed, [first, second])

        raise JudgeError(
            "judge failed to produce valid JSON after one retry",
            cid=row.cid,
            qa_index=row.qa_index,
            model=model,
            raw=second.text,
            first_error=first_parsed.error,
            second_error=second_parsed.error,
        )

    @staticmethod
    def _judged_qa(
        row: SampleRow,
        model: str,
        parsed: ParseResult,
        chats: list[ChatResult],
    ) -> JudgedQA:
        return JudgedQA(
            cid=row.cid,
            qa_index=row.qa_index,
            topic=row.topic,
            evidence_ids_nonempty=row.evidence_ids_nonempty,
            num_evidence_attached=len(row.evidence_attached),
            model=model,
            claims=parsed.claims,
            prompt_tokens=sum(c.prompt_tokens for c in chats),
            completion_tokens=sum(c.completion_tokens for c in chats),
            latency_ms=sum(c.latency_ms for c in chats),
            split=row.split,
        )
