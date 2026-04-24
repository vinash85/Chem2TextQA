---
title: "Chem2TextQA — Related Work"
task: "C6 — comparison against prior chemistry / biomedical QA datasets"
status: "draft v1 — needs citation polish and author review"
last_updated: 2026-04-24
---

# Related Work

Chem2TextQA occupies a narrow band in a crowded landscape: it is neither a pure
benchmark nor a pure instruction corpus, and it treats SMILES as a first-class
input with literature evidence as the grounding signal. Reviewer comment **C6**
asks us to position the dataset explicitly against the datasets most likely to
be confused with it. Six are relevant: two LLM-chemistry benchmarks (ChemBench,
ChemLLMBench), two instruction-tuning corpora (Mol-Instructions, SMolInstruct),
and two biomedical/scholarly QA datasets (PubMedQA, SciQA). We summarise each
on nine axes in Table 1, then discuss how Chem2TextQA's design choices are
responses to specific weaknesses in each.

## Table 1 — Comparison of Chem2TextQA against six related datasets

| Dimension | **Chem2TextQA** | ChemBench (Mirza et al., *Nat. Chem.* 2025) | ChemLLMBench (Guo et al., NeurIPS 2023) | Mol-Instructions (Fang et al., ICLR 2024) | SMolInstruct / LlaSMol (Yu et al., COLM 2024) | PubMedQA (Jin et al., EMNLP 2019) | SciQA (Auer et al., *Sci. Rep.* 2023) |
|---|---|---|---|---|---|---|---|
| **Size** | 15,547 compounds + 120 canaries, ~211 K raw Q&A, ~189 K agree-only | ~2,700 QA pairs | 8 tasks, thousands of items per task (MoleculeNet-derived) | ~706 K instructions (148 K mol + 505 K protein + 53 K text) | ~3.3 M samples, 1.6 M distinct molecules, 14 tasks | 1 K expert + 61 K unlabeled + 211 K auto (~273 K) | 2,565 QA pairs (100 manual + 2,465 template-generated) |
| **Q&A format** | Open-ended natural-language QA grounded in one evidence sentence | Mixed: MCQ + numerical + open-ended free-text | Task-specific (classification, generation, SMILES-to-X, reaction prediction) | Free-form instruction/response (template + GPT-paraphrased) | Task-specific input→output strings (SMILES⇄name, reaction, properties) | 3-way yes/no/maybe + long-answer conclusion | SPARQL-backed factoid QA over a scholarly KG |
| **Label provenance** | Two-model cross-validation: Gemini-3-Flash generates, Kimi-K2.5 re-answers blind, Gemma-4-31B judges → `agree` subset only | 35-author human-expert curation, largely drawn from chemistry textbooks and exams | Mostly repurposed from existing datasets (MoleculeNet, USPTO, etc.); gold labels inherited | Template + GPT-3.5 paraphrase; gold from source biochem databases; "stringent quality control" but no second-model check | Gold labels inherited from public sources (PubChem, MoleculeNet, USPTO, ChEBI-20); human review for templates | Original PMC abstract conclusions ("long answer") mapped to yes/no/maybe; 1 K hand-labeled | Knowledge-graph-derived; SPARQL queries verified against ORKG |
| **Grounding strategy** | Per-Q&A evidence bundle: redacted literature sentence(s) linked by `evidence_ids` — every claim must trace to a compound-name-redacted source sentence | None at the QA level; "textbook/exam facts" assumed canonical | None at the QA level; task inputs (e.g., a SMILES) *are* the grounding | Text descriptions exist but the instruction/response pair is not tied to a citable span | No external grounding; labels are canonical mappings | Full PMC abstract provided as context; yes/no requires reading-comprehension over it | ORKG knowledge-graph triples serve as grounding |
| **SMILES as first-class input** | **Yes** — every Q&A carries the compound SMILES; structural claims must be SMILES-derivable (soft rule) | Partial — SMILES appears in some items but most questions are text | **Yes** for SMILES⇄IUPAC, property, reaction tasks | **Yes** for the molecule-oriented subset (148 K) | **Yes** — SMILES is canonical input across all 14 tasks | No | No |
| **Cross-validation signal (second model)** | **Yes** — Kimi re-answer + Gemma judge on every item | No | No | No | No | No (human agreement only, on the 1 K expert subset) | No |
| **Held-out contamination test** | **Yes** — 120 "late-training" canary compounds (earliest PubMed article ≥ 2024-01-01) reserved in a separate file; compound name replaced with `[COMPOUND]` in evidence to reduce memorization leakage. Authors acknowledge the canary is weaker than a true post-cutoff set (strict ≥ 2025-09-01 yielded zero usable compounds) | Not systematic; paper discusses leakage concern qualitatively | Not reported | Not reported | Pretraining-contamination not discussed; intra-dataset leakage controlled by pairing matched samples into the same split | Not reported (pre-dates modern LLM contamination concerns) | Not reported |
| **Scaffold split** | **Yes** — MoleculeNet-standard strict Murcko scaffold split, 70/15/15, 5,916 unique scaffolds, zero scaffold leakage between train/val/test (verified programmatically) | N/A (questions, not molecules) | Partially (inherits MoleculeNet scaffold splits on borrowed tasks) | Not reported (likely random) | **Yes** on the 6 property-prediction tasks (canonical Bemis–Murcko), random elsewhere | N/A | N/A |
| **Availability** | (TBD — repo under `chem2textqa`; agree-only JSONL on release) | MIT; benchmark + code public | MIT; GitHub + data public | CC-BY-4.0 (data), MIT (code); HF `zjunlp/Mol-Instructions` | HF `osunlp/SMolInstruct`; models + code on GitHub | MIT; github.com/pubmedqa/pubmedqa | CC-BY-4.0; HF `orkg/SciQA` |

