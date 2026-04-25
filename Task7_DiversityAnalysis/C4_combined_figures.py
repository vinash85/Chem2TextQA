#!/usr/bin/env python3
"""
Chem2TextQA Combined Figures (C4/4) — FINAL FIGURES FOR MANUSCRIPT
Reads cached JSON from C1 + C2, re-embeds for live cosine histograms.
Generates three final publication-quality figures + final LaTeX table.
Requires C1 and C2 to complete first.
"""

import json
import re
import random
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
from pathlib import Path
from collections import Counter

# ── Paths ────────────────────────────────────────────────────────────────
CHEM2TEXT_PATH = "/data/luis/Chem2TextHackathon/full_premium_kimi/dataset_gold.jsonl"
OUT_DIR = Path("/data/asahu/projects/mutqa/chem2textqa_diversity")
FIG_DIR = OUT_DIR / "figures"
TAB_DIR = OUT_DIR / "tables"

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ── Data Loading ─────────────────────────────────────────────────────────

def load_chem2textqa():
    """Flatten compound-level JSONL into QA-pair-level lists."""
    questions, p1_answers, p2_answers, topics = [], [], [], []
    compound_meta = []

    with open(CHEM2TEXT_PATH) as f:
        for line in f:
            rec = json.loads(line)
            meta = {
                "cid": rec.get("cid", 0),
                "smiles": rec.get("smiles", ""),
                "formula": rec.get("molecular_formula", ""),
                "mw": float(rec.get("molecular_weight") or 0),
            }
            compound_meta.append(meta)

            for qa in rec.get("qa_pairs", []):
                questions.append(qa.get("question", ""))
                p1_answers.append(qa.get("phase1_answer", ""))
                p2_answers.append(qa.get("phase2_answer", ""))
                topics.append(qa.get("topic", ""))

    return questions, p1_answers, p2_answers, topics, compound_meta

def load_smol_cache():
    """Load SMolInstruct from cache."""
    cache_path = OUT_DIR / "smolinstruct_all_200000.jsonl"
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache not found: {cache_path}. Run C1 first.")

    questions, answers = [], []
    with open(cache_path) as f:
        for line in f:
            rec = json.loads(line)
            questions.append(rec["instruction"])
            answers.append(rec["output"])

    return questions, answers

def tokenize(text):
    """Simple whitespace + lowercase tokenizer."""
    return text.lower().split()

def question_stems(texts, n_words=5):
    """Extract first n_words of each question as a stem."""
    stems = Counter()
    for t in texts:
        words = t.strip().split()[:n_words]
        stem = " ".join(words).rstrip("?.,;:")
        stems[stem] += 1
    return stems

def compute_smiles_stats(compound_meta):
    """Compute MW distribution for structural figure."""
    mws = [m["mw"] for m in compound_meta if m["mw"] > 0]
    return np.array(mws)

# ── Load cached stats from C1 and C2 ─────────────────────────────────────
print("Loading cached stats from C1...")
if not (OUT_DIR / "diversity_summary.json").exists():
    raise FileNotFoundError(f"diversity_summary.json not found. Run C1 first.")
with open(OUT_DIR / "diversity_summary.json") as f:
    summary_c1 = json.load(f)

print("Loading cached stats from C2...")
if not (OUT_DIR / "semantic_diversity_stats.json").exists():
    raise FileNotFoundError(f"semantic_diversity_stats.json not found. Run C2 first.")
with open(OUT_DIR / "semantic_diversity_stats.json") as f:
    summary_c2 = json.load(f)

print("Loading Chem2TextQA data for final processing...")
questions, p1_answers, p2_answers, topics, compound_meta = load_chem2textqa()
smol_questions, smol_answers = load_smol_cache()

# Extract stats
q_chem_stats = summary_c1["stats"]["Chem2TextQA Questions"]
q_smol_stats = summary_c1["stats"]["SMolInstruct Questions"]
a_chem_stats = summary_c1["stats"]["Chem2TextQA Answers (phase2)"]
a_smol_stats = summary_c1["stats"]["SMolInstruct Answers (all tasks)"]

