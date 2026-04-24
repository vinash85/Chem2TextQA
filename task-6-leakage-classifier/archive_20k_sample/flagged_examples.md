# Flagged Examples (for review)

Sampled with seed=42, up to 20 per category. Full flagged list is in `per_qa_leakage.jsonl`. No judgments are made here — for each case the answer and the best-matching evidence sentence are shown so you can decide leakage vs legitimate terminology reuse.


---

## LCS > threshold (verbatim phrase reuse)  — 0 total, showing 0

_No cases._


---

## 5-gram overlap > threshold  — 184 total, showing 20

### CID 23960 · qa_index 4 · topic `mechanism` · split `train`

- metrics: lcs_tokens=10, ngram5_overlap=6, cos_max=0.854 (answer_len_tokens=21, n_evidence_sentences=436)

**Answer (phase1):**

> The compound has been found to inhibit mitochondrial respiration by targeting respiratory chain complex IV (cytochrome c oxidase) at sub-micromolar concentrations.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] was found to inhibit respiratory chain complex IV (cytochrome c oxidase) at sub-micromolar concentrations (IC50 ~ 0.4 μM, 90 μg/L).

### CID 5054 · qa_index 18 · topic `design_levers` · split `train`

- metrics: lcs_tokens=10, ngram5_overlap=6, cos_max=0.844 (answer_len_tokens=27, n_evidence_sentences=100)

**Answer (phase1):**

> Incorporating a thiazolylazo moiety transforms the simple phenolic scaffold into a dual inhibitor of Aurora A and Aurora B kinases, shifting its application toward antineoplastic drug development.

**Closest evidence sentence (by token LCS):**

> Here, we report a [COMPOUND] derivative, 5-methyl-4-(2-thiazolylazo) [COMPOUND] (PTK66), a dual inhibitor of Aurora A and Aurora B kinases.

### CID 25052023 · qa_index 17 · topic `toxicity` · split `val`

- metrics: lcs_tokens=10, ngram5_overlap=6, cos_max=0.724 (answer_len_tokens=20, n_evidence_sentences=500)

**Answer (phase1):**

> No, the compound is highly selective and does not show agonistic or antagonistic effects on glucocorticoid, androgen, or progesterone receptors.

**Closest evidence sentence (by token LCS):**

> In vitro studies showed that [COMPOUND] specifically inhibits the binding of aldosterone to MR and does not have agonistic or antagonistic effects on glucocorticoid, androgen, or progesterone receptors, even at high concentrations [24].

### CID 118984355 · qa_index 3 · topic `mechanism` · split `train`

- metrics: lcs_tokens=9, ngram5_overlap=5, cos_max=0.720 (answer_len_tokens=50, n_evidence_sentences=24)

**Answer (phase1):**

> The compound acts as a cell-permeable iron donor that expands the labile iron pool. This increase in intracellular iron can induce oxidative stress through the production of reactive oxygen species (ROS) and lipid peroxidation, eventually leading to ferroptotic cell death or the accumulation of proteins like amyloid precursor protein (APP).

**Closest evidence sentence (by token LCS):**

> We show that supplementation of exogenous iron in the form of [COMPOUND] at submillimolar doses induces production of reactive oxygen species (ROS) and lipid peroxidation in mitochondria that precede ferroptosis in H9c2 cardiomyocytes.

### CID 6494 · qa_index 3 · topic `mechanism` · split `train`

- metrics: lcs_tokens=9, ngram5_overlap=5, cos_max=0.696 (answer_len_tokens=33, n_evidence_sentences=5)

**Answer (phase1):**

> The compound acts as a ganglionic blocking agent, inhibiting the transmission of nerve impulses through the superior cervical ganglion. It achieves this blockade without affecting the conduction of the preganglionic nerve fiber itself.

**Closest evidence sentence (by token LCS):**

> Paraldehyde and [COMPOUND] blocked transmission of nerve impulses through the superior cervical ganglion of the cat when the drugs were administered intra-arterially to the ganglion or intravenously using the nictitating membrane as an indicator.

