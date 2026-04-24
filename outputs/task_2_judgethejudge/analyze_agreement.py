#!/usr/bin/env python3
"""Task 2 deliverables — inter-judge agreement analysis.

Joins samples_input.jsonl (Gemma's verdicts) with the three judged_*.jsonl
files produced by run_all_judges.sh, then emits the paper-ready outputs:

    outputs/multi_judge/
      ├── samples.jsonl               — merged rows with all 4 verdicts
      ├── per_judge_distribution.json — verdict counts per judge
      ├── agreement_matrix.json       — pairwise Cohen's κ + Krippendorff's α
      └── disagreement_analysis.md    — κ table, majority-disagrees rate, examples

Headline number: % of rows where the majority (≥2) of the three new judges
disagrees with Gemma — flagged vs the 15 % threshold from the PDF.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
from itertools import combinations
from pathlib import Path

import krippendorff
from sklearn.metrics import cohen_kappa_score

DEFAULT_DIR = Path(__file__).parent / "outputs" / "multi_judge"
JUDGES = ["gemma", "sonnet", "gpt5", "gemini"]
VALID_VERDICTS = ("agree", "disagree", "unclear")


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_merged(out_dir: Path) -> list[dict]:
    samples = load_jsonl(out_dir / "samples_input.jsonl")
    by_key = {f"{r['cid']}:{r['qa_index']}": r for r in samples}

    file_map = {
        "sonnet": out_dir / "final_judged_sonnet46.jsonl",
        "gpt5": out_dir / "final_judged_gpt5.jsonl",
        "gemini": out_dir / "final_judged_gemini25pro.jsonl",
    }

    for tag, path in file_map.items():
        if not path.exists():
            raise FileNotFoundError(f"missing {path}")
        for r in load_jsonl(path):
            key = r.get("key") or f"{r.get('cid')}:{r.get('qa_index')}"
            base = by_key.get(key)
            if base is None:
                continue
            base.setdefault("verdicts", {})[tag] = r.get("verdict")
            base.setdefault("reasonings", {})[tag] = r.get("reasoning") or ""
            if r.get("error"):
                base.setdefault("errors", {})[tag] = r["error"]

    merged: list[dict] = []
    for key, r in by_key.items():
        verdicts = r.get("verdicts", {})
        verdicts["gemma"] = r.get("gemma_verdict")
        r["verdicts"] = verdicts
        reasonings = r.get("reasonings", {})
        reasonings["gemma"] = r.get("gemma_reasoning", "")
        r["reasonings"] = reasonings
        merged.append(r)

    merged.sort(key=lambda x: (x.get("cid") or 0, x.get("qa_index") or 0))
    return merged


def per_judge_distribution(merged: list[dict]) -> dict:
    out: dict[str, dict[str, int]] = {}
    for j in JUDGES:
        c = collections.Counter()
        for r in merged:
            v = r["verdicts"].get(j)
            if v in VALID_VERDICTS:
                c[v] += 1
            else:
                c["error_or_missing"] += 1
        out[j] = {
            "agree": c.get("agree", 0),
            "disagree": c.get("disagree", 0),
            "unclear": c.get("unclear", 0),
            "error_or_missing": c.get("error_or_missing", 0),
            "total": sum(c.values()),
        }
    return out


def pairwise_kappa(merged: list[dict]) -> dict:
    """Cohen's κ for every pair of judges (excluding rows where either is missing)."""
    out: dict[str, dict] = {}
    for a, b in combinations(JUDGES, 2):
        va, vb = [], []
        for r in merged:
            x = r["verdicts"].get(a)
            y = r["verdicts"].get(b)
            if x in VALID_VERDICTS and y in VALID_VERDICTS:
                va.append(x)
                vb.append(y)
        if va:
            k = float(cohen_kappa_score(va, vb, labels=list(VALID_VERDICTS)))
        else:
            k = None
        out[f"{a}__{b}"] = {"kappa": k, "n": len(va)}
    return out


def krippendorff_alpha(merged: list[dict]) -> float | None:
    """Nominal α over a 4×N matrix, using np.nan for missing/invalid verdicts."""
    import numpy as np
    label_ids = {v: i for i, v in enumerate(VALID_VERDICTS)}
    mat = []
    for j in JUDGES:
        row = []
        for r in merged:
            v = r["verdicts"].get(j)
            row.append(label_ids.get(v, np.nan))
        mat.append(row)
    mat = np.array(mat, dtype=float)
    try:
        return float(krippendorff.alpha(reliability_data=mat, level_of_measurement="nominal"))
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: krippendorff alpha failed: {exc}")
        return None


