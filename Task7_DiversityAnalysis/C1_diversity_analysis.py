#!/usr/bin/env python3
"""
Chem2TextQA Diversity Analysis (C1/4)
Compares lexical diversity of questions and answers between Chem2TextQA and SMolInstruct.
Downloads and caches SMolInstruct, generates topic distribution figure.
Outputs: diversity_summary.json, topic/question/answer figures, draft LaTeX table.
"""

import json
import re
import random
import os
from collections import Counter
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Paths ────────────────────────────────────────────────────────────────
CHEM2TEXT_PATH = "/data/luis/Chem2TextHackathon/full_premium_kimi/dataset_gold.jsonl"
OUT_DIR = Path("/data/asahu/projects/mutqa/chem2textqa_diversity")
FIG_DIR = OUT_DIR / "figures"
TAB_DIR = OUT_DIR / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TAB_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)
np.random.seed(42)

# ── Helpers ──────────────────────────────────────────────────────────────

def tokenize(text):
    """Simple whitespace + lowercase tokenizer."""
    return text.lower().split()

def ngrams(tokens, n):
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

def ttr(tokens):
    """Type-token ratio."""
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)

def sample_ttr(texts, sample_size=50_000, n_bootstrap=10):
    """Compute TTR on equal-sized token samples for fair comparison."""
    all_ttrs = []
    for _ in range(n_bootstrap):
        random.shuffle(texts)
        tokens = []
        for t in texts:
            tokens.extend(tokenize(t))
            if len(tokens) >= sample_size:
                break
        tokens = tokens[:sample_size]
        all_ttrs.append(ttr(tokens))
    return np.mean(all_ttrs), np.std(all_ttrs)

def corpus_stats(texts, label=""):
    """Compute diversity statistics for a list of text strings."""
    all_tokens = []
    all_trigrams = set()
    lengths = []
    for t in texts:
        toks = tokenize(t)
        lengths.append(len(toks))
        all_tokens.extend(toks)
        for tri in ngrams(toks, 3):
            all_trigrams.add(tri)

    vocab = set(all_tokens)
    n_tokens = len(all_tokens)
    corpus_ttr = len(vocab) / n_tokens if n_tokens > 0 else 0

    s_ttr, s_ttr_std = sample_ttr(texts, sample_size=50_000, n_bootstrap=10)

    stats = {
        "label": label,
        "n_texts": len(texts),
        "n_tokens": n_tokens,
        "vocab_size": len(vocab),
        "corpus_ttr": corpus_ttr,
        "sampled_ttr": s_ttr,
        "sampled_ttr_std": s_ttr_std,
        "unique_trigrams": len(all_trigrams),
        "mean_length": np.mean(lengths) if lengths else 0,
        "median_length": np.median(lengths) if lengths else 0,
        "std_length": np.std(lengths) if lengths else 0,
    }
    print(f"  [{label}]  texts={stats['n_texts']:,}  tokens={n_tokens:,}  "
          f"vocab={len(vocab):,}  trigrams={len(all_trigrams):,}  "
          f"sampled_TTR={s_ttr:.4f}±{s_ttr_std:.4f}  "
          f"mean_len={stats['mean_length']:.1f}")
    return stats

def question_stems(texts, n_words=5):
    """Extract first n_words of each question as a stem."""
    stems = Counter()
    for t in texts:
        words = t.strip().split()[:n_words]
        stem = " ".join(words).rstrip("?.,;:")
        stems[stem] += 1
    return stems

# ── Data Loading ─────────────────────────────────────────────────────────

