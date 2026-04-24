#!/usr/bin/env python3
"""Render Task 2 result figures to ./figures/.

Reads outputs/multi_judge/{samples.jsonl,per_judge_distribution.json,
agreement_matrix.json} and produces 6 PNG figures summarising the
multi-judge re-evaluation of Phase-3 verdicts.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "outputs" / "multi_judge"
FIG_DIR = HERE / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

JUDGES = ["gemma", "sonnet", "gpt5", "gemini"]
JUDGE_LABELS = {
    "gemma": "Gemma 4 31B",
    "sonnet": "Sonnet 4.6",
    "gpt5": "GPT-5",
    "gemini": "Gemini 2.5 Pro",
}
VERDICTS = ["agree", "disagree", "unclear"]
VERDICT_COLORS = {"agree": "#2b8a3e", "disagree": "#c92a2a", "unclear": "#f08c00", "error/missing": "#868e96"}
DPI = 200

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 10,
})

samples = [json.loads(l) for l in open(OUT_DIR / "samples.jsonl")]
dist = json.loads((OUT_DIR / "per_judge_distribution.json").read_text())
agree_mat = json.loads((OUT_DIR / "agreement_matrix.json").read_text())


def _panel_majority(row) -> str | None:
    """Plurality verdict among the 3 new judges, for visualization only.

    Returns the most-common clean vote (or None if <2 clean votes or a tie).
    """
    votes = [row["verdicts"].get(j) for j in ("sonnet", "gpt5", "gemini")]
    votes = [v for v in votes if v in VERDICTS]
    if len(votes) < 2:
        return None
    c = collections.Counter(votes).most_common(1)[0]
    return c[0] if c[1] >= 2 else None


def _panel_majority_disagrees(row) -> tuple[bool, bool]:
    """PDF-consistent check: '≥2 of the 3 new judges disagree with Gemma'.

    Returns (evaluable, disagrees) — evaluable=False if Gemma verdict missing
    or fewer than 2 panel judges voted. Matches analyze_agreement.py's
    majority_vs_gemma() and the markdown report.
    """
    g = row["verdicts"].get("gemma")
    if g not in VERDICTS:
        return False, False
    panel = [row["verdicts"].get(j) for j in ("sonnet", "gpt5", "gemini")]
    panel = [v for v in panel if v in VERDICTS]
    if len(panel) < 2:
        return False, False
    mismatches = sum(1 for v in panel if v != g)
    return True, mismatches >= 2


# ---------------------------------------------------------------------------
# Figure 1 — per-judge verdict distribution
# ---------------------------------------------------------------------------
def fig1():
    fig, ax = plt.subplots(figsize=(8, 4.6))
    x = np.arange(len(JUDGES))
    width = 0.2
    cats = VERDICTS + ["error_or_missing"]
    cat_label = {"error_or_missing": "error/missing"}

    for i, cat in enumerate(cats):
        label = cat_label.get(cat, cat)
        vals = [dist[j][cat] for j in JUDGES]
        color = VERDICT_COLORS["error/missing" if cat == "error_or_missing" else cat]
        bars = ax.bar(x + (i - 1.5) * width, vals, width, label=label, color=color)
        for b, v in zip(bars, vals):
            if v > 0:
                ax.text(b.get_x() + b.get_width() / 2, v + 10, str(v),
                        ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([JUDGE_LABELS[j] for j in JUDGES])
    ax.set_ylabel("count (n = 1000 samples)")
    ax.set_title("Per-judge verdict distribution on the 1000-Q&A panel")
    ax.legend(loc="upper right", frameon=False, ncols=4, bbox_to_anchor=(1, 1.12))
    ax.set_ylim(0, max(dist[j]["agree"] for j in JUDGES) * 1.15)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "01_per_judge_verdict_distribution.png", dpi=DPI)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2 — pairwise Cohen's κ heatmap
# ---------------------------------------------------------------------------
def fig2():
    pairs = agree_mat["pairwise_cohens_kappa"]
    mat = np.ones((4, 4))
    for pair, info in pairs.items():
        a, b = pair.split("__")
        ia, ib = JUDGES.index(a), JUDGES.index(b)
        k = info["kappa"]
        if k is None:
            continue
        mat[ia, ib] = k
        mat[ib, ia] = k

    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    im = ax.imshow(mat, vmin=0.5, vmax=1.0, cmap="viridis")
    for i in range(4):
        for j in range(4):
            txt = f"{mat[i, j]:.3f}"
            color = "white" if mat[i, j] < 0.78 else "black"
            ax.text(j, i, txt, ha="center", va="center", color=color, fontsize=10)
    ax.set_xticks(range(4), [JUDGE_LABELS[j] for j in JUDGES], rotation=20, ha="right")
    ax.set_yticks(range(4), [JUDGE_LABELS[j] for j in JUDGES])
    fig.colorbar(im, ax=ax, label="Cohen's κ")
    alpha = agree_mat.get("krippendorff_alpha_nominal")
    title = "Pairwise Cohen's κ — verdict agreement"
    if alpha is not None:
        title += f"\nKrippendorff's α (4 judges, nominal): {alpha:.3f}"
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "02_pairwise_kappa_heatmap.png", dpi=DPI)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3 — Gemma × panel-majority confusion matrix
# ---------------------------------------------------------------------------
def fig3():
    counts = np.zeros((len(VERDICTS), len(VERDICTS) + 1), dtype=int)
    col_labels = VERDICTS + ["no majority /\nmissing"]
    for r in samples:
        g = r["verdicts"].get("gemma")
        if g not in VERDICTS:
            continue
        maj = _panel_majority(r)
        if maj is None:
            counts[VERDICTS.index(g), -1] += 1
        else:
            counts[VERDICTS.index(g), VERDICTS.index(maj)] += 1

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    im = ax.imshow(counts, cmap="Blues")
    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            v = counts[i, j]
            if v == 0:
                continue
            # highlight off-diagonal (panel-majority ≠ Gemma)
            diag = (i == j)
            color = "white" if v > counts.max() * 0.55 else "black"
            ax.text(j, i, str(v), ha="center", va="center",
                    color=color, fontsize=11,
                    fontweight="bold" if not diag and j < len(VERDICTS) else "normal")
    ax.set_xticks(range(counts.shape[1]), col_labels)
    ax.set_yticks(range(counts.shape[0]), VERDICTS)
    ax.set_xlabel("panel majority (≥2 of Sonnet / GPT-5 / Gemini)")
    ax.set_ylabel("Gemma verdict")
    ax.set_title("Gemma verdict vs panel majority (off-diagonal = disagreement)")
    fig.colorbar(im, ax=ax, label="count")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "03_gemma_vs_panel_majority.png", dpi=DPI)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 4 — majority-disagrees rate by Gemma's original verdict
# ---------------------------------------------------------------------------
def fig4():
    buckets = {v: [0, 0] for v in VERDICTS}  # [n_evaluable, n_majority_disagrees]
    for r in samples:
        evaluable, disagrees = _panel_majority_disagrees(r)
        if not evaluable:
            continue
        g = r["verdicts"]["gemma"]
        buckets[g][0] += 1
        if disagrees:
            buckets[g][1] += 1

    totals = [buckets[v][0] for v in VERDICTS]
    rates = [100 * buckets[v][1] / buckets[v][0] if buckets[v][0] else 0 for v in VERDICTS]

    fig, ax = plt.subplots(figsize=(6.4, 4.3))
    bars = ax.bar(VERDICTS, rates,
                  color=[VERDICT_COLORS[v] for v in VERDICTS])
    for b, rate, n, dis in zip(bars, rates,
                                totals,
                                [buckets[v][1] for v in VERDICTS]):
        ax.text(b.get_x() + b.get_width() / 2, rate + 0.8,
                f"{rate:.1f} %\n({dis}/{n})",
                ha="center", va="bottom", fontsize=9)

    ax.axhline(15, color="red", linestyle="--", linewidth=1,
               label="15 % alarm threshold (PDF)")
    overall = sum(buckets[v][1] for v in VERDICTS) / sum(buckets[v][0] for v in VERDICTS) * 100
    ax.axhline(overall, color="black", linestyle=":", linewidth=1,
               label=f"overall rate: {overall:.1f} %")
    ax.set_ylabel("% rows where panel majority disagrees with Gemma")
    ax.set_xlabel("Gemma's original verdict")
    ax.set_title("Majority-disagrees-with-Gemma rate, stratified by Gemma's own verdict")
    ax.set_ylim(0, max(rates) * 1.35 + 5)
    ax.legend(loc="upper left", frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "04_majority_disagrees_by_verdict.png", dpi=DPI)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 5 — majority-disagrees rate by topic (top 20 by n)
# ---------------------------------------------------------------------------
def fig5():
    topic_stats: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    for r in samples:
        evaluable, disagrees = _panel_majority_disagrees(r)
        if not evaluable:
            continue
        t = r.get("topic", "?")
        topic_stats[t][0] += 1
        if disagrees:
            topic_stats[t][1] += 1

    top = sorted(topic_stats.items(), key=lambda kv: -kv[1][0])[:20]
    topics = [k for k, _ in top]
    ns = [v[0] for _, v in top]
    rates = [100 * v[1] / v[0] for _, v in top]

    # sort displayed bars by rate (ascending), so highest is at top
    order = np.argsort(rates)
    topics = [topics[i] for i in order]
    ns = [ns[i] for i in order]
    rates = [rates[i] for i in order]

    fig, ax = plt.subplots(figsize=(8.2, 6.4))
    bars = ax.barh(topics, rates, color="#1c7ed6")
    for b, r, n in zip(bars, rates, ns):
        ax.text(r + 0.3, b.get_y() + b.get_height() / 2,
                f"{r:.1f}%  (n={n})", va="center", fontsize=8)
    ax.set_xlabel("% rows where panel majority disagrees with Gemma")
    ax.set_title("Majority-disagrees rate by topic (top 20 topics by sample size)")
    ax.axvline(4.7, color="black", linestyle=":", linewidth=1, label="overall rate: 4.7 %")
    ax.axvline(15, color="red", linestyle="--", linewidth=1, label="15 % alarm threshold")
    ax.set_xlim(0, max(rates) * 1.4 + 3)
    ax.legend(loc="lower right", frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "05_majority_disagrees_by_topic.png", dpi=DPI)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 6 — per-judge confusion vs Gemma
# ---------------------------------------------------------------------------
def fig6():
    new_judges = ["sonnet", "gpt5", "gemini"]
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.4), sharey=True)

    all_counts = []
    for j in new_judges:
        mat = np.zeros((len(VERDICTS), len(VERDICTS) + 1), dtype=int)
        for r in samples:
            g = r["verdicts"].get("gemma")
            v = r["verdicts"].get(j)
            if g not in VERDICTS:
                continue
            if v in VERDICTS:
                mat[VERDICTS.index(g), VERDICTS.index(v)] += 1
            else:
                mat[VERDICTS.index(g), -1] += 1
        all_counts.append(mat)
    vmax = max(m.max() for m in all_counts)

    col_labels = VERDICTS + ["missing"]
    for ax, j, mat in zip(axes, new_judges, all_counts):
        im = ax.imshow(mat, cmap="Blues", vmin=0, vmax=vmax)
        for i in range(mat.shape[0]):
            for k in range(mat.shape[1]):
                v = mat[i, k]
                if v == 0:
                    continue
                color = "white" if v > vmax * 0.55 else "black"
                bold = (i != k and k < len(VERDICTS))
                ax.text(k, i, str(v), ha="center", va="center",
                        color=color, fontsize=10,
                        fontweight="bold" if bold else "normal")
        ax.set_xticks(range(mat.shape[1]), col_labels, rotation=20, ha="right")
        ax.set_yticks(range(mat.shape[0]), VERDICTS)
        kappa_pair = agree_mat["pairwise_cohens_kappa"].get(f"gemma__{j}", {})
        k_val = kappa_pair.get("kappa")
        ktxt = f" (κ={k_val:.3f})" if k_val is not None else ""
        ax.set_title(f"Gemma vs {JUDGE_LABELS[j]}{ktxt}")
        ax.set_xlabel(f"{JUDGE_LABELS[j]} verdict")
    axes[0].set_ylabel("Gemma verdict")
    fig.suptitle("Per-judge verdicts vs Gemma's verdict (off-diagonal = disagreement)",
                 fontsize=12, y=1.02)
    fig.colorbar(im, ax=axes, label="count", shrink=0.85)
    fig.savefig(FIG_DIR / "06_per_judge_confusion_vs_gemma.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6()
    for f in sorted(FIG_DIR.iterdir()):
        print(f"wrote {f.relative_to(HERE)}  ({f.stat().st_size // 1024} KB)")
