"""Strict parser for the claim-decomposition judge response.

`ClaimParser.parse(raw, attached_ids)` returns a `ParseResult`:
- `ok=True` with a tuple of `Claim` objects if and only if `raw` is valid JSON
  matching the documented schema and every non-null `evidence_id` is one of
  `attached_ids`.
- `ok=False` with a short `error` string otherwise. The caller (judge runner)
  uses the error to decide whether to retry once and, on second failure, log
  the raw response to `claims_per_qa.errors.jsonl`.
"""
from __future__ import annotations

import json

from .models import LABEL_VALUES, Claim, ParseResult

_REQUIRED_FIELDS = ("claim", "label", "evidence_id", "rationale")


class ClaimParser:
    """Strict JSON + schema validator for the judge's response."""

    @staticmethod
    def parse(raw: str | None, attached_ids: set[int]) -> ParseResult:
        if not isinstance(raw, str):
            return ParseResult(
                ok=False,
                error=f"raw response is not a string (got {type(raw).__name__})",
            )
        try:
            payload = json.loads(_strip_fences(raw))
        except json.JSONDecodeError as exc:
            return ParseResult(ok=False, error=f"invalid JSON: {exc.msg}")

        if not isinstance(payload, dict):
            return ParseResult(ok=False, error="root must be a JSON object")
        if "claims" not in payload:
            return ParseResult(ok=False, error="missing 'claims' key")
        claims_raw = payload["claims"]
        if not isinstance(claims_raw, list):
            return ParseResult(ok=False, error="'claims' must be a list")

        claims: list[Claim] = []
        for i, item in enumerate(claims_raw):
            err = _validate_claim_shape(item, i)
            if err is not None:
                return ParseResult(ok=False, error=err)

            label = item["label"]
            if label not in LABEL_VALUES:
                return ParseResult(
                    ok=False,
                    error=f"claim[{i}].label must be one of {LABEL_VALUES}, got {label!r}",
                )

            evidence_id = item["evidence_id"]
            if evidence_id is not None:
                if not isinstance(evidence_id, int) or isinstance(evidence_id, bool):
                    return ParseResult(
                        ok=False,
                        error=f"claim[{i}].evidence_id must be int or null, got {type(evidence_id).__name__}",
                    )
                if evidence_id not in attached_ids:
                    return ParseResult(
                        ok=False,
                        error=(
                            f"claim[{i}].evidence_id={evidence_id} not in attached "
                            f"ids {sorted(attached_ids)}"
                        ),
                    )

            claims.append(
                Claim(
                    claim=item["claim"],
                    label=label,
                    evidence_id=evidence_id,
                    rationale=item["rationale"],
                )
            )

        return ParseResult(ok=True, claims=tuple(claims))


def _strip_fences(raw: str) -> str:
    # Some models (notably gemini-2.5-pro) wrap JSON in ```json ... ``` despite
    # being told not to. Strip a leading fence line and a trailing fence so the
    # JSON body is what hits json.loads.
    s = raw.strip()
    if s.startswith("```"):
        nl = s.find("\n")
        s = s[nl + 1 :] if nl != -1 else s[3:]
        s = s.rstrip()
        if s.endswith("```"):
            s = s[:-3].rstrip()
    return s


def _validate_claim_shape(item: object, i: int) -> str | None:
    if not isinstance(item, dict):
        return f"claim[{i}] must be a JSON object"
    for f in _REQUIRED_FIELDS:
        if f not in item:
            return f"claim[{i}] missing field {f!r}"
    if not isinstance(item["claim"], str):
        return f"claim[{i}].claim must be a string"
    if item["rationale"] is not None and not isinstance(item["rationale"], str):
        return f"claim[{i}].rationale must be a string or null"
    if not isinstance(item["label"], str):
        return f"claim[{i}].label must be a string"
    return None
