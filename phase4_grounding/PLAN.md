# Phase 4 — Grounding Audit Plan

## Goal
For each functional Q&A, decompose the `phase2_answer` into **atomic claims**; label each claim as
`STATED` / `IMPLIED` / `UNSUPPORTED` (and optionally `STRUCTURAL`) against the parent compound's
evidence sentences. Aggregate to measure how often the soft rule allows training-recall claims to
slip into the dataset.

This audit addresses C1 (claim grounding) and C3 (training-recall risk) directly.

## Dataset facts (verified)
- `data/dataset_gold.jsonl`: **15,509 compounds, 188,541 Q&A pairs** (train 10,820 / val 2,340 / test 2,349).
- Each compound has `evidence_sentences` with fields `{id, pmid, source, text}`. Per-QA `evidence_ids` is mostly empty (the soft rule).
- Functional topic counts (top): engineering 21,904 · mechanism 17,669 · therapeutic_use 14,691 · metabolism 12,236 · toxicity 11,114 · adme 8,850 · design_levers 4,860 · drug_interactions 3,944 · prodrug_activation · resistance_mechanism · etc.
- `scripts/topic_bucket.py::bucket_topic` already classifies a topic as `structural` / `functional` / `other` — reuse it.
- The audit target is `phase2_answer` (the long, soft-rule answer). Phase 1 answer and judge reasoning are **not** shown to the judge, to keep the test honest.

## Output layout
All code under `phase4_grounding/`. Outputs co-located so the deliverable is one folder. Code is organized as a small package with a clear separation between **library modules** (testable) and **entry-point scripts** (each script has a `main()` that parses args and delegates to the library).
```
phase4_grounding/
├── PLAN.md                       # this file
├── __init__.py
├── grounding/                    # library package — pure modules, no I/O at import
│   ├── __init__.py
│   ├── sampling.py               # Sampler class — stratified sampler
│   ├── evidence.py               # EvidenceAttacher — selects/numbers evidence per QA
│   ├── prompt.py                 # PromptBuilder — renders claim_decomp prompt
│   ├── openrouter_client.py      # OpenRouterClient — async, retries, cost tracker
│   ├── judge.py                  # ClaimJudge — orchestrates client + prompt + parsing
│   ├── parser.py                 # ClaimParser — strict JSON parse + schema validate
│   ├── aggregator.py             # Aggregator — both keep/drop views, Wilson CI
│   ├── reporter.py               # Reporter — markdown writers
│   └── models.py                 # @dataclass: Claim, JudgedQA, SampleRow, ViewConfig
├── prompts/
│   └── claim_decomp.txt
├── scripts/                      # entry-point scripts, each with main()
│   ├── sample_qa.py
│   ├── judge_claims.py
│   └── aggregate.py
├── tests/                        # pytest, mirrors grounding/ layout
│   ├── conftest.py               # fixtures: tiny dataset, fake OpenRouter client
│   ├── test_sampling.py
│   ├── test_evidence.py
│   ├── test_prompt.py
│   ├── test_parser.py
│   ├── test_judge.py             # uses fake client (no network)
│   ├── test_aggregator.py
│   ├── test_reporter.py
│   └── data/
│       └── tiny_dataset.jsonl    # 5–10 hand-crafted compounds for deterministic tests
├── run_phase4_grounding.sh       # orchestrator
└── outputs/
    ├── sample.jsonl              # sampled QA + attached evidence bundle
    ├── claims_per_qa.jsonl       # primary judge output
    ├── claims_per_qa.gemini.jsonl # cross-check subset (optional)
    ├── claims_per_qa.errors.jsonl # rows where JSON parse failed twice
    ├── grounding_summary_keep_structural.md   # Option A view
    └── grounding_summary_drop_structural.md   # Option B view
```

### Module boundaries
- **`models.py`** — typed dataclasses passed between modules; the library's contract surface.
- **`sampling.py`** — `Sampler` class: `__init__(dataset_path, seed)`, `sample(n, weights) -> list[SampleRow]`. Pure; no network.
- **`evidence.py`** — `EvidenceAttacher.attach(qa, compound) -> list[EvidenceItem]`. Pure.
- **`prompt.py`** — `PromptBuilder.build(sample_row) -> str`. Loads `claim_decomp.txt` once.
- **`openrouter_client.py`** — `OpenRouterClient(api_key, concurrency, max_usd)`; `async chat(model, prompt, **kw) -> ChatResult`. Has a `FakeOpenRouterClient` subclass in tests/conftest for deterministic outputs.
- **`parser.py`** — `ClaimParser.parse(raw: str, attached_ids: set[int]) -> ParseResult`. Strict JSON + schema check + cross-ref of `evidence_id` against attached ids.
- **`judge.py`** — `ClaimJudge(client, prompt_builder, parser)`; `async judge(sample_row, model) -> JudgedQA`. One retry on parse failure.
- **`aggregator.py`** — `Aggregator(judged_qas)`; `.compute(view: Literal["keep","drop"]) -> ViewMetrics`. Wilson CI in a small helper.
- **`reporter.py`** — `Reporter(metrics_keep, metrics_drop, judged_qas)`; `.write(out_dir)` writes both summary files.