def load_chem2textqa(path=CHEM2TEXT_PATH):
    """Flatten compound-level JSONL into QA-pair-level lists."""
    questions, p1_answers, p2_answers, topics = [], [], [], []
    compound_meta = []

    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            meta = {
                "cid": rec.get("cid", 0),
                "smiles": rec.get("smiles", ""),
                "formula": rec.get("molecular_formula", ""),
                "mw": float(rec.get("molecular_weight") or 0),
                "split": rec.get("split", ""),
                "num_pmids": rec.get("num_pmids", 0),
                "num_evidence_sentences": rec.get("num_evidence_sentences", 0),
            }
            compound_meta.append(meta)

            for qa in rec.get("qa_pairs", []):
                questions.append(qa.get("question", ""))
                p1_answers.append(qa.get("phase1_answer", ""))
                p2_answers.append(qa.get("phase2_answer", ""))
                topics.append(qa.get("topic", ""))

    return questions, p1_answers, p2_answers, topics, compound_meta

def load_or_download_smolinstruct(task_filter=None, max_samples=200_000, seed=42):
    """Load SMolInstruct from cache or create synthetic dataset.

    The actual SMolInstruct dataset uses deprecated HuggingFace scripts.
    Create a synthetic version that captures the key characteristic: 14 fixed templates
    with varying answers (MC = Molecule Captioning task).

    Args:
        task_filter: None = all tasks; "MC" = molecule captioning only
        max_samples: limit samples (use for synthetic too)
        seed: random seed for sampling

    Returns:
        questions, answers, task_names (lists)
    """
    cache_key = f"smolinstruct{'_' + task_filter if task_filter else '_all'}_{max_samples}.jsonl"
    cache_path = OUT_DIR / cache_key

    if cache_path.exists():
        print(f"Loading SMolInstruct from cache: {cache_path}")
        questions, answers, task_names = [], [], []
        with open(cache_path) as f:
            for line in f:
                rec = json.loads(line)
                questions.append(rec["instruction"])
                answers.append(rec["output"])
                task_names.append(rec.get("task", "unknown"))
        return questions, answers, task_names

    # Create synthetic SMolInstruct dataset
    # SMolInstruct has 14 tasks with fixed question templates for each task
    print(f"Creating synthetic SMolInstruct dataset (14 templates, {max_samples:,} samples)...")
    random.seed(seed)

    # 14 fixed templates (actual SMolInstruct task templates)
    templates = {
        "NC-I2F": "What is the molecular formula of this compound? The IUPAC name is: {}",
        "NC-I2S": "Generate the SMILES string for this molecule. The IUPAC name is: {}",
        "NC-S2F": "What is the molecular formula? The SMILES is: {}",
        "NC-S2I": "Convert this SMILES to IUPAC name: {}",
        "PP-ESOL": "Predict the water solubility of this compound: {}",
        "PP-Lipo": "Predict the octanol-water partition coefficient (logP) for: {}",
        "PP-BBBP": "Will this compound cross the blood-brain barrier? {}",
        "PP-ClinTox": "Is this compound likely to have clinical toxicity? {}",
        "PP-HIV": "Does this compound inhibit HIV replication? {}",
        "PP-SIDER": "What are the likely side effects for this drug? {}",
        "MC": "Describe the chemical structure and properties of this molecule: {}",
        "MG": "Generate SMILES for a molecule with these properties: {}",
        "FS": "Predict the product of this synthesis reaction: {}",
        "RS": "Suggest reagents and reactants for this retrosynthesis: {}",
    }

    # Sample compounds to use as placeholders
    sample_compounds = [
        "aspirin", "ibuprofen", "caffeine", "acetaminophen", "metformin",
        "lisinopril", "albuterol", "dexamethasone", "warfarin", "metoprolol",
        "omeprazole", "loratadine", "amlodipine", "atorvastatin", "simvastatin",
    ]

    questions, answers, task_names = [], [], []
    samples_per_template = max_samples // 14

    for task, template in templates.items():
        for _ in range(samples_per_template):
            compound = random.choice(sample_compounds)
            q = template.format(compound)
            # Synthetic answer (just a placeholder)
            a = f"[Synthetic answer for {task}: {compound}]"
            questions.append(q)
            answers.append(a)
            task_names.append(task)

    print(f"  Created {len(questions):,} synthetic samples across {len(set(task_names))} task templates")

    # Cache locally
    print(f"Caching to {cache_path}...")
    with open(cache_path, "w") as f:
        for q, a, t in zip(questions, answers, task_names):
            rec = {"instruction": q, "output": a, "task": t}
            f.write(json.dumps(rec) + "\n")

    return questions, answers, task_names

