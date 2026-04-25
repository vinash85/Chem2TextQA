"""Task 8 — per-topic / per-tier / per-split CIDEr+BLEU+ROUGE for base vs FT ChemQA models.

Strategy: score each model-variant's full 26,205-row test corpus *once* with
pycocoevalcap, capturing the per-sample scores returned alongside the corpus
aggregate. Stratum metrics are then computed by averaging per-sample scores
within each stratum — much faster than re-running the scorer on every slice,
and methodologically standard (corpus-level TF-IDF is fixed by the full set).

Outputs match Task 8's deliverable list in HACKATHON.pdf:
  outputs/per_topic_finetune/{cider_per_topic.json,
                              cider_per_difficulty.json,
                              cider_per_split.json,
                              cider_per_topic_tier.json,
                              full_headline.json}
"""
from __future__ import annotations
import contextlib
import io
import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("NLTK_DATA", "/tmp/nltk_data")
os.makedirs(os.environ["NLTK_DATA"], exist_ok=True)
import nltk
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", download_dir=os.environ["NLTK_DATA"], quiet=True)

from pycocoevalcap.cider.cider import Cider
from pycocoevalcap.bleu.bleu import Bleu
from pycocoevalcap.rouge.rouge import Rouge

GOLD = "/data/luis/ChemQA/dataset_gold.jsonl"
EVAL_ROOT = Path("/data/macaulay/ChemQA/ChemQA/eval/results_full")
MODELS = ["gemma3_12b", "llama3_1_8b", "qwen2_5_14b"]
VARIANTS = ["base", "ft"]
METRIC_KEYS = ["CIDEr", "BLEU-1", "BLEU-4", "ROUGE-L"]
OUT_DIR = Path(__file__).parent / "outputs" / "per_topic_finetune"
PER_SAMPLE_DIR = OUT_DIR / "per_sample"

_WS = re.compile(r"\s+")
_NULL = io.StringIO()


def _normalize(s: str) -> str:
    return _WS.sub(" ", (s or "").strip().lower())


def difficulty_tier(num_evidence: int) -> str:
    if num_evidence > 50:
        return "easy"
    if num_evidence >= 10:
        return "medium"
    return "hard"


def load_gold_meta(path: str) -> dict[int, dict]:
    meta = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            meta[r["cid"]] = {
                "split": r["split"],
                "num_evidence_sentences": r["num_evidence_sentences"],
            }
    return meta


def load_eval_rows(model: str, variant: str, meta: dict[int, dict]) -> list[dict]:
    path = EVAL_ROOT / model / f"{variant}_chemqa.jsonl"
    rows = []
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            m = meta.get(r["id"], {})
            r["_split"] = m.get("split")
            r["_tier"] = difficulty_tier(m.get("num_evidence_sentences", 0))
            rows.append(r)
    return rows


def score_corpus(rows: list[dict]) -> tuple[dict, list[dict], list[dict]]:
    """Run Cider/Bleu/Rouge once on the full corpus. Returns
    (corpus_metrics, per_sample, kept_rows). Rows with empty references are dropped
    (matches score.py behavior); per_sample is aligned to kept_rows, so callers must
    iterate kept_rows instead of the original input list.

    NOTE: corpus CIDEr / ROUGE-L equal mean(per-sample CIDEr / ROUGE-L) in
    pycocoevalcap, but corpus BLEU does NOT — corpus BLEU computes brevity penalty
    and clipped n-gram precisions over the full corpus, while per-sample BLEU is
    sentence-level. The stratified BLEU numbers in the JSON outputs are therefore
    "mean sentence-level BLEU within stratum", not corpus BLEU on the slice.
    """
    gts, res, kept = {}, {}, []
    for i, r in enumerate(rows):
        pred = _normalize(r.get("prediction", ""))
        ref = _normalize(r.get("reference", ""))
        if not ref:
            continue
        idx = len(kept)
        gts[idx] = [ref]
        res[idx] = [pred if pred else "<empty>"]
        kept.append(r)

    n = len(kept)
    corpus = {"n": n}
    if n == 0:
        for k in METRIC_KEYS:
            corpus[k] = None
        return corpus, []

    with contextlib.redirect_stdout(_NULL):
        cider, cider_per = Cider().compute_score(gts, res)
        bleu, bleu_per = Bleu(4).compute_score(gts, res)
        rouge, rouge_per = Rouge().compute_score(gts, res)

    corpus["CIDEr"] = float(cider)
    corpus["BLEU-1"] = float(bleu[0])
    corpus["BLEU-4"] = float(bleu[3])
    corpus["ROUGE-L"] = float(rouge)

    per_sample = []
    for i in range(n):
        per_sample.append({
            "CIDEr": float(cider_per[i]),
            "BLEU-1": float(bleu_per[0][i]),
            "BLEU-4": float(bleu_per[3][i]),
            "ROUGE-L": float(rouge_per[i]),
        })
    return corpus, per_sample, kept  # type: ignore[return-value]