### CID 16211214 · qa_index 9 · topic `metabolism` · split `train`

- metrics: lcs_tokens=9, ngram5_overlap=5, cos_max=0.684 (answer_len_tokens=28, n_evidence_sentences=89)

**Answer (phase1):**

> The compound influences obesity-associated molecules, including leptin, insulin-like growth factor 1 (IGF-I), and heat shock proteins (HSP70), suggesting a role in modulating metabolic stress and lipid-related endocrine signaling.

**Closest evidence sentence (by token LCS):**

> The aim of this study was to investigate the effects of boric acid (BA) and [COMPOUND] (BX) on live weight and obesity associated molecules including leptin, L-carnitine, insulin-like growth factor 1 (IGF-I), and heat shock proteins 70 (HSP70) in rats fed with high-fat diet.

### CID 11168203 · qa_index 9 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=9, ngram5_overlap=5, cos_max=0.680 (answer_len_tokens=21, n_evidence_sentences=500)

**Answer (phase1):**

> The compound mitigates osteoarthritis progression by reducing the production of matrix metalloproteinases (MMPs) and reactive oxygen species (ROS) in fibroblast-like synoviocytes.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] effectively attenuates lipopolysaccharide (LPS)-induced abnormal migration and invasion and the production of inflammatory mediators, matrix metalloproteinases (MMPs), and reactive oxygen species (ROS) in FLSs, contributing to the restoration of the synovial microenvironment.

### CID 6456015 · qa_index 5 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=8, ngram5_overlap=6, cos_max=0.683 (answer_len_tokens=24, n_evidence_sentences=15)

**Answer (phase1):**

> It is primarily used for the treatment of advanced renal cell carcinoma (RCC), gastrointestinal stromal tumors (GIST), and progressive, well-differentiated pancreatic neuroendocrine tumors (pNETs).

**Closest evidence sentence (by token LCS):**

> [COMPOUND], an oral multitargeted tyrosine kinase inhibitor (TKI), has been approved for the treatment of advanced renal cell carcinoma and gastrointestinal stromal tumors.

### CID 25204 · qa_index 18 · topic `muscle_regeneration` · split `train`

- metrics: lcs_tokens=8, ngram5_overlap=4, cos_max=0.812 (answer_len_tokens=46, n_evidence_sentences=240)

**Answer (phase1):**

> Injury induced by the compound causes a rapid and sustained increase in muscle glucose uptake. This is accompanied by a complex temporal shift in glucose transporter expression, where GLUT1 and GLUT6 increase early, while GLUT4 levels initially drop before undergoing super-compensation during later stages of repair.

**Closest evidence sentence (by token LCS):**

> The statistical test and sample size for each data set are indicated in the figure legends.ResultsBaCl2-induced injury stimulates a rapid and sustained increase in muscle glucose uptakeIntramuscular injection of the myotoxic agent [COMPOUND] induces acute injury and regeneration of rodent skeletal muscle [24–26].

### CID 1234 · qa_index 6 · topic `physicochemical` · split `train`

- metrics: lcs_tokens=8, ngram5_overlap=4, cos_max=0.757 (answer_len_tokens=33, n_evidence_sentences=32)

**Answer (phase1):**

> The capacity of the compound to interfere with cation transport is highly dependent on the availability of a protonated configuration; the ionized site on the tertiary amine is critical for its calcium-antagonistic properties.

**Closest evidence sentence (by token LCS):**

> These findings indicate that the capacity of [COMPOUND] to interfere with the transport of cations is critically dependent on the availability of a protonated configuration of the drug.

### CID 16362 · qa_index 18 · topic `drug_interactions` · split `test`

- metrics: lcs_tokens=8, ngram5_overlap=4, cos_max=0.721 (answer_len_tokens=21, n_evidence_sentences=140)

**Answer (phase1):**

> A reduction of the normal dose is recommended for CYP2D6-predicted poor metabolizers (PMs) and intermediate metabolizers (IMs) to avoid toxic accumulation.

**Closest evidence sentence (by token LCS):**

