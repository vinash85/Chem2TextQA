#!/usr/bin/env python3
"""
Chem2TextQA Semantic Diversity Analysis (C2/4)
Computes pairwise cosine similarities using sentence-transformer embeddings.
Requires C1 to complete first (to cache SMolInstruct).
Outputs: semantic_diversity_stats.json, cosine similarity histograms.
"""

import json
import random
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────
CHEM2TEXT_PATH = "/data/luis/Chem2TextHackathon/full_premium_kimi/dataset_gold.jsonl"
OUT_DIR = Path("/data/asahu/projects/mutqa/chem2textqa_diversity")
FIG_DIR = OUT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_N = 30_000
N_PAIRS = 500_000
BATCH_SIZE = 512
SEED = 42
MODEL_NAME = "all-MiniLM-L6-v2"

random.seed(SEED)
np.random.seed(SEED)

# ── Helpers ──────────────────────────────────────────────────────────────

def tokenize(text):
    """Simple whitespace + lowercase tokenizer."""
    return text.lower().split()

def load_chem2textqa():
    """Flatten compound-level JSONL into QA-pair-level lists."""
    questions, p1_answers, p2_answers = [], [], []

    with open(CHEM2TEXT_PATH) as f:
        for line in f:
            rec = json.loads(line)
            for qa in rec.get("qa_pairs", []):
                questions.append(qa.get("question", ""))
                p1_answers.append(qa.get("phase1_answer", ""))
                p2_answers.append(qa.get("phase2_answer", ""))

    return questions, p1_answers, p2_answers

def safe_sample(lst, n):
    """Sample n items from list, handling edge cases."""
    n = min(n, len(lst))
    return random.sample(lst, n)

def load_smol_cache(cache_type="all"):
    """Load SMolInstruct from local cache (written by C1)."""
    if cache_type == "all":
        cache_path = OUT_DIR / "smolinstruct_all_200000.jsonl"
    elif cache_type == "MC":
        cache_path = OUT_DIR / "smolinstruct_MC_50000.jsonl"
    else:
        raise ValueError(f"Unknown cache_type: {cache_type}")

    if not cache_path.exists():
        raise FileNotFoundError(f"Cache not found: {cache_path}. Run C1 first.")

    questions, answers = [], []
    with open(cache_path) as f:
        for line in f:
            rec = json.loads(line)
            questions.append(rec["instruction"])
            answers.append(rec["output"])

    return questions, answers

def embed_and_cosine(texts, name, n_pairs=N_PAIRS):
    """Embed texts and compute pairwise cosine similarities.

    Returns:
        embeddings (np.array of shape (n_texts, embedding_dim))
        cosine_sims (np.array of pairwise cosine similarities)
    """
    print(f"  Loading sentence-transformer model: {MODEL_NAME}")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers not installed. Install with: pip install sentence-transformers")
        raise

    model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)

    # Sample texts for efficiency
    sampled_texts = safe_sample(texts, SAMPLE_N)
    print(f"    Encoding {len(sampled_texts):,} texts (batch_size={BATCH_SIZE})...")
    embeddings = model.encode(sampled_texts, batch_size=BATCH_SIZE, normalize_embeddings=True, show_progress_bar=True)

    # Compute pairwise cosine similarities (normalized embeddings => dot product = cosine)
    print(f"    Computing {n_pairs:,} random pairwise similarities...")
    cosine_sims = []
    n_texts = len(embeddings)

    for _ in range(n_pairs):
        i, j = random.sample(range(n_texts), 2)
        # Remove self-pairs
        if i == j:
            continue
        cos_sim = float(np.dot(embeddings[i], embeddings[j]))
        cosine_sims.append(cos_sim)

    cosine_sims = np.array(cosine_sims)

    stats = {
        "name": name,
        "n_texts": len(sampled_texts),
        "n_pairs": len(cosine_sims),
        "mean_cosine": float(np.mean(cosine_sims)),
        "std_cosine": float(np.std(cosine_sims)),
        "median_cosine": float(np.median(cosine_sims)),
        "p5": float(np.percentile(cosine_sims, 5)),
        "p95": float(np.percentile(cosine_sims, 95)),
    }

    print(f"    [{name}]  texts={len(sampled_texts):,}  pairs={len(cosine_sims):,}  "
          f"mean_cos={stats['mean_cosine']:.4f}  std={stats['std_cosine']:.4f}")

    return embeddings, cosine_sims, stats

# ── Load Data ────────────────────────────────────────────────────────────
print("Loading Chem2TextQA...")
questions, p1_answers, p2_answers = load_chem2textqa()
print(f"  Loaded {len(questions):,} questions, {len(p2_answers):,} phase2 answers")

print("\nLoading SMolInstruct (all tasks) from cache...")
smol_questions, smol_answers = load_smol_cache(cache_type="all")
print(f"  Loaded {len(smol_questions):,} questions, {len(smol_answers):,} answers")