### Entry-point scripts
Each script in `scripts/` follows the same shape:
```python
def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    # construct library objects, call them, write outputs
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```
This makes scripts importable in tests (`from phase4_grounding.scripts.sample_qa import main`) and exits with proper return codes for CI.

## CLI parameters (all user-overridable)
Each script accepts:

| Flag | Default | Notes |
|---|---|---|
| `--n` | required for `sample_qa.py` | total sample size; user supplies after manager approval |
| `--api-key-file` | `~/.openrouter_key` | path to text file containing the OpenRouter API key |
| `--primary-model` | `anthropic/claude-sonnet-4.6` | OpenRouter model id for primary judge |
| `--cross-check-model` | `google/gemini-2.5-pro` | only used if cross-check enabled |
| `--skip-cross-check` | `false` | when set, the second-model run is skipped entirely |
| `--cross-check-n` | `30` | size of the overlap subset for the second model |
| `--seed` | `0` | RNG seed for sampling |
| `--max-usd` | `15` | abort runner if cumulative OpenRouter spend exceeds this |
| `--concurrency` | `5` | async semaphore for OpenRouter calls |
| `--data-path` | `data/dataset_gold.jsonl` | input dataset |
| `--out-dir` | `phase4_grounding/outputs` | output directory |

The API key is read **only** from the file at `--api-key-file`; never logged, never echoed.

## Step 1 — Stratified sample (`sample_qa.py --n N`)
- Filter QA where `bucket_topic(topic) == 'functional'`.
- Strata = topic. Allocate the `N` slots **proportionally within the functional pool** but with a fixed weighting that emphasizes the four headline topics:
  - `mechanism : metabolism : toxicity : engineering : therapeutic_use : (others)` = `0.20 : 0.17 : 0.17 : 0.20 : 0.13 : 0.13`
  - "others" pool = `adme + design_levers + drug_interactions + prodrug_activation + resistance_mechanism + remaining functional topics`, allocated proportionally inside the 0.13 slice.
  - Allocations are computed from `N` so the user just passes `--n` (e.g. `--n 300` or `--n 600`).
- Within each topic, split the slot 50/50 between `evidence_ids` non-empty vs empty (this is the headline metric breakdown). Fall back to whichever pool has rows when the other is exhausted; record the actual split in `sample.jsonl`.
- Sample across all splits (train/val/test) — this is a dataset audit, not a model eval.
- Persist `sample.jsonl` with the attached evidence bundle so judging is fully reproducible:
  ```json
  {"cid":..., "qa_index":..., "topic":..., "split":..., "evidence_ids_nonempty":bool,
   "compound":{"name":..., "smiles":..., "molecular_formula":...},
   "question":"...", "phase2_answer":"...",
   "evidence_attached":[{"id":1,"text":"..."}, ...]}
  ```
- Evidence attachment rule:
  - `evidence_ids` non-empty → keep only those parent `evidence_sentences` (matched by `id`).
  - else → attach all `evidence_sentences` for that compound.

## Step 2 — Judge prompt (`prompts/claim_decomp.txt`)
The judge sees: compound name, SMILES, molecular formula, question, phase2 answer, numbered evidence (`[E1] ...`, `[E2] ...`). Required output is strict JSON:
```json
{"claims":[
  {"claim":"<atomic statement>",
   "label":"STATED|IMPLIED|UNSUPPORTED|STRUCTURAL",
   "evidence_id": 2,
   "rationale":"<<=25 words>"}
]}
```
Label semantics enforced in the prompt:
- **STATED** — directly written in some evidence sentence (must cite the id).
- **IMPLIED** — inferable from evidence by one routine domain-reasoning step (cite id, give the step).
- **STRUCTURAL** — derivable from SMILES / formula / molecular weight alone (no evidence needed). See clarification below.
- **UNSUPPORTED** — none of the above; flagged as a **training-recall candidate**.

Atomicity rules in the prompt: one assertion per claim; split conjunctions; numerical values, named entities, and mechanisms are atomic units; preserve hedging ("may", "is thought to") inside the claim — do not decompose hedges.