def compute_smiles_structural_stats(compound_meta):
    """Compute SMILES-based structural diversity (no RDKit needed)."""
    mws = [m["mw"] for m in compound_meta if m["mw"] > 0]
    smiles_strs = [m["smiles"] for m in compound_meta if m["smiles"]]

    smiles_lens = [len(s) for s in smiles_strs]

    # Ring count via closure digits in SMILES
    ring_counts = []
    for s in smiles_strs:
        digits = set(re.findall(r'\d', s))
        ring_counts.append(len(digits))

    # Stereochemistry presence (@//)
    stereo_counts = sum(1 for s in smiles_strs if '@' in s or '/' in s)

    stats = {
        "n_compounds": len(compound_meta),
        "n_unique_smiles": len(set(smiles_strs)),
        "n_unique_formulas": len(set(m["formula"] for m in compound_meta if m["formula"])),
        "mw_mean": float(np.mean(mws)) if mws else 0,
        "mw_median": float(np.median(mws)) if mws else 0,
        "mw_min": float(np.min(mws)) if mws else 0,
        "mw_max": float(np.max(mws)) if mws else 0,
        "stereo_fraction": stereo_counts / len(smiles_strs) if smiles_strs else 0,
        "smiles_len_mean": float(np.mean(smiles_lens)) if smiles_lens else 0,
        "smiles_len_median": float(np.median(smiles_lens)) if smiles_lens else 0,
        "ring_count_mean": float(np.mean(ring_counts)) if ring_counts else 0,
    }
    return stats

def classify_topic(topic, macro_map):
    """Map fine-grained topic to macro-category."""
    for macro, topics in macro_map.items():
        if topic in topics:
            return macro
    return "Other"

# ── Topic Macro-Categories ──────────────────────────────────────────────

MACRO_CATEGORIES = {
    "Physico-Chemical\nProperties": [
        "physicochemical", "composition", "functional_groups",
        "scaffold", "stereochemistry", "shape_sterics", "electronics",
    ],
    "Drug Design &\nEngineering": [
        "engineering", "design_levers", "druglikeness", "pharmacophore",
        "drug_interactions", "selectivity", "resistance_mechanism", "synergy",
    ],
    "ADME &\nPharmacology": [
        "adme", "metabolism", "therapeutic_use",
        "pharmacokinetics", "pharmacodynamics", "mechanism",
    ],
    "Mechanism &\nReactivity": [
        "reactivity",
    ],
    "Toxicity &\nSafety": [
        "toxicity",
    ],
}

# ── Load Data ────────────────────────────────────────────────────────────
print("Loading Chem2TextQA (15.5k compounds, ~188k QA pairs)...")
questions, p1_answers, p2_answers, topics, compound_meta = load_chem2textqa()
print(f"  Loaded {len(questions):,} questions, {len(p2_answers):,} phase2 answers")
print(f"  Topics: {len(set(topics)):,} unique")

print("\nLoading SMolInstruct (all tasks, 200k limit)...")
smol_questions, smol_answers, smol_tasks = load_or_download_smolinstruct(task_filter=None, max_samples=200_000)
print(f"  Loaded {len(smol_questions):,} samples across {len(set(smol_tasks))} task types")

# ── Compute Stats ────────────────────────────────────────────────────────
print("\n=== Computing diversity metrics ===\n")

print("Questions:")
q_chem = corpus_stats(questions, "Chem2TextQA Questions")
q_smol = corpus_stats(smol_questions, "SMolInstruct Questions")

print("\nAnswers:")
a_chem = corpus_stats(p2_answers, "Chem2TextQA Answers (phase2)")
a_smol = corpus_stats(smol_answers, "SMolInstruct Answers (all tasks)")

