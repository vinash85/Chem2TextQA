# Leakage Summary

Source: `per_qa_leakage.jsonl` (20000 rows, sampled from `dataset_gold.jsonl`; n=20000, seed=42).

## Setup

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- LCS = longest common *contiguous token substring* (word tokens, lowercased, punct-stripped)
- 5-gram overlap = `|5grams(answer) ∩ 5grams(⋃ evidence sentences)|`
- Cosine = max dot product of answer embedding vs any evidence-sentence embedding (both L2-normed)

## Flag thresholds

| Metric | Threshold | Flag rule |
|---|---|---|
| `lcs_tokens` | > 40 | contiguous ≥41-token reuse |
| `ngram5_overlap` | > 3 | ≥4 shared 5-grams |
| `cos_max` | > 0.85 | ≥0.85 max cosine |

## Flag rates

| Flag | Count | Rate |
|---|---|---|
| `flag_lcs`   (LCS > 40) | 0 | 0.00% |
| `flag_ngram` (5-gram overlap > 3) | 184 | 0.92% |
| `flag_cos`   (cos > 0.85) | 418 | 2.09% |
| `flag_any`   (any of the three) | 572 | 2.86% |

## Co-flagging

| Combination | Count | Rate |
|---|---|---|
| lcs ∩ ngram | 0 | 0.00% |
| lcs ∩ cos   | 0 | 0.00% |
| ngram ∩ cos | 30 | 0.15% |
| all three   | 0 | 0.00% |

## Metric distributions (all rows)

| Metric | mean | median | p90 | p95 | p99 | max |
|---|---|---|---|---|---|---|
| lcs_tokens | 2.5835 | 2.0 | 4 | 5 | 7 | 16 |
| ngram5_overlap | 0.1518 | 0.0 | 0 | 1 | 3 | 13 |
| cos_max | 0.5267 | 0.5263 | 0.7612 | 0.8094 | 0.8787 | 0.9697 |

## Flag-any rate by split

| split | flagged | total | rate |
|---|---|---|---|
| test | 92 | 2862 | 3.21% |
| train | 395 | 14265 | 2.77% |
| val | 85 | 2873 | 2.96% |

## Flag-any rate by topic (top 20 topics with ≥30 sampled Q&A, sorted by rate)

| topic | flagged | total | rate |
|---|---|---|---|
| synergy | 3 | 36 | 8.33% |
| biosynthesis | 3 | 38 | 7.89% |
| therapeutic_use | 119 | 1572 | 7.57% |
| drug_interactions | 32 | 446 | 7.17% |
| mechanism | 129 | 1824 | 7.07% |
| resistance_mechanism | 4 | 61 | 6.56% |
| diagnostics | 2 | 32 | 6.25% |
| analytical_chemistry | 2 | 33 | 6.06% |
| toxicity | 62 | 1170 | 5.30% |
| metabolism | 54 | 1305 | 4.14% |
| adme | 34 | 901 | 3.77% |
| design_levers | 10 | 493 | 2.03% |
| reactivity | 13 | 1170 | 1.11% |
| physicochemical | 12 | 1829 | 0.66% |
| pharmacophore | 5 | 875 | 0.57% |
| stereochemistry | 2 | 567 | 0.35% |
| shape_sterics | 1 | 466 | 0.21% |
| engineering | 4 | 2330 | 0.17% |
| scaffold | 1 | 756 | 0.13% |
| functional_groups | 0 | 1048 | 0.00% |

## Notes

- Flag rates measure *borrowing signal*, not judgment. Technical terminology, IUPAC fragments, and mechanism names legitimately recur in both evidence and answers. `flagged_examples.md` stages cases for manual review without calling them leakage.

- Strong signal is co-flagging: items flagged on multiple metrics are much more likely to be actual paraphrase/copy.
