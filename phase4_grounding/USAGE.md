# Phase 4 — Grounding Audit Usage

End-to-end usage for the claim-grounding audit. Decomposes each functional
`phase2_answer` into atomic claims, labels them against the parent compound's
evidence sentences, and aggregates the result into two summary markdown files.

See `PLAN.md` for the full design rationale.

## Prerequisites

```bash
pip install httpx pytest pytest-asyncio
```

- `data/dataset_gold.jsonl` available at the repo root (or pass `--data-path`).
- An OpenRouter API key in a plain-text file (default: `~/.openrouter_key`).
  The key is read **only** from this file — never echoed, never logged.

## One-shot run (recommended)

```bash
bash phase4_grounding/run_phase4_grounding.sh \
    --n 300 \
    --api-key-file ~/.openrouter_key \
    --skip-cross-check
```

The orchestrator runs three steps in order. Each step is resumable, so it is
safe to re-run after a crash, network blip, or budget abort.

| Flag | Default | Description |
|---|---|---|
| `--n` | required | total sample size |
| `--api-key-file` | `~/.openrouter_key` | path to the OpenRouter API key |
| `--data-path` | `data/dataset_gold.jsonl` | input dataset |
| `--out-dir` | `phase4_grounding/outputs` | output directory |
| `--primary-model` | `anthropic/claude-sonnet-4.6` | primary judge |
| `--cross-check-model` | `google/gemini-2.5-pro` | second-opinion judge |
| `--skip-cross-check` | off | disable the cross-check pass |
| `--cross-check-n` | `30` | size of the cross-check overlap subset |
| `--max-usd` | `15` | hard budget cap; runner aborts past this |
| `--concurrency` | `5` | async semaphore for OpenRouter calls |
| `--seed` | `0` | RNG seed for sampling |

## Per-step invocation

If you want to run the steps individually (e.g. tweak the sample, then judge):

### 1. Stratified sample

```bash
python -m phase4_grounding.scripts.sample_qa \
    --n 300 \
    --seed 0 \
    --data-path data/dataset_gold.jsonl \
    --out-dir phase4_grounding/outputs
```

Writes `sample.jsonl`. Stratifies by topic with a fixed weighting that
emphasizes the four headline topics (mechanism / engineering / metabolism /
toxicity) and splits 50/50 between QAs with non-empty vs empty `evidence_ids`.

### 2. Judge claims

```bash
python -m phase4_grounding.scripts.judge_claims \
    --api-key-file ~/.openrouter_key \
    --primary-model anthropic/claude-sonnet-4.6 \
    --skip-cross-check \
    --max-usd 15 \
    --concurrency 5 \
    --out-dir phase4_grounding/outputs
```

Reads `sample.jsonl`. Skips `(cid, qa_index)` rows already in
`claims_per_qa.jsonl` so re-runs are idempotent. Writes:
- `claims_per_qa.jsonl` — successful rows (one JSON per line)
- `claims_per_qa.errors.jsonl` — rows where JSON parsing failed twice
- `claims_per_qa.gemini.jsonl` — cross-check pass (only if not skipped)

If cumulative spend crosses `--max-usd`, the runner refuses the next call,
prints the abort reason, and preserves all rows written so far.

### 3. Aggregate

```bash
python -m phase4_grounding.scripts.aggregate \
    --out-dir phase4_grounding/outputs
```

Writes both summary files:
- `grounding_summary_keep_structural.md` — STRUCTURAL claims kept as their own
  bucket, **excluded** from the STATED / IMPLIED / UNSUPPORTED denominator.
- `grounding_summary_drop_structural.md` — STRUCTURAL collapsed into IMPLIED.

Each summary prints the decision-rule banner at the top:
- UNSUPPORTED > 20% → **NARROW** the paper's grounding claim.
- UNSUPPORTED 10–20% → **CAVEAT** in DATASHEET / RESPONSIBLE_AI.
- UNSUPPORTED < 10% → **WELL-BEHAVED**; quote in the dataset card.

## Output layout

```
phase4_grounding/outputs/
├── sample.jsonl
├── claims_per_qa.jsonl
├── claims_per_qa.errors.jsonl
├── claims_per_qa.gemini.jsonl              # only if cross-check enabled
├── claims_per_qa.gemini.errors.jsonl
├── grounding_summary_keep_structural.md
└── grounding_summary_drop_structural.md
```

## Tests

```bash
python -m pytest phase4_grounding/tests -q
```

All tests are offline — `OpenRouterClient` is replaced with a scripted fake.
No live API keys or network access are needed to run the suite.

## Library API (for programmatic use)

```python
from pathlib import Path

from phase4_grounding.grounding.aggregator import Aggregator
from phase4_grounding.grounding.evidence import EvidenceAttacher
from phase4_grounding.grounding.judge import ClaimJudge
from phase4_grounding.grounding.openrouter_client import OpenRouterClient
from phase4_grounding.grounding.prompt import PromptBuilder
from phase4_grounding.grounding.reporter import Reporter
from phase4_grounding.grounding.sampling import Sampler

# 1. Sample
sampler = Sampler(dataset_path="data/dataset_gold.jsonl", seed=0)
rows = sampler.sample(n=300)

# 2. Judge (async)
async with OpenRouterClient(api_key="...", max_usd=15.0) as client:
    judge = ClaimJudge(client, PromptBuilder())
    judged = [await judge.judge(r, model="anthropic/claude-sonnet-4.6") for r in rows]

# 3. Aggregate + report
agg = Aggregator(judged)
Reporter(agg.compute("keep"), agg.compute("drop"), judged).write(Path("outputs"))
```

## Cost estimate (rule of thumb)

For `--n 300` with `claude-sonnet-4.6` as the primary and a 30-row Gemini
cross-check, expect prompts of ~1–2k tokens and completions of ~500 tokens per
row. At list price that is ~$3–6 USD. Set `--max-usd` to your comfort level;
the runner aborts cleanly the first time spend crosses the cap.

## Resumability

Both `judge_claims.py` and the orchestrator are resumable:
- `judge_claims.py` reads existing `claims_per_qa.jsonl` and skips
  `(cid, qa_index)` already judged.
- A budget abort, network failure, or `Ctrl-C` leaves the partial output
  intact. Just re-run the same command — only the missing rows are judged.

## Troubleshooting

- **`pytest.mark.asyncio` warnings / failures** — install `pytest-asyncio`.
- **`api-key-file` not found** — pass an explicit `--api-key-file` pointing at
  a plain-text file containing only the key.
- **All rows go to `claims_per_qa.errors.jsonl`** — usually the model is
  emitting markdown fences. The parser is strict; the judge auto-retries once
  with a "no markdown fences" hint, but a persistently-broken model will fail
  twice. Check the raw text in the errors file and consider switching models.
