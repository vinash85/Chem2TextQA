# Flagged Examples (for review)

Top-20 per category, ranked **most egregious first**. The LCS category has no threshold — rows are taken in descending order of `lcs_tokens` over the entire corpus (see the threshold curve in the summary for rate-at-cutoff). The ngram and cos categories use their fixed thresholds; the co-flagged list uses a composite score that sums each flagged metric's excess over threshold, normalized by the observed max. The full scored list is in `per_qa_leakage.jsonl` (filter/sort on `lcs_tokens`, `flag_ngram`, `flag_cos`, or `cos_max`). No judgments are made here — for each case the answer and the best-matching evidence sentence are shown so you can decide leakage vs legitimate terminology reuse.


---

## Top LCS (all rows, descending by `lcs_tokens`)  — 188541 total, showing top 20

### CID 16129665 · qa_index 21 · topic `metabolism` · split `val`

- metrics: lcs_tokens=19, ngram5_overlap=15, cos_max=0.914 (answer_len_tokens=22, n_evidence_sentences=500)

**Answer (phase1):**

> The liver plays a major role in the degradation of plasma cyclic AMP produced by target tissues responding to the compound's stimulation.

**Closest evidence sentence (by token LCS):**

> The results reported here suggest that the liver plays a major role in the degradation of plasma cyclic AMP produced by target tissues responding to [COMPOUND], and in the release of cyclic AMP under glucagon.

### CID 65575 · qa_index 18 · topic `mechanism` · split `train`

- metrics: lcs_tokens=19, ngram5_overlap=15, cos_max=0.881 (answer_len_tokens=29, n_evidence_sentences=123)

**Answer (phase1):**

> Reverse pharmacophore mapping suggests that the compound may interact with proviral integration Moloney virus kinase (PIM1), vascular endothelial growth factor receptor 2 (VEGFR2), and c-Jun N-terminal kinase 1 (JNK1).

**Closest evidence sentence (by token LCS):**

> The results of PharmMapper analysis indicated that three kinases could be potential targets for [COMPOUND]: proviral integration Moloney virus kinase (PIM1), vascular endothelial growth factor receptor 2 (VEGFR2), and c-Jun N-terminal kinase 1 (JNK1) (Table 5).

### CID 3001055 · qa_index 21 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=18, ngram5_overlap=14, cos_max=0.984 (answer_len_tokens=22, n_evidence_sentences=500)

**Answer (phase1):**

> The compound is approximately four to ten times more potent than cimetidine on a molar basis in inhibiting stimulated gastric acid secretion.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is four to ten times more potent than cimetidine on a molar basis in inhibiting stimulated gastric acid secretion.

### CID 54697325 · qa_index 6 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=18, ngram5_overlap=14, cos_max=0.879 (answer_len_tokens=20, n_evidence_sentences=224)

**Answer (phase1):**

> It is approved for the treatment of community-acquired bacterial pneumonia (CABP) and acute bacterial skin and skin structure infections (ABSSSI).

**Closest evidence sentence (by token LCS):**

> There is now increasing momentum toward developing and studying novel drugs or drug combinations for treating Mab disease, evidenced by the emergence of new chemical entities in preclinical stages and ongoing clinical trials.[COMPOUND] is an aminomethylcycline that is FDA approved for the treatment of community-acquired bacterial pneumonia (CABP) and acute bacterial skin and skin structure infections (ABSSSI).

### CID 441361 · qa_index 4 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=16, ngram5_overlap=16, cos_max=0.801 (answer_len_tokens=36, n_evidence_sentences=14)

**Answer (phase1):**

> The compound is indicated as a maintenance therapy to reduce the risk of relapse in adult and pediatric patients with high-risk neuroblastoma who have shown at least a partial response to prior multiagent and multimodality treatments.

**Closest evidence sentence (by token LCS):**

> On December 13, 2023, the US Food and Drug Administration (FDA) approved eflornithine ([COMPOUND], US WorldMeds) to reduce the risk of relapse in adult and pediatric patients with high-risk neuroblastoma who have demonstrated at least a partial response to prior multiagent, multimodality therapy including anti-GD2 immunotherapy.

### CID 11243969 · qa_index 9 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=16, ngram5_overlap=14, cos_max=0.598 (answer_len_tokens=22, n_evidence_sentences=300)

**Answer (phase1):**

> The compound is indicated as an adjunct to diet and exercise to improve glycemic control in adults with type 2 diabetes mellitus.

**Closest evidence sentence (by token LCS):**

> This FDC is indicated as an adjunct to diet and exercise to improve glycemic control in adults with T2DM who have inadequate glycemic control with metformin and/or sulfonylurea and either of the individual components of the combination or who already received treatment with dapagliflozin and [COMPOUND] (16).

### CID 71621331 · qa_index 6 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=16, ngram5_overlap=13, cos_max=0.775 (answer_len_tokens=33, n_evidence_sentences=12)

**Answer (phase1):**

> The compound is indicated for the treatment of adult patients with previously treated, unresectable, locally advanced or metastatic intrahepatic cholangiocarcinoma. Its use is specifically targeted toward tumors harboring FGFR2 fusions or other rearrangements.

**Closest evidence sentence (by token LCS):**

> On September 30, 2022, the FDA granted accelerated approval to [COMPOUND] for the treatment of adult patients with previously treated, unresectable, locally advanced or metastatic intrahepatic cholangiocarcinoma (iCCA) with FGFR2 fusions or other rearrangements.

### CID 166177189 · qa_index 4 · topic `therapeutic_use` · split `test`

- metrics: lcs_tokens=15, ngram5_overlap=13, cos_max=0.771 (answer_len_tokens=34, n_evidence_sentences=64)

**Answer (phase1):**

> The compound is primarily being developed for the treatment of idiopathic pulmonary fibrosis (IPF) and progressive pulmonary fibrosis (PPF). Its pharmacological profile also suggests potential utility in treating systemic sclerosis-associated interstitial lung disease (SSc-ILD).

**Closest evidence sentence (by token LCS):**

> [COMPOUND] ([COMPOUND], 1) is a potent and selective inhibitor of phosphodiesterase type 4 (PDE4) being developed for the treatment of idiopathic pulmonary fibrosis (IPF) and progressive pulmonary fibrosis (PPF).

### CID 11750009 · qa_index 6 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.903 (answer_len_tokens=34, n_evidence_sentences=51)

**Answer (phase1):**

