"""Tests for grounding.evidence.EvidenceAttacher."""
from __future__ import annotations

from phase4_grounding.grounding.evidence import EvidenceAttacher
from phase4_grounding.grounding.models import EvidenceItem


def _compound(*sentences: dict) -> dict:
    return {"evidence_sentences": list(sentences)}


def _qa(evidence_ids: list[int] | None = None) -> dict:
    return {"evidence_ids": list(evidence_ids) if evidence_ids is not None else []}


def test_attaches_only_listed_ids_when_evidence_ids_nonempty():
    compound = _compound(
        {"id": 1, "text": "alpha", "pmid": "111", "source": "abstract"},
        {"id": 2, "text": "beta", "pmid": "222", "source": "abstract"},
        {"id": 3, "text": "gamma", "pmid": "333", "source": "abstract"},
    )
    qa = _qa([1, 3])
    attached = EvidenceAttacher.attach(qa, compound)
    assert [e.text for e in attached] == ["alpha", "gamma"]


def test_attaches_all_when_evidence_ids_empty():
    compound = _compound(
        {"id": 1, "text": "alpha", "pmid": "111", "source": "abstract"},
        {"id": 2, "text": "beta", "pmid": "222", "source": "abstract"},
    )
    qa = _qa([])
    attached = EvidenceAttacher.attach(qa, compound)
    assert [e.text for e in attached] == ["alpha", "beta"]


def test_attaches_all_when_evidence_ids_missing():
    compound = _compound({"id": 1, "text": "alpha", "pmid": "111", "source": "abstract"})
    qa: dict = {}  # no evidence_ids key at all
    attached = EvidenceAttacher.attach(qa, compound)
    assert len(attached) == 1
    assert attached[0].text == "alpha"


def test_display_ids_are_sequential_starting_at_one():
    compound = _compound(
        {"id": 7, "text": "alpha", "pmid": "p", "source": "abstract"},
        {"id": 9, "text": "beta", "pmid": "p", "source": "abstract"},
        {"id": 11, "text": "gamma", "pmid": "p", "source": "abstract"},
    )
    # Non-empty branch: display ids must be 1..N regardless of source ids.
    attached = EvidenceAttacher.attach(_qa([9, 11]), compound)
    assert [e.id for e in attached] == [1, 2]
    # Empty branch: same renumbering rule.
    attached_all = EvidenceAttacher.attach(_qa([]), compound)
    assert [e.id for e in attached_all] == [1, 2, 3]


def test_preserves_order_of_evidence_ids_list():
    compound = _compound(
        {"id": 1, "text": "alpha", "pmid": "p", "source": "abstract"},
        {"id": 2, "text": "beta", "pmid": "p", "source": "abstract"},
        {"id": 3, "text": "gamma", "pmid": "p", "source": "abstract"},
    )
    # listed in 3, 1, 2 order — output must follow that order, not source order.
    attached = EvidenceAttacher.attach(_qa([3, 1, 2]), compound)
    assert [e.text for e in attached] == ["gamma", "alpha", "beta"]
    assert [e.id for e in attached] == [1, 2, 3]


def test_unknown_evidence_ids_are_skipped():
    compound = _compound(
        {"id": 1, "text": "alpha", "pmid": "p", "source": "abstract"},
        {"id": 2, "text": "beta", "pmid": "p", "source": "abstract"},
    )
    attached = EvidenceAttacher.attach(_qa([1, 99, 2]), compound)
    assert [e.text for e in attached] == ["alpha", "beta"]
    assert [e.id for e in attached] == [1, 2]


def test_returns_empty_when_no_sentences_at_all():
    attached = EvidenceAttacher.attach(_qa([]), _compound())
    assert attached == ()


def test_returns_empty_when_listed_ids_all_unknown():
    compound = _compound({"id": 1, "text": "alpha", "pmid": "p", "source": "abstract"})
    attached = EvidenceAttacher.attach(_qa([42, 43]), compound)
    assert attached == ()


def test_pmid_and_source_are_carried_through():
    compound = _compound(
        {"id": 1, "text": "alpha", "pmid": "12345", "source": "fulltext"},
    )
    attached = EvidenceAttacher.attach(_qa([1]), compound)
    assert attached[0].pmid == "12345"
    assert attached[0].source == "fulltext"


def test_pmid_none_when_missing():
    compound = _compound({"id": 1, "text": "alpha", "source": "abstract"})
    attached = EvidenceAttacher.attach(_qa([1]), compound)
    assert attached[0].pmid is None
    assert attached[0].source == "abstract"


def test_returned_items_are_evidence_item_instances():
    compound = _compound({"id": 1, "text": "alpha", "pmid": "p", "source": "abstract"})
    attached = EvidenceAttacher.attach(_qa([1]), compound)
    assert all(isinstance(e, EvidenceItem) for e in attached)


def test_works_with_tiny_dataset_records(tiny_dataset_records):
    """Smoke test against the hand-crafted tiny_dataset.jsonl fixture."""
    aspirin = tiny_dataset_records[0]
    assert aspirin["name"] == "Aspirin"

    # qa_index 1 (mechanism) cites evidence_ids [1, 2]
    qa1 = aspirin["qa_pairs"][0]
    attached = EvidenceAttacher.attach(qa1, aspirin)
    assert len(attached) == 2
    assert [e.id for e in attached] == [1, 2]
    assert "irreversibly acetylates" in attached[0].text

    # qa_index 3 (engineering) has empty evidence_ids → all 3 sentences
    qa3 = aspirin["qa_pairs"][2]
    attached_all = EvidenceAttacher.attach(qa3, aspirin)
    assert len(attached_all) == 3
    assert [e.id for e in attached_all] == [1, 2, 3]
