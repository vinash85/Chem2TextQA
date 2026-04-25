"""Markdown writers for the dual grounding-summary view.

`Reporter(metrics_keep, metrics_drop, judged_qas).write(out_dir)` writes:
- `grounding_summary_keep_structural.md`
- `grounding_summary_drop_structural.md`

Each summary cites the other so the reader can compare the two views. The
decision rule (>20% / 10–20% / <10% UNSUPPORTED) is printed at the top.
"""
from __future__ import annotations

from pathlib import Path

from .models import JudgedQA, ViewMetrics

_KEEP_FILE = "grounding_summary_keep_structural.md"
_DROP_FILE = "grounding_summary_drop_structural.md"


def _decision(unsupported_rate: float) -> str:
    pct = unsupported_rate * 100
    if pct > 20:
        return (
            f"**Decision: NARROW.** UNSUPPORTED = {pct:.1f}% > 20%. Narrow the "
            "paper's grounding claim; flag training-recall risk in DATASHEET / "
            "RESPONSIBLE_AI."
        )
    if pct < 10:
        return (
            f"**Decision: WELL-BEHAVED.** UNSUPPORTED = {pct:.1f}% < 10%. The "
            "soft rule looks safe; quote this number in the dataset card."
        )
    return (
        f"**Decision: CAVEAT.** UNSUPPORTED = {pct:.1f}% (10–20%). Add a caveat "
        "to DATASHEET / RESPONSIBLE_AI; do not claim full grounding."
    )


def _fmt_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def _fmt_count_pct(count: int, total: int) -> str:
    rate = (count / total) if total else 0.0
    return f"{count} ({rate * 100:.2f}%)"


class Reporter:
    """Renders both summary markdown files from a pair of `ViewMetrics`."""

    def __init__(
        self,
        metrics_keep: ViewMetrics,
        metrics_drop: ViewMetrics,
        judged_qas: list[JudgedQA] | tuple[JudgedQA, ...],
    ) -> None:
        if metrics_keep.view != "keep":
            raise ValueError("metrics_keep must be a 'keep' view")
        if metrics_drop.view != "drop":
            raise ValueError("metrics_drop must be a 'drop' view")
        self.metrics_keep = metrics_keep
        self.metrics_drop = metrics_drop
        self.judged_qas = tuple(judged_qas)

    def write(self, out_dir: Path) -> tuple[Path, Path]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        keep_path = out_dir / _KEEP_FILE
        drop_path = out_dir / _DROP_FILE

        keep_path.write_text(
            self._render(
                metrics=self.metrics_keep,
                title="Grounding Summary — KEEP STRUCTURAL view",
                description=(
                    "STRUCTURAL claims (derivable from SMILES / formula alone) are "
                    "kept as their own bucket and **excluded from the denominator** "
                    "for STATED / IMPLIED / UNSUPPORTED rates. This view treats "
                    "UNSUPPORTED as a clean proxy for training-recall risk."
                ),
                cross_link=f"See also `{_DROP_FILE}` for the alternate view.",
            )
        )

        drop_path.write_text(
            self._render(
                metrics=self.metrics_drop,
                title="Grounding Summary — DROP STRUCTURAL view",
                description=(
                    "STRUCTURAL claims are collapsed into IMPLIED — i.e. SMILES / "
                    "formula are treated as 'evidence' in a loose sense. Closer to "
                    "the original PLAN spec."
                ),
                cross_link=f"See also `{_KEEP_FILE}` for the alternate view.",
            )
        )

        return keep_path, drop_path

    def _render(
        self,
        *,
        metrics: ViewMetrics,
        title: str,
        description: str,
        cross_link: str,
    ) -> str:
        lo, hi = metrics.unsupported_ci
        lines: list[str] = []
        lines.append(f"# {title}")
        lines.append("")
        lines.append(_decision(metrics.unsupported_rate))
        lines.append("")
        lines.append(description)
        lines.append("")
        lines.append(cross_link)
        lines.append("")
        lines.append("## Headline metrics")
        lines.append("")
        lines.append(f"- Total claims (denominator): **{metrics.total_claims}**")
        lines.append(f"- Q&A judged: **{len(self.judged_qas)}**")
        if metrics.view == "keep":
            lines.append(
                f"- STRUCTURAL claims (excluded from denominator): "
                f"**{metrics.structural_count}**"
            )
        for label, count in metrics.counts.items():
            lines.append(
                f"- {label}: {_fmt_count_pct(count, metrics.total_claims)}"
            )
        lines.append(f"- Grounded (STATED + IMPLIED): **{_fmt_pct(metrics.grounded_rate)}**")
        lines.append(
            f"- UNSUPPORTED: **{_fmt_pct(metrics.unsupported_rate)}** "
            f"(95% Wilson CI: {_fmt_pct(lo)} – {_fmt_pct(hi)})"
        )
        lines.append("")

        lines.extend(self._breakdown_table("By topic", metrics.by_topic, sort_keys=True))
        lines.extend(
            self._breakdown_table(
                "By evidence_ids non-empty",
                {str(k): v for k, v in metrics.by_evidence_ids_nonempty.items()},
                sort_keys=False,
            )
        )
        lines.extend(self._breakdown_table("By split", metrics.by_split, sort_keys=True))

        lines.append("## Per-Q&A UNSUPPORTED histogram")
        lines.append("")
        lines.append("| UNSUPPORTED claims in QA | # of QAs |")
        lines.append("|---|---|")
        for k in sorted(metrics.per_qa_unsupported_histogram):
            lines.append(f"| {k} | {metrics.per_qa_unsupported_histogram[k]} |")
        lines.append("")

        lines.append(f"## Top {len(metrics.top_qa_by_unsupported)} Q&A by UNSUPPORTED rate")
        lines.append("")
        if metrics.top_qa_by_unsupported:
            lines.append(
                "| cid | qa_index | topic | split | UNSUPPORTED | total | rate |"
            )
            lines.append("|---|---|---|---|---|---|---|")
            for r in metrics.top_qa_by_unsupported:
                lines.append(
                    f"| {r['cid']} | {r['qa_index']} | {r['topic']} | "
                    f"{r['split']} | {r['unsupported']} | "
                    f"{r['total_claims']} | {_fmt_pct(r['unsupported_rate'])} |"
                )
        else:
            lines.append("(no Q&A judged)")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _breakdown_table(
        title: str, data: dict, *, sort_keys: bool
    ) -> list[str]:
        if not data:
            return [f"## {title}", "", "(no data)", ""]
        keys = sorted(data.keys()) if sort_keys else list(data.keys())
        sample = data[keys[0]]
        label_keys = [k for k in sample if not k.endswith("_rate") and k != "total"]
        out = [f"## {title}", ""]
        header = (
            "| key | total | "
            + " | ".join(label_keys)
            + " | "
            + " | ".join(f"{lbl}%" for lbl in label_keys)
            + " |"
        )
        out.append(header)
        out.append("|" + "---|" * (2 + 2 * len(label_keys)))
        for key in keys:
            row = data[key]
            cells = [f"{key}", f"{row['total']}"]
            cells.extend(str(row.get(lbl, 0)) for lbl in label_keys)
            cells.extend(_fmt_pct(row.get(f"{lbl}_rate", 0.0)) for lbl in label_keys)
            out.append("| " + " | ".join(cells) + " |")
        out.append("")
        return out