### Clarification of the STRUCTURAL label
**Why this label exists.** C3 worries about *training recall* — the model writing functional claims from memorized literature instead of from the evidence. But many "functional" Q&A answers also contain claims that are pure structural inference, e.g. "the compound contains a primary amine" inside a *mechanism* answer. If those structural claims get bucketed as `UNSUPPORTED`, we systematically **overestimate** training recall. A separate `STRUCTURAL` label keeps `UNSUPPORTED` a clean proxy for "model used memorized literature, not the evidence and not the molecule itself."

**Decision: produce both views as separate outputs — no choice required up-front.**
The judge always emits all 4 labels (`STATED` / `IMPLIED` / `UNSUPPORTED` / `STRUCTURAL`). The aggregator post-processes the same `claims_per_qa.jsonl` two ways and writes two summary files:
- **`grounding_summary_keep_structural.md`** — STRUCTURAL kept as its own bucket. Headline: `UNSUPPORTED / (STATED + IMPLIED + UNSUPPORTED)`; STRUCTURAL excluded from the denominator (it isn't an evidence-grounding question).
- **`grounding_summary_drop_structural.md`** — STRUCTURAL collapsed into IMPLIED (closer to the original spec; treats SMILES as "evidence" in a loose sense). Headline: `UNSUPPORTED / (STATED + IMPLIED + UNSUPPORTED)` over the collapsed labels.

Both summaries cite each other so the reader can compare. The 10% / 20% decision rule (§Step 4) is applied to **each** view independently — if the conclusion flips between the two views, that's itself a finding worth flagging in the paper.

## Step 3 — Judge runner (`judge_claims.py`)
- `httpx.AsyncClient`, semaphore = `--concurrency` (default 5), exponential backoff on 429 / 5xx.
- **Resumable**: read existing `claims_per_qa.jsonl`, skip `(cid, qa_index)` already judged.
- Strict JSON parsing. On parse failure, one retry appending "your previous output was not valid JSON, return only the JSON object". Second failure → write to `claims_per_qa.errors.jsonl` with the raw response, continue.
- Per-row record:
  ```json
  {"cid":..., "qa_index":..., "topic":..., "evidence_ids_nonempty":bool,
   "num_evidence_attached": int, "model":"...", "claims":[...],
   "usage":{"prompt_tokens":int,"completion_tokens":int},
   "latency_ms": int}
  ```
- **Cost ceiling**: abort if cumulative cost (estimated from token usage and OpenRouter's per-model price) exceeds `--max-usd`. Print running total every 25 calls.
- Cross-check pass (skipped if `--skip-cross-check`):
  - Take the first `--cross-check-n` rows of `sample.jsonl`, re-judge with `--cross-check-model`, write to `claims_per_qa.gemini.jsonl`. Same retry / cost logic.

## Step 4 — Aggregation (`aggregate.py` → two summary files)
Claim-level denominator = all atomic claims across the run. Aggregator runs twice over the same `claims_per_qa.jsonl`, once per view, writing the two summary files listed in the output layout.

### Headline metrics (computed for both views)
- % STATED · % IMPLIED · % UNSUPPORTED · % STRUCTURAL (STRUCTURAL row collapses into IMPLIED in the "drop" view)
- **Grounded fraction** = STATED + IMPLIED
- **Training-recall candidate fraction** = UNSUPPORTED

### Breakdowns
- By topic (mechanism / metabolism / toxicity / engineering / therapeutic_use / others).
- By `evidence_ids_nonempty` true vs false — this is the spec-required cut.
- By split (train / val / test).
- Per-QA: histogram of UNSUPPORTED claim count; **top-20 QA by UNSUPPORTED rate** for qualitative spot-checking.

### Statistical honesty
- Wilson 95% CI on the UNSUPPORTED rate. With `N` chosen by the user, half-width ≈ `1.96 * sqrt(p(1-p)/n_claims)`; reported in the summary so a reader can see whether `N` is large enough to discriminate the 10% / 20% cutoffs.

### Cross-check (only if not skipped)
- On the overlap subset, collapse to {grounded, ungrounded} and compute Cohen's κ between primary and cross-check models. Disagreement examples listed in an appendix.

### Decision rule (printed at the top of the summary)
- UNSUPPORTED > 20% → narrow the paper's grounding claim; note training-recall risk in DATASHEET / RESPONSIBLE_AI.
- UNSUPPORTED < 10% → soft rule "well-behaved"; quote the number in the dataset card.
- 10–20% → add a caveat to DATASHEET / RESPONSIBLE_AI; do not claim full grounding.

## Step 5 — Manual validation
- Spot-check **20 random claims** from `claims_per_qa.jsonl` by hand; record agreement with the judge in the appendix of `grounding_summary.md`.
- Sanity gate: every claim with a non-null `evidence_id` must reference an attached evidence sentence; otherwise auto-relabel that row as a parse error.

## Orchestrator (`run_phase4_grounding.sh`)
Three-step pipeline (resumable; safe to re-run):
1. `python -m phase4_grounding.scripts.sample_qa --n "$N" --seed 0`
2. `python -m phase4_grounding.scripts.judge_claims --api-key-file "$KEY" --primary-model "$PRIMARY" [--skip-cross-check] [--cross-check-model "$XCHECK"] --max-usd "$BUDGET"`
3. `python -m phase4_grounding.scripts.aggregate`

User runs e.g.:
```
bash phase4_grounding/run_phase4_grounding.sh --n 300 --api-key-file ~/.openrouter_key --skip-cross-check
```

## Testing strategy
- **Framework**: pytest (already in `[project.optional-dependencies] dev`); tests live under `phase4_grounding/tests/` and are discovered when the existing `[tool.pytest.ini_options] testpaths` is extended in `pyproject.toml`.
- **Fixtures (`conftest.py`)**:
  - `tiny_dataset` — 5–10 hand-crafted compounds, all functional topics represented, both `evidence_ids` non-empty and empty cases.
  - `fake_openrouter_client` — returns scripted responses (well-formed JSON, malformed JSON, 429 → success). No network in any test.
  - `tmp_out_dir` — pytest `tmp_path` for output writers.
- **Coverage targets per module**:
  - `sampling`: stratification correctness, deterministic with seed, graceful when a stratum is empty, exact-N total.
  - `evidence`: selects only listed `evidence_ids` when non-empty, attaches all when empty, stable numbering.
  - `prompt`: contains all required fields, evidence is numbered `[E1]`, `[E2]`...; snapshot test against a small golden string.
  - `parser`: accepts well-formed JSON; rejects malformed; rejects `evidence_id` not in attached set; preserves all 4 labels.
  - `judge`: end-to-end with fake client — parse-success path, retry-then-success path, retry-then-error-log path.
  - `openrouter_client`: cost tracker arithmetic; `--max-usd` raises `BudgetExceeded`; backoff sleeps respect `Retry-After` (mocked clock).
  - `aggregator`: keep view excludes STRUCTURAL from denominator; drop view collapses STRUCTURAL → IMPLIED; Wilson CI matches a known reference for fixed inputs; per-topic and per-`evidence_ids_nonempty` breakdowns sum to the total.
  - `reporter`: writes both files; decision-rule string matches the computed UNSUPPORTED rate.
- **Network policy**: every test that touches `OpenRouterClient` uses the fake; one optional `@pytest.mark.live` smoke test (skipped by default; opt-in with `--live`) hits OpenRouter with one cheap call.
- **Run locally**: `pytest phase4_grounding/tests -q --cov=phase4_grounding/grounding`.

## Step-by-step implementation
The work is sliced into small, ordered steps. **Acceptance gate for each step: its unit tests pass (`pytest phase4_grounding/tests -q`).** No PR workflow, no CI pipeline, no coverage thresholds — just a green test run before moving to the next step. No step touches production data or makes network calls in tests (everything uses the fake client).

| Step | Scope | Gate |
|---|---|---|
| 1 | Skeleton: package layout, `models.py` dataclasses, `tests/conftest.py` with `tiny_dataset` fixture | tests collect cleanly; one smoke test on a dataclass passes |
| 2 | `sampling.Sampler` + `test_sampling.py` | tests cover stratification, seed determinism, exhausted-stratum |
| 3 | `evidence.EvidenceAttacher` + `test_evidence.py` | covers both `evidence_ids` branches |
| 4 | `prompt.PromptBuilder` + `prompts/claim_decomp.txt` + `test_prompt.py` | snapshot test passes |
| 5 | `parser.ClaimParser` + `test_parser.py` | covers well/malformed JSON and bogus `evidence_id` |
| 6 | `openrouter_client.OpenRouterClient` + `FakeOpenRouterClient` + `test_openrouter_client.py` | retry, backoff, budget cap |
| 7 | `judge.ClaimJudge` + `test_judge.py` | end-to-end with fake client |
| 8 | `scripts/sample_qa.py` + `scripts/judge_claims.py` (entry points, `main()`, argparse) + integration test against `tiny_dataset` | integration test produces expected `claims_per_qa.jsonl` shape |
| 9 | `aggregator.Aggregator` + `reporter.Reporter` + `scripts/aggregate.py` + tests | both summary files generated; numbers match hand-computed reference |
| 10 | `run_phase4_grounding.sh` orchestrator | bash script runs all three steps end-to-end on `tiny_dataset` |

Once step 10 passes, the real audit is a one-off manual run of the orchestrator with the user-approved `--n` and the production API key.

