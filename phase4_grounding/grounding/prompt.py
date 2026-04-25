"""Render the claim-decomposition judge prompt for a single sample row.

The template lives at `phase4_grounding/prompts/claim_decomp.txt` and uses
`{{NAME}}`-style placeholders so the embedded JSON example does not collide
with `str.format`'s `{` / `}` syntax.
"""
from __future__ import annotations

from pathlib import Path

from .models import EvidenceItem, SampleRow

_DEFAULT_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "claim_decomp.txt"
)


class PromptBuilder:
    """Render the claim-decomposition prompt for a `SampleRow`."""

    def __init__(self, template_path: str | Path = _DEFAULT_TEMPLATE_PATH) -> None:
        self.template_path = Path(template_path)
        self._template: str | None = None

    def _load(self) -> str:
        if self._template is None:
            self._template = self.template_path.read_text()
        return self._template

    @staticmethod
    def _render_evidence(items: tuple[EvidenceItem, ...]) -> str:
        if not items:
            return "(no evidence sentences attached)"
        return "\n".join(f"[E{e.id}] {e.text}" for e in items)

    def build(self, row: SampleRow) -> str:
        template = self._load()
        replacements = {
            "{{COMPOUND_NAME}}": row.compound.name,
            "{{SMILES}}": row.compound.smiles,
            "{{MOLECULAR_FORMULA}}": row.compound.molecular_formula,
            "{{QUESTION}}": row.question,
            "{{PHASE2_ANSWER}}": row.phase2_answer,
            "{{EVIDENCE_BLOCK}}": self._render_evidence(row.evidence_attached),
        }
        out = template
        for key, value in replacements.items():
            out = out.replace(key, value)
        return out