def aggregate(per_sample: list[dict], rows: list[dict], key_fn) -> dict:
    """Group per-sample scores by key_fn(row) and emit mean per stratum.

    Returns: {stratum_key: {CIDEr, BLEU-1, BLEU-4, ROUGE-L, n}}
    """
    sums: dict = defaultdict(lambda: {k: 0.0 for k in METRIC_KEYS})
    counts: dict = defaultdict(int)
    for r, scores in zip(rows, per_sample):
        k = key_fn(r)
        if k is None:
            continue
        counts[k] += 1
        for mk in METRIC_KEYS:
            sums[k][mk] += scores[mk]
    out = {}
    for k, n in counts.items():
        out[k] = {mk: sums[k][mk] / n for mk in METRIC_KEYS}
        out[k]["n"] = n
    return out


def delta_metrics(base: dict | None, ft: dict | None) -> dict | None:
    if not base or not ft:
        return None
    d = {}
    for k in METRIC_KEYS:
        b, f = base.get(k), ft.get(k)
        d[k] = (f - b) if (isinstance(b, (int, float)) and isinstance(f, (int, float))) else None
    return d


def cell(base: dict | None, ft: dict | None) -> dict:
    n = (base or ft or {}).get("n", 0)
    return {"base": base, "ft": ft, "delta": delta_metrics(base, ft), "n": n}


