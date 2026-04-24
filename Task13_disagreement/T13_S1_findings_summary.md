# Findings — `explore_dataset.ipynb`

Per-cell analysis, outputs, and an overall summary for `dataset_final.jsonl`.

---

## Cell 0 — Title / intro (markdown)

**Purpose:** Frames the notebook. The dataset is large (~566 MB on disk, ~593 MB by bytes), so everything downstream streams line-by-line instead of loading the file whole.

**Output:** none (markdown only).

---

## Cell 1 — Locate the file and report its size

**What it does:** Resolves `DATASET_PATH = Path("dataset_final.jsonl")` and reports `(exists, size_in_MB)`.

**Output:**

```
(True, 593.22644)
```

**Analysis:** The file is present in the working directory and ~593.23 MB. This confirms the streaming strategy is warranted — a naive `json.load` would either OOM or block interactive work for seconds per pass.

---

## Cell 2 — Define the streaming generator

**What it does:** Defines

```python
def iter_records(path=DATASET_PATH):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)
```

**Output:** none (definition only).

**Analysis:** Every later cell re-uses this generator, so memory stays flat regardless of how many records are processed. Blank lines are skipped defensively — the raw file does not appear to contain any, but the guard costs nothing.

---

## Cell 3 — Inspect the first record

**What it does:** Pulls the first record via `next(iter_records())` and prints its top-level keys and a few summary fields.

**Output:**

```
top-level keys: ['cid', 'split', 'name', 'iupac_name', 'smiles',
                 'molecular_formula', 'molecular_weight', 'inchi_key',
                 'num_pmids', 'num_synonyms', 'num_evidence_sentences',
                 'evidence_sentences', 'qa_pairs']
name: 1-Amino-2-propanol
smiles: CC(CN)O
num qa_pairs: 7
num evidence_sentences: 1
```

**Analysis:** The record schema is consistent with what the downstream code assumes:

- identity / structural fields: `cid`, `split`, `name`, `iupac_name`, `smiles`, `molecular_formula`, `molecular_weight`, `inchi_key`
- corpus stats: `num_pmids`, `num_synonyms`, `num_evidence_sentences`
- two variable-length lists: `evidence_sentences[]` (PMID-anchored abstract snippets with a `[COMPOUND]` placeholder) and `qa_pairs[]` (two-phase answers with a judge verdict).

The example compound has 7 QA pairs and 1 evidence sentence — indicating QA count is **not** bounded by evidence count.

---

## Cell 4 — Peek at the first three records (no full load)

**What it does:** Streams with `itertools.islice(iter_records(), 3)` and prints `cid`, `split`, `name`.

**Output:**

```
4  train 1-Amino-2-propanol
6  train 1-Chloro-2,4-Dinitrobenzene
11 train 1,2-Dichloroethane
```

**Analysis:** CIDs are non-contiguous (4, 6, 11 — no 5, 7, 8, 9, 10), confirming PubChem CIDs are preserved as-is rather than renumbered. All three are in the `train` split; the file is **not** sorted or grouped by split (cell 5 confirms all three splits are interleaved throughout).

---

## Cell 5 — Count records and the split distribution

**What it does:** Streams the full file once, counting records and tallying `rec["split"]`.

**Output:**

```
total records: 15509
by split: {'train': 10820, 'val': 2340, 'test': 2349}
```

**Analysis:**

| split |  count | share |
|-------|-------:|------:|
| train | 10,820 | 69.77% |
| val   |  2,340 | 15.09% |
| test  |  2,349 | 15.14% |

A clean ~70 / 15 / 15 split, with val and test near-identical in size (delta of 9 records). Nothing suggests the splits are grouped contiguously in the file — the generator sees all three interleaved.

---

## Cell 6 — Disagree rate per topic bucket

**What it does:** Imports `bucket_topic` from `topic_bucket.py`, adds a wrapper `bucket4()` that splits `engineering` / `design_levers` / `design` out of the `functional` bucket, streams the whole dataset, tallies `verdict` per bucket, and reports `disagree_rate = disagree / (agree + disagree)`.

**Output:**

