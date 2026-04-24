# Leakage Summary

Source: `per_qa_leakage.jsonl` (188541 rows, sampled from `dataset_gold.jsonl`; n=500000, seed=42).

## Setup

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- LCS = longest common *contiguous token substring* (word tokens, lowercased, punct-stripped)
- 5-gram overlap = `|5grams(answer) ∩ 5grams(⋃ evidence sentences)|`
- Cosine = max dot product of answer embedding vs any evidence-sentence embedding (both L2-normed)

## Flag thresholds

LCS is reported as a threshold curve below (no single cutoff).
The other two metrics use fixed thresholds:

| Metric | Threshold | Flag rule |
|---|---|---|
| `ngram5_overlap` | > 3 | ≥4 shared 5-grams |
| `cos_max` | > 0.85 | ≥0.85 max cosine |

## LCS threshold curve (tokens > T)

| T | rows with lcs_tokens > T | rate |
|---:|---:|---:|
| 4 | 14433 | 7.655% |
| 5 | 6343 | 3.364% |
| 6 | 2896 | 1.536% |
| 7 | 1373 | 0.728% |
| 8 | 646 | 0.343% |
| 9 | 304 | 0.161% |
| 10 | 153 | 0.081% |
| 12 | 47 | 0.025% |
| 15 | 7 | 0.004% |
| 18 | 2 | 0.001% |
| 19 | 0 | 0.000% |
| 20 | 0 | 0.000% |
| 25 | 0 | 0.000% |
| 30 | 0 | 0.000% |
| 40 | 0 | 0.000% |

_Max LCS observed in the corpus = 19 tokens; any threshold above that flags zero rows._

## Flag rates (ngram + cos)

| Flag | Count | Rate |
|---|---|---|
| `flag_ngram` (5-gram overlap > 3) | 1821 | 0.97% |
| `flag_cos`   (cos > 0.85) | 4068 | 2.16% |
| `flag_any`   (ngram ∨ cos) | 5569 | 2.95% |
| `ngram ∩ cos` (strongest signal) | 320 | 0.17% |

## Metric distributions (all rows)

| Metric | mean | median | p90 | p95 | p99 | max |
|---|---|---|---|---|---|---|
| lcs_tokens | 2.5944 | 2 | 4 | 5 | 7 | 19 |
| ngram5_overlap | 0.1523 | 0 | 0 | 1 | 3 | 16 |
| cos_max | 0.5295 | 0.5299 | 0.7619 | 0.8088 | 0.8788 | 0.9835 |

## Flag-any rate by split

| split | flagged | total | rate |
|---|---|---|---|
| test | 853 | 26205 | 3.26% |
| train | 3840 | 135234 | 2.84% |
| val | 876 | 27102 | 3.23% |

## Flag-any rate by topic (top 20 topics with ≥30 sampled Q&A, sorted by rate)

| topic | flagged | total | rate |
|---|---|---|---|
| binding_mode | 8 | 39 | 20.51% |
| cell_biology | 19 | 99 | 19.19% |
| epigenetics | 8 | 43 | 18.60% |
| signaling_pathways | 18 | 110 | 16.36% |
| oncology | 9 | 63 | 14.29% |
| dermatology | 5 | 35 | 14.29% |
| immunology | 15 | 109 | 13.76% |
| cardiovascular_effects | 14 | 106 | 13.21% |
| therapeutic_potential | 5 | 39 | 12.82% |
| clinical_significance | 4 | 34 | 11.76% |
| biomarker | 4 | 34 | 11.76% |
| combination_therapy | 5 | 45 | 11.11% |
| distribution | 5 | 45 | 11.11% |
| enzymology | 4 | 38 | 10.53% |
| kinetics | 4 | 38 | 10.53% |
| pharmacology | 12 | 116 | 10.34% |
| biocatalysis | 5 | 51 | 9.80% |
| antimicrobial_activity | 5 | 52 | 9.62% |
| remediation | 4 | 42 | 9.52% |
| signaling | 4 | 45 | 8.89% |

## Notes

- Flag rates measure *borrowing signal*, not judgment. Technical terminology, IUPAC fragments, and mechanism names legitimately recur in both evidence and answers. `flagged_examples.md` stages cases for manual review without calling them leakage.

- Strong signal is co-flagging: items flagged on multiple metrics are much more likely to be actual paraphrase/copy.
