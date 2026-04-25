"""Typed dataclasses passed between phase4_grounding modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ClaimLabel = Literal["STATED", "IMPLIED", "UNSUPPORTED", "STRUCTURAL"]
LABEL_VALUES: tuple[ClaimLabel, ...] = ("STATED", "IMPLIED", "UNSUPPORTED", "STRUCTURAL")


@dataclass(frozen=True)
class EvidenceItem:
    id: int
    text: str
    pmid: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class Compound:
    cid: int
    name: str
    smiles: str
    molecular_formula: str


@dataclass(frozen=True)
class SampleRow:
    cid: int
    qa_index: int
    topic: str
    split: str
    evidence_ids_nonempty: bool
    compound: Compound
    question: str
    phase2_answer: str
    evidence_attached: tuple[EvidenceItem, ...]


@dataclass(frozen=True)
class Claim:
    claim: str
    label: ClaimLabel
    evidence_id: int | None
    rationale: str | None


@dataclass(frozen=True)
class JudgedQA:
    cid: int
    qa_index: int
    topic: str
    evidence_ids_nonempty: bool
    num_evidence_attached: int
    model: str
    claims: tuple[Claim, ...]
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    split: str = ""


@dataclass(frozen=True)
class ParseResult:
    ok: bool
    claims: tuple[Claim, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class ChatResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int


@dataclass(frozen=True)
class ViewMetrics:
    view: Literal["keep", "drop"]
    total_claims: int
    counts: dict[str, int]
    rates: dict[str, float]
    grounded_rate: float
    unsupported_rate: float
    unsupported_ci: tuple[float, float]
    structural_count: int = 0
    by_topic: dict[str, dict[str, float]] = field(default_factory=dict)
    by_evidence_ids_nonempty: dict[bool, dict[str, float]] = field(default_factory=dict)
    by_split: dict[str, dict[str, float]] = field(default_factory=dict)
    per_qa_unsupported_histogram: dict[int, int] = field(default_factory=dict)
    top_qa_by_unsupported: tuple[dict, ...] = field(default_factory=tuple)
