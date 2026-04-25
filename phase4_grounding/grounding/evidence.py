"""Attach evidence sentences to a sampled Q&A.

Rules (mirrors §Step 1 of PLAN.md):
- If the QA's `evidence_ids` list is non-empty, select only the parent
  `evidence_sentences` whose source `id` is listed, preserving the order given
  in `evidence_ids`. Unknown ids are skipped silently.
- Otherwise attach all `evidence_sentences` for the compound, in their original
  order.

The returned items are renumbered with **display ids** `1..N` so the judge
prompt can label them `[E1]`, `[E2]`, ... and the parser can validate that the
judge's `evidence_id` belongs to `{1..N}`.

This module is pure: no I/O at import, no network.
"""
from __future__ import annotations

from .models import EvidenceItem


class EvidenceAttacher:
    """Pure helper that selects and renumbers evidence for a single QA."""

    @staticmethod
    def attach(qa: dict, compound: dict) -> tuple[EvidenceItem, ...]:
        sentences = compound.get("evidence_sentences") or []
        id_to_sent: dict[int, dict] = {}
        for s in sentences:
            try:
                id_to_sent[int(s["id"])] = s
            except (KeyError, TypeError, ValueError):
                continue

        evidence_ids = qa.get("evidence_ids") or []
        if evidence_ids:
            selected: list[dict] = []
            for eid in evidence_ids:
                try:
                    key = int(eid)
                except (TypeError, ValueError):
                    continue
                s = id_to_sent.get(key)
                if s is not None:
                    selected.append(s)
        else:
            selected = list(sentences)

        attached: list[EvidenceItem] = []
        for display_id, s in enumerate(selected, start=1):
            pmid = s.get("pmid")
            attached.append(
                EvidenceItem(
                    id=display_id,
                    text=s.get("text", ""),
                    pmid=str(pmid) if pmid is not None else None,
                    source=s.get("source"),
                )
            )
        return tuple(attached)