> The compound is indicated for the topical treatment of acne vulgaris in patients 12 years of age and older, serving as the first topical hormonal therapy to target the androgenic drivers of the disease.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is an androgen receptor inhibitor which has been approved by the United States Food and Drug Administration for the topical treatment of acne vulgaris in patients 12 years of age and older.

### CID 72720442 · qa_index 5 · topic `engineering` · split `train`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.895 (answer_len_tokens=40, n_evidence_sentences=33)

**Answer (phase1):**

> Cobalt doping enhances the adsorption of Cr(VI) by decreasing electron occupancy in the eg orbitals and reducing the spin state of the iron ions. This electronic modification increases the affinity for anionic pollutants without significantly altering the compound's magnetic properties.

**Closest evidence sentence (by token LCS):**

> Compared to pristine [COMPOUND], cobalt doping significantly enhances the capability of [COMPOUND] to adsorption Cr(VI) by decreasing electron occupancy in the eg orbitals and reducing the spin state of Fe ions.

### CID 6918305 · qa_index 5 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.887 (answer_len_tokens=24, n_evidence_sentences=84)

**Answer (phase1):**

> The compound was first approved for the treatment of seizures associated with cyclin-dependent kinase-like 5 (CDKL5) deficiency disorder (CDD) in pediatric and adult patients.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] received its first approval in March 2022 in the USA for the treatment of seizures associated with cyclin-dependent kinase-like 5 (CDKL5) deficiency disorder (CDD) in patients 2 years of age and older.

### CID 3883 · qa_index 37 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.812 (answer_len_tokens=35, n_evidence_sentences=500)

**Answer (phase1):**

> Clinical evidence suggests that the compound is associated with a significantly lower risk of developing gout compared to other PPIs like omeprazole or pantoprazole, potentially due to its unique effects on adipogenesis and insulin sensitivity.

**Closest evidence sentence (by token LCS):**

> Additionally, research is needed to examine the effects of each type of PPI on gout.ConclusionOur study found that [COMPOUND] is associated with a significantly lower risk of developing gout compared to other PPIs.

### CID 54726192 · qa_index 3 · topic `functional_groups` · split `val`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.712 (answer_len_tokens=28, n_evidence_sentences=104)

**Answer (phase1):**

> The D-ring (the fully aromatic ring in the tetracycline core) is substituted with a fluorine atom at the C-7 position and a pyrrolidinoacetamido group at the C-9 position.

**Closest evidence sentence (by token LCS):**

> The possible reason for this is that the few key distinctions between [COMPOUND] and tigecycline, a fluorine atom at the C-7 position and a pyrrolidinoacetamido group at the C-9 position, take effect.

### CID 4062 · qa_index 11 · topic `toxicity` · split `train`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.664 (answer_len_tokens=25, n_evidence_sentences=157)

**Answer (phase1):**

> Spinal administration has been associated with a higher incidence of transient neurologic symptoms (TNS) and transient nerve root irritation compared to longer-acting agents like bupivacaine.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] was associated with a higher incidence of transient neurologic symptoms (TNS) and transient nerve root irritation (TRI) (OR, 9.18; 95% CI 2.42-34.88).

### CID 3032581 · qa_index 10 · topic `drug_interactions` · split `train`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.662 (answer_len_tokens=19, n_evidence_sentences=63)

**Answer (phase1):**

> The oxidative stress response is regulated in parallel by cytochrome P450 2E1 (CYP2E1) and inducible nitric oxide synthase (iNOS).

**Closest evidence sentence (by token LCS):**

> [COMPOUND] (MB)- and paraquat (PQ)-induced oxidative stress in rat polymorphonuclear leukocytes (PMNs) is regulated in parallel by cytochrome P450 2E1 (CYP2E1) and inducible nitric oxide synthase (iNOS).

### CID 44472635 · qa_index 11 · topic `drug_interactions` · split `val`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.576 (answer_len_tokens=30, n_evidence_sentences=132)

**Answer (phase1):**

> No, the compound exhibits no inhibitory or inducing effects on CYP isoenzymes such as CYP3A4 and CYP2D6, making it relatively safe for use with concomitant medications metabolized by these pathways.

**Closest evidence sentence (by token LCS):**

> Moreover, while mirabegron is partially metabolized by cytochrome P450 (CYP) 3A4 and inhibits CYP2D6, [COMPOUND] exhibits no inhibitory or inducing effects on CYP isoenzymes such as CYP3A4 and CYP2D6, reducing the risk of drug–drug interactions [13].In clinical trials in Japan, the United States, and Korea, [COMPOUND] was shown to be effective in improving symptoms of OAB and was tolerated extremely well in terms of safety [16, 17, 18].

### CID 86705695 · qa_index 10 · topic `therapeutic_use` · split `test`

- metrics: lcs_tokens=14, ngram5_overlap=11, cos_max=0.787 (answer_len_tokens=23, n_evidence_sentences=327)

**Answer (phase1):**

> It is primarily used for the treatment of adults with previously treated, unresectable locally advanced or metastatic cholangiocarcinoma harboring FGFR2 fusions or rearrangements.

**Closest evidence sentence (by token LCS):**

> 1
 [COMPOUND] has been approved by the US Food and Drug Administration,
2
 European Medicines Agency,
3
 and Japanese Ministry of Health, Labor, and Welfare
4
 and conditionally approved by Health Canada
5
 for the treatment of adults with previously treated, unresectable locally advanced or metastatic cholangiocarcinoma with an FGFR2 fusion or other rearrangement.[COMPOUND] is a Biopharmaceutics Classification System Class II compound with high permeability and pH‐dependent solubility.

### CID 644019 · qa_index 7 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=14, ngram5_overlap=10, cos_max=0.924 (answer_len_tokens=23, n_evidence_sentences=500)

**Answer (phase1):**

> The compound is FDA-approved for the treatment of seizures associated with Lennox-Gastaut syndrome, Dravet syndrome, and tuberous sclerosis complex, particularly in pediatric populations.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] (CBD), a major cannabinoid found in Cannabis sativa L., has been used in the treatment of seizures associated with Lennox-Gastaut syndrome, Dravet syndrome, and tuberous sclerosis complex.

### CID 162859 · qa_index 10 · topic `anti_tumor_mechanism` · split `val`

- metrics: lcs_tokens=14, ngram5_overlap=10, cos_max=0.888 (answer_len_tokens=20, n_evidence_sentences=104)

**Answer (phase1):**

