"""Shared constants for the leakage-classifier pipeline.

Edit here; all other scripts import from this module.
"""
from __future__ import annotations

from pathlib import Path

# Paths
GOLD_JSONL = Path("/data/luis/Chem2TextHackathon/full_premium_kimi/dataset_gold.jsonl")

# Home dir — small outputs (summaries, scripts' default cwd) live here.
OUT_DIR = Path("/home/dandreas/chem2text/outputs/leakage")
# Data lab dir — large outputs (multi-hundred-MB artifacts) live here to
# avoid the home-dir quota. Scripts write here directly; symlinks are
# installed back into OUT_DIR for browsing convenience (see ensure_symlink).
BIG_DIR = Path("/data/dandreas/chem2text/outputs/leakage")

SAMPLE_JSONL = BIG_DIR / "sample.jsonl"         # ~1 GB
EMBEDDINGS_NPZ = BIG_DIR / "embeddings.npz"     # ~1.6 GB
TEXT_INDEX_JSON = BIG_DIR / "text_index.json"   # ~200 MB

PER_QA_JSONL = OUT_DIR / "per_qa_leakage.jsonl"
SUMMARY_MD = OUT_DIR / "leakage_summary.md"
FLAGGED_MD = OUT_DIR / "flagged_examples.md"
RUN_LOG = OUT_DIR / "run.log"


def ensure_symlink(big_path: Path) -> None:
    """Install a convenience symlink at OUT_DIR/<name> -> big_path."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    link = OUT_DIR / big_path.name
    if link.is_symlink() or link.exists():
        if link.is_symlink() and link.resolve() == big_path.resolve():
            return
        link.unlink()
    link.symlink_to(big_path)

# Sample
# Set to a number > total Q&A count (~188K in gold) to run on the full dataset.
# sample.py short-circuits and includes every Q&A when len(keys) <= SAMPLE_SIZE.
SAMPLE_SIZE = 500_000
SAMPLE_SEED = 42

# Thresholds for flagging
LCS_TOKEN_THRESHOLD = 40       # longest common contiguous token substring
NGRAM5_OVERLAP_THRESHOLD = 3   # distinct 5-grams shared with any evidence sentence
COSINE_THRESHOLD = 0.85        # max cosine of answer vs any evidence-sentence embedding

# Embedding model
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_BATCH_SIZE = 256

# Flagged-example sampling (for the markdown review file)
EXAMPLES_PER_CATEGORY = 20
EXAMPLES_SAMPLE_SEED = 42