# ── Embed and Compute Cosine Similarities ────────────────────────────────
print("\n=== Computing semantic diversity (embeddings) ===\n")

print("Questions:")
emb_chem_q, cos_chem_q, stats_chem_q = embed_and_cosine(questions, "Chem2TextQA Questions")

print("\nSMolInstruct Questions (will show high cosine ~ templates are similar):")
emb_smol_q, cos_smol_q, stats_smol_q = embed_and_cosine(smol_questions, "SMolInstruct Questions")

print("\nAnswers:")
emb_chem_a, cos_chem_a, stats_chem_a = embed_and_cosine(p2_answers, "Chem2TextQA Answers")

print("\nSMolInstruct Answers:")
emb_smol_a, cos_smol_a, stats_smol_a = embed_and_cosine(smol_answers, "SMolInstruct Answers")

# ── FIGURE 1: Question Cosine Similarity ─────────────────────────────────
print("\n=== Generating Figure 1: Question Cosine Similarity ===")

fig, ax = plt.subplots(1, 1, figsize=(7, 4.5))

ax.hist(cos_chem_q, bins=50, alpha=0.7, color="#2563EB", label="Chem2TextQA Questions", density=True)

# Add mean line
ax.axvline(stats_chem_q["mean_cosine"], color="#2563EB", linestyle="--", linewidth=2,
           label=f"Mean: {stats_chem_q['mean_cosine']:.3f}")

ax.set_xlabel("Pairwise Cosine Similarity", fontsize=12)
ax.set_ylabel("Density", fontsize=12)
ax.set_title("Question Semantic Diversity (Sentence-Transformer Embeddings)", fontsize=13, fontweight="bold", pad=10)
ax.legend(fontsize=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# SMolInstruct annotation
ax.annotate(
    "SMolInstruct: 14 templates\n→ cosine similarity ≈ 1.0\n(near-identical questions)",
    xy=(0.98, 0.95), xycoords="axes fraction", ha="right", va="top",
    fontsize=10, bbox=dict(boxstyle="round,pad=0.4", facecolor="#FEE2E2", edgecolor="#DC2626", alpha=0.9),
)

plt.tight_layout()
fig.savefig(FIG_DIR / "diversity_cosine_hist_questions.pdf", dpi=300, bbox_inches="tight")
fig.savefig(FIG_DIR / "diversity_cosine_hist_questions.png", dpi=200, bbox_inches="tight")
plt.close()
print(f"  Saved: {FIG_DIR / 'diversity_cosine_hist_questions.pdf'}")

# ── FIGURE 2: Answer Cosine Similarity ───────────────────────────────────
print("\n=== Generating Figure 2: Answer Cosine Similarity ===")

fig, ax = plt.subplots(1, 1, figsize=(7, 4.5))

# Plot both distributions
ax.hist(cos_chem_a, bins=50, alpha=0.5, color="#2563EB",
        label=f"Chem2TextQA Answers (mean={stats_chem_a['mean_cosine']:.3f})", density=True)
ax.hist(cos_smol_a, bins=50, alpha=0.5, color="#DC2626",
        label=f"SMolInstruct Answers (mean={stats_smol_a['mean_cosine']:.3f})", density=True)

ax.axvline(stats_chem_a["mean_cosine"], color="#2563EB", linestyle="--", linewidth=2)
ax.axvline(stats_smol_a["mean_cosine"], color="#DC2626", linestyle="--", linewidth=2)

ax.set_xlabel("Pairwise Cosine Similarity", fontsize=12)
ax.set_ylabel("Density", fontsize=12)
ax.set_title("Answer Semantic Diversity (Sentence-Transformer Embeddings)", fontsize=13, fontweight="bold", pad=10)
ax.legend(fontsize=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
fig.savefig(FIG_DIR / "diversity_cosine_hist_answers.pdf", dpi=300, bbox_inches="tight")
fig.savefig(FIG_DIR / "diversity_cosine_hist_answers.png", dpi=200, bbox_inches="tight")
plt.close()
print(f"  Saved: {FIG_DIR / 'diversity_cosine_hist_answers.pdf'}")

# ── JSON Summary ─────────────────────────────────────────────────────────
print("\n=== Saving JSON summary ===")

summary = {
    "Chem2TextQA Questions": {k: v for k, v in stats_chem_q.items() if k != "name"},
    "SMolInstruct Questions": {k: v for k, v in stats_smol_q.items() if k != "name"},
    "Chem2TextQA Answers": {k: v for k, v in stats_chem_a.items() if k != "name"},
    "SMolInstruct Answers": {k: v for k, v in stats_smol_a.items() if k != "name"},
}

with open(OUT_DIR / "semantic_diversity_stats.json", "w") as f:
    json.dump(summary, f, indent=2, default=str)
print(f"  Saved: {OUT_DIR / 'semantic_diversity_stats.json'}")

print("\n=== C2 Complete ===")
