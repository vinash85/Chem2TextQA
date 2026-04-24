# Task 2 — Multi-judge LLM panel on Phase-3 verdicts

## Headline: does Gemma look noisy?

- Evaluable rows (all 4 judges voted + Gemma): **1000 / 1000**
- Rows where **majority of the 3 new judges disagrees with Gemma**: **47** (4.7 %)
- Verdict: **WITHIN** the 15 % threshold. **>15 % → gold subset noisier than claimed.**

## Per-judge verdict distribution

| judge | agree | disagree | unclear | err / missing | total |
|---|---:|---:|---:|---:|---:|
| gemma | 500 | 469 | 31 | 0 | 1000 |
| sonnet | 499 | 466 | 12 | 23 | 1000 |
| gpt5 | 509 | 453 | 38 | 0 | 1000 |
| gemini | 495 | 487 | 18 | 0 | 1000 |

## Pairwise Cohen's κ

| judge pair | n | κ |
|---|---:|---:|
| gemma × sonnet | 977 | 0.882 |
| gemma × gpt5 | 1000 | 0.882 |
| gemma × gemini | 1000 | 0.893 |
| sonnet × gpt5 | 977 | 0.830 |
| sonnet × gemini | 977 | 0.855 |
| gpt5 × gemini | 1000 | 0.869 |
| **Gemma-vs-panel avg** | — | **0.885** |

**Krippendorff's α (nominal, 4 judges):** 0.868

## Majority-disagrees-with-Gemma, broken down by Gemma's original verdict

| Gemma verdict | n | majority disagrees | rate |
|---|---:|---:|---:|
| agree | 500 | 21 | 4.2 % |
| disagree | 469 | 16 | 3.4 % |
| unclear | 31 | 10 | 32.3 % |

## Majority-disagrees rate — top 20 topics by sample size

| topic | n | majority disagrees | rate |
|---|---:|---:|---:|
| stereochemistry | 105 | 4 | 3.8 % |
| physicochemical | 93 | 6 | 6.5 % |
| composition | 85 | 7 | 8.2 % |
| engineering | 84 | 5 | 6.0 % |
| functional_groups | 76 | 4 | 5.3 % |
| scaffold | 72 | 4 | 5.6 % |
| pharmacophore | 62 | 3 | 4.8 % |
| reactivity | 57 | 2 | 3.5 % |
| mechanism | 57 | 1 | 1.8 % |
| therapeutic_use | 44 | 0 | 0.0 % |
| toxicity | 41 | 0 | 0.0 % |
| metabolism | 40 | 1 | 2.5 % |
| electronics | 38 | 3 | 7.9 % |
| adme | 37 | 3 | 8.1 % |
| shape_sterics | 21 | 1 | 4.8 % |
| design_levers | 18 | 0 | 0.0 % |
| druglikeness | 17 | 1 | 5.9 % |
| drug_interactions | 13 | 0 | 0.0 % |
| biosynthesis | 2 | 0 | 0.0 % |
| industrial_application | 2 | 0 | 0.0 % |

## 20 qualitative disagreements (sampled from 47)

### Example 1 — cid 1567, qa_index 18 (topic: mechanism)

**Question:** How does the compound affect the enzymatic activity of certain cysteine proteinases?

**Phase-1 answer:** It can act as a stimulator or activator for enzymes that require a reduced sulfhydryl group in their active site for catalytic function.

**Phase-2 answer:** The compound, a simple thiol containing both hydroxyl and sulfhydryl groups, serves as a model thiol for studying cysteine proteinase active-site chemistry. Its reactivity profile with these enzymes provides insight into catalytic-site solvation properties, with the ratio of its reaction kinetics relative to other thiol probes varying markedly across different cysteine proteinases such as papaya peptidase A, actinidin, ficin, and papain. This variation reflects differences in the electrostatic e

| judge | verdict | reasoning |
|---|---|---|
| gemma | unclear | Answer 1 claims the compound acts as a stimulator/activator, whereas Answer 2 describes it as a model thiol used to study reaction kinetics and active-site chemistry without explicitly stating whether it activates or inhibits the enzymes. |
| sonnet | agree | Both answers agree that the compound interacts with cysteine proteinases through their active-site sulfhydryl (cysteine) groups. Answer 1 focuses on its role as an activator/stimulator for enzymes requiring reduced sulfhydryl groups, while Answer 2 provides more detail about its use as a model thiol probe to study active-site chemistry. Both are consistent in describing the compound's interaction  |
| gpt5 | unclear | Answer 1 claims the compound stimulates/activates cysteine proteinases, while Answer 2 describes its use as a reactive thiol probe with variable kinetics and does not address activation. They cover different aspects without a clear, matching conclusion. |
| gemini | agree | Both answers describe the compound's interaction with the active site of cysteine proteinases. Answer 1 states the outcome is stimulation/activation, while Answer 2 explains its use as a model compound to study the reactivity of that same active site. These are complementary, not contradictory, descriptions of the same underlying chemical interaction. |

### Example 2 — cid 16213884, qa_index 24 (topic: adme)