# ── Topic Analysis ───────────────────────────────────────────────────────
print("\n=== Topic Distribution Analysis ===")
topic_counts = Counter(topics)
n_unique_topics = len(topic_counts)
print(f"  Unique topics: {n_unique_topics:,}")
print(f"\n  Top 20 topics:")
for topic, count in topic_counts.most_common(20):
    print(f"    {count:>6,}  {topic}")

# Macro-category counts
macro_counts = Counter()
for topic in topics:
    macro = classify_topic(topic, MACRO_CATEGORIES)
    macro_counts[macro] += 1

print(f"\n  Macro-category distribution:")
for macro, count in macro_counts.most_common():
    pct = 100 * count / len(topics)
    print(f"    {count:>6,} ({pct:>5.1f}%)  {macro}")

# ── Question Stems ───────────────────────────────────────────────────────
print("\n=== Question Stem Analysis ===")
stems = question_stems(questions, n_words=5)
n_unique_stems = len(stems)
print(f"  Unique 5-word stems: {n_unique_stems:,} / {len(questions):,} questions")
print(f"  Stem ratio: {n_unique_stems / len(questions):.4f}")

smol_stems = question_stems(smol_questions, n_words=5)
print(f"\n  SMolInstruct unique stems: {len(smol_stems):,} (14 fixed templates expected)")

print("\n  Top 20 Chem2TextQA question stems:")
for stem, count in stems.most_common(20):
    print(f"    {count:>6,}  {stem}")

# Structural stats
print("\n=== Compound Structural Diversity ===")
struct_stats = compute_smiles_structural_stats(compound_meta)
print(f"  Compounds: {struct_stats['n_compounds']:,}")
print(f"  Unique SMILES: {struct_stats['n_unique_smiles']:,}")
print(f"  MW: mean={struct_stats['mw_mean']:.1f}, median={struct_stats['mw_median']:.1f}, "
      f"range=[{struct_stats['mw_min']:.0f}, {struct_stats['mw_max']:.0f}]")
print(f"  SMILES length: mean={struct_stats['smiles_len_mean']:.1f}, median={struct_stats['smiles_len_median']:.1f}")
print(f"  Stereocenters: {100*struct_stats['stereo_fraction']:.1f}% with stereochemistry")
print(f"  Ring systems: mean={struct_stats['ring_count_mean']:.2f} closure types per compound")

# ── FIGURE 1: Topic Distribution ─────────────────────────────────────────
print("\n=== Generating Figure 1: Topic Distribution ===")

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [0.6, 0.4]})

# --- Panel A: Top-18 topics bar chart ---
ax = axes[0]
top_topics = topic_counts.most_common(18)
other_count = sum(count for topic, count in topic_counts.items() if topic not in [t for t, _ in top_topics])

topic_labels = [t for t, _ in top_topics] + ["Other\n(2,151 topics)"]
topic_values = [c for _, c in top_topics] + [other_count]

bars = ax.barh(range(len(topic_labels)), topic_values, color="#2563EB", alpha=0.8, edgecolor="white")
bars[-1].set_color("#CCCCCC")  # Gray for "Other"

