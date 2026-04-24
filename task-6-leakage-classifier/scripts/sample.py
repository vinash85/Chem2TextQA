"""Deterministically sample 20,000 Q&A from the gold dataset.

Sampling unit is (cid, qa_index). Draw is uniform across all Q&A — compounds
with more Q&A are proportionally more likely to contribute rows, which is what
we want for an unbiased per-Q&A leakage-rate estimate.

Output: one JSON line per sampled Q&A with:
  cid, qa_index, split, topic, phase1_answer, evidence_sentences
Where evidence_sentences is the parent compound's full evidence list (each
{id, pmid, source, text}).
"""
from __future__ import annotations

import json
import logging
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import (  # noqa: E402
    BIG_DIR,
    GOLD_JSONL,
    OUT_DIR,
    SAMPLE_JSONL,
    SAMPLE_SEED,
    SAMPLE_SIZE,
    ensure_symlink,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sample")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    BIG_DIR.mkdir(parents=True, exist_ok=True)

    # Pass 1: enumerate all (cid, qa_index) pairs.
    log.info("Pass 1: enumerating Q&A keys from %s", GOLD_JSONL)
    t0 = time.time()
    keys: list[tuple[int, int]] = []
    with GOLD_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            cid = int(rec["cid"])
            for qa in rec.get("qa_pairs") or []:
                qi = int(qa.get("qa_index", 0))
                keys.append((cid, qi))
    log.info("Enumerated %d Q&A in %.1fs", len(keys), time.time() - t0)

    # Deterministic sample.
    keys.sort()  # stable iteration order regardless of input ordering
    rng = random.Random(SAMPLE_SEED)
    if len(keys) <= SAMPLE_SIZE:
        chosen = set(keys)
    else:
        chosen = set(rng.sample(keys, SAMPLE_SIZE))
    log.info("Sampled %d Q&A with seed=%d", len(chosen), SAMPLE_SEED)

    # Pass 2: stream again and write full rows for the chosen keys.
    log.info("Pass 2: writing sample to %s", SAMPLE_JSONL)
    t0 = time.time()
    written = 0
    with GOLD_JSONL.open("r", encoding="utf-8") as f, \
         SAMPLE_JSONL.open("w", encoding="utf-8") as out:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            cid = int(rec["cid"])
            evidence = rec.get("evidence_sentences") or []
            for qa in rec.get("qa_pairs") or []:
                qi = int(qa.get("qa_index", 0))
                if (cid, qi) not in chosen:
                    continue
                row = {
                    "cid": cid,
                    "qa_index": qi,
                    "split": rec.get("split"),
                    "topic": qa.get("topic"),
                    "phase1_answer": qa.get("phase1_answer", "") or "",
                    "evidence_sentences": evidence,
                }
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                written += 1
    log.info("Wrote %d rows in %.1fs", written, time.time() - t0)
    ensure_symlink(SAMPLE_JSONL)
    log.info("Symlinked %s -> %s", OUT_DIR / SAMPLE_JSONL.name, SAMPLE_JSONL)


if __name__ == "__main__":
    main()