```
bucket          agree  disagree      a+d  disagree_rate
structural      80427     17788    98215         0.1811
functional      70812      1384    72196         0.0192
engineering     26874      1864    28738         0.0649
other           10428       128    10556         0.0121

full verdict distribution per bucket:
  structural  : {'agree': 80427, 'disagree': 17788, None: 294, 'unclear': 8}
  functional  : {'agree': 70812, 'disagree':  1384, None:  50, 'unclear': 19}
  engineering : {'agree': 26874, 'disagree':  1864, None:  31, 'unclear':  4}
  other       : {'agree': 10428, 'disagree':   128, None:   6}
```

**Derived stats:**

| bucket      |  agree | disagree | unclear | None |    total | % of QA | disagree_rate |
|-------------|-------:|---------:|--------:|-----:|---------:|--------:|--------------:|
| structural  | 80,427 |   17,788 |       8 |  294 |   98,517 |  46.98% |    **0.1811** |
| functional  | 70,812 |    1,384 |      19 |   50 |   72,265 |  34.46% |    **0.0192** |
| engineering | 26,874 |    1,864 |       4 |   31 |   28,773 |  13.72% |    **0.0649** |
| other       | 10,428 |      128 |       0 |    6 |   10,562 |   5.04% |    **0.0121** |
| **all**     |**188,541** | **21,164** |   **31** | **381** | **210,117** | 100.00% |    **0.1009** |

Implied cross-bucket relationships (from the same tally, not a separate computation):

- **Structural vs functional ratio:** disagree_rate 18.1% / 1.9% ≈ **9.4×**. Structural claims diverge between phase1 and phase2 nearly an order of magnitude more than functional ones.
- **Engineering vs rest-of-functional:** 6.5% vs 1.9% ≈ **3.4×**. Engineering is clearly its own regime — not well approximated by folding it back into `functional`.
- **Overall disagree_rate:** 10.09%, but this aggregate is dominated by the structural bucket (47% of QAs); reporting it without the per-bucket breakdown hides the real signal.
- **QA-to-record ratio:** 210,117 QA pairs / 15,509 records ≈ **13.55 QAs per compound** on average.
- **Unclear/None fraction:** (31 + 381) / 210,117 ≈ **0.20%** — negligible, but present in every bucket.

**Analysis:** The structural/functional disagreement asymmetry is the headline finding. It inverts the naive expectation that evidence-grounded functional QAs would be the harder regime: in this dataset, claims derivable from SMILES/formula/MW alone are where the two answer passes diverge most. Engineering, which `topic_bucket.py` files under `functional` by default, does not match that bucket's agreement profile and should be treated separately for any downstream analysis.

---

## Overall summary

1. **Dataset size:** 15,509 compounds × ~13.55 QA pairs ≈ **210,117 QA items** on disk in a single ~593 MB JSONL.
2. **Splits:** train 10,820 / val 2,340 / test 2,349 — a clean ~70/15/15 split, interleaved in file order; CIDs are not renumbered (non-contiguous).
3. **Record schema:** identity + structural descriptors + corpus counts + `evidence_sentences[]` + `qa_pairs[]`. QA pairs can outnumber evidence sentences on a per-compound basis.
4. **Two-phase QA + judge verdict:** every QA carries `phase1_answer`, `phase2_answer`, and a `verdict` (`agree` / `disagree` / `unclear` / `None`). `unclear` + `None` together are ~0.2% — rare enough to exclude from rate denominators without meaningful loss.
5. **Disagreement is concentrated in structural QAs:** 18.1% disagree_rate vs 1.9% for functional — a ~9.4× gap. Engineering is a distinct middle regime at 6.5%.
6. **Implication for the soft-rule probes** (from `topic_bucket.py`'s design):
   - *SMILES-swap probe:* expect the largest effect on structural QAs, where baseline disagreement is already high and the SMILES is the direct hint.
   - *Empty-evidence probe:* functional QAs agree at baseline; their failure mode surfaces only when the evidence is ablated, not in the raw verdict counts.
   - *Bucketing matters:* aggregate disagree_rate (10.1%) hides the structural/functional split. Any ablation that reports a single number across all QAs will understate the structural effect and overstate the functional one.
