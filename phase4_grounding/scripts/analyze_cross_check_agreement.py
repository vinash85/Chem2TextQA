"""Compute primary (sonnet) vs cross-check (gemini) agreement on the 30
dual-judged rows from the Phase 4 grounding audit.

The two models produce independent claim decompositions, so claim-level
1:1 alignment is undefined. Instead we measure rate-level agreement
per Q&A: each model produces a UNSUPPORTED rate and a Grounded rate
for the same row; we compare those.

Writes a Markdown summary to outputs/cross_check_agreement.md.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
PRIMARY = OUT_DIR / "claims_per_qa.jsonl"
GEMINI = OUT_DIR / "claims_per_qa.gemini.jsonl"
REPORT = OUT_DIR / "cross_check_agreement.md"


def _load(path):
    rows = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            rows[(int(d["cid"]), int(d["qa_index"]))] = d
    return rows


def _label_counts(claims):
    counts = {"STATED": 0, "IMPLIED": 0, "UNSUPPORTED": 0, "STRUCTURAL": 0}
    for c in claims:
        counts[c["label"]] = counts.get(c["label"], 0) + 1
    return counts


def _rates(counts, view):
    if view == "keep":
        denom = counts["STATED"] + counts["IMPLIED"] + counts["UNSUPPORTED"]
    else:
        denom = sum(counts.values())
    if denom == 0:
        return None, None, denom
    if view == "keep":
        unsupported = counts["UNSUPPORTED"] / denom
        grounded = (counts["STATED"] + counts["IMPLIED"]) / denom
    else:
        unsupported = counts["UNSUPPORTED"] / denom
        grounded = (counts["STATED"] + counts["IMPLIED"] + counts["STRUCTURAL"]) / denom
    return unsupported, grounded, denom


def main():
    primary = _load(PRIMARY)
    gemini = _load(GEMINI)
    keys = sorted(set(primary) & set(gemini))

    rows_keep = []
    rows_drop = []
    primary_models = set()
    gemini_models = set()
    for k in keys:
        p = primary[k]
        g = gemini[k]
        primary_models.add(p["model"])
        gemini_models.add(g["model"])
        pc = _label_counts(p["claims"])
        gc = _label_counts(g["claims"])
        for view, sink in (("keep", rows_keep), ("drop", rows_drop)):
            pu, pg, pd = _rates(pc, view)
            gu, gg, gd = _rates(gc, view)
            if pu is None or gu is None:
                continue
            sink.append(
                {
                    "cid": k[0],
                    "qa": k[1],
                    "p_unsupported": pu,
                    "g_unsupported": gu,
                    "diff": gu - pu,
                    "p_n": pd,
                    "g_n": gd,
                }
            )

    def _summary(rows, view_name):
        diffs = [r["diff"] for r in rows]
        abs_diffs = [abs(d) for d in diffs]
        p_macro = (
            sum(r["p_unsupported"] * r["p_n"] for r in rows) / sum(r["p_n"] for r in rows)
        )
        g_macro = (
            sum(r["g_unsupported"] * r["g_n"] for r in rows) / sum(r["g_n"] for r in rows)
        )
        return {
            "view": view_name,
            "n_rows": len(rows),
            "primary_macro_unsupported": p_macro,
            "gemini_macro_unsupported": g_macro,
            "macro_diff": g_macro - p_macro,
            "mean_abs_per_row_diff": statistics.fmean(abs_diffs) if abs_diffs else 0.0,
            "median_abs_per_row_diff": statistics.median(abs_diffs) if abs_diffs else 0.0,
            "max_abs_per_row_diff": max(abs_diffs) if abs_diffs else 0.0,
            "rows_within_10pp": sum(1 for d in abs_diffs if d <= 0.10),
            "rows_within_20pp": sum(1 for d in abs_diffs if d <= 0.20),
        }

    summ_keep = _summary(rows_keep, "keep-structural")
    summ_drop = _summary(rows_drop, "drop-structural")

    lines = []
    lines.append("# Cross-check agreement — primary (sonnet-4.6) vs cross-check (gemini-2.5-pro)\n")
    lines.append(
        f"Comparison on {len(keys)} Q&A rows judged independently by both models.\n"
    )
    lines.append(f"- Primary models present in subset: {sorted(primary_models)}")
    lines.append(f"- Cross-check models: {sorted(gemini_models)}\n")

    for s in (summ_keep, summ_drop):
        lines.append(f"## {s['view']} view")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        lines.append(f"| n rows compared | {s['n_rows']} |")
        lines.append(f"| Primary macro UNSUPPORTED | **{s['primary_macro_unsupported']*100:.2f}%** |")
        lines.append(f"| Gemini macro UNSUPPORTED  | **{s['gemini_macro_unsupported']*100:.2f}%** |")
        lines.append(f"| Macro diff (gemini − primary) | {s['macro_diff']*100:+.2f}pp |")
        lines.append(f"| Mean abs per-row diff | {s['mean_abs_per_row_diff']*100:.2f}pp |")
        lines.append(f"| Median abs per-row diff | {s['median_abs_per_row_diff']*100:.2f}pp |")
        lines.append(f"| Max abs per-row diff | {s['max_abs_per_row_diff']*100:.2f}pp |")
        lines.append(f"| Rows within 10pp | {s['rows_within_10pp']} / {s['n_rows']} |")
        lines.append(f"| Rows within 20pp | {s['rows_within_20pp']} / {s['n_rows']} |")
        lines.append("")

    lines.append("## Per-row UNSUPPORTED rates (keep-structural)")
    lines.append("")
    lines.append("| cid | qa | primary | gemini | diff |")
    lines.append("|---|---|---|---|---|")
    for r in sorted(rows_keep, key=lambda r: -abs(r["diff"])):
        lines.append(
            f"| {r['cid']} | {r['qa']} | {r['p_unsupported']*100:.1f}% "
            f"| {r['g_unsupported']*100:.1f}% | {r['diff']*100:+.1f}pp |"
        )

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"wrote {REPORT}")
    for s in (summ_keep, summ_drop):
        print(
            f"  {s['view']}: primary {s['primary_macro_unsupported']*100:.2f}% | "
            f"gemini {s['gemini_macro_unsupported']*100:.2f}% | "
            f"diff {s['macro_diff']*100:+.2f}pp | "
            f"mean abs per-row {s['mean_abs_per_row_diff']*100:.2f}pp"
        )


if __name__ == "__main__":
    main()
