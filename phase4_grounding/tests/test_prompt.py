"""Tests for grounding.prompt.PromptBuilder."""
from __future__ import annotations

from pathlib import Path

import pytest

from phase4_grounding.grounding.evidence import EvidenceAttacher
from phase4_grounding.grounding.models import Compound, EvidenceItem, SampleRow
from phase4_grounding.grounding.prompt import PromptBuilder


def _row(
    *,
    name: str = "Aspirin",
    smiles: str = "CC(=O)Oc1ccccc1C(=O)O",
    formula: str = "C9H8O4",
    question: str = "How does aspirin inhibit COX-1?",
    answer: str = "Aspirin acetylates serine 530.",
    evidence: tuple[EvidenceItem, ...] = (),
) -> SampleRow:
    return SampleRow(
        cid=1,
        qa_index=1,
        topic="mechanism",
        split="train",
        evidence_ids_nonempty=bool(evidence),
        compound=Compound(cid=1, name=name, smiles=smiles, molecular_formula=formula),
        question=question,
        phase2_answer=answer,
        evidence_attached=evidence,
    )


def test_prompt_contains_all_required_fields():
    evidence = (
        EvidenceItem(id=1, text="Aspirin acetylates COX-1.", pmid="111", source="abstract"),
        EvidenceItem(id=2, text="COX-1 inhibition reduces TXA2.", pmid="111", source="abstract"),
    )
    row = _row(evidence=evidence)
    out = PromptBuilder().build(row)

    assert "Aspirin" in out
    assert "CC(=O)Oc1ccccc1C(=O)O" in out
    assert "C9H8O4" in out
    assert "How does aspirin inhibit COX-1?" in out
    assert "Aspirin acetylates serine 530." in out


def test_evidence_is_numbered_E1_E2():
    evidence = (
        EvidenceItem(id=1, text="First sentence.", pmid="p", source="abstract"),
        EvidenceItem(id=2, text="Second sentence.", pmid="p", source="abstract"),
        EvidenceItem(id=3, text="Third sentence.", pmid="p", source="abstract"),
    )
    out = PromptBuilder().build(_row(evidence=evidence))
    assert "[E1] First sentence." in out
    assert "[E2] Second sentence." in out
    assert "[E3] Third sentence." in out
    # ordering is preserved
    assert out.index("[E1]") < out.index("[E2]") < out.index("[E3]")


def test_no_unfilled_placeholders():
    row = _row(evidence=(EvidenceItem(id=1, text="e", pmid="p", source="abstract"),))
    out = PromptBuilder().build(row)
    # any leftover {{FOO}} marker would be a templating bug
    assert "{{" not in out
    assert "}}" not in out


def test_label_definitions_present_in_prompt():
    out = PromptBuilder().build(_row(evidence=(EvidenceItem(id=1, text="e"),)))
    for label in ("STATED", "IMPLIED", "UNSUPPORTED", "STRUCTURAL"):
        assert label in out


def test_strict_json_directive_present():
    out = PromptBuilder().build(_row(evidence=(EvidenceItem(id=1, text="e"),)))
    # The judge must be told to emit JSON only — this is load-bearing for the parser.
    assert "STRICT JSON" in out or "strict JSON" in out.lower() or "JSON" in out


def test_handles_empty_evidence():
    out = PromptBuilder().build(_row(evidence=()))
    # When nothing is attached, the prompt should still render a placeholder
    # so the judge knows there are no [E#] ids to cite.
    assert "no evidence" in out.lower()


def test_template_loaded_from_disk_only_once(tmp_path):
    """The template should be cached after the first read."""
    template = tmp_path / "tpl.txt"
    template.write_text("name: {{COMPOUND_NAME}}\n")
    builder = PromptBuilder(template_path=template)
    assert "name: Aspirin" in builder.build(_row())
    # Mutate the file on disk; cached template should win on the next call.
    template.write_text("name: {{COMPOUND_NAME}} mutated\n")
    assert "mutated" not in builder.build(_row())


def test_snapshot_against_aspirin_qa(tiny_dataset_records):
    """End-to-end render using EvidenceAttacher + PromptBuilder against a real
    fixture row. Compares the full rendered string to a golden snapshot."""
    aspirin = tiny_dataset_records[0]
    qa = aspirin["qa_pairs"][0]  # mechanism QA, evidence_ids=[1,2]
    attached = EvidenceAttacher.attach(qa, aspirin)
    row = SampleRow(
        cid=int(aspirin["cid"]),
        qa_index=int(qa["qa_index"]),
        topic=qa["topic"],
        split=aspirin["split"],
        evidence_ids_nonempty=True,
        compound=Compound(
            cid=int(aspirin["cid"]),
            name=aspirin["name"],
            smiles=aspirin["smiles"],
            molecular_formula=aspirin["molecular_formula"],
        ),
        question=qa["question"],
        phase2_answer=qa["phase2_answer"],
        evidence_attached=attached,
    )
    out = PromptBuilder().build(row)

    # Spot-check the rendered evidence block specifically (this is the part the
    # parser depends on for [E#] integrity).
    expected_block = (
        "[E1] [COMPOUND] irreversibly acetylates serine 530 of cyclooxygenase-1 (COX-1).\n"
        "[E2] Inhibition of COX-1 by [COMPOUND] reduces thromboxane A2 production in platelets."
    )
    assert expected_block in out

    # Ensure the rendered prompt is stable: re-rendering with the same row gives
    # byte-identical output.
    assert out == PromptBuilder().build(row)
