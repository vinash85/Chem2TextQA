# Phase 4 grounding audit — results

Empirical measurement of how grounded Chem2TextQA's Phase-2 answers are
against the cited evidence. This document fixes the headline numbers
referenced in `DATASHEET.md`, `RESPONSIBLE_AI.md`, and `LIMITATIONS.md`.

The orchestrator and code live alongside this file in
`phase4_grounding/`; see `USAGE.md` to reproduce. The detailed per-topic
/ per-split summary tables and per-row cross-check comparison are
regenerated into `phase4_grounding/outputs/` by the orchestrator
(gitignored — reproducible, not redistributed).

## Headline

A model judges every Phase-2 answer claim-by-claim against the attached
evidence and labels each claim as **STATED**, **IMPLIED**, **STRUCTURAL**
(derivable from SMILES alone), or **UNSUPPORTED** (training-recall
candidate). UNSUPPORTED is the proxy for training-recall risk; the PLAN
threshold for narrowing the paper's grounding claim is 20%.

| View | n claims | UNSUPPORTED | 95% Wilson CI | Decision |
|---|---|---|---|---|
| **keep-structural** *(STRUCTURAL excluded from denominator — clean training-recall proxy)* | 3,076 | **55.20%** | 53.43–56.97% | **NARROW** |
| **drop-structural** *(STRUCTURAL collapsed into IMPLIED — original PLAN spec)* | 3,799 | **44.70%** | 43.11–46.30% | **NARROW** |

Both views are well above the 20% PLAN threshold. The paper's grounding
claim must be narrowed and training-recall risk explicitly flagged.

## Sample

- **300 Q&As** sampled with seed 0 from the gold dataset
  (`data/dataset_gold.jsonl`), stratified across topic / split /
  evidence-attached buckets.
- All 300 judged successfully (292 by the primary model, 8 by the
  cross-check model after primary refusals — see "Refusals" below).
- 30 Q&As were independently re-judged by a second model for agreement
  validation.

## Methodology

| Stage | Model | Role |
|---|---|---|
| Sample | (deterministic) | `sample_qa.py --n 300 --seed 0` |
| Primary judge | `anthropic/claude-sonnet-4.6` | per-claim label |
| Cross-check | `google/gemini-2.5-pro` (n=30) | independent re-judgment |
| Aggregate | (deterministic) | rates, CIs, by-topic / by-split splits |

Total cost: **$10.16** ($9.76 primary + cross-check + $0.39 rejudge
fallback for the 8 refused rows).

## Where the recall risk concentrates (keep-structural)

UNSUPPORTED rate by topic:

| Topic | UNSUPPORTED | n |
|---|---|---|
| **engineering** | **74.6%** | ~640 |
| adme | 69.5% | ~120 |
| metabolism | 68.8% | ~460 |
| design_levers | 67.1% | ~165 |
| drug_interactions | 64.8% | ~55 |
| toxicity | 40.6% | ~540 |
| mechanism | 40.7% | ~615 |
| therapeutic_use | 38.2% | ~415 |

Engineering / design / metabolism Q&As have the worst grounding —
unsurprisingly, since these topics ask for analog-design or pathway
reasoning that goes beyond what an evidence sentence directly states.

Q&As **with** evidence attached have a *higher* UNSUPPORTED rate
(62.94%) than those without (46.49%) in the keep-structural view —
counterintuitive but consistent with training-recall: when evidence is
attached, the model is also more likely to add unsourced elaboration on
top of it.

Full breakdown by topic / evidence / split, the per-Q&A UNSUPPORTED
histogram, and the top-20 worst-grounded Q&As regenerate into
`outputs/grounding_summary_keep_structural.md` on each run.

## Cross-check validation

30 of the 300 Q&As were independently re-judged by `gemini-2.5-pro`.
Macro UNSUPPORTED rates:

| View | sonnet (primary) | gemini (cross-check) | macro Δ |
|---|---|---|---|
| keep-structural | 59.73% | 63.41% | **+3.68pp** |
| drop-structural | 47.09% | 48.40% | **+1.31pp** |

The two models agree closely on the macro rate (within 4pp, both above
the 20% threshold). Per-row agreement is looser — mean absolute diff
~11pp (keep) — but **26/30 rows agree to within 20pp**, and the few
larger per-row disagreements average out at the macro level.

This validates the headline UNSUPPORTED rate as model-agnostic to the
choice of judge, not an artifact of one model's labeling style.

Full per-row table regenerates into `outputs/cross_check_agreement.md`.

## Refusals — a methodological note

The primary model (`claude-sonnet-4.6`) refused on 8 of 300 Q&As (2.7%)
by returning empty/null content. All 8 are **dual-use chemistry
queries**: engineering of toxins or controlled substances (ziconotide,
yessotoxin, anthopleurin B), pesticide modifications (carbofuran),
heavy-metal substitutions (lead chloride), and toxicity questions about
known toxins. The pattern is consistent with Anthropic's safety filter
on synthesis-uplift adjacent prompts.

Falling back to `gemini-2.5-pro` on the same 8 prompts succeeded on all
8 with structurally reasonable claim decompositions.

Implication for users:

- Single-model audits of dual-use chemistry datasets will systematically
  undercount the "engineering" topic. A heterogeneous-judge protocol is
  required for full coverage.
- Anyone reproducing this audit with a single model should expect ~3%
  loss on that topic and report it.

## Reproducing

```bash
phase4_grounding/run_phase4_grounding.sh --n 300 --max-usd 100
python -m phase4_grounding.scripts.rejudge_errors          # gemini fallback for refusals
python -m phase4_grounding.scripts.aggregate --out-dir phase4_grounding/outputs
python -m phase4_grounding.scripts.analyze_cross_check_agreement
```

Final cost: ~$10. See `USAGE.md` for argument reference.
