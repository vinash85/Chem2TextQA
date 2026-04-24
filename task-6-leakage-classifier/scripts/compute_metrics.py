"""Compute three leakage metrics per sampled Q&A.

Metrics
-------
lcs_tokens       Longest common contiguous token substring between the answer
                 and any single evidence sentence for the parent compound.
                 Computed via difflib.SequenceMatcher on token sequences.
ngram5_overlap   |5-grams(answer) ∩ 5-grams(union of evidence sentences)|,
                 where tokens are the same normalization used for LCS.
cos_max          Max cosine similarity between the answer embedding and any
                 evidence-sentence embedding for the parent compound.
                 Embeddings are L2-normalized, so cosine = dot product.

Each row in per_qa_leakage.jsonl also carries the booleans
`flag_lcs`, `flag_ngram`, `flag_cos`, and `flag_any`.
"""
from __future__ import annotations

import difflib
import json
import logging
import string
import sys
import time
from pathlib import Path

import numpy as np
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from config import (  # noqa: E402
    COSINE_THRESHOLD,
    EMBEDDINGS_NPZ,
    LCS_TOKEN_THRESHOLD,
    NGRAM5_OVERLAP_THRESHOLD,
    PER_QA_JSONL,
    SAMPLE_JSONL,
    TEXT_INDEX_JSON,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("metrics")

_PUNCT = string.punctuation


def tokenize(text: str) -> list[str]:
    """Lowercase, whitespace-split, strip surrounding punctuation.

    Shared by LCS and n-gram computations so results are consistent.
    """
    out = []
    for tok in text.lower().split():
        tok = tok.strip(_PUNCT)
        if tok:
            out.append(tok)
    return out


def ngrams(tokens: list[str], n: int = 5) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def lcs_tokens(a: list[str], b: list[str]) -> int:
    """Longest common contiguous token substring length."""
    if not a or not b:
        return 0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b)).size


def main() -> None:
    # Load text index and embeddings.
    log.info("Loading text index from %s", TEXT_INDEX_JSON)
    with TEXT_INDEX_JSON.open("r", encoding="utf-8") as f:
        idx = json.load(f)
    texts: list[str] = idx["texts"]
    text_to_id = {t: i for i, t in enumerate(texts)}

    log.info("Loading embeddings from %s", EMBEDDINGS_NPZ)
    with np.load(EMBEDDINGS_NPZ) as z:
        emb: np.ndarray = z["emb"]
    log.info("Embeddings shape: %s", emb.shape)

    # Pre-tokenize every unique text once (same normalization for both metrics).
    log.info("Pre-tokenizing %d unique texts", len(texts))
    t0 = time.time()
    tokenized: list[list[str]] = [tokenize(t) for t in texts]
    log.info("Tokenized in %.1fs", time.time() - t0)

    # Count rows for tqdm
    with SAMPLE_JSONL.open("r", encoding="utf-8") as f:
        n_rows = sum(1 for _ in f)
    log.info("Scoring %d sampled Q&A", n_rows)

    n_flagged = {"lcs": 0, "ngram": 0, "cos": 0, "any": 0}
    t0 = time.time()
    with SAMPLE_JSONL.open("r", encoding="utf-8") as fin, \
         PER_QA_JSONL.open("w", encoding="utf-8") as fout:
        for line in tqdm(fin, total=n_rows, mininterval=1.0):
            row = json.loads(line)
            answer = (row.get("phase1_answer") or "").strip()
            evidence = row.get("evidence_sentences") or []

            a_tokens: list[str] = []
            a_ngrams: set[tuple[str, ...]] = set()
            a_id = text_to_id.get(answer, -1) if answer else -1
            if a_id >= 0:
                a_tokens = tokenized[a_id]
                a_ngrams = ngrams(a_tokens, 5)

            # Collect evidence token-lists and embedding ids.
            ev_token_lists: list[list[str]] = []
            ev_ngrams: set[tuple[str, ...]] = set()
            ev_emb_ids: list[int] = []
            for e in evidence:
                etext = (e.get("text") or "").strip()
                if not etext:
                    continue
                eid = text_to_id.get(etext, -1)
                if eid < 0:
                    continue
                ev_token_lists.append(tokenized[eid])
                ev_ngrams |= ngrams(tokenized[eid], 5)
                ev_emb_ids.append(eid)

            # LCS: max contiguous token run across all evidence sentences.
            if a_tokens and ev_token_lists:
                lcs_val = max(lcs_tokens(a_tokens, eb) for eb in ev_token_lists)
            else:
                lcs_val = 0

            # 5-gram intersection with the union of evidence 5-grams.
            n_overlap = len(a_ngrams & ev_ngrams) if a_ngrams and ev_ngrams else 0

            # Cosine: max dot product (embeddings are normalized).
            if a_id >= 0 and ev_emb_ids:
                cos_vals = emb[ev_emb_ids] @ emb[a_id]
                cos_max = float(cos_vals.max())
            else:
                cos_max = 0.0

            flag_lcs = lcs_val > LCS_TOKEN_THRESHOLD
            flag_ngram = n_overlap > NGRAM5_OVERLAP_THRESHOLD
            flag_cos = cos_max > COSINE_THRESHOLD
            flag_any = flag_lcs or flag_ngram or flag_cos
            n_flagged["lcs"] += int(flag_lcs)
            n_flagged["ngram"] += int(flag_ngram)
            n_flagged["cos"] += int(flag_cos)
            n_flagged["any"] += int(flag_any)

            out_row = {
                "cid": row["cid"],
                "qa_index": row["qa_index"],
                "split": row.get("split"),
                "topic": row.get("topic"),
                "answer_len_tokens": len(a_tokens),
                "n_evidence_sentences": len(ev_token_lists),
                "lcs_tokens": int(lcs_val),
                "ngram5_overlap": int(n_overlap),
                "cos_max": cos_max,
                "flag_lcs": bool(flag_lcs),
                "flag_ngram": bool(flag_ngram),
                "flag_cos": bool(flag_cos),
                "flag_any": bool(flag_any),
            }
            fout.write(json.dumps(out_row, ensure_ascii=False) + "\n")

    log.info("Scored in %.1fs", time.time() - t0)
    log.info("Flag counts: %s (of %d rows)", n_flagged, n_rows)


if __name__ == "__main__":
    main()