> It prevents VEGF-induced and IL-8-induced angiogenesis by blocking the activation of mitogen-activated protein kinases (MAPKs), including ERK, p38, and JNK.

**Closest evidence sentence (by token LCS):**

> Taken together, [COMPOUND] directly and indirectly prevents VEGF-induced and IL-8-induced angiogenesis by blocking the activation of mitogen-activated protein kinases (MAPKs).

### CID 67286591 · qa_index 4 · topic `mechanism` · split `test`

- metrics: lcs_tokens=14, ngram5_overlap=10, cos_max=0.867 (answer_len_tokens=36, n_evidence_sentences=43)

**Answer (phase1):**

> The compound targets the polymerase basic protein 2 (PB2) subunit of the influenza A virus polymerase complex. By binding to the PB2 cap-binding site, it inhibits the initiation of viral mRNA synthesis and reduces RNA replication.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is a nonnucleoside inhibitor of the polymerase basic protein 2 (PB2) subunit of the influenza A virus polymerase complex, resulting in reduced RNA replication [12].


---

## 5-gram overlap > threshold  — 1821 total, showing top 20

### CID 441361 · qa_index 4 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=16, ngram5_overlap=16, cos_max=0.801 (answer_len_tokens=36, n_evidence_sentences=14)

**Answer (phase1):**

> The compound is indicated as a maintenance therapy to reduce the risk of relapse in adult and pediatric patients with high-risk neuroblastoma who have shown at least a partial response to prior multiagent and multimodality treatments.

**Closest evidence sentence (by token LCS):**

> On December 13, 2023, the US Food and Drug Administration (FDA) approved eflornithine ([COMPOUND], US WorldMeds) to reduce the risk of relapse in adult and pediatric patients with high-risk neuroblastoma who have demonstrated at least a partial response to prior multiagent, multimodality therapy including anti-GD2 immunotherapy.

### CID 16129665 · qa_index 21 · topic `metabolism` · split `val`

- metrics: lcs_tokens=19, ngram5_overlap=15, cos_max=0.914 (answer_len_tokens=22, n_evidence_sentences=500)

**Answer (phase1):**

> The liver plays a major role in the degradation of plasma cyclic AMP produced by target tissues responding to the compound's stimulation.

**Closest evidence sentence (by token LCS):**

> The results reported here suggest that the liver plays a major role in the degradation of plasma cyclic AMP produced by target tissues responding to [COMPOUND], and in the release of cyclic AMP under glucagon.

### CID 65575 · qa_index 18 · topic `mechanism` · split `train`

- metrics: lcs_tokens=19, ngram5_overlap=15, cos_max=0.881 (answer_len_tokens=29, n_evidence_sentences=123)

**Answer (phase1):**

> Reverse pharmacophore mapping suggests that the compound may interact with proviral integration Moloney virus kinase (PIM1), vascular endothelial growth factor receptor 2 (VEGFR2), and c-Jun N-terminal kinase 1 (JNK1).

**Closest evidence sentence (by token LCS):**

> The results of PharmMapper analysis indicated that three kinases could be potential targets for [COMPOUND]: proviral integration Moloney virus kinase (PIM1), vascular endothelial growth factor receptor 2 (VEGFR2), and c-Jun N-terminal kinase 1 (JNK1) (Table 5).

### CID 3001055 · qa_index 21 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=18, ngram5_overlap=14, cos_max=0.984 (answer_len_tokens=22, n_evidence_sentences=500)

**Answer (phase1):**

> The compound is approximately four to ten times more potent than cimetidine on a molar basis in inhibiting stimulated gastric acid secretion.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is four to ten times more potent than cimetidine on a molar basis in inhibiting stimulated gastric acid secretion.

### CID 54697325 · qa_index 6 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=18, ngram5_overlap=14, cos_max=0.879 (answer_len_tokens=20, n_evidence_sentences=224)

**Answer (phase1):**

> It is approved for the treatment of community-acquired bacterial pneumonia (CABP) and acute bacterial skin and skin structure infections (ABSSSI).

**Closest evidence sentence (by token LCS):**

> There is now increasing momentum toward developing and studying novel drugs or drug combinations for treating Mab disease, evidenced by the emergence of new chemical entities in preclinical stages and ongoing clinical trials.[COMPOUND] is an aminomethylcycline that is FDA approved for the treatment of community-acquired bacterial pneumonia (CABP) and acute bacterial skin and skin structure infections (ABSSSI).

### CID 25151352 · qa_index 5 · topic `therapeutic_use` · split `test`

- metrics: lcs_tokens=9, ngram5_overlap=14, cos_max=0.860 (answer_len_tokens=31, n_evidence_sentences=443)

**Answer (phase1):**

> It is approved for the treatment of adult patients with symptomatic tenosynovial giant cell tumor (TGCT) that is associated with severe morbidity or functional limitations and is not amenable to surgery.

**Closest evidence sentence (by token LCS):**

> BACKGROUND: [COMPOUND] ([COMPOUND]) is the only systemic therapy approved by the FDA for the treatment of adult patients with symptomatic tenosynovial giant-cell tumor (TGCT) associated with severe morbidity or functional limitations, and not amenable to improvement with surgery.

### CID 11243969 · qa_index 9 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=16, ngram5_overlap=14, cos_max=0.598 (answer_len_tokens=22, n_evidence_sentences=300)

**Answer (phase1):**

> The compound is indicated as an adjunct to diet and exercise to improve glycemic control in adults with type 2 diabetes mellitus.

**Closest evidence sentence (by token LCS):**

> This FDC is indicated as an adjunct to diet and exercise to improve glycemic control in adults with T2DM who have inadequate glycemic control with metformin and/or sulfonylurea and either of the individual components of the combination or who already received treatment with dapagliflozin and [COMPOUND] (16).

### CID 71621331 · qa_index 6 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=16, ngram5_overlap=13, cos_max=0.775 (answer_len_tokens=33, n_evidence_sentences=12)

**Answer (phase1):**

> The compound is indicated for the treatment of adult patients with previously treated, unresectable, locally advanced or metastatic intrahepatic cholangiocarcinoma. Its use is specifically targeted toward tumors harboring FGFR2 fusions or other rearrangements.

**Closest evidence sentence (by token LCS):**

> On September 30, 2022, the FDA granted accelerated approval to [COMPOUND] for the treatment of adult patients with previously treated, unresectable, locally advanced or metastatic intrahepatic cholangiocarcinoma (iCCA) with FGFR2 fusions or other rearrangements.