**Question:** Does the compound cross the blood-brain barrier (BBB)?

**Phase-1 answer:** While the compound itself is a major constituent of brain tissue, it is also used in intranasal formulations to enhance the delivery of drugs from the nose to the brain.

**Phase-2 answer:** The compound is a phosphatidylcholine-based phospholipid with two long fatty acyl chains (palmitoyl and linoleoyl/oleoyl) and a zwitterionic headgroup. Its molecular weight of ~758 Da and highly lipophilic character (logP estimated >8) make passive diffusion across the blood-brain barrier unlikely. However, the compound is widely employed as a formulation excipient in brain-targeting drug delivery systems, including intranasal polymeric micelles and lipid-polymer hybrid nanoparticles designed to

| judge | verdict | reasoning |
|---|---|---|
| gemma | unclear | Answer 1 implies the compound is present in the brain but does not explicitly state if it crosses the BBB. Answer 2 explicitly states that passive diffusion across the BBB is unlikely. |
| sonnet | agree | Both answers agree that the compound itself does not readily cross the BBB on its own, but is used as an excipient in intranasal/nose-to-brain drug delivery formulations to enhance CNS delivery of co-administered drugs. |
| gpt5 | unclear | Answer 2 states the compound is unlikely to cross the BBB by passive diffusion, while Answer 1 does not directly address BBB permeability—it notes brain presence and intranasal use to enhance drug delivery. Since Answer 1 doesn’t take a clear position on BBB crossing, agreement cannot be determined. |
| gemini | agree | Both answers reach the same conclusion: the compound's primary relevance to the blood-brain barrier is its use as a formulation excipient to help other drugs cross, rather than crossing effectively on its own. Answer 2 provides more detail, stating that passive diffusion is unlikely, which is consistent with the role described in both answers. |

### Example 3 — cid 44176376, qa_index 1 (topic: composition)

**Question:** What is the degree of unsaturation for the compound, and how is it distributed?

**Phase-1 answer:** The compound has a degree of unsaturation of 2. This is accounted for by one carbon-carbon double bond in the long-chain base and one carbon-oxygen double bond in the amide linkage.

**Phase-2 answer:** The compound has two degrees of unsaturation: one carbon-carbon double bond in the N-acyl chain (trans-alkene, C13=C14) and one carbonyl group in the N-formyl substituent on the sphingosine backbone. The long-chain base contains no additional unsaturation, and the phosphocholine head group is fully saturated.

| judge | verdict | reasoning |
|---|---|---|
| gemma | agree | Both answers agree that the degree of unsaturation is 2, consisting of one carbon-carbon double bond and one carbon-oxygen double bond (carbonyl). |
| sonnet | agree | Both answers agree that the compound has 2 degrees of unsaturation: one C=C double bond and one C=O (carbonyl) group. They differ slightly in which part of the molecule contains the carbonyl (amide linkage vs. N-formyl substituent), but both identify the same two types of unsaturation contributing to the total degree of 2. |
| gpt5 | disagree | Both state a total degree of unsaturation of 2, but they place the unsaturations in different parts of the molecule (C=C in long-chain base vs N-acyl chain; carbonyl in amide linkage vs N-formyl group), so the distribution conflicts. |
| gemini | disagree | While both answers agree on the total degree of unsaturation (2), they contradict each other on the location of the carbon-carbon double bond. Answer 1 places it in the 'long-chain base', whereas Answer 2 places it in the 'N-acyl chain' and explicitly states the long-chain base has no unsaturation. |

### Example 4 — cid 564, qa_index 17 (topic: reactivity)

**Question:** Is the compound susceptible to nucleophilic attack under physiological conditions?

**Phase-1 answer:** No, the carboxylic acid and primary amine are stable; the compound lacks highly reactive electrophilic centers or strained rings.

**Phase-2 answer:** The compound contains a primary amine and a carboxylic acid, which exist predominantly as a zwitterion (ammonium carboxylate) at physiological pH. The carboxylic acid carbonyl is electron-deficient and susceptible to nucleophilic attack, though the negative charge on the carboxylate reduces its electrophilicity compared to a protonated acid. The primary amine, being protonated at pH 7.4, is not nucleophilic under these conditions. The compound's role as a plasminogen-binding antagonist relies on

| judge | verdict | reasoning |
|---|---|---|
| gemma | disagree | Answer 1 explicitly states the compound is not susceptible to nucleophilic attack, whereas Answer 2 states the carboxylic acid carbonyl is susceptible to nucleophilic attack, albeit with reduced electrophilicity. |
| sonnet | disagree | Answer 1 concludes the compound lacks highly reactive electrophilic centers and is not susceptible to nucleophilic attack, while Answer 2 states the carboxylic acid carbonyl is electron-deficient and susceptible to nucleophilic attack (albeit reduced by the carboxylate charge). These are contradictory conclusions on the main claim. |
| gpt5 | agree | Both conclude the compound is not meaningfully susceptible to nucleophilic attack under physiological conditions. Answer 2 notes theoretical carbonyl susceptibility but emphasizes that at pH 7.4 the carboxylate is deactivated and the amine is protonated, aligning with Answer 1’s overall ‘no’ assessment. |
| gemini | agree | Both answers conclude that the compound is not significantly susceptible to nucleophilic attack under physiological conditions. Answer 1 states this directly, while Answer 2 provides a more detailed explanation, noting that the potential electrophilic center (carbonyl) has its reactivity greatly reduced at physiological pH, leading to the same practical conclusion. |

