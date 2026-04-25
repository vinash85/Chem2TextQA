"""Tests for grounding.aggregator.Aggregator and the wilson_ci helper."""
from __future__ import annotations

import math

import pytest

from phase4_grounding.grounding.aggregator import Aggregator, wilson_ci
from phase4_grounding.grounding.models import Claim, JudgedQA


def _qa(
    cid: int,
    *,
    topic: str = "mechanism",
    split: str = "train",
    evidence_ids_nonempty: bool = True,
    labels: list[str],
) -> JudgedQA:
    claims = tuple(
        Claim(claim=f"c{i}", label=lbl, evidence_id=None, rationale="r")
        for i, lbl in enumerate(labels)
    )
    return JudgedQA(
        cid=cid,
        qa_index=1,
        topic=topic,
        evidence_ids_nonempty=evidence_ids_nonempty,
        num_evidence_attached=2,
        model="m",
        claims=claims,
        prompt_tokens=10,
        completion_tokens=10,
        latency_ms=10,
        split=split,
    )


def test_wilson_ci_known_reference():
    # 50/100 → centre 0.5, 95% CI ≈ (0.404, 0.596)
    lo, hi = wilson_ci(50, 100)
    assert math.isclose(lo, 0.4038, abs_tol=1e-3)
    assert math.isclose(hi, 0.5962, abs_tol=1e-3)


def test_wilson_ci_zero_total_returns_zero_zero():
    assert wilson_ci(0, 0) == (0.0, 0.0)


def test_wilson_ci_zero_successes():
    lo, hi = wilson_ci(0, 100)
    assert lo == 0.0
    assert hi > 0.0


def test_keep_view_excludes_structural_from_denominator():
    qas = [
        _qa(1, labels=["STATED", "STRUCTURAL", "UNSUPPORTED"]),
        _qa(2, labels=["IMPLIED", "STRUCTURAL"]),
    ]
    metrics = Aggregator(qas).compute("keep")
    # 2 STRUCTURAL excluded from denominator (3 remaining)
    assert metrics.total_claims == 3
    assert metrics.structural_count == 2
    assert metrics.counts == {"STATED": 1, "IMPLIED": 1, "UNSUPPORTED": 1}
    assert metrics.unsupported_rate == pytest.approx(1 / 3)
    assert metrics.grounded_rate == pytest.approx(2 / 3)


def test_drop_view_collapses_structural_into_implied():
    qas = [
        _qa(1, labels=["STATED", "STRUCTURAL", "UNSUPPORTED"]),
        _qa(2, labels=["IMPLIED", "STRUCTURAL"]),
    ]
    metrics = Aggregator(qas).compute("drop")
    # all 5 claims counted; STRUCTURAL → IMPLIED
    assert metrics.total_claims == 5
    assert metrics.counts["IMPLIED"] == 3  # 1 IMPLIED + 2 STRUCTURAL
    assert metrics.counts["STATED"] == 1
    assert metrics.counts["UNSUPPORTED"] == 1
    assert metrics.unsupported_rate == pytest.approx(1 / 5)


def test_unsupported_ci_matches_wilson():
    qas = [_qa(1, labels=["UNSUPPORTED"] * 25 + ["STATED"] * 75)]
    metrics = Aggregator(qas).compute("keep")
    expected = wilson_ci(25, 100)
    assert metrics.unsupported_ci == pytest.approx(expected)


def test_by_topic_breakdown_sums_to_total():
    qas = [
        _qa(1, topic="mechanism", labels=["STATED", "STATED"]),
        _qa(2, topic="toxicity", labels=["UNSUPPORTED"]),
        _qa(3, topic="mechanism", labels=["IMPLIED"]),
    ]
    metrics = Aggregator(qas).compute("keep")
    assert metrics.by_topic["mechanism"]["total"] == 3
    assert metrics.by_topic["toxicity"]["total"] == 1
    sum_total = sum(v["total"] for v in metrics.by_topic.values())
    assert sum_total == metrics.total_claims


def test_by_evidence_ids_nonempty_breakdown():
    qas = [
        _qa(1, evidence_ids_nonempty=True, labels=["STATED"]),
        _qa(2, evidence_ids_nonempty=False, labels=["UNSUPPORTED", "UNSUPPORTED"]),
    ]
    metrics = Aggregator(qas).compute("keep")
    assert metrics.by_evidence_ids_nonempty[True]["total"] == 1
    assert metrics.by_evidence_ids_nonempty[False]["total"] == 2
    assert metrics.by_evidence_ids_nonempty[False]["UNSUPPORTED"] == 2


def test_by_split_breakdown():
    qas = [
        _qa(1, split="train", labels=["STATED"]),
        _qa(2, split="val", labels=["UNSUPPORTED"]),
        _qa(3, split="test", labels=["IMPLIED"]),
    ]
    metrics = Aggregator(qas).compute("keep")
    assert set(metrics.by_split) == {"train", "val", "test"}


def test_per_qa_unsupported_histogram():
    qas = [
        _qa(1, labels=["STATED"]),  # 0 UNSUPPORTED
        _qa(2, labels=["UNSUPPORTED"]),  # 1
        _qa(3, labels=["UNSUPPORTED", "UNSUPPORTED"]),  # 2
        _qa(4, labels=["UNSUPPORTED"]),  # 1
    ]
    metrics = Aggregator(qas).compute("keep")
    assert metrics.per_qa_unsupported_histogram == {0: 1, 1: 2, 2: 1}


def test_top_qa_sorted_by_unsupported_rate():
    qas = [
        _qa(1, labels=["STATED", "STATED"]),  # rate 0
        _qa(2, labels=["UNSUPPORTED"]),  # rate 1.0
        _qa(3, labels=["UNSUPPORTED", "STATED"]),  # rate 0.5
    ]
    metrics = Aggregator(qas).compute("keep")
    top = metrics.top_qa_by_unsupported
    assert top[0]["cid"] == 2
    assert top[1]["cid"] == 3


def test_invalid_view_raises():
    with pytest.raises(ValueError):
        Aggregator([]).compute("bogus")  # type: ignore[arg-type]


def test_empty_input_yields_zero_metrics():
    metrics = Aggregator([]).compute("keep")
    assert metrics.total_claims == 0
    assert metrics.unsupported_rate == 0.0
    assert metrics.unsupported_ci == (0.0, 0.0)