### CID 166177189 · qa_index 4 · topic `therapeutic_use` · split `test`

- metrics: lcs_tokens=15, ngram5_overlap=13, cos_max=0.771 (answer_len_tokens=34, n_evidence_sentences=64)

**Answer (phase1):**

> The compound is primarily being developed for the treatment of idiopathic pulmonary fibrosis (IPF) and progressive pulmonary fibrosis (PPF). Its pharmacological profile also suggests potential utility in treating systemic sclerosis-associated interstitial lung disease (SSc-ILD).

**Closest evidence sentence (by token LCS):**

> [COMPOUND] ([COMPOUND], 1) is a potent and selective inhibitor of phosphodiesterase type 4 (PDE4) being developed for the treatment of idiopathic pulmonary fibrosis (IPF) and progressive pulmonary fibrosis (PPF).

### CID 132999 · qa_index 7 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=11, ngram5_overlap=13, cos_max=0.693 (answer_len_tokens=39, n_evidence_sentences=500)

**Answer (phase1):**

> It is indicated for the symptomatic treatment of chronic stable angina pectoris and the management of chronic heart failure with reduced ejection fraction in patients with a resting heart rate of at least 70 or 75 beats per minute.

**Closest evidence sentence (by token LCS):**

> It is indicated for the symptomatic treatment of chronic stable angina in adults with CAD with normal sinus rhythm and HR of at least 70 bpm as well as for management of chronic heart failure patients.[COMPOUND] improves coronary blood flow through different mechanisms compared with BBs and this raises the opportunity for combination treatment in patients who remain symptomatic with BB therapy alone.

### CID 71715374 · qa_index 5 · topic `mechanism` · split `test`

- metrics: lcs_tokens=11, ngram5_overlap=12, cos_max=0.897 (answer_len_tokens=40, n_evidence_sentences=181)

**Answer (phase1):**

> The compound is a first-in-class inhibitor of ubiquitin-like modifier activating enzyme 1 (UBA1). It acts as an AMP mimetic that binds the nucleotide-binding site and forms a covalent adduct with ubiquitin, effectively blocking the first step of the ubiquitylation cascade.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is a first-in-class inhibitor of ubiquitin-like modifier activating enzyme 1 that catalyzes ubiquitin activation, the first step in the ubiquitylation cascade.

### CID 3062316 · qa_index 5 · topic `therapeutic_use` · split `val`

- metrics: lcs_tokens=12, ngram5_overlap=12, cos_max=0.687 (answer_len_tokens=33, n_evidence_sentences=500)

**Answer (phase1):**

> It is primarily indicated for the treatment of chronic myeloid leukemia (CML) and Philadelphia chromosome-positive acute lymphoblastic leukemia (Ph+ ALL), particularly in patients who are resistant or intolerant to prior therapies like imatinib.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] (DSB) is a second-generation tyrosine kinase inhibitor widely used for treating chronic myeloid leukemia (CML) and Philadelphia chromosome-positive acute lymphoblastic leukemia (Ph + ALL).

### CID 11750009 · qa_index 6 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.903 (answer_len_tokens=34, n_evidence_sentences=51)

**Answer (phase1):**

> The compound is indicated for the topical treatment of acne vulgaris in patients 12 years of age and older, serving as the first topical hormonal therapy to target the androgenic drivers of the disease.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is an androgen receptor inhibitor which has been approved by the United States Food and Drug Administration for the topical treatment of acne vulgaris in patients 12 years of age and older.

### CID 72720442 · qa_index 5 · topic `engineering` · split `train`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.895 (answer_len_tokens=40, n_evidence_sentences=33)

**Answer (phase1):**

> Cobalt doping enhances the adsorption of Cr(VI) by decreasing electron occupancy in the eg orbitals and reducing the spin state of the iron ions. This electronic modification increases the affinity for anionic pollutants without significantly altering the compound's magnetic properties.

**Closest evidence sentence (by token LCS):**

> Compared to pristine [COMPOUND], cobalt doping significantly enhances the capability of [COMPOUND] to adsorption Cr(VI) by decreasing electron occupancy in the eg orbitals and reducing the spin state of Fe ions.

### CID 6918305 · qa_index 5 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.887 (answer_len_tokens=24, n_evidence_sentences=84)

**Answer (phase1):**

> The compound was first approved for the treatment of seizures associated with cyclin-dependent kinase-like 5 (CDKL5) deficiency disorder (CDD) in pediatric and adult patients.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] received its first approval in March 2022 in the USA for the treatment of seizures associated with cyclin-dependent kinase-like 5 (CDKL5) deficiency disorder (CDD) in patients 2 years of age and older.

### CID 5461123 · qa_index 3 · topic `therapeutic_use` · split `test`

- metrics: lcs_tokens=13, ngram5_overlap=11, cos_max=0.862 (answer_len_tokens=31, n_evidence_sentences=500)

**Answer (phase1):**

> The compound promotes bone healing by enhancing mitochondrial function in macrophages via the Drp1-Mff pathway, which facilitates the transfer of functional mitochondria to endothelial and neuronal cells to restore energy metabolism.

**Closest evidence sentence (by token LCS):**

> The mechanism of [COMPOUND] involves promoting mitochondrial proliferation in macrophages through the upregulation of the Drp1‐Mff pathway, which facilitates the transfer of functional mitochondria to endothelial and neuronal cells.

### CID 44480399 · qa_index 5 · topic `therapeutic_use` · split `test`

- metrics: lcs_tokens=10, ngram5_overlap=11, cos_max=0.828 (answer_len_tokens=28, n_evidence_sentences=500)

**Answer (phase1):**

> The compound is primarily approved for the treatment of adult patients with metastatic colorectal cancer (mCRC) who have previously received standard therapies, including fluoropyrimidine-, oxaliplatin-, and irinotecan-based chemotherapy.

**Closest evidence sentence (by token LCS):**

> AIMS: [COMPOUND] is a selective small molecule tyrosine kinase inhibitor of vascular endothelial growth factor receptor (VEGFR)-1, -2, and -3 recently approved in the United States (US) for the treatment of adult patients with metastatic colorectal cancer (CRC) who have previously been treated with fluoropyrimidine-, oxaliplatin-, and irinotecan-based chemotherapy, an anti-VEGF biological therapy, and if RAS wild-type and medically appropriate, anti-epidermal growth factor receptor therapy.