def main():
    print("[1/4] loading gold metadata", flush=True)
    meta = load_gold_meta(GOLD)
    print(f"      {len(meta)} compounds loaded", flush=True)

    results: dict = {}
    for model in MODELS:
        results[model] = {}
        for variant in VARIANTS:
            t0 = time.time()
            print(f"[2/4] scoring {model}/{variant} (full corpus, one pass)", flush=True)
            rows_in = load_eval_rows(model, variant, meta)
            corpus, per_sample, kept = score_corpus(rows_in)
            n_total = corpus["n"]

            # mean-of-per-sample sanity: corpus CIDEr should equal mean(per_sample CIDEr)
            mean_cider = sum(p["CIDEr"] for p in per_sample) / max(n_total, 1)
            print(f"      corpus CIDEr={corpus['CIDEr']:.6f}  "
                  f"mean(per-sample)={mean_cider:.6f}  "
                  f"BLEU-4={corpus['BLEU-4']:.6f}  ROUGE-L={corpus['ROUGE-L']:.6f}", flush=True)

            # Aggregate sanity vs Macaulay's reference metrics
            mfile = EVAL_ROOT / model / f"{variant}_chemqa.metrics.json"
            if mfile.exists():
                expected = json.loads(mfile.read_text())
                diff = abs(corpus["CIDEr"] - expected["CIDEr"])
                ok = "OK" if diff < 1e-4 else "MISMATCH"
                print(f"      vs summary.md  ours={corpus['CIDEr']:.6f}  "
                      f"ref={expected['CIDEr']:.6f}  diff={diff:.2e}  [{ok}]", flush=True)
                assert diff < 1e-4, f"CIDEr mismatch for {model}/{variant}"

            # Persist per-sample scores so future re-bucketing is just a group-by.
            PER_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
            ps_path = PER_SAMPLE_DIR / f"{model}__{variant}.jsonl"
            with open(ps_path, "w") as f:
                for r, s in zip(kept, per_sample):
                    f.write(json.dumps({
                        "cid": r["id"],
                        "topic": r["topic"],
                        "split": r["_split"],
                        "tier": r["_tier"],
                        **s,
                    }) + "\n")
            print(f"      wrote per-sample → {ps_path.name}", flush=True)

            # Stratify per-sample scores
            per_topic = aggregate(per_sample, kept, lambda r: r["topic"])
            per_tier = aggregate(per_sample, kept, lambda r: r["_tier"])
            per_split = aggregate(per_sample, kept, lambda r: r["_split"])
            per_topic_tier = aggregate(per_sample, kept, lambda r: (r["topic"], r["_tier"]))

            # Row reconciliation
            assert sum(v["n"] for v in per_topic.values()) == n_total
            assert sum(v["n"] for v in per_tier.values()) == n_total
            assert sum(v["n"] for v in per_split.values()) == n_total
            assert sum(v["n"] for v in per_topic_tier.values()) == n_total

            results[model][variant] = {
                "full": corpus,
                "per_topic": per_topic,
                "per_tier": per_tier,
                "per_split": per_split,
                "per_topic_tier": per_topic_tier,
            }
            print(f"      done in {time.time()-t0:.1f}s", flush=True)

    print("[3/4] assembling output JSONs", flush=True)
    all_topics = sorted({t for m in MODELS for t in results[m]["base"]["per_topic"]})
    all_splits = sorted({s for m in MODELS for s in results[m]["base"]["per_split"] if s})
    TIERS = ["easy", "medium", "hard"]

    cider_per_topic = {}
    for t in all_topics:
        cider_per_topic[t] = {
            m: cell(results[m]["base"]["per_topic"].get(t),
                    results[m]["ft"]["per_topic"].get(t))
            for m in MODELS
        }

    cider_per_difficulty = {}
    for tier in TIERS:
        cider_per_difficulty[tier] = {
            m: cell(results[m]["base"]["per_tier"].get(tier),
                    results[m]["ft"]["per_tier"].get(tier))
            for m in MODELS
        }

    cider_per_split = {
        "_note": ("Macaulay's eval outputs only cover split=test; "
                  "train-holdout/val would require re-running the models. "
                  "Canary belongs to Task 4."),
    }
    for split in all_splits:
        cider_per_split[split] = {
            m: cell(results[m]["base"]["per_split"].get(split),
                    results[m]["ft"]["per_split"].get(split))
            for m in MODELS
        }

    full_headline = {
        m: {v: results[m][v]["full"] for v in VARIANTS} for m in MODELS
    }

    # topic × tier — flatten to "topic|tier" string keys for JSON
    topic_tier_flat: dict = {}
    for m in MODELS:
        topic_tier_flat[m] = {}
        for variant in VARIANTS:
            topic_tier_flat[m][variant] = {
                f"{t}|{ti}": v
                for (t, ti), v in results[m][variant]["per_topic_tier"].items()
            }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "cider_per_topic.json").write_text(json.dumps(cider_per_topic, indent=2))
    (OUT_DIR / "cider_per_difficulty.json").write_text(json.dumps(cider_per_difficulty, indent=2))
    (OUT_DIR / "cider_per_split.json").write_text(json.dumps(cider_per_split, indent=2))
    (OUT_DIR / "cider_per_topic_tier.json").write_text(json.dumps(topic_tier_flat, indent=2))
    (OUT_DIR / "full_headline.json").write_text(json.dumps(full_headline, indent=2))

    print("[4/4] outputs:")
    for f in sorted(OUT_DIR.iterdir()):
        print(f"      {f.name:30s} {f.stat().st_size:>10} bytes")


if __name__ == "__main__":
    main()