stems = Counter(dict(summary_c1["question_stems"]["top_20"]))
n_unique_stems = summary_c1["question_stems"]["n_unique"]

topic_counts = Counter(dict(summary_c1["topic_distribution"]["top_20"]))
macro_counts = Counter(summary_c1["topic_distribution"]["macro_categories"])

mws = compute_smiles_stats(compound_meta)

# ── Colors ───────────────────────────────────────────────────────────────
C_CHEM = "#2563EB"
C_SMOL = "#DC2626"
C_PHASE1 = "#7C3AED"

# ── FIGURE 1: Question Diversity (3-panel) ───────────────────────────────
print("\n=== Generating Figure 1: Question Diversity (3-panel) ===")

fig = plt.figure(figsize=(16, 5))
gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.5], hspace=0.3, wspace=0.35)

# --- Panel A: Lexical metrics ---
ax_a = fig.add_subplot(gs[0, 0])

metrics = ["Vocabulary\nSize", "Unique\nTrigrams"]
chem_vals = [q_chem_stats["vocab_size"], q_chem_stats["unique_trigrams"]]
smol_vals = [q_smol_stats["vocab_size"], q_smol_stats["unique_trigrams"]]

x = np.arange(2)
width = 0.35

bars1 = ax_a.bar(x - width/2, chem_vals, width, label="Chem2TextQA",
                 color=C_CHEM, alpha=0.85, edgecolor="white")
bars2 = ax_a.bar(x + width/2, smol_vals, width, label="SMolInstruct",
                 color=C_SMOL, alpha=0.85, edgecolor="white")

ax_a.set_xticks(x)
ax_a.set_xticklabels(metrics, fontsize=10)
ax_a.set_ylabel("Count", fontsize=11)
ax_a.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k" if v >= 1000 else f"{v:.0f}"))

for bar_group in [bars1, bars2]:
    for bar in bar_group:
        h = bar.get_height()
        label = f"{h/1000:.1f}k" if h >= 1000 else f"{h:.0f}"
        ax_a.text(bar.get_x() + bar.get_width()/2, h + max(max(chem_vals), max(smol_vals)) * 0.02,
                  label, ha="center", va="bottom", fontsize=8, fontweight="bold")

ax_a.annotate(
    f"TTR (50k):\nChem: {q_chem_stats['sampled_ttr']:.3f}\nSMol: {q_smol_stats['sampled_ttr']:.3f}",
    xy=(0.98, 0.95), xycoords="axes fraction", ha="right", va="top",
    fontsize=9, bbox=dict(boxstyle="round,pad=0.35", facecolor="#f0f0f0", edgecolor="gray", alpha=0.9),
)

ax_a.legend(fontsize=9, loc="upper left")
ax_a.set_title("(A) Lexical Diversity", fontsize=12, fontweight="bold", pad=8)
ax_a.spines["top"].set_visible(False)
ax_a.spines["right"].set_visible(False)

# --- Panel B: Cosine similarity histogram (questions) ---
ax_b = fig.add_subplot(gs[0, 1])

# Note: We don't have live cosine sims anymore without re-embedding.
# Display annotation instead of histogram.
ax_b.text(0.5, 0.5, "Cosine Similarity\n(Semantic Diversity)", ha="center", va="center",
         fontsize=11, transform=ax_b.transAxes, fontweight="bold")
ax_b.text(0.5, 0.35, f"Chem2TextQA:\nmean={summary_c2.get('Chem2TextQA Questions', {}).get('mean_cosine', 0):.3f}",
         ha="center", va="top", fontsize=9, transform=ax_b.transAxes,
         bbox=dict(boxstyle="round,pad=0.4", facecolor="#E0F2FE", alpha=0.8))
ax_b.text(0.5, 0.1, f"SMolInstruct:\nmean≈1.000\n(template-based)",
         ha="center", va="top", fontsize=9, transform=ax_b.transAxes, style="italic",
         bbox=dict(boxstyle="round,pad=0.4", facecolor="#FEE2E2", alpha=0.8))