### CID 54562 · qa_index 29 · topic `mechanism` · split `train`

- metrics: lcs_tokens=13, ngram5_overlap=11, cos_max=0.818 (answer_len_tokens=24, n_evidence_sentences=355)

**Answer (phase1):**

> Yes, the compound can inhibit glutamate efflux in the striatum and attenuate the excitatory effects of NMDA and AMPA receptors in the prefrontal cortex.

**Closest evidence sentence (by token LCS):**

> In addition, [COMPOUND] has been shown to attenuate the excitatory effects of NMDA and AMPA receptors in the prefrontal cortex (Tseng and O’Donnell 2004) and striatum (Cepeda et al. 1993).

### CID 3883 · qa_index 37 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.812 (answer_len_tokens=35, n_evidence_sentences=500)

**Answer (phase1):**

> Clinical evidence suggests that the compound is associated with a significantly lower risk of developing gout compared to other PPIs like omeprazole or pantoprazole, potentially due to its unique effects on adipogenesis and insulin sensitivity.

**Closest evidence sentence (by token LCS):**

> Additionally, research is needed to examine the effects of each type of PPI on gout.ConclusionOur study found that [COMPOUND] is associated with a significantly lower risk of developing gout compared to other PPIs.

### CID 10071196 · qa_index 5 · topic `therapeutic_use` · split `val`

- metrics: lcs_tokens=13, ngram5_overlap=11, cos_max=0.805 (answer_len_tokens=16, n_evidence_sentences=321)

**Answer (phase1):**

> It is approved for the treatment of hallucinations and delusions associated with Parkinson's disease psychosis (PDP).

**Closest evidence sentence (by token LCS):**

> Background: [COMPOUND], a 5-HT2A receptor inverse agonist/antagonist, is the only medication approved by the FDA for the treatment of hallucinations and delusions associated with Parkinson's disease psychosis (PDP).


---

## Cosine > threshold (paraphrase)  — 4068 total, showing top 20

### CID 3001055 · qa_index 21 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=18, ngram5_overlap=14, cos_max=0.984 (answer_len_tokens=22, n_evidence_sentences=500)

**Answer (phase1):**

> The compound is approximately four to ten times more potent than cimetidine on a molar basis in inhibiting stimulated gastric acid secretion.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is four to ten times more potent than cimetidine on a molar basis in inhibiting stimulated gastric acid secretion.

### CID 5505 · qa_index 18 · topic `mechanism` · split `train`

- metrics: lcs_tokens=5, ngram5_overlap=1, cos_max=0.982 (answer_len_tokens=22, n_evidence_sentences=107)

**Answer (phase1):**

> In healthy subjects, somatostatin inhibits the compound-induced insulin release, but it fails to inhibit this release in patients with pancreatic beta-cell tumors.

**Closest evidence sentence (by token LCS):**

> In contrast to its effective inhibition of insulin release in normal subjects, somatostatin, without exception, failed to inhibit [COMPOUND]-induced insulin release in the patients with pancreatic beta-cell tumors.

### CID 443879 · qa_index 28 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=7, ngram5_overlap=4, cos_max=0.980 (answer_len_tokens=23, n_evidence_sentences=500)

**Answer (phase1):**

> The compound is generally better tolerated than oxybutynin, particularly showing a lower incidence and severity of dry mouth while maintaining similar clinical efficacy.

**Closest evidence sentence (by token LCS):**

> Comparative, randomised, double-blind studies show that [COMPOUND] (administered as immediate-release [IR] tablets 2 mg b.i.d.) is as effective as oxybutynin (5 mg t.i.d.) in improving all of the troublesome symptoms of OAB but with a significantly lower incidence and severity of dry mouth.

### CID 65064 · qa_index 24 · topic `mechanism` · split `train`

- metrics: lcs_tokens=9, ngram5_overlap=6, cos_max=0.977 (answer_len_tokens=22, n_evidence_sentences=500)

**Answer (phase1):**

> The compound decreases ET-1 expression and secretion from endothelial cells by stimulating Akt- and AMPK-mediated regulation of the ET-1 promoter via FOXO1.

**Closest evidence sentence (by token LCS):**

> We conclude that [COMPOUND] decreases ET-1 expression and secretion from endothelial cells, in part, via Akt- and AMPK-stimulated FOXO1 regulation of the ET-1 promoter.

### CID 2723816 · qa_index 7 · topic `drug_interactions` · split `train`

- metrics: lcs_tokens=7, ngram5_overlap=3, cos_max=0.973 (answer_len_tokens=24, n_evidence_sentences=10)

**Answer (phase1):**

> Melatonin has been shown to alleviate the circadian rhythm disturbances and pancreatic developmental disorders induced by the compound, likely by modulating the thyroid system.

**Closest evidence sentence (by token LCS):**

> CONCLUSION: Melatonin, while modulating the thyroid system, significantly alleviates [COMPOUND]-induced circadian rhythm disturbances and pancreatic developmental disorders.

### CID 6603945 · qa_index 16 · topic `mechanism` · split `train`

- metrics: lcs_tokens=9, ngram5_overlap=5, cos_max=0.972 (answer_len_tokens=19, n_evidence_sentences=500)

**Answer (phase1):**

> The compound inhibits basolateral 10-pS Cl- channels in the TAL through a cGMP/PKG-dependent signaling pathway initiated by NO release.

**Closest evidence sentence (by token LCS):**

> We concluded that [COMPOUND] inhibited the basolateral 10-pS Cl- channels in the TAL through a cGMP/PKG signaling pathway.

### CID 104817 · qa_index 12 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=6, ngram5_overlap=4, cos_max=0.972 (answer_len_tokens=18, n_evidence_sentences=500)

**Answer (phase1):**

> The compound is frequently utilized as a first-line therapeutic agent to alleviate nausea and vomiting of pregnancy (NVP).

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is frequently utilized as a therapeutic agent for nausea and vomiting of pregnancy (NVP).

### CID 10113978 · qa_index 21 · topic `toxicity` · split `train`

- metrics: lcs_tokens=4, ngram5_overlap=0, cos_max=0.972 (answer_len_tokens=22, n_evidence_sentences=500)

**Answer (phase1):**

> Pneumothorax is a rare but documented pulmonary complication associated with the use of the compound in patients who have pre-existing lung metastases.

**Closest evidence sentence (by token LCS):**

> CONCLUSIONS: Pneumothorax is a rare pulmonary complication after [COMPOUND] use in patients with lung metastasis.