> Reduction of the normal dose is recommended for aripiprazole, brexpiprazole, haloperidol, [COMPOUND], risperidone and zuclopenthixol for CYP2D6-predicted PMs, and for [COMPOUND] and zuclopenthixol also for CYP2D6 IMs. For CYP2D6 UMs, a dose increase or an alternative drug is recommended for haloperidol and an alternative drug or titration of the dose for risperidone.

### CID 49800004 · qa_index 30 · topic `metabolism` · split `train`

- metrics: lcs_tokens=8, ngram5_overlap=4, cos_max=0.659 (answer_len_tokens=29, n_evidence_sentences=500)

**Answer (phase1):**

> The compound is administered in its active form and does not undergo significant metabolic activation or conversion to major active metabolites; it is primarily cleared as the parent drug.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is administered in its active form and is primarily excreted through nonrenal mechanisms, allowing it to reach peak blood concentrations more rapidly.

### CID 4876 · qa_index 4 · topic `mechanism` · split `train`

- metrics: lcs_tokens=8, ngram5_overlap=4, cos_max=0.655 (answer_len_tokens=27, n_evidence_sentences=13)

**Answer (phase1):**

> The compound serves as an essential precursor in the biosynthesis of folate cofactors. It is required for the survival and proliferation of various pathogens, including Chlamydia trachomatis.

**Closest evidence sentence (by token LCS):**

> Chlamydia protein associating with death domains (CADD) is involved in the biosynthesis of [COMPOUND] (pABA), an essential component of the folate cofactor that is required for the survival and proliferation of the human pathogen Chlamydia trachomatis.

### CID 1367 · qa_index 4 · topic `drug_interactions` · split `train`

- metrics: lcs_tokens=8, ngram5_overlap=4, cos_max=0.643 (answer_len_tokens=43, n_evidence_sentences=9)

**Answer (phase1):**

> The compound is used as a tool to determine the relative contribution of oxidative metabolism to a drug's clearance. By pre-treating with this broad-spectrum inhibitor, researchers can observe changes in AUC and Cmax to quantify the role of P450-mediated pathways versus non-P450 pathways.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] (ABT) is a non-isoform specific, time-dependent inhibitor of cytochrome P450 (CYP) enzymes used extensively in preclinical studies to determine the relative contribution of oxidative metabolism.

### CID 3541112 · qa_index 7 · topic `pharmacophore` · split `val`

- metrics: lcs_tokens=7, ngram5_overlap=5, cos_max=0.530 (answer_len_tokens=27, n_evidence_sentences=176)

**Answer (phase1):**

> The carboxylate group and the specific distance to the 3-hydroxyl group are critical for binding to the hydroxycarboxylic acid receptor 2 (HCA2), which mediates its anti-lipolytic effects.

**Closest evidence sentence (by token LCS):**

> Background The ketone body [COMPOUND] (3-OHB) increases cardiac output (CO) in patients with heart failure through unknown mechanisms. 3-OHB activates the hydroxycarboxylic acid receptor 2 (HCA2), which increases prostaglandins and suppresses circulating free fatty acids.

### CID 72281 · qa_index 27 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=7, ngram5_overlap=4, cos_max=0.857 (answer_len_tokens=26, n_evidence_sentences=500)

**Answer (phase1):**

> The compound exerts an interventional effect on gastric carcinogenesis by modulating exosomal circ0008274 and its interaction with miR-526b-5p, thereby inhibiting proliferation and cancer stem cell-like characteristics.

**Closest evidence sentence (by token LCS):**

> TGES-1-EX circ0008274 promoted the proliferation, EMT, and cancer stem cell-like characteristics in GES-1 cells through miR-526b-5p-mediated regulatory mechanisms. CONCLUSION: [COMPOUND] exerted an interventional effect on the gastric carcinogenesis process, particularly through the modulation of exosomal circ0008274 and its interaction with miR-526b-5p.

### CID 24247 · qa_index 6 · topic `analytical_chemistry` · split `test`

- metrics: lcs_tokens=7, ngram5_overlap=4, cos_max=0.784 (answer_len_tokens=25, n_evidence_sentences=36)

**Answer (phase1):**