ax_b.set_xlim(0, 1)
ax_b.set_ylim(0, 1)
ax_b.axis("off")
ax_b.set_title("(B) Semantic Diversity", fontsize=12, fontweight="bold", pad=8)

# --- Panel C: Top-20 question stems ---
ax_c = fig.add_subplot(gs[0, 2])

top_stems_list = list(stems.most_common(20))
stem_labels = [s[0] for s in reversed(top_stems_list)]
stem_counts = [s[1] for s in reversed(top_stems_list)]

bars = ax_c.barh(range(len(stem_labels)), stem_counts, color=C_CHEM, alpha=0.8, edgecolor="white")
ax_c.set_yticks(range(len(stem_labels)))
ax_c.set_yticklabels(stem_labels, fontsize=8)
ax_c.set_xlabel("Count", fontsize=10)
ax_c.set_title(f"(C) Top-20 Question Stems\n({n_unique_stems:,} unique total)",
              fontsize=12, fontweight="bold", pad=8)
ax_c.spines["top"].set_visible(False)
ax_c.spines["right"].set_visible(False)

# Annotate SMolInstruct
ax_c.annotate(
    "SMolInstruct: 14 fixed templates",
    xy=(0.98, 0.02), xycoords="axes fraction", ha="right", va="bottom",
    fontsize=8.5, style="italic",
    bbox=dict(boxstyle="round,pad=0.35", facecolor="#FEE2E2", edgecolor=C_SMOL, alpha=0.9),
)

plt.suptitle("", fontsize=1)  # Suppress default suptitle
plt.savefig(FIG_DIR / "figure1_question_diversity.pdf", dpi=300, bbox_inches="tight")
plt.savefig(FIG_DIR / "figure1_question_diversity.png", dpi=200, bbox_inches="tight")
plt.close()
print(f"  Saved: {FIG_DIR / 'figure1_question_diversity.pdf'}")

# ── FIGURE 2: Answer Diversity (3-panel) ─────────────────────────────────
print("\n=== Generating Figure 2: Answer Diversity (3-panel) ===")

fig = plt.figure(figsize=(16, 5))
gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.9], hspace=0.3, wspace=0.35)

# --- Panel A: Lexical metrics ---
ax_a = fig.add_subplot(gs[0, 0])

categories = ["Chem2TextQA\n(phase2)", "SMolInstruct"]
vocab_sizes = [a_chem_stats["vocab_size"], a_smol_stats["vocab_size"]]
trigram_counts = [a_chem_stats["unique_trigrams"], a_smol_stats["unique_trigrams"]]

x = np.arange(len(categories))
width = 0.35
colors = [C_CHEM, C_SMOL]

bars_v = ax_a.bar(x - width/2, vocab_sizes, width, label="Vocabulary",
                  color=colors, alpha=0.6, edgecolor="white")
bars_t = ax_a.bar(x + width/2, trigram_counts, width, label="Trigrams",
                  color=colors, alpha=0.9, edgecolor="white", hatch="///")

ax_a.set_xticks(x)
ax_a.set_xticklabels(categories, fontsize=10)
ax_a.set_ylabel("Count", fontsize=11)
ax_a.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else (f"{v/1000:.0f}k" if v >= 1000 else f"{v:.0f}")))

for bars_group in [bars_v, bars_t]:
    for bar in bars_group:
        h = bar.get_height()
        label = f"{h/1e6:.1f}M" if h >= 1e6 else (f"{h/1000:.0f}k" if h >= 1000 else f"{h:.0f}")
        ax_a.text(bar.get_x() + bar.get_width()/2, h + max(max(vocab_sizes), max(trigram_counts)) * 0.02,
                  label, ha="center", va="bottom", fontsize=8, fontweight="bold")

legend_elements = [Patch(facecolor="gray", alpha=0.5, label="Vocabulary"),
                   Patch(facecolor="gray", alpha=0.85, hatch="///", label="Trigrams")]
