"""Smoke tests: dataclass construction and tiny_dataset shape."""
from __future__ import annotations

import pytest

from phase4_grounding.grounding.models import (
    LABEL_VALUES,
    ChatResult,
    Claim,
    Compound,
    EvidenceItem,
    JudgedQA,
    SampleRow,
)


def test_claim_label_values_exact():
    assert LABEL_VALUES == ("STATED", "IMPLIED", "UNSUPPORTED", "STRUCTURAL")


def test_dataclasses_are_frozen():
    c = Claim(claim="x", label="STATED", evidence_id=1, rationale="r")
    with pytest.raises(Exception):
        c.label = "IMPLIED"  # type: ignore[misc]


def test_sample_row_construct():
    compound = Compound(cid=1, name="X", smiles="C", molecular_formula="CH4")
    row = SampleRow(
        cid=1,
        qa_index=1,
        topic="mechanism",
        split="train",
        evidence_ids_nonempty=True,
        compound=compound,
        question="Q?",
        phase2_answer="A.",
        evidence_attached=(EvidenceItem(id=1, text="t"),),
    )
    assert row.compound.smiles == "C"
    assert row.evidence_attached[0].id == 1


def test_judged_qa_construct():
    j = JudgedQA(
        cid=1,
        qa_index=1,
        topic="mechanism",
        evidence_ids_nonempty=False,
        num_evidence_attached=0,
        model="m",
        claims=(Claim(claim="x", label="UNSUPPORTED", evidence_id=None, rationale=""),),
        prompt_tokens=10,
        completion_tokens=5,
        latency_ms=42,
    )
    assert j.claims[0].label == "UNSUPPORTED"


def test_chat_result_construct():
    r = ChatResult(text="hi", prompt_tokens=1, completion_tokens=1, latency_ms=1)
    assert r.text == "hi"


def test_tiny_dataset_loads(tiny_dataset_records):
    assert len(tiny_dataset_records) >= 3
    topics = {qa["topic"] for rec in tiny_dataset_records for qa in rec["qa_pairs"]}
    assert {"mechanism", "metabolism", "toxicity", "engineering"} <= topics
    has_nonempty = any(
        qa.get("evidence_ids") for rec in tiny_dataset_records for qa in rec["qa_pairs"]
    )
    has_empty = any(
        not qa.get("evidence_ids") for rec in tiny_dataset_records for qa in rec["qa_pairs"]
    )
    assert has_nonempty and has_empty