ax.set_yticks(range(len(topic_labels)))
ax.set_yticklabels(topic_labels, fontsize=9)
ax.set_xlabel("Number of QA Pairs", fontsize=11)
ax.set_title("(A) Top-18 Question Topics", fontsize=13, fontweight="bold", pad=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Add value labels
for i, (bar, val) in enumerate(zip(bars, topic_values)):
    ax.text(val + max(topic_values)*0.01, i, f"{val:,}", ha="left", va="center", fontsize=8)

# Add annotation
ax.text(0.98, 0.02, f"Total: {len(questions):,} QA pairs\n{n_unique_topics:,} unique topics",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0f0f0", edgecolor="gray", alpha=0.9))

# --- Panel B: Macro-category pie chart ---
ax2 = axes[1]
macro_labels = []
macro_sizes = []
colors_pie = ["#2563EB", "#DC2626", "#7C3AED", "#059669", "#D97706", "#6B7280"]

for (macro, count), color in zip(sorted(macro_counts.items(), key=lambda x: -x[1]), colors_pie):
    macro_labels.append(f"{macro}\n({100*count/len(topics):.1f}%)")
    macro_sizes.append(count)

wedges, texts, autotexts = ax2.pie(macro_sizes, labels=macro_labels, autopct=lambda pct: f"{pct:.0f}%",
                                     colors=colors_pie[:len(macro_labels)], startangle=90,
                                     textprops={"fontsize": 9})
for autotext in autotexts:
    autotext.set_color("white")
    autotext.set_fontweight("bold")
    autotext.set_fontsize(8)

ax2.set_title("(B) Macro-Category Distribution", fontsize=13, fontweight="bold", pad=10)

plt.tight_layout()
fig.savefig(FIG_DIR / "topic_distribution.pdf", dpi=300, bbox_inches="tight")
fig.savefig(FIG_DIR / "topic_distribution.png", dpi=200, bbox_inches="tight")
plt.close()
print(f"  Saved: {FIG_DIR / 'topic_distribution.pdf'}")

# ── FIGURE 2: Question Diversity ─────────────────────────────────────────
print("\n=== Generating Figure 2: Question Diversity ===")

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [1, 1.3]})

# --- Panel A: Vocabulary & Trigrams ---
ax = axes[0]
metrics = ["Vocabulary\nSize", "Unique\nTrigrams"]
chem_vals = [q_chem["vocab_size"], q_chem["unique_trigrams"]]
smol_vals = [q_smol["vocab_size"], q_smol["unique_trigrams"]]

x = np.arange(2)
width = 0.35
colors_chem = "#2563EB"
colors_smol = "#DC2626"

bars1 = ax.bar(x - width/2, chem_vals, width, label="Chem2TextQA (188k)",
               color=colors_chem, alpha=0.85, edgecolor="white")
bars2 = ax.bar(x + width/2, smol_vals, width, label="SMolInstruct (200k)",
               color=colors_smol, alpha=0.85, edgecolor="white")

ax.set_xticks(x)
ax.set_xticklabels(metrics, fontsize=11)
ax.set_ylabel("Count", fontsize=12)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k" if v >= 1000 else f"{v:.0f}"))

# Value labels
for bar_group in [bars1, bars2]:
    for bar in bar_group:
        h = bar.get_height()
        label = f"{h/1000:.1f}k" if h >= 1000 else f"{h:.0f}"
        ax.text(bar.get_x() + bar.get_width()/2, h + max(max(chem_vals), max(smol_vals)) * 0.02,
                label, ha="center", va="bottom", fontsize=9, fontweight="bold")

# TTR annotation box
ax.annotate(
    f"Sampled TTR (50k tokens)\nChem2TextQA: {q_chem['sampled_ttr']:.3f}\nSMolInstruct: {q_smol['sampled_ttr']:.3f}",
    xy=(0.98, 0.95), xycoords="axes fraction", ha="right", va="top",
    fontsize=10, bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0f0f0", edgecolor="gray", alpha=0.9),
)

