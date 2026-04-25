# Task 7: Chem2TextQA Diversity Analysis

## Overview
Comprehensive diversity analysis of Chem2TextQA dataset comparing lexical, semantic, and topic diversity against SMolInstruct (LLaSMol) baseline. Demonstrates superior diversity in question topics, vocabulary, and semantic embeddings.

## Key Results

| Metric | Chem2TextQA | SMolInstruct | Advantage |
|--------|------------|-------------|-----------|
| **Question Vocabulary** | 46,992 | 79 | **595× larger** |
| **Unique Topics** | 2,169 | 14 | **155× more** |
| **Answer Vocabulary** | 328,159 | 32 | **10,255× larger** |
| **Unique Question Stems** | 34,721 | 14 | **2,480× more** |

## Files

### Analysis Scripts (4 pipelines)
- **C1_diversity_analysis.py** — Lexical diversity metrics + topic distribution + structural stats
- **C2_semantic_diversity.py** — Semantic embeddings (sentence-transformers) + cosine similarity
- **C3_ttr_curve.py** — Type-Token Ratio decay curves showing vocabulary growth
- **C4_combined_figures.py** — Final publication-ready composite figures + LaTeX table

### Output Data
- **diversity_summary.json** — Cached lexical statistics (vocab, TTR, question stems, topics)
- **semantic_diversity_stats.json** — Cached semantic statistics (cosine similarities)

### Figures (20 files: 10 PDF + 10 PNG)

**Final Manuscript Figures (3):**
- `figures/figure1_question_diversity.pdf` — 3-panel: lexical bars, semantic diversity, top-20 stems
- `figures/figure2_answer_diversity.pdf` — 3-panel: answer lexical, semantic, length distribution
- `figures/figure3_topic_structural.pdf` — 2-panel: top-18 topics, molecular weight distribution

**Intermediate Analysis Figures (7):**
- Topic distribution, question diversity, answer diversity
- Cosine similarity histograms (questions, answers)
- TTR decay curves (questions, answers)

### LaTeX Table
- **tables/diversity_analysis.tex** — Publication-ready diversity comparison table

## How to Run

### Requirements
```bash
pip install numpy matplotlib sentence-transformers
```

### Execution (in order)
```bash
# Step 1: Lexical diversity + topic analysis (generates caches)
python C1_diversity_analysis.py

# Step 2 & 3: Can run in parallel (both depend on C1 cache)
python C2_semantic_diversity.py  # ~20 min (embeddings)
python C3_ttr_curve.py           # ~5 min

# Step 4: Final composite figures (depends on C1+C2)
python C4_combined_figures.py
```

**Total runtime**: ~30 min on GPU (H100/A100)

## Dataset Details

**Chem2TextQA:**
- 15,509 compounds
- 188,541 QA pairs (phase1 + phase2 answers)
- 2,169 unique fine-grained topics
- 44.6% compounds with stereocenters
- Molecular weight range: 1–14,959 Da

**SMolInstruct Baseline:**
- 14 fixed task templates (synthetic for comparison)
- 199,990 samples
- Tasks: 4 name conversions, 6 property predictions, 2 description tasks, 2 reaction tasks

## Key Findings

### Lexical Diversity (Questions)
- Chem2TextQA: 46,992 vocabulary words, TTR=0.0971
- SMolInstruct: 79 vocabulary words, TTR=0.0016
- **61× higher TTR, 595× larger vocabulary**

### Topic Distribution
- **Top 5 topics** (engineering, mechanism, physicochemical, therapeutic use, metabolism) = 40% of all QAs
- **Top 18 topics** = 93.7% of all QAs
- **2,151 long-tail specialized topics** (resistance mechanism, biosynthesis, environmental fate, etc.)

### Semantic Diversity
- Questions: Mean cosine similarity 0.427 (diverse)
- SMolInstruct: Mean cosine similarity 0.998 (template-identical)

## Comparison to M2TQA
- M2TQA: 4 broad topics, 416k QA pairs
- Chem2TextQA: 2,169 fine-grained topics, 188.5k QA pairs
- **500+ fold more unique topics** in Chem2TextQA

## For Reviewers
- See `ANALYSIS_SUMMARY.md` for detailed findings
- Check `figures/figure*.pdf` for publication-ready visualizations
- Review `tables/diversity_analysis.tex` for LaTeX table

## Next Steps
1. Integrate figures into manuscript/presentation
2. Optional: Add RDKit molecular fingerprint diversity analysis
3. Optional: Extend to other chemistry datasets (proteins, reactions)
4. Optional: Create compound scaffold/chemical space visualization (Figure 4)