### CID 73078 · qa_index 29 · topic `immunology` · split `train`

- metrics: lcs_tokens=9, ngram5_overlap=5, cos_max=0.972 (answer_len_tokens=21, n_evidence_sentences=500)

**Answer (phase1):**

> The compound inhibits CD28-costimulated T-cell proliferation and cytokine production through a mechanism distinct from cyclosporine, indicating its potential as an immunomodulator.

**Closest evidence sentence (by token LCS):**

> RESULTS: [COMPOUND] inhibited CD28-costimulated T-cell proliferation and cytokine production through a mechanism different from that of cyclosporine.

### CID 26218 · qa_index 21 · topic `mechanism` · split `val`

- metrics: lcs_tokens=4, ngram5_overlap=0, cos_max=0.971 (answer_len_tokens=21, n_evidence_sentences=263)

**Answer (phase1):**

> The compound decreases intracellular leptin content by activating a cAMP/PKA-dependent pathway that enhances the degradation of leptin via the proteasome system.

**Closest evidence sentence (by token LCS):**

> These results indicate that [COMPOUND] decreases the intracellular leptin content by increased degradation via a cAMP/PKA-dependent process involving proteasome activation.

### CID 60753 · qa_index 10 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=6, ngram5_overlap=2, cos_max=0.971 (answer_len_tokens=13, n_evidence_sentences=121)

**Answer (phase1):**

> The compound is generally more effective at terminating atrial flutter than atrial fibrillation.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is more effective in terminating atrial flutter than atrial fibrillation.

### CID 3034034 · qa_index 26 · topic `toxicity` · split `train`

- metrics: lcs_tokens=7, ngram5_overlap=6, cos_max=0.970 (answer_len_tokens=23, n_evidence_sentences=500)

**Answer (phase1):**

> Observational data suggest that use of the compound in COPD patients is associated with an increased risk of acute exacerbations and overall mortality.

**Closest evidence sentence (by token LCS):**

> Conclusion: In the current study, we found an association between the use of [COMPOUND] in patients with COPD and an increased risk of acute exacerbations and death.

### CID 5281616 · qa_index 20 · topic `dermatology` · split `train`

- metrics: lcs_tokens=7, ngram5_overlap=3, cos_max=0.970 (answer_len_tokens=18, n_evidence_sentences=195)

**Answer (phase1):**

> The compound protects against UVB-induced senescence by enhancing SIRT1-mediated p53 deacetylation, thereby reducing dermal aging and cellular senescence.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] treatment mitigates UVB-induced cellular senescence by enhancing SIRT1-mediated p53 deacetylation, thereby inhibiting nuclear translocation and reducing dermal senescence.

### CID 41781 · qa_index 30 · topic `therapeutic_use` · split `test`

- metrics: lcs_tokens=5, ngram5_overlap=1, cos_max=0.970 (answer_len_tokens=28, n_evidence_sentences=369)

**Answer (phase1):**

> In patients with HFpEF, the compound has been associated with reduced rates of rehospitalization for heart failure compared to furosemide, although it does not significantly reduce all-cause mortality.

**Closest evidence sentence (by token LCS):**

> CONCLUSIONS: Compared with furosemide, [COMPOUND] did not significantly reduce all-cause mortality, but there was association between [COMPOUND] and reduced rehospitalization for heart failure in patients with HFpEF.

### CID 11163 · qa_index 14 · topic `solvation` · split `train`

- metrics: lcs_tokens=7, ngram5_overlap=3, cos_max=0.969 (answer_len_tokens=19, n_evidence_sentences=118)

**Answer (phase1):**

> DMSO contributes to the additional strengthening of the water hydrogen bonds within the reinforced hydration sphere surrounding the compound.

**Closest evidence sentence (by token LCS):**

> In the DMSO-[COMPOUND] system, DMSO contributes to the additional strengthening of water hydrogen bonds in the reinforced hydration sphere of [COMPOUND].

### CID 441891 · qa_index 15 · topic `cell_biology` · split `train`

- metrics: lcs_tokens=5, ngram5_overlap=1, cos_max=0.969 (answer_len_tokens=20, n_evidence_sentences=39)

**Answer (phase1):**

> The compound inhibits EMT by upregulating the protein expression of E-cadherin while simultaneously decreasing the expression of N-cadherin and vimentin.

**Closest evidence sentence (by token LCS):**

> Moreover, [COMPOUND] inhibited EMT through increased protein expression of E-cadherin and decreased protein expression of N-cadherin and vimentin.

### CID 5564 · qa_index 28 · topic `toxicity` · split `train`

- metrics: lcs_tokens=9, ngram5_overlap=5, cos_max=0.968 (answer_len_tokens=22, n_evidence_sentences=500)

**Answer (phase1):**

> The compound may adversely affect bone health by disrupting endocrine regulation and energy metabolism, specifically through interference with the PI3K-Akt signaling pathway.

**Closest evidence sentence (by token LCS):**

> Collectively, these results indicate that [COMPOUND] adversely affects bone health by disrupting endocrine regulation and energy metabolism through the PI3K-Akt pathway.

### CID 159287 · qa_index 23 · topic `metabolism` · split `train`

- metrics: lcs_tokens=8, ngram5_overlap=4, cos_max=0.968 (answer_len_tokens=18, n_evidence_sentences=197)

**Answer (phase1):**

> The compound and its glycosides have been shown to inhibit the expression and activity of xanthine oxidase (XO).

**Closest evidence sentence (by token LCS):**

> Overall, the findings suggest that [COMPOUND] can effectively attenuate pain and inflammation induced by osteoarthritis by inhibiting the NF-κB signaling pathway, suppressing proinflammatory cytokine expression, and reducing chondrocyte apoptosis [82].To summarize, [COMPOUND] and its glycosides have been shown to possess anti-inflammatory effects through their radical scavenging activities.

### CID 5280569 · qa_index 8 · topic `mechanism` · split `train`

- metrics: lcs_tokens=5, ngram5_overlap=1, cos_max=0.967 (answer_len_tokens=23, n_evidence_sentences=224)

**Answer (phase1):**

> The compound inhibits Th17 differentiation by repressing the expression and activity of RORγt, the master transcription factor required for the production of IL-17A.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] Inhibits Th17 Differentiation by Suppressing Transcription Factor RORγtSeveral studies have reported a relation between IL-17 and IPF.