### Example 5 — cid 442126, qa_index 21 (topic: metabolism)

**Question:** Does the compound inhibit cytochrome P450 enzymes or other metabolic enzymes?

**Phase-1 answer:** The compound is a highly potent and selective reversible inhibitor of human monoamine oxidase A (MAO-A), with an IC50 comparable to clinical antidepressants like toloxatone.

**Phase-2 answer:** The compound is a pyranocoumarin featuring a coumarin lactone fused to a dihydropyran ring with an angelate ester side chain. While the SMILES reveals no structural features that would inherently suggest direct cytochrome P450 inhibition (such as azole moieties or furan rings known for mechanism-based inactivation), the evidence indicates it undergoes substantial hepatic first-pass metabolism, being rapidly converted to its metabolite decursinol. This metabolic lability and its demonstrated inte

| judge | verdict | reasoning |
|---|---|---|
| gemma | unclear | Answer 1 focuses specifically on the inhibition of MAO-A, while Answer 2 discusses the lack of evidence for CYP450 inhibition and mentions interactions with other enzymes like COX and MMPs. They address different enzyme classes and do not provide a common point of comparison regarding the main question. |
| sonnet | disagree | Answer 1 identifies the compound as a MAO-A inhibitor, while Answer 2 describes a pyranocoumarin (decursin-like compound) with potential CYP450 and other enzyme interactions but no established MAO-A inhibition. The two answers describe entirely different compounds and different enzyme inhibition profiles. |
| gpt5 | unclear | Answer 1 asserts strong inhibition of MAO-A (a metabolic enzyme), while Answer 2 says CYP inhibition is not established and only suggests possible broader enzyme interactions without addressing MAO-A. They don’t directly contradict but don’t clearly align on the main claim. |
| gemini | agree | Both answers agree that the compound interacts with metabolic enzymes other than cytochrome P450. Answer 1 is highly specific, identifying it as a potent inhibitor of MAO-A, while Answer 2 discusses its metabolism and interactions with other enzymes more broadly, which is consistent with the claim in Answer 1. |

### Example 6 — cid 3016738, qa_index 1 (topic: composition)

**Question:** What are the primary structural features and molecular weight of the compound?

**Phase-1 answer:** The compound is a substituted pyridine derivative with a molecular weight of 124.06 Da. It consists of a pyridine ring substituted with a methoxy group and a primary amine group at the 2 and 3 positions, respectively.

**Phase-2 answer:** The compound is a 3-methoxypyridin-2-amine featuring a pyridine ring substituted with a methoxy group at the 3-position and an amino group at the 2-position, with a molecular weight of 124.06 g/mol.

| judge | verdict | reasoning |
|---|---|---|
| gemma | agree | Both answers identify the compound as a pyridine derivative with a methoxy group and an amine group at the 2 and 3 positions, and both report the same molecular weight of 124.06. |
| sonnet | agree | Both answers describe the same compound: a pyridine ring with a methoxy group and an amino group, with a molecular weight of 124.06. The only minor difference is the order in which the substituent positions are described, but both agree on the 2-amino and 3-methoxy substitution pattern. |
| gpt5 | disagree | They agree on the molecular weight (124.06) but assign opposite positions for the substituents: Answer 1 places methoxy at C2 and amine at C3, while Answer 2 places methoxy at C3 and amine at C2. |
| gemini | disagree | The answers contradict each other on the positions of the substituents. Answer 1 states the methoxy group is at position 2 and the amine at position 3, while Answer 2 states the methoxy group is at position 3 and the amine at position 2. |

### Example 7 — cid 104150, qa_index 4 (topic: physicochemical)

**Question:** How do the rotatable bonds in this molecule influence its physical state and binding profile?

**Phase-1 answer:** With 8 rotatable bonds, the compound is highly flexible, which typically results in a liquid state at room temperature and allows it to adopt multiple conformations to fit into the hydrophobic pockets of various insect chemosensory receptors.

**Phase-2 answer:** The compound possesses six rotatable bonds (four C–C single bonds in the butyl chain, one N–C bond, and one ester C–O bond), conferring high conformational flexibility. This flexibility allows the molecule to adopt diverse geometries, contributing to its liquid physical state at ambient temperature and enabling adaptive binding to multiple target sites through induced-fit mechanisms.

| judge | verdict | reasoning |
|---|---|---|
| gemma | disagree | The answers disagree on the number of rotatable bonds, with Answer 1 stating there are 8 and Answer 2 stating there are 6. |
| sonnet | — |  |
| gpt5 | agree | Despite differing on the exact rotatable bond count (8 vs 6), both answers conclude that high conformational flexibility leads to a liquid state at room temperature and enables adaptive/induced-fit binding to receptor sites. |
| gemini | agree | Both answers agree on the main conclusions: the molecule's high number of rotatable bonds confers flexibility, which results in a liquid physical state and allows it to adapt its shape for binding to biological targets. They disagree on the exact count of rotatable bonds (8 vs. 6), but this is a difference in a supporting detail, not the primary claim about the influence of these bonds. |

