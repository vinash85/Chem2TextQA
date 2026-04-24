# Reproducibility Manifest for Chem2TextQA

This document records every source of randomness, every pinned model, every
prompt, every data snapshot, and every configuration required to re-create
the `dataset_gold.jsonl` release of Chem2TextQA. It addresses reviewer
concern **C5** (stochasticity and reproducibility) in the hackathon agenda.

Three artifacts together constitute the reproducibility bundle:

- `REPRODUCIBILITY.md` — this document.
- `environment.lock.yml` — exact conda environment snapshot
  (`conda env export`).
- `prompts_frozen/` — dated, read-only copies of every prompt file used in
  Phases 1–3.

---

## 1. Models

All LLM calls go through OpenRouter. Models are pinned by ID in
`chem2textqa/qa_pipeline/config.py` and overridden per-run by the shell
scripts.

| Phase | Role | OpenRouter model ID | Temperature | Reasoning tokens |
|---|---|---|---|---|
| 1 — Q&A generation | Primary author | `google/gemini-3-flash-preview` | 0.3 | default |
| 2 — Blind re-answer | Independent peer | `moonshotai/kimi-k2.5` | 0.3 | **disabled** (`reasoning={"enabled": false}`) |
| 3 — Judge | Agreement classifier | `google/gemma-4-31b-it` | 0.0 | **disabled** |

Training-cutoff notes (per model card at time of use):

- `google/gemini-3-flash-preview` — approximately early 2025.
- `moonshotai/kimi-k2.5` — approximately mid-2025.
- `google/gemma-4-31b-it` — approximately mid-2025.

The conservative post-cutoff boundary adopted in `CONTAMINATION.md` is
**2025-09-01**. The realized canary uses the weaker **2024-01-01** cutoff
(see §3).

**Deprecation risk.** `google/gemini-3-flash-preview` is a preview model and
may be withdrawn from OpenRouter without notice. If that happens,
regenerating the dataset end-to-end will produce a different output.
Response caching is proposed but not yet implemented (`LIMITATIONS.md` §7).

---

## 2. Sources of randomness (the "RNG surface")

| Component | Mechanism | Seed / control |
|---|---|---|
| Phase 0 evidence sampling | Per-compound subsampling of matching redacted sentences down to the 500-sentence cap | `random.Random(cid)` — seeded by the compound's PubChem CID, so deterministic given the same CID and the same source corpus |
| Phase 1 generation | OpenRouter temperature sampling | `temperature=0.3`. No `seed` parameter passed to the API; content is therefore non-deterministic across runs |
| Phase 2 re-answering | OpenRouter temperature sampling | `temperature=0.3`, reasoning disabled |
| Phase 3 judging | OpenRouter temperature sampling | `temperature=0.0` (greedy). Output is ~deterministic per model version |
| Phase 3 heuristic pre-filter | Token-overlap classifier in `phase_3_validate/heuristic.py` | Fully deterministic; assigns a fraction of verdicts without any LLM call. Each output record's `judge_source` field indicates `"heuristic"` or `"llm"` |
| Train / dev / test split | Deterministic hash of CID string | `chem2textqa/qa_pipeline/assemble.py::assign_split` — 80 / 10 / 10 by CID hash; canary records get `split="canary"` regardless |
| Canary set construction | Date filter, not random | `scripts/build_contamination_canary.py` with `--cutoff 2024-01-01` |

Measured seed-to-seed variance on Phase 1 (30 compounds × 3 independent
runs, identical evidence, temperature 0.3):

| Metric | Value |
|---|---|
| Mean (max − min) Q&A count per compound | 0.36 |
| Mean pairwise answer token-Jaccard across seeds | 0.344 |
| Per-run API failure rate | ~3% (1–2 of 30 compounds per seed) |
| Compounds producing Q&A in all three runs | 28 / 30 |

Interpretation: **counts** are stable across seeds; **content** is ~34%
token-overlap across seeds. Paraphrase-level drift, not structural drift.
See `LIMITATIONS.md` §6.

**Published dataset seed.** The shipped `dataset_gold.jsonl` is a
**single-seed run** (one pass through Phase 1 per compound). Users who want
seed-averaged content must re-invoke the pipeline with
`scripts/measure_seed_variance.py` as a template.

---

## 3. Canary cutoff date

| Parameter | Value |
|---|---|
| Planned (conservative) cutoff | **2025-09-01** |
| Realized cutoff (feasibility) | **2024-01-01** |
| Canary compounds retained | 120 with evidence (119 shipped; one lost during assembly) |
| Main compounds | 15,547 (15,509 in gold subset) |

The stricter 2025-09-01 cutoff yielded zero compounds with ≥3
premium-tier articles, so the weaker 2024-01-01 cutoff was adopted. This
is a **late-training canary**, not a true post-cutoff canary. See
`CONTAMINATION.md` "Realized canary size and its limitation".

---

## 4. Prompts

Prompts are versioned with the repo and, for this release, additionally
copied into `prompts_frozen/` with the freeze date in the filename.

| Phase | Live source | Frozen copy |
|---|---|---|
| 1 — Q&A generation (system + per-question) | `chem2textqa/qa_pipeline/phase_1_qa/prompts.py` | `prompts_frozen/phase_1_prompts_<YYYY-MM-DD>.py` |
| 2 — Blind re-answer | `chem2textqa/qa_pipeline/phase_2_independent/independent.py` | `prompts_frozen/phase_2_independent_<YYYY-MM-DD>.py` |
| 3 — Judge | `chem2textqa/qa_pipeline/phase_3_validate/judge.py` | `prompts_frozen/phase_3_judge_<YYYY-MM-DD>.py` |

