#!/usr/bin/env python3
"""Stratified sampler for Task 2 — Multi-judge LLM panel.

Flattens /data/luis/ChemQA/dataset_final.jsonl into per-Q&A rows and draws a
verdict-stratified sample for re-judging:
    500 agree + 469 disagree + all 31 unclear = 1000.

Writes outputs/multi_judge/samples_input.jsonl (one row per sampled Q&A).
Downstream scripts join on the key f"{cid}:{qa_index}".
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random
import sys
from pathlib import Path

DEFAULT_INPUT = Path("/data/luis/ChemQA/dataset_final.jsonl")
DEFAULT_OUTPUT = Path(__file__).parent / "outputs" / "multi_judge" / "samples_input.jsonl"

# Target counts per verdict. If --n is not 1000 these are rescaled keeping
# unclear=ALL and agree:disagree proportions of 500:469.
TARGET_AGREE = 500
TARGET_DISAGREE = 469
TARGET_UNCLEAR_ALL = True  # take every unclear available


def flatten(path: Path):
    """Yield per-Q&A rows from dataset_final.jsonl."""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            cid = rec.get("cid")
            split = rec.get("split")
            for qa in rec.get("qa_pairs") or []:
                yield {
                    "cid": cid,
                    "split": split,
                    "qa_index": qa.get("qa_index"),
                    "topic": qa.get("topic"),
                    "question": qa.get("question") or "",
                    "phase1_answer": qa.get("phase1_answer") or "",
                    "phase2_answer": qa.get("phase2_answer") or "",
                    "gemma_verdict": qa.get("verdict"),
                    "gemma_reasoning": qa.get("judge_reasoning") or "",
                }


def is_valid(row: dict) -> bool:
    return bool(
        row["cid"] is not None
        and row["qa_index"] is not None
        and row["question"].strip()
        and row["phase1_answer"].strip()
        and row["phase2_answer"].strip()
        and row["gemma_verdict"] in ("agree", "disagree", "unclear")
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--n", type=int, default=1000, help="Total sample size (default 1000).")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument(
        "--agree", type=int, default=TARGET_AGREE,
        help="How many 'agree' rows to sample (default 500).",
    )
    ap.add_argument(
        "--disagree", type=int, default=TARGET_DISAGREE,
        help="How many 'disagree' rows to sample (default 469).",
    )
    args = ap.parse_args()

    if not args.input.exists():
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        return 1

    # Bucket rows by verdict
    buckets: dict[str, list[dict]] = {"agree": [], "disagree": [], "unclear": []}
    dropped = 0
    for row in flatten(args.input):
        if not is_valid(row):
            dropped += 1
            continue
        buckets[row["gemma_verdict"]].append(row)

    print(
        f"flattened {sum(len(v) for v in buckets.values()) + dropped} Q&A rows "
        f"(dropped {dropped} with missing fields / invalid verdict)"
    )
    for v in ("agree", "disagree", "unclear"):
        print(f"  {v:<9} available: {len(buckets[v])}")

    rng = random.Random(args.seed)
    sampled: list[dict] = []

    # unclear — take all available
    unclear_rows = list(buckets["unclear"])
    rng.shuffle(unclear_rows)
    if len(unclear_rows) < 31:
        print(f"WARNING: only {len(unclear_rows)} unclear rows (expected 31)")
    sampled.extend(unclear_rows)

    def draw(verdict: str, k: int):
        pool = buckets[verdict]
        if k > len(pool):
            print(
                f"ERROR: requested {k} from '{verdict}' but only {len(pool)} available",
                file=sys.stderr,
            )
            sys.exit(2)
        picks = rng.sample(pool, k)
        sampled.extend(picks)

    draw("agree", args.agree)
    draw("disagree", args.disagree)

    if len(sampled) != args.n:
        print(
            f"WARNING: sampled {len(sampled)} rows, expected {args.n}. "
            f"Breakdown: agree={args.agree} disagree={args.disagree} "
            f"unclear={len(unclear_rows)}",
            file=sys.stderr,
        )

    rng.shuffle(sampled)

    # Uniqueness check
    keys = {(r["cid"], r["qa_index"]) for r in sampled}
    assert len(keys) == len(sampled), "sampled rows contain duplicate (cid, qa_index)"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for r in sampled:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Report
    print(f"\nwrote {len(sampled)} rows → {args.output}")
    by_v = collections.Counter(r["gemma_verdict"] for r in sampled)
    by_split = collections.Counter(r["split"] for r in sampled)
    by_topic_top = collections.Counter(r["topic"] for r in sampled).most_common(10)
    print("verdict counts:", dict(by_v))
    print("split counts:  ", dict(by_split))
    print("top 10 topics: ")
    for t, c in by_topic_top:
        print(f"  {c:4d}  {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