### Example 8 — cid 71158, qa_index 34 (topic: adme)

**Question:** How is the compound's absorption affected by food?

**Phase-1 answer:** The oral absorption of the compound is relatively poor and can be further decreased when taken with food, which is a factor in its complex dosing requirements.

**Phase-2 answer:** The compound contains a free sulfonic acid group (S(=O)(=O)O), which is highly polar and ionized at physiological pH, and an acetamide moiety. These features render the molecule hydrophilic with low lipophilicity, characteristics that typically result in poor passive absorption across biological membranes. The structural similarity to amino acids and the presence of the acetylated amine suggest it may utilize active transport mechanisms for absorption. The compound is administered as a calcium s

| judge | verdict | reasoning |
|---|---|---|
| gemma | unclear | Answer 1 explicitly states that food decreases absorption, whereas Answer 2 only speculates that food 'may not significantly enhance' bioavailability based on the dosing regimen, without confirming a decrease. |
| sonnet | disagree | Answer 1 states that food decreases absorption, while Answer 2 suggests food may not significantly enhance bioavailability but does not indicate food decreases absorption. These represent different conclusions about the direction of food's effect on absorption. |
| gpt5 | unclear | Answer 1 states food decreases absorption, while Answer 2 only suggests that food may not enhance bioavailability without stating a decrease. The conclusions are not directly aligned. |
| gemini | agree | Both answers agree that the compound has poor or modest oral absorption. Regarding the effect of food, Answer 1 states that absorption is decreased by food, while Answer 2 infers that food does not significantly enhance bioavailability. These two statements are consistent and lead to the same conclusion that food does not improve the compound's absorption. |

### Example 9 — cid 7947, qa_index 7 (topic: synthetic_utility)

**Question:** In what capacity does the compound serve in the synthesis of complex organometallic or macrocyclic complexes?

**Phase-1 answer:** The compound can function as a non-coordinating or weakly coordinating solvent/reagent that facilitates the formation of binuclear metal complexes, such as mu-oxo bis-Fe(III) species. Its symmetric, hydrophobic nature makes it suitable for stabilizing large macrocyclic structures during oxidation or metal-insertion steps.

**Phase-2 answer:** The compound, a trimethylbenzene derivative with three methyl substituents on an aromatic ring, serves as a sterically hindered, electron-rich aromatic core in the construction of C3-symmetric ligands and macrocyclic architectures. Its symmetric 1,3,5-trimethyl substitution pattern provides a rigid, planar scaffold for positioning functional groups in a three-fold symmetric arrangement, while the methyl groups offer both steric protection and handles for further functionalization. In organometal

| judge | verdict | reasoning |
|---|---|---|
| gemma | agree | Both answers agree that the compound is used to facilitate the synthesis and stabilization of macrocyclic complexes and organometallic species, specifically highlighting its role in providing symmetry and stability. |
| sonnet | disagree | Answer 1 describes the compound as a non-coordinating/weakly coordinating solvent or reagent that stabilizes binuclear metal complexes, while Answer 2 describes it as an electron-rich aromatic core that serves as a C3-symmetric ligand scaffold with direct coordination to metal centers. These are fundamentally different roles in organometallic synthesis. |
| gpt5 | disagree | Answer 1 frames the compound as a non/weakly coordinating solvent facilitating complex formation, whereas Answer 2 presents it as a ligand/scaffold (C3-symmetric core) that can coordinate and be functionalized. These are different, conflicting roles. |
| gemini | disagree | The answers describe fundamentally different roles for the compound. Answer 1 claims it acts as a non-coordinating or weakly coordinating solvent, while Answer 2 claims it serves as an electron-rich structural core that is incorporated into ligands and facilitates coordination to metals. |

### Example 10 — cid 6337004, qa_index 1 (topic: composition)

**Question:** What is the elemental composition and stoichiometry of the compound?

**Phase-1 answer:** The compound is an inorganic arsenic sulfide consisting of two arsenic atoms and three sulfur atoms, corresponding to the molecular formula As2S3 (represented here as As2H6S3 in its hydrated or protonated form). It has a molecular weight of approximately 251.81 g/mol.

**Phase-2 answer:** The compound has the molecular formula As₂H₆S₃, indicating a stoichiometry of 2 arsenic atoms, 6 hydrogen atoms, and 3 sulfur atoms. The SMILES representation (S.S.S.[As].[As]) suggests a structure containing elemental sulfur and arsenic components, consistent with an arsenic sulfide mineral phase. This composition reflects a reduced arsenic-sulfur compound where arsenic is present in a low oxidation state, capable of participating in redox transformations and acid mine drainage generation under

