# Task 6 — Leakage Classifier (evidence → answer text overlap)

**Question.** Does the Phase-1 model ever borrow text verbatim from evidence sentences? Detect per-Q&A leakage via n-gram, longest-match, and embedding metrics.

**Scope.** Addresses critique C2 (prompt forbids quoting evidence; does the model follow the rule in practice?). The pilot-set forbidden-phrase audit was 0.07% — this task goes deeper, looking for paraphrase-grade and verbatim borrowing across the full dataset.

## Results (all 188,541 agree-only Q&A)

| Metric | Threshold | Flagged | Rate |
|---|---|---|---|
| `lcs_tokens` (longest common contiguous token substring) | reported as threshold curve — see `leakage_summary.md` | — | max observed = **19 tokens** |
| `ngram5_overlap` | > 3 | 1,821 | 0.97% |
| `cos_max` (all-MiniLM-L6-v2) | > 0.85 | 4,068 | 2.16% |
| `flag_ngram ∨ flag_cos` | — | 5,569 | 2.95% |
| `ngram ∩ cos` (strongest signal) | both | 320 | 0.17% |

- **No Q&A has a 40+ token verbatim contiguous run copied from evidence.** The maximum LCS anywhere in the corpus is 19 tokens. See `leakage_summary.md` for the full threshold curve (rows flagged at `lcs_tokens > T` for T ∈ {4, 5, …, 40}).
- Leakage concentrates in the topics that *must* draw on evidence (therapeutic_use, mechanism, toxicity, drug_interactions, binding_mode, cell_biology, signaling_pathways — rates 10–20%), and is near-zero on purely structural topics (functional_groups 0%, scaffold, engineering, shape_sterics < 0.5%). This is the SMILES-derivable-vs-evidence-supported design rule working as intended.

## Files

| | |
|---|---|
| `PLAN.md` | The locked plan / contract. Decisions around metric semantics, thresholds, sampling. |
| `leakage_summary.md` | Aggregate stats: flag rates, LCS threshold curve, metric distributions, per-split and per-topic breakdowns. |
| `flagged_examples.md` | Top-20 per category (LCS descending, ngram, cos, co-flagged), each with answer + closest evidence sentence staged for review. |
| `per_qa_leakage.jsonl` | One row per Q&A with `lcs_tokens`, `ngram5_overlap`, `cos_max`, and flag booleans. ~50 MB. |
| `scripts/` | Reproducible pipeline (see below). |
| `archive_20k_sample/` | Initial 20K-Q&A pilot run's summary, flagged examples, and per-Q&A file — preserved for audit/comparison. |

## Reproducing the pipeline

The scripts use absolute paths specific to the author's machine layout:
- Input: `/data/luis/Chem2TextHackathon/full_premium_kimi/dataset_gold.jsonl`
- Small outputs: `/home/dandreas/chem2text/outputs/leakage/`
- Large outputs (sample.jsonl 9.1 GB, embeddings.npz 1.9 GB, text_index.json 282 MB): `/data/dandreas/chem2text/outputs/leakage/` with symlinks back into the home-dir outputs folder.

Edit `scripts/config.py` to point at your own paths, then:

```bash
bash scripts/setup_env.sh        # creates chem2text_leakage conda env (torch cu128, sentence-transformers, etc.)
bash scripts/run.sh              # drives: sample.py → embed.py → compute_metrics.py → summarize.py
```

Approximate runtime on one H100: ~25 min end-to-end (embedding 1.28 M unique texts ≈ 4.5 min, scoring 188 K Q&A ≈ 9 min, the rest is I/O and summary).

## Metric definitions

- **LCS (longest common contiguous token substring).** Max contiguous token run shared between the answer and any single evidence sentence of the parent compound. Tokens = lowercased, whitespace-split, punctuation-stripped. Computed via `difflib.SequenceMatcher.find_longest_match`.
- **5-gram overlap.** Count of distinct word 5-grams shared between the answer and the union of parent compound's evidence 5-grams. Same tokenization as LCS.
- **Cosine.** Max dot product between the answer's `all-MiniLM-L6-v2` embedding and any parent-compound evidence-sentence embedding. Both L2-normalized.

## Sampling

Final run covers the entire gold dataset (188,541 Q&A, 15,509 compounds). The plan reserves a `SAMPLE_SIZE` knob in `config.py` for deterministic subsampling (seed=42); the `archive_20k_sample/` directory is the 20K-Q&A pilot that was done first to validate the pipeline.

## Design notes

- LCS is reported as a threshold curve rather than a single-threshold flag because the max value observed (19 tokens) fell well below the originally-specified cutoff of 40, so a fixed threshold always produced zero flags. The curve makes the real distribution visible.
- The ngram + cos thresholds (> 3 and > 0.85 respectively) are from the task spec; they yield tractable flagged counts.
- The `ngram ∩ cos` intersection is the most load-bearing signal: 320 Q&A (0.17%) co-flag, and manual inspection of the top-composite cases (see `flagged_examples.md`) reveals clear paraphrase-grade borrowing on functional-topic answers (therapeutic use, mechanism, toxicity).
