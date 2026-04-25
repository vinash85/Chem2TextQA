#!/usr/bin/env python3
"""
Chem2TextQA TTR Decay Curves (C3/4)
Plots Type-Token Ratio as a function of corpus size.
Shows that Chem2TextQA questions maintain vocabulary growth while SMolInstruct plateaus.
Outputs: TTR decay figures.
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

MAX_TOKENS = 200_000
N_POINTS = 600
N_RUNS = 3
SEED = 42

random.seed(SEED)
np.random.seed(SEED)

# ── Helpers ──────────────────────────────────────────────────────────────

def tokenize(text):
    """Simple whitespace + lowercase tokenizer."""
    return text.lower().split()

def load_chem2textqa():
    """Flatten compound-level JSONL into QA-pair-level lists."""
    questions, p2_answers = [], []

    with open(CHEM2TEXT_PATH) as f:
        for line in f:
            rec = json.loads(line)
            for qa in rec.get("qa_pairs", []):
                questions.append(qa.get("question", ""))
                p2_answers.append(qa.get("phase2_answer", ""))

    return questions, p2_answers

def load_smol_cache():
    """Load SMolInstruct from cache (written by C1)."""
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

def compute_ttr_curve(texts, max_tokens=MAX_TOKENS, n_points=N_POINTS):
    """Compute Type-Token Ratio as a function of corpus size.

    Returns:
        token_counts (np.array): increasing token counts
        ttr_values (np.array): TTR at each checkpoint
    """
    all_tokens = []
    for t in texts:
        all_tokens.extend(tokenize(t))

    # Shuffle for fair sampling
    random.shuffle(all_tokens)

    # Compute TTR at evenly-spaced checkpoints
    vocab = set()
    ttr_values = []
    token_counts = []

    checkpoint_interval = max_tokens // n_points
    next_checkpoint = checkpoint_interval

    for i, token in enumerate(all_tokens):
        vocab.add(token)

        if i >= next_checkpoint:
            ttr = len(vocab) / len(vocab.union(set(all_tokens[i-checkpoint_interval:i+1])))
            token_counts.append(i)
            ttr_values.append(len(vocab) / (i + 1))
            next_checkpoint += checkpoint_interval

            if i >= max_tokens:
                break

    return np.array(token_counts), np.array(ttr_values)

def compute_ttr_curve_avg(texts, max_tokens=MAX_TOKENS, n_points=N_POINTS, n_runs=N_RUNS):
    """Average TTR curves over multiple shuffles."""
    all_runs_token_counts = []
    all_runs_ttr = []

    for run_num in range(n_runs):
        print(f"    Run {run_num+1}/{n_runs}...")
        tokens, ttrs = compute_ttr_curve(texts, max_tokens=max_tokens, n_points=n_points)
        all_runs_token_counts.append(tokens)
        all_runs_ttr.append(ttrs)

    # Align to shortest run
    min_len = min(len(t) for t in all_runs_token_counts)
    token_counts = all_runs_token_counts[0][:min_len]
    mean_ttr = np.mean([ttr[:min_len] for ttr in all_runs_ttr], axis=0)

    return token_counts, mean_ttr

# ── Load Data ────────────────────────────────────────────────────────────
print("Loading Chem2TextQA...")
questions, p2_answers = load_chem2textqa()
print(f"  Loaded {len(questions):,} questions, {len(p2_answers):,} answers")

print("\nLoading SMolInstruct from cache...")
smol_questions, smol_answers = load_smol_cache()
print(f"  Loaded {len(smol_questions):,} questions, {len(smol_answers):,} answers")

# ── Compute TTR Curves ───────────────────────────────────────────────────
print("\n=== Computing TTR decay curves ===\n")

print("Chem2TextQA Questions:")
chem_q_tokens, chem_q_ttr = compute_ttr_curve_avg(questions, max_tokens=MAX_TOKENS, n_points=N_POINTS, n_runs=N_RUNS)

print("\nSMolInstruct Questions (will plateau due to 14 fixed templates):")
smol_q_tokens, smol_q_ttr = compute_ttr_curve_avg(smol_questions, max_tokens=MAX_TOKENS, n_points=N_POINTS, n_runs=N_RUNS)

print("\nChem2TextQA Answers:")
chem_a_tokens, chem_a_ttr = compute_ttr_curve_avg(p2_answers, max_tokens=MAX_TOKENS, n_points=N_POINTS, n_runs=N_RUNS)

print("\nSMolInstruct Answers:")
smol_a_tokens, smol_a_ttr = compute_ttr_curve_avg(smol_answers, max_tokens=MAX_TOKENS, n_points=N_POINTS, n_runs=N_RUNS)

# ── FIGURE 1: Question TTR Curves ────────────────────────────────────────
print("\n=== Generating Figure 1: Question TTR Curves ===")

fig, ax = plt.subplots(figsize=(6, 4.5))

ax.plot(chem_q_tokens / 1000, chem_q_ttr, color="#2563EB", linewidth=2.5, label="Chem2TextQA Questions")
ax.plot(smol_q_tokens / 1000, smol_q_ttr, color="#DC2626", linewidth=2.5, linestyle="--", label="SMolInstruct Questions (14 templates)")

ax.set_xlabel("Tokens (thousands)", fontsize=12)
ax.set_ylabel("Type-Token Ratio", fontsize=12)
ax.set_title("Question Lexical Diversity Growth", fontsize=13, fontweight="bold", pad=10)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
fig.savefig(FIG_DIR / "ttr_curve_questions.pdf", dpi=300, bbox_inches="tight")
fig.savefig(FIG_DIR / "ttr_curve_questions.png", dpi=200, bbox_inches="tight")
plt.close()
print(f"  Saved: {FIG_DIR / 'ttr_curve_questions.pdf'}")

# ── FIGURE 2: Answer TTR Curves ──────────────────────────────────────────
print("\n=== Generating Figure 2: Answer TTR Curves ===")

fig, ax = plt.subplots(figsize=(6, 4.5))

ax.plot(chem_a_tokens / 1000, chem_a_ttr, color="#2563EB", linewidth=2.5, label="Chem2TextQA Answers")
ax.plot(smol_a_tokens / 1000, smol_a_ttr, color="#DC2626", linewidth=2.5, linestyle="--", label="SMolInstruct Answers")

ax.set_xlabel("Tokens (thousands)", fontsize=12)
ax.set_ylabel("Type-Token Ratio", fontsize=12)
ax.set_title("Answer Lexical Diversity Growth", fontsize=13, fontweight="bold", pad=10)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
fig.savefig(FIG_DIR / "ttr_curve_answers.pdf", dpi=300, bbox_inches="tight")
fig.savefig(FIG_DIR / "ttr_curve_answers.png", dpi=200, bbox_inches="tight")
plt.close()
print(f"  Saved: {FIG_DIR / 'ttr_curve_answers.pdf'}")

print("\n=== C3 Complete ===")