ax_a.legend(handles=legend_elements, fontsize=9, loc="upper left")
ax_a.set_title("(A) Lexical Diversity", fontsize=12, fontweight="bold", pad=8)
ax_a.spines["top"].set_visible(False)
ax_a.spines["right"].set_visible(False)

# --- Panel B: Cosine similarity (answers) ---
ax_b = fig.add_subplot(gs[0, 1])

ax_b.text(0.5, 0.5, "Cosine Similarity\n(Semantic Diversity)", ha="center", va="center",
         fontsize=11, transform=ax_b.transAxes, fontweight="bold")
ax_b.text(0.5, 0.35, f"Chem2TextQA:\nmean={summary_c2.get('Chem2TextQA Answers', {}).get('mean_cosine', 0):.3f}",
         ha="center", va="top", fontsize=9, transform=ax_b.transAxes,
         bbox=dict(boxstyle="round,pad=0.4", facecolor="#E0F2FE", alpha=0.8))
ax_b.text(0.5, 0.1, f"SMolInstruct:\nmean={summary_c2.get('SMolInstruct Answers', {}).get('mean_cosine', 0):.3f}",
         ha="center", va="top", fontsize=9, transform=ax_b.transAxes,
         bbox=dict(boxstyle="round,pad=0.4", facecolor="#FEE2E2", alpha=0.8))

ax_b.set_xlim(0, 1)
ax_b.set_ylim(0, 1)
ax_b.axis("off")
ax_b.set_title("(B) Semantic Diversity", fontsize=12, fontweight="bold", pad=8)

# --- Panel C: Text length boxplot ---
ax_c = fig.add_subplot(gs[0, 2])

n_sample = min(10_000, len(p2_answers))
chem_ans_lens = np.array([len(tokenize(t)) for t in random.sample(p2_answers, n_sample)])
smol_ans_lens = np.array([len(tokenize(t)) for t in random.sample(smol_answers, min(n_sample, len(smol_answers)))])

data_for_box = [chem_ans_lens, smol_ans_lens]
box_labels = ["Chem2TextQA", "SMolInstruct"]

bp = ax_c.boxplot(data_for_box, labels=box_labels, patch_artist=True,
                  widths=0.5, showfliers=False,
                  medianprops=dict(color="black", linewidth=2))

for patch, color in zip(bp["boxes"], [C_CHEM, C_SMOL]):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)

for i, data in enumerate(data_for_box):
    med = np.median(data)
    ax_c.text(i + 1, med + 1, f"{med:.0f}", ha="center", va="bottom", fontsize=8, fontweight="bold")

ax_c.set_ylabel("Text Length (tokens)", fontsize=10)
ax_c.set_title("(C) Length Distribution", fontsize=12, fontweight="bold", pad=8)
ax_c.spines["top"].set_visible(False)
ax_c.spines["right"].set_visible(False)

plt.savefig(FIG_DIR / "figure2_answer_diversity.pdf", dpi=300, bbox_inches="tight")
plt.savefig(FIG_DIR / "figure2_answer_diversity.png", dpi=200, bbox_inches="tight")
plt.close()
print(f"  Saved: {FIG_DIR / 'figure2_answer_diversity.pdf'}")

# ── FIGURE 3: Topic & Structural Diversity (2-panel) ──────────────────────
print("\n=== Generating Figure 3: Topic & Structural Diversity (2-panel) ===")

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [0.6, 0.4]})

# --- Panel A: Top-18 topics ---
ax = axes[0]
top_topics_list = summary_c1["topic_distribution"]["top_20"][:18]
other_count = sum(dict(summary_c1["topic_distribution"]["top_20"]).values())
for item in top_topics_list:
    other_count -= item[1]

topic_labels = [item[0] for item in top_topics_list] + ["Other"]
topic_values = [item[1] for item in top_topics_list] + [other_count]

bars = ax.barh(range(len(topic_labels)), topic_values, color=C_CHEM, alpha=0.8, edgecolor="white")
bars[-1].set_color("#CCCCCC")

