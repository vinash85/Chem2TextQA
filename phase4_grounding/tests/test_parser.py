"""Tests for grounding.parser.ClaimParser."""
from __future__ import annotations

import json

import pytest

from phase4_grounding.grounding.models import LABEL_VALUES
from phase4_grounding.grounding.parser import ClaimParser


def _wrap(claims: list[dict]) -> str:
    return json.dumps({"claims": claims})


def test_parses_well_formed_json_with_all_four_labels():
    payload = _wrap(
        [
            {"claim": "stated one", "label": "STATED", "evidence_id": 1, "rationale": "directly cited"},
            {"claim": "implied one", "label": "IMPLIED", "evidence_id": 2, "rationale": "one step"},
            {"claim": "structural one", "label": "STRUCTURAL", "evidence_id": None, "rationale": "from SMILES"},
            {"claim": "unsupported one", "label": "UNSUPPORTED", "evidence_id": None, "rationale": "no support"},
        ]
    )
    result = ClaimParser.parse(payload, attached_ids={1, 2})
    assert result.ok, result.error
    labels = [c.label for c in result.claims]
    assert labels == ["STATED", "IMPLIED", "STRUCTURAL", "UNSUPPORTED"]
    # all four allowed labels are preserved by name
    assert set(labels) <= set(LABEL_VALUES)


def test_rejects_malformed_json():
    result = ClaimParser.parse("{not json", attached_ids={1})
    assert not result.ok
    assert "invalid JSON" in (result.error or "")


def test_rejects_non_object_root():
    result = ClaimParser.parse("[]", attached_ids={1})
    assert not result.ok
    assert "object" in (result.error or "")


def test_rejects_missing_claims_key():
    result = ClaimParser.parse('{"foo":1}', attached_ids={1})
    assert not result.ok
    assert "claims" in (result.error or "")


def test_rejects_claims_not_a_list():
    result = ClaimParser.parse('{"claims":"oops"}', attached_ids={1})
    assert not result.ok
    assert "list" in (result.error or "")


def test_rejects_unknown_label():
    payload = _wrap(
        [{"claim": "x", "label": "MAYBE", "evidence_id": 1, "rationale": "r"}]
    )
    result = ClaimParser.parse(payload, attached_ids={1})
    assert not result.ok
    assert "label" in (result.error or "")


def test_rejects_evidence_id_not_in_attached_set():
    payload = _wrap(
        [{"claim": "x", "label": "STATED", "evidence_id": 99, "rationale": "r"}]
    )
    result = ClaimParser.parse(payload, attached_ids={1, 2})
    assert not result.ok
    assert "evidence_id" in (result.error or "")
    assert "99" in (result.error or "")


def test_rejects_evidence_id_wrong_type():
    payload = _wrap(
        [{"claim": "x", "label": "STATED", "evidence_id": "1", "rationale": "r"}]
    )
    result = ClaimParser.parse(payload, attached_ids={1})
    assert not result.ok
    assert "evidence_id" in (result.error or "")


def test_rejects_boolean_evidence_id():
    """JSON `true` would silently become Python True, which `isinstance(_, int)`
    accepts. The parser must guard against this corner."""
    payload = _wrap(
        [{"claim": "x", "label": "STATED", "evidence_id": True, "rationale": "r"}]
    )
    result = ClaimParser.parse(payload, attached_ids={1})
    assert not result.ok


def test_rejects_missing_required_field():
    payload = _wrap([{"claim": "x", "label": "STATED", "evidence_id": 1}])
    result = ClaimParser.parse(payload, attached_ids={1})
    assert not result.ok
    assert "rationale" in (result.error or "")


def test_rejects_non_string_claim():
    payload = _wrap(
        [{"claim": 123, "label": "STATED", "evidence_id": 1, "rationale": "r"}]
    )
    result = ClaimParser.parse(payload, attached_ids={1})
    assert not result.ok


