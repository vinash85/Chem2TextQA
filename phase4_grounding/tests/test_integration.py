"""Integration tests for the Step-8 entry-point scripts.

Exercises `scripts.sample_qa.main` and the core of `scripts.judge_claims`
(`run_judge_pass`) against `tiny_dataset.jsonl`. The judge pass uses a
scripted fake client so no network is touched.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from phase4_grounding.grounding.judge import ClaimJudge
from phase4_grounding.grounding.models import ChatResult
from phase4_grounding.grounding.prompt import PromptBuilder
from phase4_grounding.scripts import aggregate, judge_claims, sample_qa


# Tiny dataset has only 4 functional topics (mechanism/toxicity/engineering/
# metabolism), so weight all of them equally and zero out the rest to avoid
# "silent shortfall" on under-represented strata.
_EVEN_WEIGHTS = {
    "mechanism": 0.25,
    "engineering": 0.25,
    "metabolism": 0.25,
    "toxicity": 0.25,
    "therapeutic_use": 0.0,
    "_other": 0.0,
}


def _good_response(text: str = "STATED X", evidence_id: int | None = 1) -> ChatResult:
    payload = {
        "claims": [
            {
                "claim": text,
                "label": "STATED" if evidence_id is not None else "UNSUPPORTED",
                "evidence_id": evidence_id,
                "rationale": "because the evidence says so",
            }
        ]
    }
    return ChatResult(
        text=json.dumps(payload),
        prompt_tokens=100,
        completion_tokens=50,
        latency_ms=5,
    )


def test_sample_qa_writes_expected_shape(
    tiny_dataset_path: Path, tmp_out_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    # Use an even-weights sampler so the tiny dataset's 4 topics each get slots.
    monkeypatch.setattr(sample_qa, "Sampler", _EvenWeightedSamplerFactory())

    rc = sample_qa.main(
        [
            "--n",
            "4",
            "--seed",
            "0",
            "--data-path",
            str(tiny_dataset_path),
            "--out-dir",
            str(tmp_out_dir),
        ]
    )
    assert rc == 0

    out_path = tmp_out_dir / "sample.jsonl"
    assert out_path.exists()
    records = [json.loads(line) for line in out_path.read_text().splitlines() if line]
    assert len(records) == 4

    for r in records:
        # Required top-level fields per PLAN §Step 1
        assert set(r) >= {
            "cid",
            "qa_index",
            "topic",
            "split",
            "evidence_ids_nonempty",
            "compound",
            "question",
            "phase2_answer",
            "evidence_attached",
        }
        assert set(r["compound"]) == {"name", "smiles", "molecular_formula"}
        # evidence is renumbered 1..N
        for i, ev in enumerate(r["evidence_attached"], start=1):
            assert ev["id"] == i
            assert "text" in ev


class _EvenWeightedSamplerFactory:
    """Swap the default weights with the even ones for the integration test."""

    def __call__(self, *, dataset_path, seed=0, topic_weights=None):
        from phase4_grounding.grounding.sampling import Sampler

        return Sampler(
            dataset_path=dataset_path,
            seed=seed,
            topic_weights=_EVEN_WEIGHTS,
        )


@pytest.mark.asyncio
async def test_run_judge_pass_writes_claims_and_errors(
    tiny_dataset_path: Path, tmp_out_dir: Path, fake_openrouter_client, monkeypatch
):
    # 1. Build a sample file via sample_qa
    monkeypatch.setattr(sample_qa, "Sampler", _EvenWeightedSamplerFactory())
    sample_qa.main(
        [
            "--n",
            "4",
            "--seed",
            "0",
            "--data-path",
            str(tiny_dataset_path),
            "--out-dir",
            str(tmp_out_dir),
        ]
    )

    # 2. Load sample rows
    rows = judge_claims.load_sample(tmp_out_dir / "sample.jsonl")
    assert len(rows) == 4

    # 3. Script the fake client: 3 good, 1 bad (twice) → 3 success + 1 error row
    responses = [
        _good_response(),
        _good_response(),
        _good_response(),
        ChatResult(text="not json", prompt_tokens=10, completion_tokens=5, latency_ms=1),
        ChatResult(text="still not json", prompt_tokens=10, completion_tokens=5, latency_ms=1),
    ]
    client = fake_openrouter_client(responses)
    client.spend_usd = 0.0  # attribute required by run_judge_pass
    judge = ClaimJudge(client, PromptBuilder())

    out_path = tmp_out_dir / "claims_per_qa.jsonl"
    err_path = tmp_out_dir / "claims_per_qa.errors.jsonl"

    # Concurrency 1 keeps the scripted-response order deterministic.
    success = await judge_claims.run_judge_pass(
        rows,
        judge,
        client,
        model="anthropic/claude-sonnet-4.6",
        out_path=out_path,
        err_path=err_path,
        concurrency=1,
    )

    assert success == 3

    good_lines = [
        json.loads(line) for line in out_path.read_text().splitlines() if line
    ]
    assert len(good_lines) == 3
    for r in good_lines:
        assert set(r) >= {
            "cid",
            "qa_index",
            "topic",
            "evidence_ids_nonempty",
            "num_evidence_attached",
            "model",
            "claims",
            "usage",
            "latency_ms",
        }
        assert r["model"] == "anthropic/claude-sonnet-4.6"
        assert r["usage"]["prompt_tokens"] == 100
        assert r["claims"][0]["label"] in ("STATED", "IMPLIED", "UNSUPPORTED", "STRUCTURAL")

    err_lines = [
        json.loads(line) for line in err_path.read_text().splitlines() if line
    ]
    assert len(err_lines) == 1
    assert err_lines[0]["raw"] == "still not json"
    assert err_lines[0]["first_error"] is not None
    assert err_lines[0]["second_error"] is not None

    # 4. Aggregate: ensure both summary files appear and are non-empty
    rc = aggregate.main(["--out-dir", str(tmp_out_dir)])
    assert rc == 0
    keep = tmp_out_dir / "grounding_summary_keep_structural.md"
    drop = tmp_out_dir / "grounding_summary_drop_structural.md"
    assert keep.exists() and keep.read_text().strip()
    assert drop.exists() and drop.read_text().strip()


@pytest.mark.asyncio
async def test_run_judge_pass_is_resumable(
    tiny_dataset_path: Path, tmp_out_dir: Path, fake_openrouter_client, monkeypatch
):
    """Rows already in claims_per_qa.jsonl are not re-judged."""
    monkeypatch.setattr(sample_qa, "Sampler", _EvenWeightedSamplerFactory())
    sample_qa.main(
        [
            "--n",
            "4",
            "--seed",
            "0",
            "--data-path",
            str(tiny_dataset_path),
            "--out-dir",
            str(tmp_out_dir),
        ]
    )
    rows = judge_claims.load_sample(tmp_out_dir / "sample.jsonl")

    out_path = tmp_out_dir / "claims_per_qa.jsonl"
    err_path = tmp_out_dir / "claims_per_qa.errors.jsonl"

    # Pretend the first two rows were already judged on a prior run.
    with out_path.open("w") as f:
        for r in rows[:2]:
            f.write(
                json.dumps(
                    {
                        "cid": r.cid,
                        "qa_index": r.qa_index,
                        "topic": r.topic,
                        "evidence_ids_nonempty": r.evidence_ids_nonempty,
                        "num_evidence_attached": len(r.evidence_attached),
                        "model": "anthropic/claude-sonnet-4.6",
                        "claims": [],
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                        "latency_ms": 0,
                    }
                )
                + "\n"
            )

    done = judge_claims.already_judged(out_path)
    pending = [r for r in rows if (r.cid, r.qa_index) not in done]
    assert len(pending) == 2

    client = fake_openrouter_client([_good_response(), _good_response()])
    client.spend_usd = 0.0
    judge = ClaimJudge(client, PromptBuilder())

    success = await judge_claims.run_judge_pass(
        pending,
        judge,
        client,
        model="anthropic/claude-sonnet-4.6",
        out_path=out_path,
        err_path=err_path,
        concurrency=1,
    )

    assert success == 2
    # out_path now has 4 total: 2 preexisting + 2 new
    all_lines = [line for line in out_path.read_text().splitlines() if line]
    assert len(all_lines) == 4
    # fake client saw exactly 2 calls (not 4)
    assert len(client.calls) == 2