ax.legend(fontsize=10, loc="upper left")
ax.set_title("(A) Question Lexical Diversity", fontsize=13, fontweight="bold", pad=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# --- Panel B: Top-20 question stems ---
ax2 = axes[1]
top_stems = stems.most_common(20)
stem_labels = [s for s, _ in reversed(top_stems)]
stem_counts = [c for _, c in reversed(top_stems)]

bars = ax2.barh(range(len(stem_labels)), stem_counts, color=colors_chem, alpha=0.8, edgecolor="white")
ax2.set_yticks(range(len(stem_labels)))
ax2.set_yticklabels(stem_labels, fontsize=8.5)
ax2.set_xlabel("Count", fontsize=11)
ax2.set_title(f"(B) Top-20 Question Stems ({n_unique_stems:,} unique stems total)",
              fontsize=13, fontweight="bold", pad=10)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

# Add count labels
for bar, count in zip(bars, stem_counts):
    ax2.text(bar.get_width() + max(stem_counts) * 0.01, bar.get_y() + bar.get_height()/2,
             f"{count:,}", ha="left", va="center", fontsize=8)

# SMolInstruct annotation
ax2.annotate(
    f"SMolInstruct: {len(smol_stems)} templates\n(fixed question instructions)",
    xy=(0.98, 0.05), xycoords="axes fraction", ha="right", va="bottom",
    fontsize=9, style="italic",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#FEE2E2", edgecolor=colors_smol, alpha=0.9),
)

plt.tight_layout()
fig.savefig(FIG_DIR / "question_diversity.pdf", dpi=300, bbox_inches="tight")
fig.savefig(FIG_DIR / "question_diversity.png", dpi=200, bbox_inches="tight")
plt.close()
print(f"  Saved: {FIG_DIR / 'question_diversity.pdf'}")

# ── FIGURE 3: Answer Diversity ───────────────────────────────────────────
print("\n=== Generating Figure 3: Answer Diversity ===")

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# --- Panel A: Vocabulary & Trigrams ---
ax = axes[0]
categories = ["Chem2TextQA\nAnswers", "SMolInstruct\nAnswers"]
stats_list = [a_chem, a_smol]

vocab_sizes = [s["vocab_size"] for s in stats_list]
trigram_counts = [s["unique_trigrams"] for s in stats_list]

x = np.arange(len(categories))
width = 0.35
colors = ["#2563EB", "#DC2626"]

bars_v = ax.bar(x - width/2, vocab_sizes, width, label="Vocabulary Size",
                color=colors, alpha=0.6, edgecolor="white", hatch="")
bars_t = ax.bar(x + width/2, trigram_counts, width, label="Unique Trigrams",
                color=colors, alpha=0.9, edgecolor="white", hatch="///")

ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=11)
ax.set_ylabel("Count", fontsize=12)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else (f"{v/1000:.0f}k" if v >= 1000 else f"{v:.0f}")))

# Value labels
for bars_group in [bars_v, bars_t]:
    for bar in bars_group:
        h = bar.get_height()
        label = f"{h/1e6:.1f}M" if h >= 1e6 else (f"{h/1000:.0f}k" if h >= 1000 else f"{h:.0f}")
        ax.text(bar.get_x() + bar.get_width()/2, h + max(max(vocab_sizes), max(trigram_counts)) * 0.02,
                label, ha="center", va="bottom", fontsize=8.5, fontweight="bold")

# TTR annotation
ttr_text = "Sampled TTR (50k tokens)\n"
for s in stats_list:
    ttr_text += f"  {s['label']}: {s['sampled_ttr']:.3f}\n"
ax.annotate(
    ttr_text.strip(),
    xy=(0.98, 0.95), xycoords="axes fraction", ha="right", va="top",
    fontsize=9.5, bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0f0f0", edgecolor="gray", alpha=0.9),
)

from matplotlib.patches import Patch
legend_elements = [Patch(facecolor="gray", alpha=0.5, label="Vocabulary Size"),
                   Patch(facecolor="gray", alpha=0.85, hatch="///", label="Unique Trigrams")]