def test_accepts_null_evidence_id_for_unsupported():
    payload = _wrap(
        [{"claim": "x", "label": "UNSUPPORTED", "evidence_id": None, "rationale": "r"}]
    )
    result = ClaimParser.parse(payload, attached_ids={1, 2})
    assert result.ok
    assert result.claims[0].evidence_id is None


def test_accepts_null_evidence_id_for_structural():
    payload = _wrap(
        [{"claim": "x", "label": "STRUCTURAL", "evidence_id": None, "rationale": "r"}]
    )
    result = ClaimParser.parse(payload, attached_ids={1, 2})
    assert result.ok


def test_accepts_null_rationale():
    payload = _wrap(
        [
            {"claim": "x", "label": "STRUCTURAL", "evidence_id": None, "rationale": None},
            {"claim": "y", "label": "UNSUPPORTED", "evidence_id": None, "rationale": None},
        ]
    )
    result = ClaimParser.parse(payload, attached_ids={1, 2})
    assert result.ok
    assert result.claims[0].rationale is None
    assert result.claims[1].rationale is None


def test_handles_none_raw_response():
    # OpenRouter occasionally returns choices[0].message.content = null
    # (refusal, truncation, empty tool-call). Must surface as a clean parse
    # error so the judge's retry/error path takes over instead of crashing.
    result = ClaimParser.parse(None, attached_ids={1})
    assert not result.ok
    assert "not a string" in (result.error or "")


def test_strips_markdown_json_fence():
    payload = (
        '```json\n'
        + _wrap([{"claim": "x", "label": "STATED", "evidence_id": 1, "rationale": "r"}])
        + '\n```'
    )
    result = ClaimParser.parse(payload, attached_ids={1})
    assert result.ok
    assert len(result.claims) == 1


def test_strips_bare_markdown_fence():
    payload = (
        '```\n'
        + _wrap([{"claim": "x", "label": "STATED", "evidence_id": 1, "rationale": "r"}])
        + '\n```'
    )
    result = ClaimParser.parse(payload, attached_ids={1})
    assert result.ok


def test_strips_fence_with_trailing_whitespace():
    payload = (
        '   ```json\n'
        + _wrap([{"claim": "x", "label": "STATED", "evidence_id": 1, "rationale": "r"}])
        + '\n```   \n'
    )
    result = ClaimParser.parse(payload, attached_ids={1})
    assert result.ok


def test_rejects_non_string_non_null_rationale():
    payload = _wrap(
        [{"claim": "x", "label": "STATED", "evidence_id": 1, "rationale": 42}]
    )
    result = ClaimParser.parse(payload, attached_ids={1})
    assert not result.ok
    assert "rationale" in (result.error or "")


def test_empty_claims_list_is_valid():
    """A judge that decomposed nothing returns an empty list — not an error."""
    result = ClaimParser.parse('{"claims":[]}', attached_ids={1})
    assert result.ok
    assert result.claims == ()


def test_attached_ids_can_be_empty_when_all_evidence_id_null():
    """If no evidence was attached and the judge correctly emitted only null
    evidence_id values, parsing must still succeed."""
    payload = _wrap(
        [
            {"claim": "a", "label": "STRUCTURAL", "evidence_id": None, "rationale": "r"},
            {"claim": "b", "label": "UNSUPPORTED", "evidence_id": None, "rationale": "r"},
        ]
    )
    result = ClaimParser.parse(payload, attached_ids=set())
    assert result.ok
    assert len(result.claims) == 2


def test_rejects_when_attached_ids_empty_but_evidence_id_set():
    payload = _wrap(
        [{"claim": "x", "label": "STATED", "evidence_id": 1, "rationale": "r"}]
    )
    result = ClaimParser.parse(payload, attached_ids=set())
    assert not result.ok


def test_rejects_claim_item_not_object():
    payload = '{"claims":[1]}'
    result = ClaimParser.parse(payload, attached_ids={1})
    assert not result.ok
    assert "object" in (result.error or "")
