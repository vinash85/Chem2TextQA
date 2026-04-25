"""Stratified sampling of functional Q&A pairs from the gold dataset.

The sampler:
- Filters QA where `bucket_topic(topic) == 'functional'`.
- Allocates the requested N across topic strata using a fixed weighting that
  emphasizes the four headline topics (mechanism, engineering, metabolism, toxicity)
  plus therapeutic_use, with all remaining functional topics in an "other" bucket.
- Within each topic, splits 50/50 between QA with non-empty `evidence_ids` and
  QA with empty `evidence_ids`. Falls back to the available pool when one side
  is exhausted, preserving the requested per-topic count.
- Is deterministic for a given seed.

Returns a list of SampleRow with a placeholder for `evidence_attached`; the actual
evidence selection is the EvidenceAttacher's job (Step 3).
"""
from __future__ import annotations

import json
import random
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from typing import Mapping

from .models import Compound, EvidenceItem, SampleRow
from .topic_bucket import bucket_topic

DEFAULT_TOPIC_WEIGHTS: Mapping[str, float] = {
    "mechanism": 0.20,
    "engineering": 0.20,
    "metabolism": 0.17,
    "toxicity": 0.17,
    "therapeutic_use": 0.13,
    "_other": 0.13,
}

HEADLINE_TOPICS = frozenset({"mechanism", "engineering", "metabolism", "toxicity", "therapeutic_use"})


class Sampler:
    """Stratified sampler over functional Q&A pairs."""

    def __init__(
        self,
        dataset_path: str | Path,
        seed: int = 0,
        topic_weights: Mapping[str, float] = DEFAULT_TOPIC_WEIGHTS,
    ) -> None:
        self.dataset_path = Path(dataset_path)
        self.seed = seed
        self._weights = dict(topic_weights)
        self._validate_weights()

    def _validate_weights(self) -> None:
        total = sum(self._weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"topic weights must sum to 1.0, got {total}")
        for k, v in self._weights.items():
            if v < 0:
                raise ValueError(f"weight for {k} is negative: {v}")

    def _iter_records(self) -> Iterable[dict]:
        with self.dataset_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    @staticmethod
    def _topic_key(topic: str) -> str:
        """Return the stratum key: a headline topic name or '_other'."""
        normalized = topic.strip().lower().replace("-", "_")
        if normalized in HEADLINE_TOPICS:
            return normalized
        return "_other"

    def _allocate(self, n: int) -> dict[str, int]:
        """Allocate n slots to strata using the configured weights.

        Uses largest-remainder rounding so allocations sum exactly to n.
        """
        if n <= 0:
            raise ValueError(f"n must be positive, got {n}")
        raw = {k: w * n for k, w in self._weights.items()}
        floors = {k: int(v) for k, v in raw.items()}
        remainder = n - sum(floors.values())
        # distribute remainder to strata with largest fractional parts
        fracs = sorted(
            ((k, raw[k] - floors[k]) for k in self._weights),
            key=lambda kv: kv[1],
            reverse=True,
        )
        for k, _ in fracs[:remainder]:
            floors[k] += 1
        return floors

    def _index_qa(self) -> dict[str, list[tuple[dict, dict]]]:
        """Group functional QA by stratum key.

        Returns {stratum_key: [(record, qa_pair), ...]}.
        """
        index: dict[str, list[tuple[dict, dict]]] = {k: [] for k in self._weights}
        for rec in self._iter_records():
            for qa in rec.get("qa_pairs", []):
                if bucket_topic(qa.get("topic")) != "functional":
                    continue
                key = self._topic_key(qa["topic"])
                index.setdefault(key, []).append((rec, qa))
        return index

    @staticmethod
    def _split_by_evidence(
        items: list[tuple[dict, dict]],
    ) -> tuple[list[tuple[dict, dict]], list[tuple[dict, dict]]]:
        nonempty = [it for it in items if it[1].get("evidence_ids")]
        empty = [it for it in items if not it[1].get("evidence_ids")]
        return nonempty, empty

    @staticmethod
    def _draw(
        rng: random.Random,
        pool_a: list[tuple[dict, dict]],
        pool_b: list[tuple[dict, dict]],
        target_a: int,
        target_b: int,
    ) -> list[tuple[dict, dict]]:
        """Draw target_a from pool_a and target_b from pool_b. If one side is short,
        backfill from the other. Pools are sampled without replacement.
        """
        rng.shuffle(pool_a)
        rng.shuffle(pool_b)
        take_a = pool_a[: min(target_a, len(pool_a))]
        take_b = pool_b[: min(target_b, len(pool_b))]
        # backfill shortfall
        short_a = target_a - len(take_a)
        short_b = target_b - len(take_b)
        if short_a > 0:
            extra = pool_b[len(take_b) : len(take_b) + short_a]
            take_b = take_b + extra
        if short_b > 0:
            extra = pool_a[len(take_a) : len(take_a) + short_b]
            take_a = take_a + extra
        return take_a + take_b

    def sample(self, n: int) -> list[SampleRow]:
        rng = random.Random(self.seed)
        allocations = self._allocate(n)
        index = self._index_qa()

        chosen: list[tuple[dict, dict]] = []
        for stratum, k in allocations.items():
            if k == 0:
                continue
            pool = index.get(stratum, [])
            nonempty, empty = self._split_by_evidence(pool)
            half = k // 2
            target_nonempty = half
            target_empty = k - half
            chosen.extend(self._draw(rng, nonempty, empty, target_nonempty, target_empty))

        return [self._row(rec, qa) for rec, qa in chosen]

    @staticmethod
    def _row(rec: dict, qa: dict) -> SampleRow:
        compound = Compound(
            cid=int(rec["cid"]),
            name=rec.get("name", ""),
            smiles=rec.get("smiles", ""),
            molecular_formula=rec.get("molecular_formula", ""),
        )
        # SampleRow ships without evidence; EvidenceAttacher fills it in Step 3.
        return SampleRow(
            cid=int(rec["cid"]),
            qa_index=int(qa["qa_index"]),
            topic=qa["topic"],
            split=rec.get("split", ""),
            evidence_ids_nonempty=bool(qa.get("evidence_ids")),
            compound=compound,
            question=qa["question"],
            phase2_answer=qa["phase2_answer"],
            evidence_attached=(),
        )

    @staticmethod
    def with_evidence(row: SampleRow, evidence: tuple[EvidenceItem, ...]) -> SampleRow:
        """Convenience for downstream code: clone a row with attached evidence."""
        return replace(row, evidence_attached=evidence)
