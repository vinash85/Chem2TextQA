"""Tests for grounding.sampling.Sampler."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from phase4_grounding.grounding.sampling import (
    DEFAULT_TOPIC_WEIGHTS,
    HEADLINE_TOPICS,
    Sampler,
)


def test_allocate_sums_to_n_for_various_sizes(tiny_dataset_path):
    s = Sampler(tiny_dataset_path)
    for n in (1, 6, 10, 17, 300, 600):
        alloc = s._allocate(n)
        assert sum(alloc.values()) == n
        assert set(alloc) == set(DEFAULT_TOPIC_WEIGHTS)


def test_allocate_rejects_nonpositive(tiny_dataset_path):
    s = Sampler(tiny_dataset_path)
    with pytest.raises(ValueError):
        s._allocate(0)
    with pytest.raises(ValueError):
        s._allocate(-3)


def test_weights_must_sum_to_one(tiny_dataset_path):
    with pytest.raises(ValueError):
        Sampler(tiny_dataset_path, topic_weights={"mechanism": 0.5})


def test_topic_key_collapses_non_headline(tiny_dataset_path):
    s = Sampler(tiny_dataset_path)
    for t in HEADLINE_TOPICS:
        assert s._topic_key(t) == t
    assert s._topic_key("adme") == "_other"
    assert s._topic_key("design_levers") == "_other"
    assert s._topic_key("Therapeutic-Use") == "therapeutic_use"


def test_index_qa_only_functional(tiny_dataset_path):
    s = Sampler(tiny_dataset_path)
    idx = s._index_qa()
    # tiny_dataset has mechanism (x2), metabolism (x2), engineering (x2), toxicity (x2)
    assert len(idx["mechanism"]) == 2
    assert len(idx["metabolism"]) == 2
    assert len(idx["engineering"]) == 2
    assert len(idx["toxicity"]) == 2
    # therapeutic_use absent in tiny_dataset
    assert idx["therapeutic_use"] == []


def test_sample_returns_exact_n_when_pools_sufficient(tmp_path: Path):
    """Build a synthetic dataset large enough to satisfy any allocation."""
    records = []
    cid = 1
    topics_to_seed = ["mechanism", "engineering", "metabolism", "toxicity", "therapeutic_use", "adme"]
    for t in topics_to_seed:
        for evidence_branch in (True, False):
            for _ in range(20):  # 20 of each (topic, evidence-branch)
                evidence_ids = [1] if evidence_branch else []
                records.append({
                    "cid": cid,
                    "split": "train",
                    "name": f"C{cid}",
                    "smiles": "C",
                    "molecular_formula": "CH4",
                    "evidence_sentences": [{"id": 1, "text": "evidence", "pmid": "1", "source": "abstract"}],
                    "qa_pairs": [{
                        "qa_index": 1,
                        "topic": t,
                        "question": f"Q for {t}?",
                        "phase1_answer": "A1",
                        "phase2_answer": "A2",
                        "verdict": "agree",
                        "judge_reasoning": "r",
                        "evidence_ids": evidence_ids,
                    }],
                })
                cid += 1

    path = tmp_path / "ds.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    s = Sampler(path, seed=42)
    rows = s.sample(60)
    assert len(rows) == 60


def test_sample_is_deterministic_with_seed(tmp_path: Path):
    records = []
    for i in range(50):
        records.append({
            "cid": i + 1,
            "split": "train",
            "name": f"C{i}",
            "smiles": "C",
            "molecular_formula": "CH4",
            "evidence_sentences": [{"id": 1, "text": "e", "pmid": "1", "source": "abstract"}],
            "qa_pairs": [{
                "qa_index": 1,
                "topic": "mechanism",
                "question": "Q?",
                "phase1_answer": "a",
                "phase2_answer": "a",
                "verdict": "agree",
                "judge_reasoning": "r",
                "evidence_ids": [1] if i % 2 == 0 else [],
            }],
        })
    path = tmp_path / "ds.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")

    rows_a = Sampler(path, seed=7).sample(8)
    rows_b = Sampler(path, seed=7).sample(8)
    rows_c = Sampler(path, seed=8).sample(8)

    keys_a = [(r.cid, r.qa_index) for r in rows_a]
    keys_b = [(r.cid, r.qa_index) for r in rows_b]
    keys_c = [(r.cid, r.qa_index) for r in rows_c]
    assert keys_a == keys_b
    assert keys_a != keys_c


def test_sample_handles_exhausted_strata_gracefully(tiny_dataset_path):
    """tiny_dataset has only 4 functional topics with 2 QA each and no
    therapeutic_use or _other. Sampling more than the pool size should fall back
    instead of raising."""
    s = Sampler(tiny_dataset_path, seed=0)
    # request 4 to keep the math simple; allocation will request slots from
    # therapeutic_use / _other strata that are empty in tiny_dataset
    rows = s.sample(4)
    # we should still get at most as many rows as functional QA in the dataset (8)
    assert 0 < len(rows) <= 8
    # and each returned row must be a functional topic
    from phase4_grounding.grounding.topic_bucket import bucket_topic
    for r in rows:
        assert bucket_topic(r.topic) == "functional"


def test_evidence_branch_split_50_50_when_both_sides_have_supply(tmp_path: Path):
    """Within a single topic, half of the slot should come from each evidence branch."""
    records = []
    cid = 1
    for evidence_branch in (True, False):
        for _ in range(10):
            records.append({
                "cid": cid,
                "split": "train",
                "name": f"C{cid}",
                "smiles": "C",
                "molecular_formula": "CH4",
                "evidence_sentences": [{"id": 1, "text": "e", "pmid": "1", "source": "abstract"}],
                "qa_pairs": [{
                    "qa_index": 1,
                    "topic": "mechanism",
                    "question": "Q?",
                    "phase1_answer": "a",
                    "phase2_answer": "a",
                    "verdict": "agree",
                    "judge_reasoning": "r",
                    "evidence_ids": [1] if evidence_branch else [],
                }],
            })
            cid += 1
    path = tmp_path / "ds.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")

    # Use a custom weight: 100% mechanism, so allocation == n
    s = Sampler(
        path,
        seed=0,
        topic_weights={
            "mechanism": 1.0,
            "engineering": 0.0,
            "metabolism": 0.0,
            "toxicity": 0.0,
            "therapeutic_use": 0.0,
            "_other": 0.0,
        },
    )
    rows = s.sample(8)
    nonempty = sum(1 for r in rows if r.evidence_ids_nonempty)
    empty = len(rows) - nonempty
    assert nonempty == 4
    assert empty == 4