### CID 2366 · qa_index 12 · topic `toxicity` · split `train`

- metrics: lcs_tokens=4, ngram5_overlap=0, cos_max=0.967 (answer_len_tokens=21, n_evidence_sentences=316)

**Answer (phase1):**

> The compound is contraindicated in patients with pheochromocytoma and should be used with caution in those with asthma or peptic ulcers.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is contraindicated in pheochromocytoma, and care is required for its use in subjects with asthma and peptic ulcer.


---

## Co-flagged (ngram ∩ cos) — composite egregiousness  — 320 total, showing top 20

### CID 3001055 · qa_index 21 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=18, ngram5_overlap=14, cos_max=0.984 (answer_len_tokens=22, n_evidence_sentences=500)

**Answer (phase1):**

> The compound is approximately four to ten times more potent than cimetidine on a molar basis in inhibiting stimulated gastric acid secretion.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is four to ten times more potent than cimetidine on a molar basis in inhibiting stimulated gastric acid secretion.

### CID 16129665 · qa_index 21 · topic `metabolism` · split `val`

- metrics: lcs_tokens=19, ngram5_overlap=15, cos_max=0.914 (answer_len_tokens=22, n_evidence_sentences=500)

**Answer (phase1):**

> The liver plays a major role in the degradation of plasma cyclic AMP produced by target tissues responding to the compound's stimulation.

**Closest evidence sentence (by token LCS):**

> The results reported here suggest that the liver plays a major role in the degradation of plasma cyclic AMP produced by target tissues responding to [COMPOUND], and in the release of cyclic AMP under glucagon.

### CID 65866 · qa_index 7 · topic `therapeutic_use` · split `val`

- metrics: lcs_tokens=11, ngram5_overlap=9, cos_max=0.952 (answer_len_tokens=25, n_evidence_sentences=19)

**Answer (phase1):**

> The compound demonstrates comparable effectiveness to amlodipine in preventing major adverse cardiovascular events (MACE) in hypertensive patients, while potentially offering a more favorable side-effect profile.

**Closest evidence sentence (by token LCS):**

> This study aims to compare the effectiveness of [COMPOUND] and amlodipine in preventing major adverse cardiovascular events (MACE) in hypertensive patients.

### CID 65064 · qa_index 24 · topic `mechanism` · split `train`

- metrics: lcs_tokens=9, ngram5_overlap=6, cos_max=0.977 (answer_len_tokens=22, n_evidence_sentences=500)

**Answer (phase1):**

> The compound decreases ET-1 expression and secretion from endothelial cells by stimulating Akt- and AMPK-mediated regulation of the ET-1 promoter via FOXO1.

**Closest evidence sentence (by token LCS):**

> We conclude that [COMPOUND] decreases ET-1 expression and secretion from endothelial cells, in part, via Akt- and AMPK-stimulated FOXO1 regulation of the ET-1 promoter.

### CID 65575 · qa_index 18 · topic `mechanism` · split `train`

- metrics: lcs_tokens=19, ngram5_overlap=15, cos_max=0.881 (answer_len_tokens=29, n_evidence_sentences=123)

**Answer (phase1):**

> Reverse pharmacophore mapping suggests that the compound may interact with proviral integration Moloney virus kinase (PIM1), vascular endothelial growth factor receptor 2 (VEGFR2), and c-Jun N-terminal kinase 1 (JNK1).

**Closest evidence sentence (by token LCS):**

> The results of PharmMapper analysis indicated that three kinases could be potential targets for [COMPOUND]: proviral integration Moloney virus kinase (PIM1), vascular endothelial growth factor receptor 2 (VEGFR2), and c-Jun N-terminal kinase 1 (JNK1) (Table 5).

### CID 71542153 · qa_index 5 · topic `mechanism` · split `train`

- metrics: lcs_tokens=13, ngram5_overlap=9, cos_max=0.939 (answer_len_tokens=39, n_evidence_sentences=107)

**Answer (phase1):**

> The compound is a selective inhibitor of aldo-keto reductase family 1 member C3 (AKR1C3). It is designed to treat endometriosis by blocking the local production of potent androgens and estrogens in endometriotic lesions without disrupting the systemic endocrine cycle.

**Closest evidence sentence (by token LCS):**

> INTRODUCTION: [COMPOUND] is a selective inhibitor of aldo-keto reductase family 1 member C3 (AKR1C3), an enzyme implicated in the pathology of endometriosis and other disorders.

### CID 3034034 · qa_index 26 · topic `toxicity` · split `train`

- metrics: lcs_tokens=7, ngram5_overlap=6, cos_max=0.970 (answer_len_tokens=23, n_evidence_sentences=500)

**Answer (phase1):**

> Observational data suggest that use of the compound in COPD patients is associated with an increased risk of acute exacerbations and overall mortality.

**Closest evidence sentence (by token LCS):**

> Conclusion: In the current study, we found an association between the use of [COMPOUND] in patients with COPD and an increased risk of acute exacerbations and death.

### CID 442534 · qa_index 25 · topic `mechanism` · split `val`

- metrics: lcs_tokens=13, ngram5_overlap=9, cos_max=0.935 (answer_len_tokens=26, n_evidence_sentences=184)

**Answer (phase1):**

> The compound promotes RCT by stimulating cholesterol efflux from macrophages via the liver X receptor alpha (LXR-alpha) pathway and increasing levels of HDL-C and apolipoprotein A-I.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] may promote RCT by stimulating cholesterol efflux from macrophages via the liver X receptor alpha pathway, enhancing serum high-density lipoprotein cholesterol and apolipoprotein A-I levels, and regulating key genes in hepatic and intestinal RCT.

### CID 3026 · qa_index 21 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=10, ngram5_overlap=7, cos_max=0.955 (answer_len_tokens=29, n_evidence_sentences=225)

**Answer (phase1):**

> The compound has been investigated as a purging agent for autologous bone marrow transplantation in leukemia patients due to its ability to preferentially suppress the growth of leukemic cells.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] showed preferential suppression of the growth of leukemic cells and could be used as a purging agent for autologous bone marrow transplantation in the treatment of leukemia.

### CID 644019 · qa_index 7 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=14, ngram5_overlap=10, cos_max=0.924 (answer_len_tokens=23, n_evidence_sentences=500)

**Answer (phase1):**