> Increasing the concentration of the compound expands the linear detection range of hydroperoxides, allowing for the quantification of higher concentrations of analytes like cumene hydroperoxide.

**Closest evidence sentence (by token LCS):**

> The results showed that increasing the concentration of [COMPOUND] expands the linear detection range of CuHP in all the buffers and pH values tested.

### CID 1388 · qa_index 11 · topic `toxicity` · split `train`

- metrics: lcs_tokens=6, ngram5_overlap=4, cos_max=0.810 (answer_len_tokens=33, n_evidence_sentences=500)

**Answer (phase1):**

> The substantia nigra pars compacta (SNc) is the most sensitive region. The compound causes a profound loss of tyrosine hydroxylase-positive neurons in the SNc and a corresponding depletion of dopamine in the striatum.

**Closest evidence sentence (by token LCS):**

> The alterations in the function and density of
dopaminergic neurons in the substantia nigra of mice induced by [COMPOUND] were different
from those in the striatum.7,23 The nigrostriatal pathway originates from the substantia nigra
and terminates within the striatum, and the selective depletion of dopamine in the
striatum pathway is less susceptible to [COMPOUND].24,25In the present study, microglial cells and astrocytes were activated by [COMPOUND], as
reflected by the immunostaining of Iba1 and GFAP.

### CID 5511 · qa_index 3 · topic `mechanism` · split `train`

- metrics: lcs_tokens=6, ngram5_overlap=4, cos_max=0.796 (answer_len_tokens=33, n_evidence_sentences=60)

**Answer (phase1):**

> The compound acts as a centrally acting muscle relaxant by blocking voltage-gated sodium and calcium channels in the brainstem and spinal cord, which inhibits the synaptic influx of calcium and subsequent neurotransmitter release.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] directly affects the spinal cord and has imitating effects on the neurotransmitters because it inhibits the synaptic influx of calcium ions, which is the efflux of the neurotransmitters.

### CID 5569 · qa_index 22 · topic `toxicity` · split `train`

- metrics: lcs_tokens=6, ngram5_overlap=4, cos_max=0.745 (answer_len_tokens=26, n_evidence_sentences=111)

**Answer (phase1):**

> The compound has shown weak cytotoxic and genotoxic effects in some assays, including the induction of chromosomal aberrations and micronuclei in human lymphocytes and fish erythrocytes.

**Closest evidence sentence (by token LCS):**

> Sister-chromatid exchanges, chromosomal aberrations and micronuclei showed that [COMPOUND] is capable of exerting weak cytotoxic and genotoxic effects in cultured human peripheral blood lymphocytes (Ribas et al. 1996).


---

## Cosine > threshold (paraphrase)  — 418 total, showing 20

### CID 65866 · qa_index 7 · topic `therapeutic_use` · split `val`

- metrics: lcs_tokens=11, ngram5_overlap=9, cos_max=0.952 (answer_len_tokens=25, n_evidence_sentences=19)

**Answer (phase1):**

> The compound demonstrates comparable effectiveness to amlodipine in preventing major adverse cardiovascular events (MACE) in hypertensive patients, while potentially offering a more favorable side-effect profile.

**Closest evidence sentence (by token LCS):**

> This study aims to compare the effectiveness of [COMPOUND] and amlodipine in preventing major adverse cardiovascular events (MACE) in hypertensive patients.

### CID 5487 · qa_index 3 · topic `mechanism` · split `train`

- metrics: lcs_tokens=8, ngram5_overlap=4, cos_max=0.942 (answer_len_tokens=29, n_evidence_sentences=47)

**Answer (phase1):**

> The compound acts as a centrally acting alpha-2 adrenergic receptor agonist. It also demonstrates binding affinity for imidazoline receptors, which contributes to its profile as a skeletal muscle relaxant.

**Closest evidence sentence (by token LCS):**

> [COMPOUND], a muscle relaxant, exerts its mechanism as a centrally acting alpha-2 adrenergic receptor agonist and binds to imidazoline receptors.

### CID 16129670 · qa_index 11 · topic `mechanism` · split `val`