| judge | verdict | reasoning |
|---|---|---|
| gemma | agree | Both answers identify the same elemental composition and stoichiometry (2 arsenic, 6 hydrogen, and 3 sulfur atoms), with Answer 1 explicitly linking the formula As2H6S3 to the arsenic sulfide As2S3. |
| sonnet | disagree | Answer 1 treats As2H6S3 as a hydrated/protonated form of As2S3 and emphasizes the core As2S3 formula, while Answer 2 treats As2H6S3 as the actual molecular formula with 6 hydrogen atoms as a distinct component. They disagree on whether hydrogen is a meaningful part of the compound's composition or just an artifact of representation. |
| gpt5 | disagree | Answer 1 identifies the composition as As2S3 (no hydrogen), while Answer 2 states the molecular formula is As2H6S3 (including six hydrogens). These are different stoichiometries. |
| gemini | agree | Both answers identify the same molecular formula, As₂H₆S₃, and agree on the stoichiometry of 2 arsenic atoms, 6 hydrogen atoms, and 3 sulfur atoms. Answer 1 provides additional context by relating this to the simpler inorganic compound As2S3, but this does not contradict the core compositional data presented in both answers. |

### Example 11 — cid 135405876, qa_index 6 (topic: electronics)

**Question:** Discuss the aromaticity and conjugation within the pteridine system of the compound.

**Phase-1 answer:** The pteridine system is a fused heterocyclic aromatic system consisting of a pyrimidine ring fused to a pyrazine ring, providing a highly conjugated, electron-deficient pi-system that is essential for binding to enzymes like dihydrofolate reductase.

**Phase-2 answer:** The compound contains a pteridine bicyclic system (pyrazino[2,3-d]pyrimidine) formed by fusion of a pyrazine and pyrimidine ring. The pteridine core exhibits partial aromaticity: the pyrimidine ring maintains aromatic character with 6 π-electrons following Hückel's rule, while the pyrazine ring contributes to an extended conjugated π-system across the fused bicyclic framework. The C=O at position 4 and the amino substituent at position 2 participate in resonance structures that delocalize electr

| judge | verdict | reasoning |
|---|---|---|
| gemma | agree | Both answers agree that the pteridine system is a fused bicyclic system consisting of a pyrimidine and a pyrazine ring that forms a conjugated, aromatic pi-system. |
| sonnet | agree | Both answers agree that the pteridine system consists of fused pyrimidine and pyrazine rings forming an aromatic, conjugated π-system. Answer 2 provides significantly more detail (resonance effects, substituent contributions, extended conjugation), but the core claims about the bicyclic aromatic heterocyclic system are consistent with Answer 1's description. |
| gpt5 | disagree | Answer 1 describes the pteridine as an overall fused aromatic system, while Answer 2 claims only partial aromaticity with the pyrimidine ring aromatic and the pyrazine ring merely contributing to conjugation. They conflict on the extent of aromaticity. |
| gemini | disagree | The answers contradict each other on the nature of the pteridine system's aromaticity. Answer 1 describes it as a fully aromatic system, whereas Answer 2 specifies that it exhibits only partial aromaticity, with the pyrimidine ring being aromatic but the overall fused system not being fully so. |

### Example 12 — cid 138622158, qa_index 5 (topic: physicochemical)

**Question:** How do the structural features of the compound contribute to its onset of action compared to traditional proton pump inhibitors?

**Phase-1 answer:** Unlike prodrug-type irreversible proton pump inhibitors that require acid activation, this compound's basic imidazo[1,2-a]pyridine scaffold and competitive binding mechanism allow it to inhibit the H+/K+-ATPase directly. This structural independence from acid-catalyzed activation results in a significantly faster onset of action.

**Phase-2 answer:** The compound contains a pyrrolo[2,3-d]pyrimidine core with an azetidine carboxamide moiety and a 2,6-dimethylbenzylamine substituent. The planar heterocyclic scaffold enables tight binding to the proton pump's potassium-binding site, while the compact, lipophilic benzylamine group facilitates rapid membrane penetration. Unlike traditional proton pump inhibitors that require acid activation and covalent binding, this structure allows direct, reversible, competitive inhibition of the H+/K+-ATPase,

| judge | verdict | reasoning |
|---|---|---|
| gemma | agree | Both answers conclude that the compound has a faster onset of action because it inhibits the H+/K+-ATPase directly and competitively, bypassing the need for acid activation required by traditional PPIs. |
| sonnet | disagree | The two answers describe different core scaffolds: Answer 1 identifies an imidazo[1,2-a]pyridine scaffold (consistent with potassium-competitive acid blockers like vonoprazan), while Answer 2 describes a pyrrolo[2,3-d]pyrimidine core with an azetidine carboxamide moiety, indicating they are discussing different compounds. Although both agree on the faster onset via direct, reversible inhibition co |
| gpt5 | agree | Both answers conclude that the compound acts as a direct, reversible, competitive inhibitor of H+/K+-ATPase without acid activation, leading to a faster onset than traditional PPIs. They differ on scaffold details but align on the main mechanistic basis for the faster onset. |
| gemini | disagree | The answers fundamentally disagree on the core chemical structure of the compound. Answer 1 identifies an imidazo[1,2-a]pyridine scaffold, while Answer 2 describes a pyrrolo[2,3-d]pyrimidine core, which are two different heterocyclic systems. |