## 1. ChemBench (Mirza et al., *Nature Chemistry* 2025)

ChemBench is the most comprehensive *evaluation* benchmark for chemistry LLMs
to date — roughly 2,700 expert-curated QA pairs drawn from textbooks, exams,
and authored by a 35-person consortium. Its strengths are precisely what
Chem2TextQA cannot offer: hand-curated gold labels from chemists, and broad
topical coverage including safety, spectroscopy, and reasoning. Its
limitations, however, are the motivation for Chem2TextQA. **(a)** ChemBench is
a test set, not a training resource — 2.7 K items cannot support instruction
tuning. **(b)** Its questions are largely text-based; SMILES is present in
only a minority. **(c)** Label provenance is authoritative but unscalable. We
position Chem2TextQA as the *training-scale, SMILES-native complement*: when a
practitioner wants to *improve* a model on chemistry reasoning and then
*evaluate* it rigorously, ChemBench is the held-out test and Chem2TextQA is
the training instrument. The two should be used together, not interchangeably.

## 2. ChemLLMBench (Guo et al., NeurIPS 2023)

ChemLLMBench established the eight-task format that downstream work (including
SMolInstruct) has largely inherited: name conversion, property prediction,
yield prediction, reaction prediction, retrosynthesis, text-based molecule
design, molecule captioning, and reagent selection. It reuses existing gold
labels from MoleculeNet, USPTO, and ChEBI. The contribution is the prompting
and evaluation protocol, not a new dataset. For Chem2TextQA, ChemLLMBench is
upstream: several of its task formulations are implicit in how we frame
open-ended QA over a compound. The critical gap it leaves is that its items
are *structural translations* (SMILES ↔ IUPAC, SMILES → property), not
*functional* questions about a drug's mechanism, metabolism, or engineering
context — which is what Chem2TextQA targets by drawing on PubMed/PMC evidence.

## 3. Mol-Instructions (Fang et al., ICLR 2024)

Mol-Instructions was the first large-scale (~706 K) biomolecular
instruction-tuning dataset, covering molecules, proteins, and biomolecular
text. Its construction pipeline — template + GPT-3.5 paraphrase on top of
biochemistry-database gold — is the closest prior art to ours in *format*
(instruction/response pairs) but diverges sharply in *source*. Labels flow
from a single generative model with "stringent quality control" that is not
externally audited; there is no blind re-answer and no judge. The dataset
also does not use SMILES redaction, so compound identity is directly
memorizable from the prompt — a contamination vector for any model whose
pretraining overlaps PubChem. Chem2TextQA's soft rule ("compound identity is
never revealed to the models") and `[COMPOUND]`-redaction pipeline are direct
responses to this failure mode.

## 4. SMolInstruct / LlaSMol (Yu et al., COLM 2024)

SMolInstruct is the strongest direct comparator: 3.3 M samples, 14 tasks,
SMILES-first, with genuine attention to leakage — the authors explicitly pair
"matched samples" across related tasks into the same split to prevent
cross-task contamination, and apply scaffold splitting to property-prediction
tasks. Chem2TextQA differs on three axes. **(a)** SMolInstruct's tasks are
closed-form (SMILES-to-formula, property scalar, reaction string);
Chem2TextQA's are open-ended natural-language Q&A grounded in a literature
sentence. **(b)** SMolInstruct labels are inherited from canonical databases;
Chem2TextQA labels are generated and then cross-validated by a second
independent model (Kimi-K2.5) and a third-party judge (Gemma-4-31B).
**(c)** SMolInstruct does not discuss pretraining contamination of the test
set against the base models; Chem2TextQA reserves 120 late-training canary
compounds and redacts names in evidence specifically to enable that
measurement, and uses strict MoleculeNet-standard scaffold splitting
(5,916 unique Murcko scaffolds, zero leakage) across the main set.
SMolInstruct and Chem2TextQA are complementary: the former teaches structural
competence, the latter teaches functional reasoning with source attribution.