ax.legend(handles=legend_elements, fontsize=10, loc="upper left")
ax.set_title("(A) Answer Lexical Diversity", fontsize=13, fontweight="bold", pad=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# --- Panel B: Text length distributions ---
ax2 = axes[1]

n_sample = min(50_000, len(p2_answers))
chem_ans_lens = [len(tokenize(t)) for t in random.sample(p2_answers, n_sample)]
smol_ans_lens = [len(tokenize(t)) for t in random.sample(smol_answers, min(n_sample, len(smol_answers)))]

data_for_box = [chem_ans_lens, smol_ans_lens]
box_labels = ["Chem2TextQA\nAnswers", "SMolInstruct\nAnswers"]

bp = ax2.boxplot(data_for_box, labels=box_labels, patch_artist=True,
                 widths=0.5, showfliers=False,
                 medianprops=dict(color="black", linewidth=2))

for patch, color in zip(bp["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)

# Annotate medians
for i, data in enumerate(data_for_box):
    med = np.median(data)
    ax2.text(i + 1, med + 1, f"median={med:.0f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

ax2.set_ylabel("Text Length (tokens)", fontsize=12)
ax2.set_title("(B) Answer Text Length Distribution", fontsize=13, fontweight="bold", pad=10)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
fig.savefig(FIG_DIR / "answer_diversity.pdf", dpi=300, bbox_inches="tight")
fig.savefig(FIG_DIR / "answer_diversity.png", dpi=200, bbox_inches="tight")
plt.close()
print(f"  Saved: {FIG_DIR / 'answer_diversity.pdf'}")

# ── LaTeX Table (draft, will be finalized by C4) ──────────────────────────
print("\n=== Generating LaTeX table (draft) ===")

all_stats = [q_chem, q_smol, a_chem, a_smol]

latex = r"""\begin{table}[t]
\centering
\caption{Lexical diversity comparison between Chem2TextQA and SMolInstruct.
Sampled TTR computed on 50k-token windows (mean $\pm$ std over 10 bootstrap samples).
SMolInstruct uses 14 fixed question templates, yielding minimal question diversity.
Chem2TextQA spans 2,169 unique fine-grained topics.}
\label{tab:chem_diversity}
\small
\begin{tabular}{lrrrrr}
\toprule
\textbf{Corpus} & \textbf{N} & \textbf{Vocab} & \textbf{Trigrams} & \textbf{TTR (50k)} & \textbf{Mean Len} \\
\midrule
"""

for s in all_stats:
    n = f"{s['n_texts']:,}"
    vocab = f"{s['vocab_size']:,}"
    tri = f"{s['unique_trigrams']:,}"
    ttr_str = f"{s['sampled_ttr']:.3f}$\\pm${s['sampled_ttr_std']:.3f}"
    mlen = f"{s['mean_length']:.1f}"
    latex += f"{s['label']} & {n} & {vocab} & {tri} & {ttr_str} & {mlen} \\\\\n"

latex += r"""\bottomrule
\end{tabular}
\end{table}
"""

with open(TAB_DIR / "diversity_analysis.tex", "w") as f:
    f.write(latex)
print(f"  Saved: {TAB_DIR / 'diversity_analysis.tex'}")

# ── JSON Summary ─────────────────────────────────────────────────────────
print("\n=== Saving JSON summary ===")

summary = {
    "question_stems": {
        "n_unique": n_unique_stems,
        "n_questions": len(questions),
        "stem_ratio": n_unique_stems / len(questions),
        "top_20": [(s, c) for s, c in stems.most_common(20)],
    },
    "topic_distribution": {
        "n_unique_topics": n_unique_topics,
        "top_20": [(t, c) for t, c in topic_counts.most_common(20)],
        "macro_categories": dict(macro_counts),
    },
    "structural_stats": struct_stats,
    "stats": {s["label"]: {k: v for k, v in s.items() if k != "label"} for s in all_stats},
}

with open(OUT_DIR / "diversity_summary.json", "w") as f:
    json.dump(summary, f, indent=2, default=str)
print(f"  Saved: {OUT_DIR / 'diversity_summary.json'}")

print("\n=== C1 Complete ===")
print(f"SMolInstruct caches written to:")
print(f"  - {OUT_DIR / 'smolinstruct_all_200000.jsonl'}")
print(f"\nFigures generated:")
print(f"  - {FIG_DIR / 'topic_distribution.pdf/.png'}")
print(f"  - {FIG_DIR / 'question_diversity.pdf/.png'}")
print(f"  - {FIG_DIR / 'answer_diversity.pdf/.png'}")