### Example 13 — cid 135497803, qa_index 8 (topic: electronics)

**Question:** Discuss the aromaticity and conjugation present in the compound.

**Phase-1 answer:** The compound contains two distinct aromatic systems: the fused pyrrolo[3,2-d]pyrimidine bicyclic core and a trisubstituted benzene ring, which are connected via a carbon-carbon bond but are not fully coplanar.

**Phase-2 answer:** The compound contains three distinct aromatic rings: a fused bicyclic pyrimidinone system (the pyrazolopyrimidinone core), a phenyl ring substituted with sulfonamide and alkoxy groups, and a piperazine heterocycle that is non-aromatic. The pyrazolopyrimidinone scaffold is a planar, conjugated bicyclic system with 10 π-electrons delocalized across the fused 5- and 6-membered rings, satisfying Hückel's rule for aromaticity in each ring. The phenyl ring maintains a standard 6 π-electron aromatic se

| judge | verdict | reasoning |
|---|---|---|
| gemma | disagree | The answers identify different aromatic cores: Answer 1 describes a pyrrolo[3,2-d]pyrimidine core, while Answer 2 describes a pyrazolopyrimidinone core. Additionally, they differ on the connectivity, with Answer 1 stating a carbon-carbon bond and Answer 2 stating a methylene linker. |
| sonnet | disagree | Answer 1 identifies two aromatic systems (a pyrrolo[3,2-d]pyrimidine bicyclic core and a benzene ring), while Answer 2 identifies a pyrazolopyrimidinone core and a phenyl ring as aromatic, plus notes piperazine as non-aromatic. The two answers describe different bicyclic core scaffolds (pyrrolo[3,2-d]pyrimidine vs. pyrazolopyrimidinone) and differ in their characterization of the overall aromatic  |
| gpt5 | agree | Both identify two aromatic systems—a fused heteroaromatic bicyclic core and an aromatic phenyl ring—and note limited conjugation between them due to lack of coplanarity. Although Answer 2 briefly mentions three rings, it clarifies the piperazine is non-aromatic, aligning with Answer 1 overall. |
| gemini | agree | Both answers identify two main aromatic systems: a fused bicyclic core and a separate benzene/phenyl ring. They also both state that these two systems are not fully coplanar, which limits conjugation between them. Answer 2 is more detailed but its core conclusions match those of Answer 1. |

### Example 14 — cid 5958, qa_index 28 (topic: composition)

**Question:** What is the heavy atom count of the compound?

**Phase-1 answer:** The compound contains 16 heavy atoms (6 carbons, 9 oxygens, and 1 phosphorus).

**Phase-2 answer:** The compound contains 7 heavy atoms: 6 carbon atoms and 1 phosphorus atom. The molecular formula C6H13O9P confirms this count, with oxygen being a light atom (atomic number 8) that is typically excluded from heavy atom counts in standard medicinal chemistry conventions where only atoms heavier than carbon (C, N, O, F, P, S, Cl, etc.) are considered. However, if including all non-hydrogen atoms, the total would be 16 heavy atoms (6 C + 9 O + 1 P).

| judge | verdict | reasoning |
|---|---|---|
| gemma | agree | Both answers identify the same total number of non-hydrogen atoms (16), consisting of 6 carbons, 9 oxygens, and 1 phosphorus. Answer 2 provides a discussion on different counting conventions but ultimately confirms the same total as Answer 1. |
| sonnet | disagree | Answer 1 clearly states 16 heavy atoms (all non-hydrogen atoms). Answer 2 initially claims 7 heavy atoms using an incorrect definition that excludes oxygen, though it later mentions 16 as an alternative. The primary/main claim of each answer differs: 16 vs. 7. |
| gpt5 | disagree | Answer 1 states 16 heavy atoms, while Answer 2 asserts 7 heavy atoms (excluding oxygen) and only notes 16 under an alternate definition. These are conflicting main claims. |
| gemini | disagree | The answers provide different primary values for the heavy atom count. Answer 1 states the count is 16, while Answer 2's main claim is 7. Although Answer 2 mentions 16 as an alternative, its primary conclusion contradicts Answer 1. |

### Example 15 — cid 135398679, qa_index 2 (topic: pharmacophore)

**Question:** Identify the hydrogen bonding characteristics of the compound's pyrimidinone moiety.

**Phase-1 answer:** The pyrimidinone ring provides a complex hydrogen-bonding profile, acting as a donor through the N3-H and the C2-amino group, and as an acceptor through the C6-carbonyl oxygen and the N1 nitrogen.

**Phase-2 answer:** The pyrimidinone moiety of the compound presents a lactam carbonyl (C=O) as a hydrogen bond acceptor and an adjacent cyclic urea NH as a hydrogen bond donor. The exocyclic amine at the 2-position provides an additional donor, while the N1-methyl substituent eliminates a potential donor site. This hydrogen bonding pattern enables the compound to engage aspartate residues through both charged and uncharged states, with the carbonyl and imine nitrogen serving as key acceptor sites in enzyme-inhibit

