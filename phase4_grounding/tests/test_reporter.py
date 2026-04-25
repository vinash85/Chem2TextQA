"""Tests for grounding.reporter.Reporter."""
from __future__ import annotations

from pathlib import Path

import pytest

from phase4_grounding.grounding.aggregator import Aggregator
from phase4_grounding.grounding.models import Claim, JudgedQA
from phase4_grounding.grounding.reporter import Reporter


def _qa(cid: int, labels: list[str], *, topic: str = "mechanism") -> JudgedQA:
    return JudgedQA(
        cid=cid,
        qa_index=1,
        topic=topic,
        evidence_ids_nonempty=True,
        num_evidence_attached=1,
        model="m",
        claims=tuple(
            Claim(claim=f"c{i}", label=lbl, evidence_id=None, rationale="r")
            for i, lbl in enumerate(labels)
        ),
        prompt_tokens=1,
        completion_tokens=1,
        latency_ms=1,
        split="train",
    )


@pytest.fixture
def sample_metrics():
    qas = [
        _qa(1, ["STATED", "STATED", "UNSUPPORTED"]),
        _qa(2, ["IMPLIED", "STRUCTURAL"]),
        _qa(3, ["UNSUPPORTED"]),
    ]
    agg = Aggregator(qas)
    return agg.compute("keep"), agg.compute("drop"), qas


def test_writes_both_summary_files(sample_metrics, tmp_out_dir: Path):
    keep, drop, qas = sample_metrics
    reporter = Reporter(keep, drop, qas)
    keep_path, drop_path = reporter.write(tmp_out_dir)
    assert keep_path.exists()
    assert drop_path.exists()
    assert keep_path.name == "grounding_summary_keep_structural.md"
    assert drop_path.name == "grounding_summary_drop_structural.md"


def test_each_summary_cross_links_the_other(sample_metrics, tmp_out_dir: Path):
    keep, drop, qas = sample_metrics
    keep_path, drop_path = Reporter(keep, drop, qas).write(tmp_out_dir)
    assert "grounding_summary_drop_structural.md" in keep_path.read_text()
    assert "grounding_summary_keep_structural.md" in drop_path.read_text()


def test_decision_string_above_20pct(tmp_out_dir: Path):
    qas = [_qa(1, ["UNSUPPORTED"] * 30 + ["STATED"] * 70)]
    agg = Aggregator(qas)
    reporter = Reporter(agg.compute("keep"), agg.compute("drop"), qas)
    keep_path, _ = reporter.write(tmp_out_dir)
    text = keep_path.read_text()
    assert "NARROW" in text
    assert "30.0%" in text or "30.00%" in text


def test_decision_string_below_10pct(tmp_out_dir: Path):
    qas = [_qa(1, ["UNSUPPORTED"] * 5 + ["STATED"] * 95)]
    agg = Aggregator(qas)
    reporter = Reporter(agg.compute("keep"), agg.compute("drop"), qas)
    keep_path, _ = reporter.write(tmp_out_dir)
    text = keep_path.read_text()
    assert "WELL-BEHAVED" in text


def test_decision_string_in_caveat_band(tmp_out_dir: Path):
    qas = [_qa(1, ["UNSUPPORTED"] * 15 + ["STATED"] * 85)]
    agg = Aggregator(qas)
    reporter = Reporter(agg.compute("keep"), agg.compute("drop"), qas)
    keep_path, _ = reporter.write(tmp_out_dir)
    text = keep_path.read_text()
    assert "CAVEAT" in text


def test_keep_view_mentions_structural_count(sample_metrics, tmp_out_dir: Path):
    keep, drop, qas = sample_metrics
    keep_path, _ = Reporter(keep, drop, qas).write(tmp_out_dir)
    text = keep_path.read_text()
    assert "STRUCTURAL claims" in text


def test_rejects_swapped_views(sample_metrics):
    keep, drop, qas = sample_metrics
    # Pass them swapped — should raise.
    with pytest.raises(ValueError):
        Reporter(metrics_keep=drop, metrics_drop=keep, judged_qas=qas)


def test_summary_includes_topic_breakdown(tmp_out_dir: Path):
    qas = [
        _qa(1, ["STATED"], topic="mechanism"),
        _qa(2, ["UNSUPPORTED"], topic="toxicity"),
    ]
    agg = Aggregator(qas)
    reporter = Reporter(agg.compute("keep"), agg.compute("drop"), qas)
    keep_path, _ = reporter.write(tmp_out_dir)
    text = keep_path.read_text()
    assert "By topic" in text
    assert "mechanism" in text
    assert "toxicity" in text
