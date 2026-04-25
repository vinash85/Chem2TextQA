"""Aggregate judged claims into headline metrics + breakdowns.

Two views over the same `claims_per_qa.jsonl`:
- ``keep``: STRUCTURAL is its own bucket; the denominator excludes it. The
  headline UNSUPPORTED rate is `UNSUPPORTED / (STATED + IMPLIED + UNSUPPORTED)`.
- ``drop``: STRUCTURAL is collapsed into IMPLIED; everything counted.

`Aggregator(judged_qas).compute(view)` returns a `ViewMetrics`. The reporter
consumes both views to write the dual summary files.
"""
from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Literal

from .models import Claim, JudgedQA, ViewMetrics

_VIEW_LABELS_KEEP: tuple[str, ...] = ("STATED", "IMPLIED", "UNSUPPORTED")
_VIEW_LABELS_DROP: tuple[str, ...] = ("STATED", "IMPLIED", "UNSUPPORTED")
_TOP_N = 20


def wilson_ci(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% CI for a binomial proportion.

    Returns (0.0, 0.0) when total is 0 — the caller decides how to display it.
    """
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
    return (max(0.0, center - half), min(1.0, center + half))


class Aggregator:
    """Compute label rates + breakdowns + per-QA stats over judged Q&A rows."""

    def __init__(self, judged_qas: Iterable[JudgedQA]) -> None:
        self.judged_qas: tuple[JudgedQA, ...] = tuple(judged_qas)

    def compute(self, view: Literal["keep", "drop"]) -> ViewMetrics:
        if view not in ("keep", "drop"):
            raise ValueError(f"view must be 'keep' or 'drop', got {view!r}")

        labels = _VIEW_LABELS_KEEP if view == "keep" else _VIEW_LABELS_DROP

        claims_for_metrics: list[tuple[JudgedQA, Claim, str]] = []
        structural_count = 0
        for qa in self.judged_qas:
            for claim in qa.claims:
                projected = self._project_label(claim.label, view)
                if projected is None:
                    structural_count += 1
                    continue
                claims_for_metrics.append((qa, claim, projected))

        total = len(claims_for_metrics)
        counts = {label: 0 for label in labels}
        for _, _, projected in claims_for_metrics:
            counts[projected] += 1

        rates = {
            label: (counts[label] / total) if total else 0.0 for label in labels
        }
        grounded_rate = rates.get("STATED", 0.0) + rates.get("IMPLIED", 0.0)
        unsupported_rate = rates.get("UNSUPPORTED", 0.0)
        unsupported_ci = wilson_ci(counts.get("UNSUPPORTED", 0), total)

        by_topic = self._breakdown(
            claims_for_metrics, key=lambda qa, _c: qa.topic, labels=labels
        )
        by_evidence = self._breakdown(
            claims_for_metrics,
            key=lambda qa, _c: qa.evidence_ids_nonempty,
            labels=labels,
        )
        by_split = self._breakdown(
            claims_for_metrics, key=lambda qa, _c: qa.split or "(unknown)", labels=labels
        )

        histogram, top_qa = self._per_qa_stats(view)

        return ViewMetrics(
            view=view,
            total_claims=total,
            counts=counts,
            rates=rates,
            grounded_rate=grounded_rate,
            unsupported_rate=unsupported_rate,
            unsupported_ci=unsupported_ci,
            structural_count=structural_count,
            by_topic=by_topic,
            by_evidence_ids_nonempty=by_evidence,
            by_split=by_split,
            per_qa_unsupported_histogram=histogram,
            top_qa_by_unsupported=top_qa,
        )

    @staticmethod
    def _project_label(label: str, view: Literal["keep", "drop"]) -> str | None:
        """Map a raw judge label to the view-specific label.

        Returns None when the claim should be excluded from the denominator
        (the keep view drops STRUCTURAL).
        """
        if label == "STRUCTURAL":
            return None if view == "keep" else "IMPLIED"
        return label

    @staticmethod
    def _breakdown(
        claims_for_metrics: list[tuple[JudgedQA, Claim, str]],
        *,
        key,
        labels: tuple[str, ...],
    ) -> dict:
        """Group claims by `key(qa, claim)` and compute per-group rates + total."""
        buckets: dict[object, dict[str, int]] = {}
        for qa, claim, projected in claims_for_metrics:
            k = key(qa, claim)
            bucket = buckets.setdefault(k, {label: 0 for label in labels})
            bucket[projected] = bucket.get(projected, 0) + 1

        out: dict = {}
        for k, counts in buckets.items():
            total = sum(counts.values())
            entry = {label: counts.get(label, 0) for label in labels}
            entry["total"] = total
            for label in labels:
                entry[f"{label}_rate"] = (counts.get(label, 0) / total) if total else 0.0
            out[k] = entry
        return out

    def _per_qa_stats(
        self, view: Literal["keep", "drop"]
    ) -> tuple[dict[int, int], tuple[dict, ...]]:
        """Histogram of UNSUPPORTED count per Q&A + top-N rows by UNSUPPORTED rate."""
        histogram: dict[int, int] = {}
        rows: list[dict] = []
        for qa in self.judged_qas:
            unsupported = 0
            denom = 0
            for claim in qa.claims:
                projected = self._project_label(claim.label, view)
                if projected is None:
                    continue
                denom += 1
                if projected == "UNSUPPORTED":
                    unsupported += 1
            histogram[unsupported] = histogram.get(unsupported, 0) + 1
            rate = (unsupported / denom) if denom else 0.0
            rows.append(
                {
                    "cid": qa.cid,
                    "qa_index": qa.qa_index,
                    "topic": qa.topic,
                    "split": qa.split,
                    "unsupported": unsupported,
                    "total_claims": denom,
                    "unsupported_rate": rate,
                }
            )

        rows.sort(
            key=lambda r: (r["unsupported_rate"], r["unsupported"]),
            reverse=True,
        )
        return histogram, tuple(rows[:_TOP_N])