| judge | verdict | reasoning |
|---|---|---|
| gemma | agree | Both answers identify the same key hydrogen bonding features: the carbonyl oxygen as an acceptor, the cyclic NH as a donor, and the C2-amino group as a donor. While Answer 2 provides more structural detail regarding the N1-methyl substituent, the core identification of donor and acceptor sites is consistent. |
| sonnet | disagree | Answer 1 identifies N1 as a hydrogen bond acceptor, while Answer 2 states that N1 bears a methyl substituent (eliminating it as a donor and implying it is not a free NH). Additionally, Answer 1 treats N3-H as the donor, whereas Answer 2 describes a 'cyclic urea NH' as the donor without specifying N3, and the two answers differ on whether N1 is methylated or free. |
| gpt5 | agree | Both identify the pyrimidinone’s donors as the ring NH and the exocyclic 2-amino group, and its acceptors as the lactam carbonyl and the ring imine (N1) nitrogen. Answer 2 adds context (N1-methylation and binding) without contradicting Answer 1. |
| gemini | disagree | The answers contradict each other regarding the N1 position of the pyrimidinone ring. Answer 1 identifies the N1 nitrogen as a hydrogen bond acceptor, whereas Answer 2 states that N1 is methylated, which is a different structural feature that eliminates a potential donor site. |

### Example 16 — cid 65864, qa_index 3 (topic: functional_groups)

**Question:** What are the key functional groups attached to the oxacephem core?

**Phase-1 answer:** The core is substituted with a 7-alpha-methoxy group, a 7-beta-difluoromethylthioacetamido side chain, and a 3-position (1-(2-hydroxyethyl)-1H-tetrazol-5-yl)thiomethyl group, along with a C-4 carboxylic acid.

**Phase-2 answer:** The compound contains an oxacephem β-lactam core with several key functional groups: a 7α-methoxy group (–OCH₃), a 7β-aminothioacetyl side chain terminated with a difluoromethylthio moiety (–SCH₂CF₂H), a 3-vinyl substituent bearing a 1,2,3-triazole-1-yl-thioethyl alcohol group (–CH₂S–C(=NN=N)–CH₂CH₂OH), and a carboxylic acid at the C-4 position. The β-lactam ring is fused to a dihydro-1,3-oxazine ring, characteristic of the oxacephem scaffold where the sulfur at position 1 of traditional cephalo

| judge | verdict | reasoning |
|---|---|---|
| gemma | agree | Both answers identify the same key substituents: the 7-alpha-methoxy group, the 7-beta-difluoromethylthioacetamido side chain, the C-4 carboxylic acid, and a complex sulfur-linked tetrazole/triazole derivative at the 3-position. |
| sonnet | agree | Both answers identify the same core functional groups: a 7α-methoxy group, a 7β-difluoromethylthioacetamido side chain, a 3-position heterocyclic thiomethyl group containing a nitrogen-rich ring with a hydroxyethyl substituent, and a C-4 carboxylic acid. The minor differences are in how the tetrazole vs. triazole ring is described and level of structural detail, but the main substituents match. |
| gpt5 | disagree | They agree on the 7α-methoxy, a 7β acyl side chain with a difluoromethylthio moiety, and the C-4 carboxyl, but they conflict on the 3-position substituent (tetrazolyl-thiomethyl vs a triazole-bearing vinyl/thiethyl group). |
| gemini | disagree | The answers contradict each other regarding the identity of the heterocyclic ring at the 3-position. Answer 1 identifies it as a tetrazole, while Answer 2 identifies it as a triazole. |

### Example 17 — cid 443021, qa_index 6 (topic: pharmacophore)

**Question:** Identify the key aromatic features that contribute to the compound's biological profile.

**Phase-1 answer:** The pharmacophore is characterized by two distinct aromatic domains: a 1,2,3-trimethoxybenzene ring and a 1,3-benzodioxole system. These electron-rich aromatic rings are held in a rigid, non-planar orientation by the fused aliphatic scaffold, which is essential for high-affinity binding to the colchicine site on tubulin.

**Phase-2 answer:** The compound contains a 1,2,3-trimethoxybenzene (TMB) motif fused to a methylenedioxy-substituted aromatic ring, forming a dibenzocyclooctadiene scaffold. The electron-rich methoxy and methylenedioxy substituents create a highly lipophilic, planar aromatic surface that enables tubulin binding and microtubule destabilization. The stereochemistry at the fused lactone ring further constrains the conformation, contributing to the compound's potent antimitotic activity.

