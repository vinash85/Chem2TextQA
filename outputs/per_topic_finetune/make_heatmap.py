"""Heatmaps over top-30 raw topics + an 'other' bucket × 3 difficulty tiers, one
sub-plot per model. Produces three figures from the persisted per-sample JSONLs
(outputs/per_topic_finetune/per_sample/*.jsonl):
  - heatmap_topic_x_difficulty.png         cell = Δ CIDEr (FT − base)
  - heatmap_topic_x_difficulty_base.png    cell = base CIDEr
  - heatmap_topic_x_difficulty_ft.png      cell = FT CIDEr
The base/ft heatmaps share a vmax so they can be compared by eye.
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


def render_heatmap(
    grids: dict,
    rows_axis: list,
    row_labels: list,
    *,
    vmin: float,
    vmax: float,
    cmap: str,
    cbar_label: str,
    suptitle: str,
    fmt: str,
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(
        1, len(MODELS),
        figsize=(4 + 4 * len(MODELS), 0.32 * len(rows_axis) + 2),
        sharey=True, constrained_layout=True,
    )
    span = vmax - vmin
    midpoint = (vmax + vmin) / 2
    for ax, model in zip(axes, MODELS):
        grid = grids[model]
        im = ax.imshow(grid, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
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
                    far_from_mid = abs(v - midpoint) > span * 0.275
                    ax.text(j, i, format(v, fmt), ha="center", va="center", fontsize=7,
                            color="white" if far_from_mid else "black")
    axes[0].set_ylabel("topic (top 30 by row count + 'other')")
    cbar = fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02)
    cbar.set_label(cbar_label)
    fig.suptitle(suptitle)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")


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

    # Per-model means for each variant, then derive Δ.
    base_grids: dict = {}
    ft_grids: dict = {}
    delta_grids: dict = {}
    for model in MODELS:
        base = load_per_sample(model, "base")
        ft = load_per_sample(model, "ft")

        def keyfn(r):
            t = r["topic"] if r["topic"] in top_set else "__other__"
            return (t, r["tier"])

        base_means = mean_cider_by(base, keyfn)
        ft_means = mean_cider_by(ft, keyfn)

        base_grid = np.full((len(rows_axis), len(TIERS)), np.nan)
        ft_grid = np.full((len(rows_axis), len(TIERS)), np.nan)
        delta_grid = np.full((len(rows_axis), len(TIERS)), np.nan)
        for i, t in enumerate(rows_axis):
            for j, tier in enumerate(TIERS):
                b = base_means.get((t, tier))
                f = ft_means.get((t, tier))
                if b is not None:
                    base_grid[i, j] = b
                if f is not None:
                    ft_grid[i, j] = f
                if b is not None and f is not None:
                    delta_grid[i, j] = f - b
        base_grids[model] = base_grid
        ft_grids[model] = ft_grid
        delta_grids[model] = delta_grid

    # Δ heatmap: symmetric colorscale around zero.
    delta_vmax = max(np.nanmax(np.abs(g)) for g in delta_grids.values())
    delta_vmax = max(delta_vmax, 0.01)
    render_heatmap(
        delta_grids, rows_axis, row_labels,
        vmin=-delta_vmax, vmax=delta_vmax,
        cmap="RdYlGn",
        cbar_label="Δ CIDEr  (FT − base)   green = gain",
        suptitle=(
            f"ChemQA fine-tuning Δ CIDEr per topic × difficulty tier "
            f"(test split, n=26,205; top {TOP_N} topics + 'other')"
        ),
        fmt="+.2f",
        out_path=OUT_DIR / "heatmap_topic_x_difficulty.png",
    )

    # Pre/post heatmaps: shared sequential scale so they're directly comparable.
    abs_vmax = max(
        np.nanmax([np.nanmax(g) for g in base_grids.values()]),
        np.nanmax([np.nanmax(g) for g in ft_grids.values()]),
    )
    abs_vmax = max(abs_vmax, 0.01)
    for variant_label, grids in (("base", base_grids), ("FT", ft_grids)):
        suffix = "base" if variant_label == "base" else "ft"
        render_heatmap(
            grids, rows_axis, row_labels,
            vmin=0.0, vmax=abs_vmax,
            cmap="viridis",
            cbar_label=f"{variant_label} CIDEr",
            suptitle=(
                f"ChemQA {variant_label} CIDEr per topic × difficulty tier "
                f"(test split, n=26,205; top {TOP_N} topics + 'other')"
            ),
            fmt=".2f",
            out_path=OUT_DIR / f"heatmap_topic_x_difficulty_{suffix}.png",
        )


if __name__ == "__main__":
    main()