- metrics: lcs_tokens=7, ngram5_overlap=3, cos_max=0.902 (answer_len_tokens=27, n_evidence_sentences=296)

**Answer (phase1):**

> Yes, the compound is a potent inhibitor of gastric emptying, a process mediated by CCK1 receptors that helps regulate the delivery of nutrients to the small intestine.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] (CCK) is a potent inhibitor of gastric emptying.

### CID 25960 · qa_index 20 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=7, ngram5_overlap=3, cos_max=0.867 (answer_len_tokens=22, n_evidence_sentences=153)

**Answer (phase1):**

> In streptozocin-induced diabetic rats, the compound reduces plasma glucose, food intake, and water intake, effectively normalizing metabolic parameters similarly to insulin treatment.

**Closest evidence sentence (by token LCS):**

> Treatment of streptozocin (STZ)-induced diabetic rats with [COMPOUND] (10-15 mumol.kg-1.day-1) for 7 wk resulted in a decrease in plasma glucose, food intake, and water intake to control or near control levels.

### CID 5280497 · qa_index 18 · topic `sex_differences` · split `train`

- metrics: lcs_tokens=4, ngram5_overlap=0, cos_max=0.907 (answer_len_tokens=35, n_evidence_sentences=500)

**Answer (phase1):**

> Prenatal hypoxia increases vasoconstrictor sensitivity to the compound in a sex-specific manner. Females show a more severe phenotype due to reduced nitric oxide modulation, while males exhibit increased sensitivity primarily through upregulated TP receptor expression.

**Closest evidence sentence (by token LCS):**

> CONCLUSIONS: Prenatal hypoxia increased [COMPOUND] vasoconstrictor capacity in the adult offspring in a sex-specific manner, via reduced NO modulation in females and increased TP expression in males.

### CID 5281328 · qa_index 12 · topic `toxicity` · split `train`

- metrics: lcs_tokens=4, ngram5_overlap=0, cos_max=0.907 (answer_len_tokens=24, n_evidence_sentences=151)

**Answer (phase1):**

> The compound shows dose-dependent cytotoxicity in HDPSCs, with viability remaining high (80%) up to 100 μg/mL but decreasing significantly at concentrations above 200 μg/mL.

**Closest evidence sentence (by token LCS):**

> The viability of HDPSCs was 80% for the medium containing up to 100 μg/mL [COMPOUND], and the viability decreased to 50% between 100 and 200 μg/mL concentrations (p < 0.001).

### CID 5318650 · qa_index 6 · topic `mechanism` · split `train`

- metrics: lcs_tokens=4, ngram5_overlap=0, cos_max=0.887 (answer_len_tokens=26, n_evidence_sentences=10)

**Answer (phase1):**

> The compound promotes fatty acid oxidation by upregulating key proteins such as PPAR-α, PGC-1α, and CPT-1A, which helps reduce triglyceride accumulation and restore cellular ATP levels.

**Closest evidence sentence (by token LCS):**

> Pharmacological experiments also demonstrated that [COMPOUND] treatment led to a significant reduction in triglyceride accumulation, increased ATP levels and direct fatty acid oxidation activity, as well as enhanced expression of proteins associated with fatty acid oxidation, including PPAR-α, PGC-1α, and CPT-1A.

### CID 16223405 · qa_index 9 · topic `toxicity` · split `test`

- metrics: lcs_tokens=4, ngram5_overlap=0, cos_max=0.870 (answer_len_tokens=25, n_evidence_sentences=65)

**Answer (phase1):**

> Clinical studies indicate that the compound does not significantly prolong the QTc interval at either standard clinical doses (0.1 mmol/kg) or supraclinical doses (0.3 mmol/kg).

**Closest evidence sentence (by token LCS):**

> AIMS: We investigated the effect of [COMPOUND], a new gadolinium-based contrast agent, on the QTc interval at clinical and supraclinical dose, considering the relative hyperosmolarity of this product.

### CID 156588438 · qa_index 2 · topic `drug_interactions` · split `val`