Any post-freeze edit to the live sources requires re-generating the
dataset — they are part of the dataset's provenance.

---

## 5. Environment

`environment.yml` (in this repo) pins only `python=3.11` and the package
itself; the concrete dependency tree is locked in `pyproject.toml`
(`[dev]` extras) and snapshot-exported to `environment.lock.yml`.

Regenerate the lock file from a clean install:

```bash
conda env create -f environment.yml
conda activate chem2textqa
pip install -e ".[dev]"
conda env export > environment.lock.yml
```

The lock file in the repo was produced with the above sequence on the
release machine; exact OS and CUDA details are in its header.

**GPU host required.** The pinned environment includes `cuda-toolkit==13.0.2`,
`torch==2.11.0`, `triton==3.6.0`, and the full `nvidia-cu13` runtime stack
(`nvidia-cublas`, `nvidia-cudnn-cu13`, `nvidia-cufft`, `nvidia-cusolver`,
`nvidia-cusparse`, `nvidia-nccl-cu13`, etc.). Reproducing the env end-to-end
requires a CUDA-13-capable Linux GPU host; a CPU-only machine cannot resolve
the full dependency graph.

---

## 6. Source data snapshots

| Corpus | Snapshot | Local path |
|---|---|---|
| PubMed XML baseline | 2026 release | `data/bulk/pubmed_baseline/*.xml.gz` (1,334 files, ~40M abstracts) |
| PubChem bulk tables | Q1 2026 | `data/bulk/CID-*.gz` (CID-SMILES, CID-Title, CID-Mass, CID-InChI-Key, CID-IUPAC, CID-PMID, CID-Synonym-filtered, CID-MeSH) |
| PMC open-access full text | Current as of **2026-04** | `data/bulk/pmc_fulltext.jsonl` |
| Curated CID lists | Fetched at build time | `data/bulk/sources/{DrugBank,HMDB,KEGG,ChEBI,BindingDB,ChEMBL}.txt` |

Bulk FTP downloads are not redistributed (GB-scale, `data/` is
gitignored). They are reproducible from the public sources by running
`bash run_pmc_download.sh` followed by `bash run_build_dataset_v2.sh`
— with the caveat that the upstream FTP snapshots advance over time, so
re-downloading after the dates above will produce a slightly different
raw pool.

---

## 7. How to replay the pipeline

Full end-to-end reproduction (~12–15 hours, ~$750 at April 2026
OpenRouter prices):

```bash
# One-time: bulk download + filter + tier (~15 GB disk, ~6 hours)
bash run_pmc_download.sh
bash run_build_dataset_v2.sh
bash run_cleanup_v2.sh

# Phase 0: extract redacted evidence bundles (no LLM, ~1–2 hours, $0)
bash run_phase0_full_premium.sh

# Phases 1–3 + assembly + agree-only gold subset, main + canary.
# Writes to data/qa_pipeline/full_premium_kimi/
bash run_qa_full_premium.sh
```

Set `OPENROUTER_API_KEY` in `.env` before running the QA phases (see
`.env.example`). The four QA phases each write append-only JSONL and
resume from their output files, so runs are interruptible and
restartable.

---

## 8. Provenance of the shipped release

The canonical release files live at
`/data/luis/Chem2TextQA/data/qa_pipeline/full_premium_kimi/`:

- `dataset_gold.jsonl` — 15,509 main compounds, ~189K agree-only Q&A, with
  `split ∈ {train, dev, test}` populated by deterministic CID-hash.
- `dataset_final.jsonl` — all Q&A including disagree / unclear (~210K).
- `canary/dataset_final.jsonl` — 119 post-2024 compounds, ~1.5K Q&A,
  `split = "canary"`.
- `cid_to_split.json` — CID → split audit trail.
- `scaffold_split_report.json`, `dataset_summary.json`,
  `dataset_gold_summary.json` — release-time statistics.

Per-record schema is documented in `HACKATHON.md` §3.

**Git commit SHA of the run.** `b0a456e` — the code state of
`/data/luis/Chem2TextQA/` at the moment `dataset_gold.jsonl` was
generated. Reviewers can recover the exact pipeline code with
`git checkout b0a456e` in a clone of the repo. Recommended to also
record this SHA in `full_premium_kimi/release_commit.txt` alongside the
JSONLs for in-band provenance.

---

## 9. Caveats

1. **Preview-model deprecation.** Phase 1 uses a preview model that may
   be withdrawn without notice. Response caching (proposed in
   `LIMITATIONS.md` §7) would mitigate this but is not implemented.
2. **No OpenRouter `seed` parameter.** Even with identical prompts and
   identical temperature, two separate runs produce different Phase 1 /
   Phase 2 outputs at the ~34% Jaccard level documented in §2. Exact
   byte-level reproduction is not achievable with the current
   architecture.
3. **Rate-limit-induced reordering.** The async OpenRouter client retries
   and reorders completions, so even the order of records in the
   appended JSONLs may vary across runs. Join on `(cid, qa_index)` for
   reproducible comparisons, not on line number.
4. **Source-corpus drift.** PubMed, PubChem, and PMC update continuously.
   Re-downloading after the dates in §6 yields a superset of the corpus
   used here. The date-pinned snapshots are not archived alongside the
   dataset.
5. **Anonymization.** This repository contains author-identifying
   information in git history. Double-blind submission requires a fresh
   clone with squashed history — a manual step not handled by the
   codebase (`LIMITATIONS.md` §9).
