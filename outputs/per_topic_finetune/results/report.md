# Task 8 — per-topic performance breakdown of fine-tuned ChemQA models

**Addresses grant-reviewer concerns C3 (soft-rule shortcuts) and C4 (compound coverage skew).**

## Headline (full test split, n=26,205)

| model | base | FT | Δ |
|---|---|---|---|
| gemma3_12b | 0.0055 | 0.2667 | +0.2612 |
| llama3_1_8b | 0.0059 | 0.2387 | +0.2328 |
| qwen2_5_14b | 0.0017 | 0.2758 | +0.2740 |


## Per difficulty tier

Difficulty tier is derived from the parent compound's `num_evidence_sentences`: **easy** > 50, **medium** 10–50, **hard** < 10.

| tier | n | gemma3_12b base | gemma3_12b FT | gemma3_12b Δ | llama3_1_8b base | llama3_1_8b FT | llama3_1_8b Δ | qwen2_5_14b base | qwen2_5_14b FT | qwen2_5_14b Δ |
|---|---|---|---|---|---|---|---|---|---|---|
| easy | 12842 | 0.0076 | 0.2693 | +0.2617 | 0.0086 | 0.2437 | +0.2351 | 0.0025 | 0.2783 | +0.2759 |
| medium | 5858 | 0.0046 | 0.2671 | +0.2625 | 0.0044 | 0.2397 | +0.2353 | 0.0017 | 0.2702 | +0.2685 |
| hard | 7505 | 0.0026 | 0.2619 | +0.2593 | 0.0025 | 0.2294 | +0.2269 | 0.0004 | 0.2757 | +0.2752 |


## Per topic (n ≥ 50)

Raw topic strings from the Q&A (no bucketing applied). 661 distinct topics appear in the test split; 19 have at least 50 rows and are shown below. Full unfiltered numbers, including singleton topics, live in `cider_per_topic.json`.

| topic | n | gemma3_12b base | gemma3_12b FT | gemma3_12b Δ | llama3_1_8b base | llama3_1_8b FT | llama3_1_8b Δ | qwen2_5_14b base | qwen2_5_14b FT | qwen2_5_14b Δ |
|---|---|---|---|---|---|---|---|---|---|---|
| engineering | 3141 | 0.0113 | 0.2602 | +0.2489 | 0.0024 | 0.2250 | +0.2227 | 0.0014 | 0.2710 | +0.2696 |
| mechanism | 2591 | 0.0027 | 0.1534 | +0.1507 | 0.0030 | 0.1582 | +0.1552 | 0.0011 | 0.1733 | +0.1723 |
| physicochemical | 2346 | 0.0052 | 0.2841 | +0.2790 | 0.0018 | 0.2634 | +0.2616 | 0.0017 | 0.2880 | +0.2863 |
| therapeutic_use | 2073 | 0.0045 | 0.1775 | +0.1730 | 0.0044 | 0.1543 | +0.1499 | 0.0012 | 0.1800 | +0.1788 |
| toxicity | 1564 | 0.0029 | 0.1992 | +0.1962 | 0.0108 | 0.1754 | +0.1646 | 0.0036 | 0.2021 | +0.1985 |
| reactivity | 1469 | 0.0035 | 0.3002 | +0.2967 | 0.0071 | 0.2787 | +0.2715 | 0.0011 | 0.3117 | +0.3106 |
| metabolism | 1446 | 0.0035 | 0.2509 | +0.2474 | 0.0127 | 0.2072 | +0.1945 | 0.0015 | 0.2445 | +0.2431 |
| pharmacophore | 1284 | 0.0065 | 0.3137 | +0.3072 | 0.0046 | 0.2854 | +0.2808 | 0.0017 | 0.3084 | +0.3067 |
| adme | 1208 | 0.0035 | 0.1833 | +0.1797 | 0.0062 | 0.1754 | +0.1692 | 0.0012 | 0.1930 | +0.1918 |
| functional_groups | 1205 | 0.0046 | 0.3421 | +0.3375 | 0.0061 | 0.3289 | +0.3228 | 0.0013 | 0.3740 | +0.3727 |
| composition | 1127 | 0.0034 | 0.5889 | +0.5855 | 0.0057 | 0.5159 | +0.5102 | 0.0016 | 0.6348 | +0.6332 |
| scaffold | 1064 | 0.0050 | 0.2676 | +0.2627 | 0.0094 | 0.2437 | +0.2343 | 0.0006 | 0.2564 | +0.2559 |
| electronics | 986 | 0.0110 | 0.3395 | +0.3285 | 0.0088 | 0.3114 | +0.3026 | 0.0066 | 0.3439 | +0.3373 |
| design_levers | 695 | 0.0067 | 0.2192 | +0.2124 | 0.0056 | 0.1858 | +0.1802 | 0.0009 | 0.2244 | +0.2234 |
| stereochemistry | 686 | 0.0009 | 0.5641 | +0.5633 | 0.0004 | 0.4696 | +0.4692 | 0.0009 | 0.6182 | +0.6173 |
| drug_interactions | 638 | 0.0068 | 0.2005 | +0.1937 | 0.0056 | 0.1603 | +0.1546 | 0.0006 | 0.1852 | +0.1846 |
| shape_sterics | 553 | 0.0097 | 0.2768 | +0.2671 | 0.0039 | 0.2190 | +0.2152 | 0.0013 | 0.2592 | +0.2579 |
| druglikeness | 314 | 0.0224 | 0.3456 | +0.3232 | 0.0098 | 0.2522 | +0.2424 | 0.0071 | 0.3381 | +0.3309 |
| resistance_mechanism | 112 | 0.0074 | 0.2082 | +0.2007 | 0.0051 | 0.2048 | +0.1997 | 0.0000 | 0.2168 | +0.2168 |


