# Task 6 — Leakage Classifier: Plan

**Question.** Does the Phase-1 model ever borrow text verbatim from evidence sentences? Detect per-Q&A leakage via n-gram, longest-match, and embedding metrics.

**Scope.** Addresses critique C2 (prompt forbids quoting evidence; does the model follow the rule in practice?). The gold dataset's pilot-set forbidden-phrase audit was 0.07% — this task goes deeper, looking for paraphrase-grade and verbatim borrowing across a broader sample.

## Inputs

- `/data/luis/Chem2TextHackathon/full_premium_kimi/dataset_gold.jsonl` (15,509 compounds, ~189K agree-only Q&A)

## Outputs

All under `/home/dandreas/chem2text/outputs/leakage/`:

| File | Contents |
|---|---|
| `PLAN.md` | This plan (the contract). |
| `sample.jsonl` | The deterministic 20K Q&A sample. One row per Q&A with cid, qa_index, topic, phase1_answer, and all parent evidence sentences. |
| `per_qa_leakage.jsonl` | One row per sampled Q&A with the three metrics + flags. |
| `flagged_examples.md` | Human-reviewable list of flagged cases (capped for readability; full list in per_qa_leakage.jsonl). No judgments — for user review. |
| `leakage_summary.md` | Aggregate flag rates, metric distributions, intersections between flag types. |

## Decisions (locked in from conversation)

1. **Longest common match = longest common contiguous token *substring*** (not subsequence). Threshold **> 40 tokens**.
   - Rationale: the task spec frames this as "verbatim phrase reuse", which is contiguous. A 40-token common *subsequence* could be 40 scattered words and would be near-zero signal; a 40-token contiguous run is unambiguous quoting.
   - Computed per (answer, evidence_sentence) pair via `difflib.SequenceMatcher(None, a_tokens, e_tokens).find_longest_match(...).size`, taking the max over all evidence sentences of the parent compound.
   - Metric recorded: `lcs_tokens` (int, max contiguous token run).

2. **Token 5-gram overlap.** Word-level. Distinct 5-grams in the answer that also appear in any of the parent compound's evidence sentences (union). Threshold **> 3**.
   - Tokenization: lowercase, split on whitespace, strip leading/trailing punctuation per token. Identical tokenizer used for LCS.
   - Metric recorded: `ngram5_overlap` (int).

3. **Embedding cosine.** `sentence-transformers/all-MiniLM-L6-v2`. Encode each unique text once. Per Q&A: max cosine between answer embedding and any parent-compound evidence-sentence embedding. Threshold **> 0.85**.
   - Metric recorded: `cos_max` (float in [-1, 1]).

4. **Coverage.** Full gold dataset (188,541 Q&A across 15,509 compounds, all splits / topics) — i.e., no sampling in the final run. The code still supports a seeded subsample via `config.SAMPLE_SIZE` (originally 20,000) for auditability: an initial 20K-sample run was done and its outputs are preserved at `outputs/leakage/archive_20k_sample/` for comparison.

5. **Answer field.** `phase1_answer` (the model under audit is the Phase-1 generator).

6. **Manual inspection.** We do not make judgments. We stage flagged cases (all three categories, plus intersections) in `flagged_examples.md` for user review. Cap at ~20 cases per category (as per the task spec's "Sample 20 flagged cases") with random seed=42 within each category; the full flagged list is in `per_qa_leakage.jsonl` for anyone who wants to look past the sample.

## Non-decisions (defaults, flag if you want them changed)

- No stratification across topics or splits in the sample — uniform across all Q&A.
- Evidence sentences are used as-is (with `[COMPOUND]` redaction still in place). The answers don't contain `[COMPOUND]` so a single shared token doesn't affect anything.
- Only `phase1_answer` is scored. Phase-2 (Kimi) is not audited here — different model, different audit.

## Method, step by step

1. **Env.** Create a fresh conda env `chem2text_leakage` with Python 3.11, torch (cu128), sentence-transformers, tqdm, numpy. Script: `scripts/leakage/setup_env.sh`.
2. **Sample.** Stream `dataset_gold.jsonl`, collect all (cid, qa_index) pairs sorted, seed 42 draw of 20,000. For each, emit a sample row with the phase1_answer and parent compound's evidence sentences. Script: `scripts/leakage/sample.py` → `sample.jsonl`.
3. **Embed.** Collect unique text strings (answers + evidence sentences) from the sample, encode on one GPU in batches, save `.npz` + id→row index map. Script: `scripts/leakage/embed.py` → `embeddings.npz`, `text_index.json`.
4. **Metrics.** For each sampled Q&A, compute `lcs_tokens`, `ngram5_overlap`, `cos_max`. Script: `scripts/leakage/compute_metrics.py` → `per_qa_leakage.jsonl`.
5. **Summarize.** Aggregate flag rates, metric distributions, co-flagging, write `leakage_summary.md` and `flagged_examples.md`. Script: `scripts/leakage/summarize.py`.
6. **Driver.** `scripts/leakage/run.sh` runs 2–5 in order, assuming 1 is done.

## Reproducibility

- All scripts take no positional arguments — all inputs/outputs are fixed paths or CLI-settable with the same defaults we used.
- `PLAN.md` records the thresholds and sample seed. The scripts read the same constants from a shared `scripts/leakage/config.py`.
- `leakage_summary.md` echoes the thresholds, sample size, and embedding model name at the top.
- `run.log` captures stdout/stderr of each step with timestamps.

## Rough compute budget

- Env setup (one-time): 3–5 min
- Sampling: < 1 min
- Embedding ~40K texts (20K answers + ~20K unique evidence sentences) on one H100 with all-MiniLM-L6-v2: ~2–5 min
- Metrics (CPU-bound, difflib dominant): ~5–10 min single-process; parallelizable if needed
- Summary: < 1 min
- Total: ~15–25 min after env is built