| judge | verdict | reasoning |
|---|---|---|
| gemma | disagree | The answers contradict each other regarding the geometry of the aromatic rings; Answer 1 describes them as being in a 'non-planar orientation', while Answer 2 describes them as forming a 'planar aromatic surface'. |
| sonnet | agree | Both answers identify the same two key aromatic features (1,2,3-trimethoxybenzene and a methylenedioxy/benzodioxole aromatic ring) and both link these electron-rich aromatic systems to tubulin binding activity. The main difference is that Answer 2 adds more detail about the dibenzocyclooctadiene scaffold and stereochemistry, but the core conclusions are consistent. |
| gpt5 | agree | Both identify the same key aromatic features— a 1,2,3-trimethoxybenzene ring and a methylenedioxy/benzodioxole ring— as electron-rich motifs driving tubulin (colchicine-site) binding and antimitotic activity. Differences about planarity and added scaffold details are supplementary and do not alter the main conclusion. |
| gemini | disagree | The answers contradict each other on a key geometric feature of the compound. Answer 1 states the aromatic rings are held in a 'non-planar orientation', while Answer 2 describes a 'planar aromatic surface'. |

### Example 18 — cid 6328144, qa_index 38 (topic: composition)

**Question:** What is the molecular formula of the compound?

**Phase-1 answer:** The molecular formula is simply Ra.

**Phase-2 answer:** Ra

| judge | verdict | reasoning |
|---|---|---|
| gemma | unclear | one or both answers are N/A-like |
| sonnet | agree | Both answers give the same molecular formula: Ra. |
| gpt5 | agree | Both answers give the same molecular formula: Ra. |
| gemini | agree | Both answers correctly identify the molecular formula as 'Ra'. Answer 1 is a complete sentence while Answer 2 provides only the formula, but they convey the same essential information. |

### Example 19 — cid 107771, qa_index 9 (topic: engineering)

**Question:** If the pyrrolidine rings were replaced with diethylamino groups, what would be the likely impact on the compound's profile?

**Phase-1 answer:** Replacing the pyrrolidine rings with diethylamino groups would yield a structure more similar to amodiaquine. This would likely decrease the potency of hemozoin nucleation inhibition and reduce the compound's ability to overcome certain chloroquine-resistance mechanisms in ring-stage parasites.

**Phase-2 answer:** The compound contains two pyrrolidine rings appended to phenolic positions via methylene linkers. Replacing these with diethylamino groups would increase basicity and lipophilicity, likely enhancing lysosomal trapping and lung tissue accumulation—properties already exploited for antimalarial and antiviral efficacy. The larger, more flexible diethylamino substituents may improve membrane permeability but could increase hERG liability and metabolic N-dealkylation susceptibility, potentially alteri

| judge | verdict | reasoning |
|---|---|---|
| gemma | unclear | Answer 1 focuses on the pharmacological potency and resistance mechanisms (antimalarial efficacy), while Answer 2 focuses on physicochemical properties, pharmacokinetics, and toxicity (basicity, lipophilicity, hERG liability). They address different aspects of the 'profile' without contradicting each other. |
| sonnet | disagree | Answer 1 predicts decreased potency and reduced ability to overcome chloroquine resistance, while Answer 2 predicts enhanced efficacy through increased basicity, lipophilicity, and lysosomal trapping. The two answers reach opposite conclusions about the likely impact on the compound's pharmacological profile. |
| gpt5 | unclear | Answer 1 predicts decreased antimalarial potency and resistance profile, while Answer 2 focuses on changes in physicochemical/PK and safety liabilities without a direct efficacy conclusion. They address different aspects and do not clearly agree or contradict. |
| gemini | disagree | The two answers contradict each other on the likely impact on the compound's efficacy. Answer 1 predicts a decrease in potency and ability to overcome resistance, whereas Answer 2 suggests the modification would enhance properties beneficial for antimalarial efficacy, such as lysosomal trapping. |

### Example 20 — cid 62034, qa_index 3 (topic: stereochemistry)

**Question:** How many stereocenters are present in the compound and what is their configuration?

**Phase-1 answer:** The compound possesses three chiral centers located at the ring junctions and the quaternary carbon bearing the methyl and aminomethyl groups. These centers are defined as (4aS, 10aR) at the fusion points, maintaining a rigid trans-fused decalin-like geometry within the saturated portion of the tricyclic system.

**Phase-2 answer:** The compound contains three stereocenters, all with defined configuration: C13 is (R), C14 is (S), and C17 is (S) according to the CIP rules applied to the tricyclic amantadine-like scaffold with the aminomethyl substituent.

| judge | verdict | reasoning |
|---|---|---|
| gemma | unclear | While both answers agree on the number of stereocenters (three), they use entirely different numbering systems and configurations (4aS, 10aR vs C13, C14, C17), making it impossible to determine if they are describing the same spatial arrangement. |
| sonnet | disagree | Both answers agree there are three stereocenters, but they assign different configurations. Answer 1 describes the configurations as (4aS, 10aR) at two fusion points (with the third implied), while Answer 2 assigns (R), (S), (S) at C13, C14, C17. The specific stereodescriptors contradict each other and reference different numbering systems with incompatible assignments. |
| gpt5 | unclear | Both answers agree there are three stereocenters, but Answer 1 only specifies configurations for two (4aS, 10aR) and leaves the third unspecified, while Answer 2 gives three configurations using a different numbering scheme (C13, C14, C17). The configurations cannot be mapped or compared directly. |
| gemini | agree | Both answers agree that the compound has three stereocenters with a defined configuration. Although they use different numbering systems and one answer only specifies two of the three configurations, they do not contradict each other on the main claims. |
