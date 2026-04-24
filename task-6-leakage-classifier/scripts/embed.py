"""Encode unique answer + evidence texts with all-MiniLM-L6-v2 on one GPU.

Builds a deterministic text_index mapping text → row index, encodes each
unique text once, saves a normalized float32 numpy array so cosine becomes
a dot product downstream.
"""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from config import (  # noqa: E402
    BIG_DIR,
    EMBED_BATCH_SIZE,
    EMBED_MODEL,
    EMBEDDINGS_NPZ,
    SAMPLE_JSONL,
    TEXT_INDEX_JSON,
    ensure_symlink,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("embed")


def main() -> None:
    BIG_DIR.mkdir(parents=True, exist_ok=True)
    # Collect unique texts: all phase1 answers + all evidence sentences that
    # appear in the sample's parent compounds.
    log.info("Collecting unique texts from %s", SAMPLE_JSONL)
    t0 = time.time()
    text_to_id: dict[str, int] = {}

    def add(text: str) -> int:
        t = text.strip()
        if not t:
            return -1
        tid = text_to_id.get(t)
        if tid is None:
            tid = len(text_to_id)
            text_to_id[t] = tid
        return tid

    with SAMPLE_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            add(row["phase1_answer"])
            for e in row.get("evidence_sentences") or []:
                add(e.get("text", ""))
    log.info("Unique texts: %d (collected in %.1fs)", len(text_to_id), time.time() - t0)

    # Deterministic ordered list: text_index[i] = text with id i
    texts: list[str] = [""] * len(text_to_id)
    for t, i in text_to_id.items():
        texts[i] = t

    # Persist index so metrics.py can look up row ids without re-encoding.
    with TEXT_INDEX_JSON.open("w", encoding="utf-8") as f:
        json.dump({"texts": texts}, f, ensure_ascii=False)
    log.info("Wrote text index with %d rows", len(texts))
    ensure_symlink(TEXT_INDEX_JSON)

    # Encode.
    log.info("Loading model %s", EMBED_MODEL)
    from sentence_transformers import SentenceTransformer
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    log.info("Using device: %s", device)
    model = SentenceTransformer(EMBED_MODEL, device=device)

    log.info("Encoding %d texts, batch_size=%d", len(texts), EMBED_BATCH_SIZE)
    t0 = time.time()
    emb = model.encode(
        texts,
        batch_size=EMBED_BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)
    log.info("Encoded in %.1fs — shape %s", time.time() - t0, emb.shape)

    # Uncompressed .npz — compression on 1M×384 float32 saves little and costs
    # real time. Use ~1.6 GB of disk, which is fine in /data/dandreas.
    np.savez(EMBEDDINGS_NPZ, emb=emb)
    log.info("Saved embeddings to %s", EMBEDDINGS_NPZ)
    ensure_symlink(EMBEDDINGS_NPZ)


if __name__ == "__main__":
    main()