def majority_vs_gemma(merged: list[dict]) -> dict:
    """% of rows where majority (≥2 of 3) of new judges disagrees with Gemma."""
    n_eval = 0
    n_disagree = 0
    buckets: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])  # by Gemma verdict
    by_topic: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    for r in merged:
        g = r["verdicts"].get("gemma")
        panel = [r["verdicts"].get(j) for j in ("sonnet", "gpt5", "gemini")]
        panel = [v for v in panel if v in VALID_VERDICTS]
        if g not in VALID_VERDICTS or len(panel) < 2:
            continue
        n_eval += 1
        buckets[g][0] += 1
        by_topic[r.get("topic", "?")][0] += 1
        # "majority disagrees with Gemma" = at least 2 panel votes are != g
        mismatches = sum(1 for v in panel if v != g)
        if mismatches >= 2:
            n_disagree += 1
            buckets[g][1] += 1
            by_topic[r.get("topic", "?")][1] += 1
    rate = (n_disagree / n_eval) if n_eval else 0.0
    return {
        "n_evaluable": n_eval,
        "n_majority_disagrees_with_gemma": n_disagree,
        "rate": rate,
        "by_gemma_verdict": {
            g: {"n": total, "disagree": dis, "rate": (dis / total) if total else 0.0}
            for g, (total, dis) in buckets.items()
        },
        "by_topic": {
            t: {"n": total, "disagree": dis, "rate": (dis / total) if total else 0.0}
            for t, (total, dis) in by_topic.items()
        },
    }


