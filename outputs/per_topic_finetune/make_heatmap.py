"""Heatmap: top-30 raw topics + an 'other' bucket × 3 difficulty tiers, one sub-plot per
model, cell = Δ CIDEr (FT − base). Computed from the persisted per-sample JSONLs
(outputs/per_topic_finetune/per_sample/*.jsonl) — re-running it does not require
re-scoring.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = Path(__file__).parent / "outputs" / "per_topic_finetune"
PER_SAMPLE_DIR = OUT_DIR / "per_sample"
MODELS = ["gemma3_12b", "llama3_1_8b", "qwen2_5_14b"]
VARIANTS = ["base", "ft"]
TIERS = ["easy", "medium", "hard"]
TOP_N = 30


def load_per_sample(model: str, variant: str) -> list[dict]:
    rows = []
    with open(PER_SAMPLE_DIR / f"{model}__{variant}.jsonl") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def mean_cider_by(rows: list[dict], key_fn) -> dict:
    sums: dict = defaultdict(float)
    counts: dict = defaultdict(int)
    for r in rows:
        k = key_fn(r)
        sums[k] += r["CIDEr"]
        counts[k] += 1
    return {k: sums[k] / counts[k] for k in counts}


def main():
    # Pick top-30 topics by row count (every model-variant has the same 26,205 rows
    # so any one of them can drive the ranking).
    sample = load_per_sample(MODELS[0], VARIANTS[0])
    topic_counts: dict = defaultdict(int)
    for r in sample:
        topic_counts[r["topic"]] += 1
    ordered = sorted(topic_counts.items(), key=lambda x: -x[1])
    top_topics = [t for t, _ in ordered[:TOP_N]]
    top_set = set(top_topics)
    other_n = sum(n for t, n in ordered[TOP_N:])
    row_labels = [f"{t}  (n={topic_counts[t]})" for t in top_topics]
    row_labels.append(f"other  (n={other_n}, {len(ordered) - TOP_N} topics)")
    rows_axis = top_topics + ["__other__"]

    # Compute Δ CIDEr per (topic × tier) for each model. "other" is the union
    # of all topics not in top_set.
    grids: dict = {}
    for model in MODELS:
        base = load_per_sample(model, "base")
        ft = load_per_sample(model, "ft")

        def keyfn(r):
            t = r["topic"] if r["topic"] in top_set else "__other__"
            return (t, r["tier"])

        base_means = mean_cider_by(base, keyfn)
        ft_means = mean_cider_by(ft, keyfn)

        grid = np.full((len(rows_axis), len(TIERS)), np.nan)
        for i, t in enumerate(rows_axis):
            for j, tier in enumerate(TIERS):
                b = base_means.get((t, tier))
                f = ft_means.get((t, tier))
                if b is not None and f is not None:
                    grid[i, j] = f - b
        grids[model] = grid

    # Symmetric colorscale around zero so green/red map to gain/loss intuitively.
    vmax = max(np.nanmax(np.abs(g)) for g in grids.values())
    vmax = max(vmax, 0.01)

    fig, axes = plt.subplots(
        1, len(MODELS),
        figsize=(4 + 4 * len(MODELS), 0.32 * len(rows_axis) + 2),
        sharey=True, constrained_layout=True,
    )

    for ax, model in zip(axes, MODELS):
        grid = grids[model]
        im = ax.imshow(grid, aspect="auto", cmap="RdYlGn", vmin=-vmax, vmax=vmax)
        ax.set_xticks(range(len(TIERS)))
        ax.set_xticklabels(TIERS)
        ax.set_yticks(range(len(rows_axis)))
        ax.set_yticklabels(row_labels)
        ax.set_title(model)
        ax.set_xlabel("difficulty tier")
        for i in range(len(rows_axis)):
            for j in range(len(TIERS)):
                v = grid[i, j]
                if np.isnan(v):
                    ax.text(j, i, "—", ha="center", va="center", fontsize=7, color="gray")
                else:
                    ax.text(j, i, f"{v:+.2f}", ha="center", va="center", fontsize=7,
                            color="white" if abs(v) > vmax * 0.55 else "black")
    axes[0].set_ylabel("topic (top 30 by row count + 'other')")
    cbar = fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02)
    cbar.set_label("Δ CIDEr  (FT − base)   green = gain")
    fig.suptitle(
        f"ChemQA fine-tuning Δ CIDEr per topic × difficulty tier "
        f"(test split, n=26,205; top {TOP_N} topics + 'other')"
    )

    out = OUT_DIR / "heatmap_topic_x_difficulty.png"
    fig.savefig(out, dpi=150)
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