## 5. PubMedQA (Jin et al., EMNLP 2019)

PubMedQA is the reference point for PMC-grounded biomedical QA. Its
reading-comprehension framing (research question → abstract context →
yes/no/maybe) pioneered the idea of treating the abstract conclusion as the
gold answer. Chem2TextQA borrows the *provenance* idea — gold answers trace
back to a specific abstract — but inverts the task shape. PubMedQA gives the
model the full abstract at inference; Chem2TextQA gives the model only the
SMILES and asks whether literature evidence supports a claim, with the
evidence used to *generate* (not supply) the QA. PubMedQA also has no
compound-level structure and no SMILES. The two datasets answer different
questions: PubMedQA tests whether a model can read a specific paper;
Chem2TextQA tests whether a model has internalised literature-consistent facts
about a compound.

## 6. SciQA (Auer et al., *Scientific Reports* 2023)

SciQA is the scholarly-KG analogue of PubMedQA: 2,565 QA pairs backed by
SPARQL queries over the Open Research Knowledge Graph, spanning ~15 K
articles. It is an important sanity check on *what KG-grounded scientific QA
looks like* — every answer is verifiable against a graph query. Chem2TextQA
does not use a KG (PubMed sentences are too unstructured and ORKG's chemistry
coverage is thin), but shares SciQA's principle that every Q&A must be
traceable to an external artifact. SciQA is too small for training; its
value for us is as a conceptual precedent, not a comparator at scale.

## Synthesis: where Chem2TextQA sits

Across the nine axes in Table 1, no prior dataset combines (i) SMILES as a
first-class input, (ii) open-ended natural-language Q&A, (iii) literature
evidence as the grounding unit, (iv) two-model cross-validation with an
independent judge, and (v) explicit held-out canary compounds for
contamination testing. The closest neighbours each share two or three of
these: SMolInstruct has SMILES-first and leakage-aware splits but is
closed-form and ungrounded; Mol-Instructions has open-ended instructions but
no cross-validation and no evidence trace; PubMedQA has literature grounding
but no SMILES; ChemBench has expert labels but no training scale.

Chem2TextQA is therefore **not a benchmark** (that role is ChemBench's) and
**not a structural instruction corpus** (that role is SMolInstruct's). It is
a training-scale resource for *evidence-grounded, functional* reasoning about
drug-like compounds, with a label pipeline designed from the outset for
contamination-resistance and cross-model validation. The density of
literature-linked, compound-redacted Q&A it produces is — to our knowledge —
absent from any of the six datasets above.

---

### Sources

- ChemBench: Mirza et al., *Nature Chemistry* 2025 — https://www.nature.com/articles/s41557-025-01815-x · https://github.com/lamalab-org/chembench · arXiv:2404.01475
- ChemLLMBench: Guo et al., NeurIPS 2023 — https://arxiv.org/abs/2305.18365 · https://github.com/ChemFoundationModels/ChemLLMBench
- Mol-Instructions: Fang et al., ICLR 2024 — https://arxiv.org/abs/2306.08018 · https://github.com/zjunlp/Mol-Instructions
- SMolInstruct / LlaSMol: Yu et al., COLM 2024 — https://arxiv.org/abs/2402.09391 · https://huggingface.co/datasets/osunlp/SMolInstruct
- PubMedQA: Jin et al., EMNLP 2019 — https://arxiv.org/abs/1909.06146 · https://pubmedqa.github.io
- SciQA: Auer et al., *Scientific Reports* 2023 — https://www.nature.com/articles/s41598-023-33607-z · https://huggingface.co/datasets/orkg/SciQA

### Reviewer notes / open questions for author pass

1. The task card attributes ChemBench to "Aldeghi et al." — the actual first
   author is Adrian Mirza; Aldeghi is among the 35 co-authors. Confirm which
   attribution to use in the final bib entry.
2. SMolInstruct → LlaSMol: the first author is Botao Yu; confirm preferred
   citation form. The paper is at COLM 2024.
3. Contamination-test claim updated from repo `CONTAMINATION.md`: 120 canary
   compounds with earliest PubMed indexing ≥ 2024-01-01 (late-training, not
   strict post-cutoff). Human-evaluation round that quantifies canary-vs-main
   accuracy is deferred — when those numbers land, update the "Held-out
   contamination test" row in Table 1 with a concrete Δ-accuracy.
4. Scaffold-split details pulled from `USAGE_FINETUNING.md`: MoleculeNet
   Murcko, 70/15/15, 5,916 scaffolds. Cite `scaffold_split_report.json`
   from the repo in the paper.
4. If space is tight, the SciQA paragraph can be collapsed into PubMedQA's
   (both are "prior-art on literature-grounded QA, neither uses SMILES").
