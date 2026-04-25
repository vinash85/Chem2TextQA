"""Tests for grounding.judge.ClaimJudge.

Uses the in-conftest FakeOpenRouterClient — no network. The fake's `calls`
attribute lets us assert what was sent on each attempt.
"""
from __future__ import annotations

import json

import pytest

from phase4_grounding.grounding.judge import ClaimJudge, JudgeError
from phase4_grounding.grounding.models import (
    ChatResult,
    Compound,
    EvidenceItem,
    SampleRow,
)
from phase4_grounding.grounding.prompt import PromptBuilder


def _row(*, evidence: tuple[EvidenceItem, ...] = ()) -> SampleRow:
    return SampleRow(
        cid=42,
        qa_index=3,
        topic="mechanism",
        split="train",
        evidence_ids_nonempty=bool(evidence),
        compound=Compound(cid=42, name="Aspirin", smiles="C", molecular_formula="CH4"),
        question="How does it work?",
        phase2_answer="It does X and Y.",
        evidence_attached=evidence,
    )


def _chat(text: str, *, prompt_tokens: int = 100, completion_tokens: int = 50) -> ChatResult:
    return ChatResult(
        text=text,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=12,
    )


def _good_json() -> str:
    return json.dumps(
        {
            "claims": [
                {"claim": "X", "label": "STATED", "evidence_id": 1, "rationale": "r"},
                {"claim": "Y", "label": "UNSUPPORTED", "evidence_id": None, "rationale": "r"},
            ]
        }
    )


@pytest.mark.asyncio
async def test_judge_success_on_first_attempt(fake_openrouter_client):
    client = fake_openrouter_client([_chat(_good_json())])
    judge = ClaimJudge(client, PromptBuilder())
    row = _row(evidence=(EvidenceItem(id=1, text="e", pmid="p", source="abstract"),))

    judged = await judge.judge(row, model="anthropic/claude-sonnet-4.6")

    assert len(judged.claims) == 2
    assert judged.cid == 42
    assert judged.qa_index == 3
    assert judged.topic == "mechanism"
    assert judged.evidence_ids_nonempty is True
    assert judged.num_evidence_attached == 1
    assert judged.model == "anthropic/claude-sonnet-4.6"
    assert judged.prompt_tokens == 100
    assert judged.completion_tokens == 50
    # only one call was made — no retry
    assert len(client.calls) == 1


@pytest.mark.asyncio
async def test_judge_retries_once_on_parse_failure_then_succeeds(fake_openrouter_client):
    client = fake_openrouter_client(
        [
            _chat("```json\n{...}\n```"),  # malformed (markdown fence + ellipsis)
            _chat(_good_json()),
        ]
    )
    judge = ClaimJudge(client, PromptBuilder())
    row = _row(evidence=(EvidenceItem(id=1, text="e", pmid="p", source="abstract"),))

    judged = await judge.judge(row, model="anthropic/claude-sonnet-4.6")
    assert len(judged.claims) == 2
    # both calls happened, and the second prompt carried the retry instruction
    assert len(client.calls) == 2
    assert "Your previous output was not valid JSON" in client.calls[1]["prompt"]
    assert "Your previous output was not valid JSON" not in client.calls[0]["prompt"]
    # token tally aggregates both calls
    assert judged.prompt_tokens == 200
    assert judged.completion_tokens == 100


@pytest.mark.asyncio
async def test_judge_raises_judge_error_after_two_failures(fake_openrouter_client):
    client = fake_openrouter_client(
        [
            _chat("not json at all"),
            _chat("still not json"),
        ]
    )
    judge = ClaimJudge(client, PromptBuilder())
    row = _row(evidence=(EvidenceItem(id=1, text="e", pmid="p", source="abstract"),))

    with pytest.raises(JudgeError) as excinfo:
        await judge.judge(row, model="anthropic/claude-sonnet-4.6")

    err = excinfo.value
    assert err.cid == 42
    assert err.qa_index == 3
    assert err.model == "anthropic/claude-sonnet-4.6"
    assert err.raw == "still not json"
    assert err.first_error is not None
    assert err.second_error is not None
    assert len(client.calls) == 2


@pytest.mark.asyncio
async def test_judge_raises_judge_error_when_evidence_id_unknown_twice(fake_openrouter_client):
    """Bogus evidence_id is a parse failure (per parser); the same error twice
    should bubble up as JudgeError."""
    bad = json.dumps(
        {"claims": [{"claim": "x", "label": "STATED", "evidence_id": 99, "rationale": "r"}]}
    )
    client = fake_openrouter_client([_chat(bad), _chat(bad)])
    judge = ClaimJudge(client, PromptBuilder())
    row = _row(evidence=(EvidenceItem(id=1, text="e", pmid="p", source="abstract"),))

    with pytest.raises(JudgeError) as excinfo:
        await judge.judge(row, model="anthropic/claude-sonnet-4.6")
    assert "99" in (excinfo.value.second_error or "")


@pytest.mark.asyncio
async def test_judge_passes_correct_attached_ids_to_parser(fake_openrouter_client):
    """If the model cites E2 and the row has 2 evidence items, parsing must succeed."""
    payload = json.dumps(
        {
            "claims": [
                {"claim": "x", "label": "STATED", "evidence_id": 2, "rationale": "r"},
            ]
        }
    )
    client = fake_openrouter_client([_chat(payload)])
    judge = ClaimJudge(client, PromptBuilder())
    row = _row(
        evidence=(
            EvidenceItem(id=1, text="a", pmid="p", source="abstract"),
            EvidenceItem(id=2, text="b", pmid="p", source="abstract"),
        )
    )
    judged = await judge.judge(row, model="anthropic/claude-sonnet-4.6")
    assert judged.claims[0].evidence_id == 2


@pytest.mark.asyncio
async def test_judge_handles_no_attached_evidence(fake_openrouter_client):
    """When no evidence is attached, the judge can still emit STRUCTURAL/UNSUPPORTED claims."""
    payload = json.dumps(
        {
            "claims": [
                {"claim": "has methyl group", "label": "STRUCTURAL", "evidence_id": None, "rationale": "r"},
                {"claim": "cures cancer", "label": "UNSUPPORTED", "evidence_id": None, "rationale": "r"},
            ]
        }
    )
    client = fake_openrouter_client([_chat(payload)])
    judge = ClaimJudge(client, PromptBuilder())
    row = _row(evidence=())  # nothing attached

    judged = await judge.judge(row, model="anthropic/claude-sonnet-4.6")
    assert judged.num_evidence_attached == 0
    assert {c.label for c in judged.claims} == {"STRUCTURAL", "UNSUPPORTED"}