- metrics: lcs_tokens=4, ngram5_overlap=0, cos_max=0.858 (answer_len_tokens=42, n_evidence_sentences=7)

**Answer (phase1):**

> The compound exhibits significant inhibitory activity against CYP2D6, CYP2E1, and CYP3A4. While it acts as a competitive inhibitor for CYP2D6 and CYP2E1, it demonstrates time-dependent, non-competitive inhibition of CYP3A4, suggesting a potential for drug-drug interactions when co-administered with substrates of these enzymes.

**Closest evidence sentence (by token LCS):**

> Moreover, the inhibition of CYP3A4 was time-dependent with the KI and Kinact values of 0.635 μM-1 and 0.0373 min-1, respectively.[COMPOUND] served as a competitive inhibitor of CYP2D6 and 2E1 exerting weak inhibition and a non-competitive inhibitor of CYP3A4 exerting moderate inhibition.

### CID 1031 · qa_index 18 · topic `toxicity` · split `train`

- metrics: lcs_tokens=4, ngram5_overlap=0, cos_max=0.857 (answer_len_tokens=25, n_evidence_sentences=183)

**Answer (phase1):**

> The compound is generally more irritative to the skin than ethanol, particularly at concentrations above 60%, and can cause significant dehydration of the skin barrier.

**Closest evidence sentence (by token LCS):**

> A recent review on the impact of [COMPOUND] on skin barrier function concluded that 1‐[COMPOUND] can cause irritation, especially at concentrations above 60% [49].

### CID 71576543 · qa_index 14 · topic `design_levers` · split `train`

- metrics: lcs_tokens=3, ngram5_overlap=0, cos_max=0.918 (answer_len_tokens=31, n_evidence_sentences=36)

**Answer (phase1):**

> Clinical data suggests that higher doses of the compound (e.g., 180 mg) are typically required to achieve sustained reversal of rivaroxaban compared to the doses needed for apixaban (e.g., 60 mg).

**Closest evidence sentence (by token LCS):**

> The reversal effect was dose dependent, with higher doses required for full reversal of rivaroxaban than for apixaban.As shown in the initial preclinical studies,9 plasma-based assays are unsuitable for measuring the effect of [COMPOUND] on anticoagulation reversal.

### CID 127299 · qa_index 5 · topic `therapeutic_use` · split `val`

- metrics: lcs_tokens=3, ngram5_overlap=0, cos_max=0.913 (answer_len_tokens=33, n_evidence_sentences=8)

**Answer (phase1):**

> Unlike TRH, the compound's hyperthermic activity is not regulated by the hypothalamic-pituitary-thyroid axis. It maintains consistent thermogenic potency even in hypothyroid states, suggesting its mechanism of action is independent of thyroid hormone levels.

**Closest evidence sentence (by token LCS):**

> In addition, the hypothalamic-pituitary-thyroid axis does not regulate the hyperthermic effect of [COMPOUND], unlike that of TRH.

### CID 15558638 · qa_index 6 · topic `hematological_effects` · split `train`

- metrics: lcs_tokens=3, ngram5_overlap=0, cos_max=0.870 (answer_len_tokens=24, n_evidence_sentences=15)

**Answer (phase1):**

> The compound promotes the oxidation of hemoglobin to methemoglobin. Because methemoglobin is incapable of effective oxygen transport, this chemical transformation impairs systemic oxygen delivery.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] oxidized hemoglobin to methemoglobin, which cannot transport oxygen.

### CID 129228 · qa_index 15 · topic `metabolism` · split `train`

- metrics: lcs_tokens=3, ngram5_overlap=0, cos_max=0.861 (answer_len_tokens=26, n_evidence_sentences=92)

**Answer (phase1):**

> The hydrolysis is estimated to occur predominantly in the microsomes (approximately two-thirds) and to a lesser extent in the cytosol (approximately one-third) of human hepatic cells.

**Closest evidence sentence (by token LCS):**

> Two-thirds of [COMPOUND] hydrolysis was estimated to occur in human microsomes and one-third in cytosol.

### CID 159864 · qa_index 8 · topic `mechanism` · split `test`