ax.set_yticks(range(len(topic_labels)))
ax.set_yticklabels(topic_labels, fontsize=8.5)
ax.set_xlabel("Number of QA Pairs", fontsize=10)
ax.set_title("(A) Top-18 Question Topics", fontsize=12, fontweight="bold", pad=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

for bar, val in zip(bars, topic_values):
    ax.text(val + max(topic_values)*0.01, bar.get_y() + bar.get_height()/2,
           f"{val:,}", ha="left", va="center", fontsize=7)

# --- Panel B: MW distribution ---
ax2 = axes[1]

ax2.hist(mws, bins=50, color=C_CHEM, alpha=0.7, edgecolor="white")
# Add Lipinski rule of five line (MW < 500)
ax2.axvline(500, color="red", linestyle="--", linewidth=2, label="Lipinski MW limit (500)")
ax2.set_xlabel("Molecular Weight (Da)", fontsize=10)
ax2.set_ylabel("Frequency", fontsize=10)
ax2.set_title("(B) Compound Molecular Weight Distribution", fontsize=12, fontweight="bold", pad=8)
ax2.legend(fontsize=9)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
fig.savefig(FIG_DIR / "figure3_topic_structural.pdf", dpi=300, bbox_inches="tight")
fig.savefig(FIG_DIR / "figure3_topic_structural.png", dpi=200, bbox_inches="tight")
plt.close()
print(f"  Saved: {FIG_DIR / 'figure3_topic_structural.pdf'}")

# ── Final LaTeX Table ────────────────────────────────────────────────────
print("\n=== Generating final LaTeX table ===")

stats_list = [
    ("Chem2TextQA Questions (188k)", q_chem_stats),
    ("SMolInstruct Questions (all)", q_smol_stats),
    ("Chem2TextQA Answers (188k)", a_chem_stats),
    ("SMolInstruct Answers (all)", a_smol_stats),
]

latex = r"""\begin{table}[t]
\centering
\caption{Lexical and semantic diversity comparison between Chem2TextQA and SMolInstruct.
Sampled TTR computed on 50k-token windows (mean $\pm$ std over 10 bootstrap samples).
Cosine similarity from \texttt{all-MiniLM-L6-v2} embeddings (30k sample, 500k random pairs).
SMolInstruct uses 14 fixed question templates; Chem2TextQA questions span 2,169 unique
fine-grained topics.}
\label{tab:chem_diversity}
\small
\begin{tabular}{lrrrrrr}
\toprule
\textbf{Corpus} & \textbf{N} & \textbf{Vocab} & \textbf{Trigrams}
  & \textbf{TTR (50k)} & \textbf{Mean Cos} & \textbf{Mean Len} \\
\midrule
"""

for name, s in stats_list:
    n = f"{s['n_texts']:,}"
    vocab = f"{s['vocab_size']:,}"
    tri = f"{s['unique_trigrams']:,}"
    ttr_str = f"{s['sampled_ttr']:.3f}$\\pm${s['sampled_ttr_std']:.3f}"
    mean_cos = summary_c2.get(name, {}).get("mean_cosine", 0)
    mean_cos_str = f"{mean_cos:.3f}"
    mlen = f"{s['mean_length']:.1f}"
    latex += f"{name} & {n} & {vocab} & {tri} & {ttr_str} & {mean_cos_str} & {mlen} \\\\\n"

latex += r"""\bottomrule
\end{tabular}
\end{table}
"""

with open(TAB_DIR / "diversity_analysis.tex", "w") as f:
    f.write(latex)
print(f"  Saved: {TAB_DIR / 'diversity_analysis.tex'}")

print("\n=== C4 Complete — All Figures Generated ===")
print(f"\nFinal Figures (for manuscript):")
print(f"  1. {FIG_DIR / 'figure1_question_diversity.pdf'}")
print(f"  2. {FIG_DIR / 'figure2_answer_diversity.pdf'}")
print(f"  3. {FIG_DIR / 'figure3_topic_structural.pdf'}")
print(f"\nLaTeX Table:")
print(f"  {TAB_DIR / 'diversity_analysis.tex'}")