> The compound is FDA-approved for the treatment of seizures associated with Lennox-Gastaut syndrome, Dravet syndrome, and tuberous sclerosis complex, particularly in pediatric populations.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] (CBD), a major cannabinoid found in Cannabis sativa L., has been used in the treatment of seizures associated with Lennox-Gastaut syndrome, Dravet syndrome, and tuberous sclerosis complex.

### CID 10113978 · qa_index 5 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=7, ngram5_overlap=8, cos_max=0.943 (answer_len_tokens=24, n_evidence_sentences=500)

**Answer (phase1):**

> The compound is approved for the treatment of advanced or metastatic renal cell carcinoma (mRCC) and advanced soft tissue sarcomas (STS), particularly non-adipocytic subtypes.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is approved for the treatment of patients with metastatic renal cell carcinoma (mRCC) and second line metastatic soft-tissue sarcomas (STS).

### CID 6603945 · qa_index 16 · topic `mechanism` · split `train`

- metrics: lcs_tokens=9, ngram5_overlap=5, cos_max=0.972 (answer_len_tokens=19, n_evidence_sentences=500)

**Answer (phase1):**

> The compound inhibits basolateral 10-pS Cl- channels in the TAL through a cGMP/PKG-dependent signaling pathway initiated by NO release.

**Closest evidence sentence (by token LCS):**

> We concluded that [COMPOUND] inhibited the basolateral 10-pS Cl- channels in the TAL through a cGMP/PKG signaling pathway.

### CID 73078 · qa_index 29 · topic `immunology` · split `train`

- metrics: lcs_tokens=9, ngram5_overlap=5, cos_max=0.972 (answer_len_tokens=21, n_evidence_sentences=500)

**Answer (phase1):**

> The compound inhibits CD28-costimulated T-cell proliferation and cytokine production through a mechanism distinct from cyclosporine, indicating its potential as an immunomodulator.

**Closest evidence sentence (by token LCS):**

> RESULTS: [COMPOUND] inhibited CD28-costimulated T-cell proliferation and cytokine production through a mechanism different from that of cyclosporine.

### CID 54697325 · qa_index 6 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=18, ngram5_overlap=14, cos_max=0.879 (answer_len_tokens=20, n_evidence_sentences=224)

**Answer (phase1):**

> It is approved for the treatment of community-acquired bacterial pneumonia (CABP) and acute bacterial skin and skin structure infections (ABSSSI).

**Closest evidence sentence (by token LCS):**

> There is now increasing momentum toward developing and studying novel drugs or drug combinations for treating Mab disease, evidenced by the emergence of new chemical entities in preclinical stages and ongoing clinical trials.[COMPOUND] is an aminomethylcycline that is FDA approved for the treatment of community-acquired bacterial pneumonia (CABP) and acute bacterial skin and skin structure infections (ABSSSI).

### CID 443879 · qa_index 28 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=7, ngram5_overlap=4, cos_max=0.980 (answer_len_tokens=23, n_evidence_sentences=500)

**Answer (phase1):**

> The compound is generally better tolerated than oxybutynin, particularly showing a lower incidence and severity of dry mouth while maintaining similar clinical efficacy.

**Closest evidence sentence (by token LCS):**

> Comparative, randomised, double-blind studies show that [COMPOUND] (administered as immediate-release [IR] tablets 2 mg b.i.d.) is as effective as oxybutynin (5 mg t.i.d.) in improving all of the troublesome symptoms of OAB but with a significantly lower incidence and severity of dry mouth.

### CID 71715374 · qa_index 5 · topic `mechanism` · split `test`

- metrics: lcs_tokens=11, ngram5_overlap=12, cos_max=0.897 (answer_len_tokens=40, n_evidence_sentences=181)

**Answer (phase1):**

> The compound is a first-in-class inhibitor of ubiquitin-like modifier activating enzyme 1 (UBA1). It acts as an AMP mimetic that binds the nucleotide-binding site and forms a covalent adduct with ubiquitin, effectively blocking the first step of the ubiquitylation cascade.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is a first-in-class inhibitor of ubiquitin-like modifier activating enzyme 1 that catalyzes ubiquitin activation, the first step in the ubiquitylation cascade.

### CID 5564 · qa_index 28 · topic `toxicity` · split `train`

- metrics: lcs_tokens=9, ngram5_overlap=5, cos_max=0.968 (answer_len_tokens=22, n_evidence_sentences=500)

**Answer (phase1):**

> The compound may adversely affect bone health by disrupting endocrine regulation and energy metabolism, specifically through interference with the PI3K-Akt signaling pathway.

**Closest evidence sentence (by token LCS):**

> Collectively, these results indicate that [COMPOUND] adversely affects bone health by disrupting endocrine regulation and energy metabolism through the PI3K-Akt pathway.

### CID 11750009 · qa_index 6 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=15, ngram5_overlap=11, cos_max=0.903 (answer_len_tokens=34, n_evidence_sentences=51)

**Answer (phase1):**

> The compound is indicated for the topical treatment of acne vulgaris in patients 12 years of age and older, serving as the first topical hormonal therapy to target the androgenic drivers of the disease.

**Closest evidence sentence (by token LCS):**

> [COMPOUND] is an androgen receptor inhibitor which has been approved by the United States Food and Drug Administration for the topical treatment of acne vulgaris in patients 12 years of age and older.

### CID 6549 · qa_index 37 · topic `therapeutic_use` · split `train`

- metrics: lcs_tokens=10, ngram5_overlap=6, cos_max=0.954 (answer_len_tokens=20, n_evidence_sentences=500)

**Answer (phase1):**

> When loaded into zinc oxide nanocomposites, the compound has demonstrated in vitro and in vivo antileishmanial effects against Leishmania major.

**Closest evidence sentence (by token LCS):**

> This study aimed to produce [COMPOUND] loaded zinc oxide nanocomposite (LZNPs) and assess its in vitro and in vivo antileishmanial effects against Leishmania major.

### CID 3845 · qa_index 24 · topic `metabolism` · split `train`

- metrics: lcs_tokens=12, ngram5_overlap=8, cos_max=0.932 (answer_len_tokens=19, n_evidence_sentences=500)

**Answer (phase1):**

> Kynurenine aminotransferase II (KAT II) is the principal enzyme responsible for the synthesis of the compound in the brain.

**Closest evidence sentence (by token LCS):**

> In the mammalian brain, kynurenine aminotransferase II (KAT II) is the principal enzyme responsible for the neosynthesis of rapidly mobilizable [COMPOUND], and therefore constitutes an attractive target for pro-cognitive interventions.