def render_markdown(
    merged: list[dict],
    dist: dict,
    kappa: dict,
    alpha: float | None,
    maj: dict,
    n_examples: int = 20,
    seed: int = 0,
) -> str:
    lines: list[str] = []
    lines.append("# Task 2 — Multi-judge LLM panel on Phase-3 verdicts\n")
    lines.append("## Headline: does Gemma look noisy?\n")

    rate_pct = maj["rate"] * 100
    threshold_note = "**>15 % → gold subset noisier than claimed.**"
    verdict_word = "EXCEEDS" if rate_pct > 15 else "WITHIN"
    lines.append(
        f"- Evaluable rows (all 4 judges voted + Gemma): **{maj['n_evaluable']} / {len(merged)}**\n"
        f"- Rows where **majority of the 3 new judges disagrees with Gemma**: "
        f"**{maj['n_majority_disagrees_with_gemma']}** ({rate_pct:.1f} %)\n"
        f"- Verdict: **{verdict_word}** the 15 % threshold. {threshold_note}\n"
    )

    lines.append("## Per-judge verdict distribution\n")
    lines.append("| judge | agree | disagree | unclear | err / missing | total |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for j in JUDGES:
        d = dist[j]
        lines.append(
            f"| {j} | {d['agree']} | {d['disagree']} | {d['unclear']} | "
            f"{d['error_or_missing']} | {d['total']} |"
        )
    lines.append("")

    lines.append("## Pairwise Cohen's κ\n")
    lines.append("| judge pair | n | κ |")
    lines.append("|---|---:|---:|")
    for pair, info in kappa.items():
        a, b = pair.split("__")
        k = info["kappa"]
        kstr = "n/a" if k is None else f"{k:.3f}"
        lines.append(f"| {a} × {b} | {info['n']} | {kstr} |")
    gem_pairs = [info["kappa"] for pair, info in kappa.items()
                 if pair.startswith("gemma__") and info["kappa"] is not None]
    if gem_pairs:
        lines.append(f"| **Gemma-vs-panel avg** | — | **{sum(gem_pairs)/len(gem_pairs):.3f}** |")
    lines.append("")

    if alpha is not None:
        lines.append(f"**Krippendorff's α (nominal, 4 judges):** {alpha:.3f}\n")
    else:
        lines.append("**Krippendorff's α (nominal, 4 judges):** n/a\n")

    lines.append("## Majority-disagrees-with-Gemma, broken down by Gemma's original verdict\n")
    lines.append("| Gemma verdict | n | majority disagrees | rate |")
    lines.append("|---|---:|---:|---:|")
    for v in VALID_VERDICTS:
        b = maj["by_gemma_verdict"].get(v)
        if not b:
            continue
        lines.append(f"| {v} | {b['n']} | {b['disagree']} | {b['rate']*100:.1f} % |")
    lines.append("")

    # top topics by count, report rate where n >= 10
    topic_rows = sorted(
        maj["by_topic"].items(), key=lambda kv: -kv[1]["n"]
    )[:20]
    lines.append("## Majority-disagrees rate — top 20 topics by sample size\n")
    lines.append("| topic | n | majority disagrees | rate |")
    lines.append("|---|---:|---:|---:|")
    for t, b in topic_rows:
        lines.append(f"| {t} | {b['n']} | {b['disagree']} | {b['rate']*100:.1f} % |")
    lines.append("")

    # qualitative examples
    rng = random.Random(seed)
    disagreements = []
    for r in merged:
        g = r["verdicts"].get("gemma")
        panel = [r["verdicts"].get(j) for j in ("sonnet", "gpt5", "gemini")]
        panel_clean = [v for v in panel if v in VALID_VERDICTS]
        if g not in VALID_VERDICTS or len(panel_clean) < 2:
            continue
        mismatches = sum(1 for v in panel_clean if v != g)
        if mismatches >= 2:
            disagreements.append(r)
    rng.shuffle(disagreements)
    picks = disagreements[:n_examples]

    lines.append(f"## {len(picks)} qualitative disagreements (sampled from {len(disagreements)})\n")
    for i, r in enumerate(picks, 1):
        q = (r.get("question") or "").replace("\n", " ")
        lines.append(f"### Example {i} — cid {r.get('cid')}, qa_index {r.get('qa_index')} (topic: {r.get('topic')})\n")
        lines.append(f"**Question:** {q}\n")
        lines.append(f"**Phase-1 answer:** {r.get('phase1_answer','').strip()[:500]}\n")
        lines.append(f"**Phase-2 answer:** {r.get('phase2_answer','').strip()[:500]}\n")
        lines.append("| judge | verdict | reasoning |")
        lines.append("|---|---|---|")
        for j in JUDGES:
            v = r["verdicts"].get(j) or "—"
            why = (r["reasonings"].get(j) or "").replace("\n", " ").replace("|", "\\|")
            lines.append(f"| {j} | {v} | {why[:400]} |")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR,
                    help="Directory containing samples_input.jsonl and judged_*.jsonl")
    ap.add_argument("--n_examples", type=int, default=20,
                    help="Qualitative disagreement examples to include in the markdown")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    merged = build_merged(args.dir)

    dist = per_judge_distribution(merged)
    kappa = pairwise_kappa(merged)
    alpha = krippendorff_alpha(merged)
    maj = majority_vs_gemma(merged)

    # samples.jsonl — clean merged rows
    out_samples = args.dir / "samples.jsonl"
    with out_samples.open("w", encoding="utf-8") as f:
        for r in merged:
            # drop the huge llm_response / full_response fields — they live in judged_*.jsonl
            slim = {k: v for k, v in r.items() if k not in ("llm_response", "full_response")}
            f.write(json.dumps(slim, ensure_ascii=False) + "\n")

    (args.dir / "per_judge_distribution.json").write_text(
        json.dumps(dist, indent=2), encoding="utf-8"
    )
    (args.dir / "agreement_matrix.json").write_text(
        json.dumps({"pairwise_cohens_kappa": kappa,
                    "krippendorff_alpha_nominal": alpha}, indent=2),
        encoding="utf-8",
    )
    md = render_markdown(merged, dist, kappa, alpha, maj,
                        n_examples=args.n_examples, seed=args.seed)
    (args.dir / "disagreement_analysis.md").write_text(md, encoding="utf-8")

    # stdout summary
    print(f"rows merged: {len(merged)}")
    print("per-judge distribution:")
    for j, d in dist.items():
        print(f"  {j:<8} agree={d['agree']:>4}  disagree={d['disagree']:>4}  "
              f"unclear={d['unclear']:>4}  err={d['error_or_missing']:>3}")
    print("Cohen's kappa:")
    for pair, info in kappa.items():
        k = info["kappa"]
        print(f"  {pair:<22} n={info['n']:>4}  kappa={'n/a' if k is None else f'{k:.3f}'}")
    print(f"Krippendorff's alpha: {alpha if alpha is None else f'{alpha:.3f}'}")
    print(f"Majority-of-3 disagrees with Gemma: "
          f"{maj['n_majority_disagrees_with_gemma']}/{maj['n_evaluable']} "
          f"({maj['rate']*100:.1f} %)")
    print(f"\nwrote:")
    for name in ("samples.jsonl", "per_judge_distribution.json",
                 "agreement_matrix.json", "disagreement_analysis.md"):
        print(f"  {args.dir / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