## Splits

Macaulay's eval outputs only cover split=test; train-holdout/val would require re-running the models. Canary belongs to Task 4.



## Rule-46 flags

- None: every topic with n ≥ 50 has a consistent-sign positive Δ CIDEr across models.


## Interpretation

- **Methodology.** Each model-variant's full 26,205-row test corpus was scored once with `pycocoevalcap`, capturing per-sample CIDEr/BLEU/ROUGE alongside the corpus aggregate. Stratum scores are the mean of per-sample scores within the stratum (corpus CIDEr and ROUGE-L are themselves means of their per-sample arrays in pycocoevalcap, so the headline matches `summary.md` exactly; corpus BLEU is not, so the BLEU numbers in the per-stratum JSONs are mean sentence-level BLEU and won't sum back to the corpus BLEU).

- **C4 (compound coverage skew).** Tier deltas are nearly uniform across difficulty for every model: gemma3_12b Δ +0.262 (easy) / +0.262 (medium) / +0.259 (hard); qwen2_5_14b Δ +0.276 / +0.269 / +0.275. Fine-tuning is **not** concentrated on the evidence-rich head; the lift extends to compounds with <10 evidence sentences. This is a defensible answer to the coverage-skew critique.

- **C3 (soft-rule shortcuts).** For qwen2_5_14b, the top-5 Δ CIDEr topics are `composition` (Δ+0.63, n=1127), `stereochemistry` (Δ+0.62, n=686), `functional_groups` (Δ+0.37, n=1205), `electronics` (Δ+0.34, n=986), `druglikeness` (Δ+0.33, n=314) — all SMILES-derivable structural claims. The bottom-5 are `toxicity` (Δ+0.20, n=1564), `adme` (Δ+0.19, n=1208), `drug_interactions` (Δ+0.18, n=638), `therapeutic_use` (Δ+0.18, n=2073), `mechanism` (Δ+0.17, n=2591) — all functional/clinical reasoning claims. The structural-vs-functional gap is real and visible in every model (see heatmap). Fair-warning statement for the paper: fine-tuning teaches structural reasoning much more strongly than functional reasoning, consistent with the soft rule allowing functional claims to draw on training recall rather than required evidence grounding.

- **Splits.** Test-only by construction. Macaulay's `results_full/` does not include train-holdout, val, or canary; canary stratification is Task 4's deliverable.

- **No rule-46 anomalies** (no sign flips or near-zero Δ on the n≥50 topics) — clean signal across all three model families.