- metrics: lcs_tokens=3, ngram5_overlap=0, cos_max=0.856 (answer_len_tokens=18, n_evidence_sentences=121)

**Answer (phase1):**

> The anorexigenic and weight-lowering effects of the compound are dependent on functional GFRAL receptors, likely involving brainstem signaling.

**Closest evidence sentence (by token LCS):**

> The full anorexigenic and anti-obesity effects of [COMPOUND] require functional GFRAL receptors.

### CID 457 · qa_index 4 · topic `metabolism` · split `train`

- metrics: lcs_tokens=3, ngram5_overlap=0, cos_max=0.855 (answer_len_tokens=24, n_evidence_sentences=118)

**Answer (phase1):**

> The compound is produced through the N-methylation of nicotinamide, a reaction catalyzed by the enzyme nicotinamide N-methyltransferase (NNMT) using S-adenosyl-methionine as the methyl donor.

**Closest evidence sentence (by token LCS):**

> Nicotinamide N-methyltransferase (NNMT) and its derivative, [COMPOUND] ([COMPOUND]), are known to be significant in conditions such as cardiovascular inflammation and renal tubular damage, and [COMPOUND] has been recognized for its anti-inflammatory effects in various diseases.

### CID 9866696 · qa_index 6 · topic `mechanism` · split `train`

- metrics: lcs_tokens=3, ngram5_overlap=0, cos_max=0.854 (answer_len_tokens=25, n_evidence_sentences=192)

**Answer (phase1):**

> The compound appears to modulate the SNHG1/miR-21 signaling axis, leading to reduced expression of inflammatory cytokines like TNF-α and IL-1β while improving myocardial cell viability.

**Closest evidence sentence (by token LCS):**

> In addition, in the LPS‐stimulated H9C2 cells, [COMPOUND] increased myocardial cell viability and decreased the levels of inflammatory cytokines, further indicating the cardioprotective effects of [COMPOUND] in sepsis.

### CID 6280 · qa_index 3 · topic `mechanism` · split `val`

- metrics: lcs_tokens=3, ngram5_overlap=0, cos_max=0.853 (answer_len_tokens=34, n_evidence_sentences=97)

**Answer (phase1):**

> The compound acts as a selective activator of voltage-gated sodium (NaV) channels. It binds to an activation site, causing persistent opening of the channels by shifting the activation threshold and delaying or preventing inactivation.

**Closest evidence sentence (by token LCS):**

> A hypothesis is presented which suggests that batrachotoxin, [COMPOUND], and divalent cations interact with an activation site associated with the action potential Na+ ionophore, whereas tetrodotoxin interacts with a physically and functionally independent site involved in the transport of monovalent cations by the ionophore.

### CID 136469009 · qa_index 10 · topic `resistance_mechanism` · split `train`

- metrics: lcs_tokens=2, ngram5_overlap=0, cos_max=0.856 (answer_len_tokens=32, n_evidence_sentences=49)

**Answer (phase1):**

> The compound can inhibit EPSPS expression in certain resistant biotypes and, when used in combination with glyphosate, can restore sensitivity or provide control by acting through its own distinct mechanism (ACCase inhibition).

**Closest evidence sentence (by token LCS):**

> These results demonstrated that the dietary exposure risk of fomesafen, clomazone, and [COMPOUND] used in soybean according to good agricultural practices (GAP) was acceptable and would not pose an unacceptable health risk to Chinese consumers.

### CID 7913 · qa_index 8 · topic `reactivity` · split `test`

- metrics: lcs_tokens=2, ngram5_overlap=0, cos_max=0.853 (answer_len_tokens=29, n_evidence_sentences=60)

**Answer (phase1):**

> When treated with hypochlorite, the compound releases approximately one-third of its total nitrogen as gas, whereas urea releases about half, reflecting the different nitrogen-to-carbonyl ratios in their respective structures.

**Closest evidence sentence (by token LCS):**

> BACKGROUND: Determination of serum total protein concentration is commonly performed by the [COMPOUND] method.


---

## Co-flagged on all three metrics  — 0 total, showing 0

_No cases._
