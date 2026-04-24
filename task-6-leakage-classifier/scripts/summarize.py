"""Produce leakage_summary.md + flagged_examples.md.

summary: aggregate flag rates, metric distributions, intersections,
         breakdown by topic and split.
flagged: up to EXAMPLES_PER_CATEGORY sampled cases per flag category
         (lcs, ngram, cos, any), for user review. No judgments.
"""
from __future__ import annotations

import json
import logging
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).parent))
from config import (  # noqa: E402
    COSINE_THRESHOLD,
    EMBED_MODEL,
    EXAMPLES_PER_CATEGORY,
    EXAMPLES_SAMPLE_SEED,
    FLAGGED_MD,
    LCS_TOKEN_THRESHOLD,
    NGRAM5_OVERLAP_THRESHOLD,
    PER_QA_JSONL,
    SAMPLE_JSONL,
    SAMPLE_SEED,
    SAMPLE_SIZE,
    SUMMARY_MD,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("summarize")


def pct(n: int, d: int) -> str:
    return f"{100.0 * n / d:.2f}%" if d else "n/a"


def quantile(xs: list[float], q: float) -> float:
    if not xs:
        return float("nan")
    xs = sorted(xs)
    i = int(round((len(xs) - 1) * q))
    return xs[i]


def main() -> None:
    rows: list[dict] = []
    with PER_QA_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    n = len(rows)
    log.info("Loaded %d scored rows", n)

    # Index sample rows by (cid, qa_index) so we can pull answer/evidence text
    # for the flagged examples file.
    sample_by_key: dict[tuple[int, int], dict] = {}
    with SAMPLE_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            sample_by_key[(int(r["cid"]), int(r["qa_index"]))] = r

    # --- Aggregates ---
    # LCS is reported as a threshold curve, not a single flag — max across the
    # corpus is ~19 tokens, so a fixed cutoff at 40 always flagged nothing and
    # obscured the real distribution. The ngram + cos flags remain single-threshold
    # because those metrics have meaningful upper tails.
    flags = {
        "ngram": [r for r in rows if r["flag_ngram"]],
        "cos": [r for r in rows if r["flag_cos"]],
        "any": [r for r in rows if r["flag_ngram"] or r["flag_cos"]],
    }
    n_flags = {k: len(v) for k, v in flags.items()}

    # Co-flagging (ngram ∩ cos is the strongest usable signal)
    co_ngram_cos = sum(1 for r in rows if r["flag_ngram"] and r["flag_cos"])

    # Metric distributions
    lcs_vals = [r["lcs_tokens"] for r in rows]
    ngram_vals = [r["ngram5_overlap"] for r in rows]
    cos_vals = [r["cos_max"] for r in rows]

    # LCS threshold curve — tokens > T
    lcs_thresholds = [4, 5, 6, 7, 8, 9, 10, 12, 15, 18, 19, 20, 25, 30, 40]
    lcs_hist = Counter(lcs_vals)
    lcs_curve = []
    for T in lcs_thresholds:
        k = sum(c for v, c in lcs_hist.items() if v > T)
        lcs_curve.append((T, k, 100.0 * k / n if n else 0.0))

    def dist(xs: list[float]) -> dict:
        return {
            "mean": round(sum(xs) / len(xs), 4) if xs else float("nan"),
            "median": round(median(xs), 4) if xs else float("nan"),
            "p90": round(quantile(xs, 0.90), 4),
            "p95": round(quantile(xs, 0.95), 4),
            "p99": round(quantile(xs, 0.99), 4),
            "max": round(max(xs), 4) if xs else float("nan"),
        }

    # Per-topic breakdown (flag_any rate: ngram OR cos)
    by_topic_total: Counter[str] = Counter()
    by_topic_flag: defaultdict[str, int] = defaultdict(int)
    for r in rows:
        t = r.get("topic") or "(none)"
        by_topic_total[t] += 1
        if r["flag_ngram"] or r["flag_cos"]:
            by_topic_flag[t] += 1
    topics_sorted = sorted(
        by_topic_total.items(),
        key=lambda kv: -(by_topic_flag[kv[0]] / kv[1] if kv[1] else 0),
    )
    topic_rows = [
        (t, by_topic_flag[t], c, 100.0 * by_topic_flag[t] / c)
        for t, c in topics_sorted
        if c >= 30  # hide rare topics in the top-of-report table
    ][:20]

    # Per-split breakdown
    by_split_total: Counter[str] = Counter()
    by_split_flag: defaultdict[str, int] = defaultdict(int)
    for r in rows:
        s = r.get("split") or "(none)"
        by_split_total[s] += 1
        if r["flag_ngram"] or r["flag_cos"]:
            by_split_flag[s] += 1

    # --- Write summary ---
    md = []
    md.append("# Leakage Summary\n")
    md.append(
        f"Source: `per_qa_leakage.jsonl` ({n} rows, sampled from "
        f"`dataset_gold.jsonl`; n={SAMPLE_SIZE}, seed={SAMPLE_SEED}).\n"
    )
    md.append("## Setup\n")
    md.append(f"- Embedding model: `{EMBED_MODEL}`")
    md.append(f"- LCS = longest common *contiguous token substring* (word tokens, lowercased, punct-stripped)")
    md.append(f"- 5-gram overlap = `|5grams(answer) ∩ 5grams(⋃ evidence sentences)|`")
    md.append(f"- Cosine = max dot product of answer embedding vs any evidence-sentence embedding (both L2-normed)\n")
    md.append("## Flag thresholds\n")
    md.append("LCS is reported as a threshold curve below (no single cutoff).")
    md.append("The other two metrics use fixed thresholds:\n")
    md.append("| Metric | Threshold | Flag rule |")
    md.append("|---|---|---|")
    md.append(f"| `ngram5_overlap` | > {NGRAM5_OVERLAP_THRESHOLD} | ≥{NGRAM5_OVERLAP_THRESHOLD + 1} shared 5-grams |")
    md.append(f"| `cos_max` | > {COSINE_THRESHOLD} | ≥{COSINE_THRESHOLD} max cosine |\n")

    md.append("## LCS threshold curve (tokens > T)\n")
    md.append("| T | rows with lcs_tokens > T | rate |")
    md.append("|---:|---:|---:|")
    for T, k, rate in lcs_curve:
        md.append(f"| {T} | {k} | {rate:.3f}% |")
    md.append("")
    md.append(
        "_Max LCS observed in the corpus = "
        f"{max(lcs_vals) if lcs_vals else 0} tokens; any threshold above that flags zero rows._\n"
    )

    md.append("## Flag rates (ngram + cos)\n")
    md.append("| Flag | Count | Rate |")
    md.append("|---|---|---|")
    md.append(f"| `flag_ngram` (5-gram overlap > {NGRAM5_OVERLAP_THRESHOLD}) | {n_flags['ngram']} | {pct(n_flags['ngram'], n)} |")
    md.append(f"| `flag_cos`   (cos > {COSINE_THRESHOLD}) | {n_flags['cos']} | {pct(n_flags['cos'], n)} |")
    md.append(f"| `flag_any`   (ngram ∨ cos) | {n_flags['any']} | {pct(n_flags['any'], n)} |")
    md.append(f"| `ngram ∩ cos` (strongest signal) | {co_ngram_cos} | {pct(co_ngram_cos, n)} |\n")

    md.append("## Metric distributions (all rows)\n")
    md.append("| Metric | mean | median | p90 | p95 | p99 | max |")
    md.append("|---|---|---|---|---|---|---|")
    for name, xs in [("lcs_tokens", lcs_vals), ("ngram5_overlap", ngram_vals), ("cos_max", cos_vals)]:
        d = dist(xs)
        md.append(f"| {name} | {d['mean']} | {d['median']} | {d['p90']} | {d['p95']} | {d['p99']} | {d['max']} |")
    md.append("")

    md.append("## Flag-any rate by split\n")
    md.append("| split | flagged | total | rate |")
    md.append("|---|---|---|---|")
    for s in sorted(by_split_total):
        md.append(f"| {s} | {by_split_flag[s]} | {by_split_total[s]} | {pct(by_split_flag[s], by_split_total[s])} |")
    md.append("")

    md.append(f"## Flag-any rate by topic (top 20 topics with ≥30 sampled Q&A, sorted by rate)\n")
    md.append("| topic | flagged | total | rate |")
    md.append("|---|---|---|---|")
    for t, f, c, r in topic_rows:
        md.append(f"| {t} | {f} | {c} | {r:.2f}% |")
    md.append("")

    md.append("## Notes\n")
    md.append(
        "- Flag rates measure *borrowing signal*, not judgment. Technical terminology, "
        "IUPAC fragments, and mechanism names legitimately recur in both evidence and "
        "answers. `flagged_examples.md` stages cases for manual review without calling "
        "them leakage.\n"
    )
    md.append(
        "- Strong signal is co-flagging: items flagged on multiple metrics are much more "
        "likely to be actual paraphrase/copy.\n"
    )

    SUMMARY_MD.write_text("\n".join(md), encoding="utf-8")
    log.info("Wrote %s", SUMMARY_MD)

    # --- Flagged examples (top-N per category by "most egregious") ---
    # Co-flagged items (ngram + cos flags together) are ranked by a composite:
    # each flagged metric's excess over its threshold is divided by a per-metric
    # scale (the range between threshold and observed dataset max), then summed.
    # This prevents one metric's units (tokens vs [0,1] cosine) from dominating.
    max_ngram = max((r["ngram5_overlap"] for r in rows), default=NGRAM5_OVERLAP_THRESHOLD + 1)
    max_cos = max((r["cos_max"] for r in rows), default=1.0)
    max_lcs = max((r["lcs_tokens"] for r in rows), default=LCS_TOKEN_THRESHOLD + 1)
    ngram_scale = max(1.0, max_ngram - NGRAM5_OVERLAP_THRESHOLD)
    cos_scale = max(1e-6, max_cos - COSINE_THRESHOLD)
    lcs_scale = max(1.0, max_lcs - LCS_TOKEN_THRESHOLD)

    def composite_score(r: dict) -> float:
        s = 0.0
        if r["flag_ngram"]:
            s += (r["ngram5_overlap"] - NGRAM5_OVERLAP_THRESHOLD) / ngram_scale
        if r["flag_cos"]:
            s += (r["cos_max"] - COSINE_THRESHOLD) / cos_scale
        if r["flag_lcs"]:
            s += (r["lcs_tokens"] - LCS_TOKEN_THRESHOLD) / lcs_scale
        return s

    # For the composite-egregiousness category we co-flag on (ngram ∩ cos),
    # since LCS no longer has a single-threshold flag. The LCS category is
    # replaced by a top-N-by-lcs-descending view over the whole corpus.
    categories = [
        # (title, candidate rows, sort key — descending)
        ("Top LCS (all rows, descending by `lcs_tokens`)",
         rows,
         lambda r: (r["lcs_tokens"], r["ngram5_overlap"], r["cos_max"])),
        ("5-gram overlap > threshold",
         flags["ngram"],
         lambda r: (r["ngram5_overlap"], r["cos_max"], r["lcs_tokens"])),
        ("Cosine > threshold (paraphrase)",
         flags["cos"],
         lambda r: (r["cos_max"], r["ngram5_overlap"], r["lcs_tokens"])),
        ("Co-flagged (ngram ∩ cos) — composite egregiousness",
         [r for r in rows if r["flag_ngram"] and r["flag_cos"]],
         lambda r: (composite_score(r), r["ngram5_overlap"], r["cos_max"], r["lcs_tokens"])),
    ]

    out: list[str] = []
    out.append("# Flagged Examples (for review)\n")
    out.append(
        f"Top-{EXAMPLES_PER_CATEGORY} per category, ranked **most egregious first**. "
        "The LCS category has no threshold — rows are taken in descending order of "
        "`lcs_tokens` over the entire corpus (see the threshold curve in the summary "
        "for rate-at-cutoff). The ngram and cos categories use their fixed thresholds; "
        "the co-flagged list uses a composite score that sums each flagged metric's "
        "excess over threshold, normalized by the observed max. The full scored list "
        "is in `per_qa_leakage.jsonl` (filter/sort on `lcs_tokens`, `flag_ngram`, "
        "`flag_cos`, or `cos_max`). No judgments are made here — for each case the "
        "answer and the best-matching evidence sentence are shown so you can decide "
        "leakage vs legitimate terminology reuse.\n"
    )

    for title, items, sort_key in categories:
        out.append(f"\n---\n\n## {title}  — {len(items)} total, showing top {min(len(items), EXAMPLES_PER_CATEGORY)}\n")
        if not items:
            out.append("_No cases._\n")
            continue
        shown = sorted(items, key=sort_key, reverse=True)[:EXAMPLES_PER_CATEGORY]
        for r in shown:
            key = (int(r["cid"]), int(r["qa_index"]))
            src = sample_by_key.get(key, {})
            answer = src.get("phase1_answer", "")
            evidence = src.get("evidence_sentences") or []
            # Pick the best-matching evidence sentence by token LCS.
            from difflib import SequenceMatcher
            def tok(t: str) -> list[str]:
                import string as _s
                return [w.strip(_s.punctuation) for w in (t or "").lower().split() if w.strip(_s.punctuation)]
            a_toks = tok(answer)
            best_sent = ""
            best_size = -1
            for e in evidence:
                etext = e.get("text", "")
                e_toks = tok(etext)
                if not a_toks or not e_toks:
                    continue
                sz = SequenceMatcher(None, a_toks, e_toks, autojunk=False).find_longest_match(0, len(a_toks), 0, len(e_toks)).size
                if sz > best_size:
                    best_size = sz
                    best_sent = etext

            out.append(
                f"### CID {r['cid']} · qa_index {r['qa_index']} · topic `{r['topic']}` · split `{r['split']}`\n"
            )
            out.append(
                f"- metrics: lcs_tokens={r['lcs_tokens']}, ngram5_overlap={r['ngram5_overlap']}, "
                f"cos_max={r['cos_max']:.3f} (answer_len_tokens={r['answer_len_tokens']}, "
                f"n_evidence_sentences={r['n_evidence_sentences']})\n"
            )
            out.append(f"**Answer (phase1):**\n\n> {answer.strip()}\n")
            if best_sent:
                out.append(f"**Closest evidence sentence (by token LCS):**\n\n> {best_sent.strip()}\n")

    FLAGGED_MD.write_text("\n".join(out), encoding="utf-8")
    log.info("Wrote %s", FLAGGED_MD)


if __name__ == "__main__":
    main()
