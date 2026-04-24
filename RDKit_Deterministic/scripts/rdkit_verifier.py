"""Task 1 — RDKit deterministic verifier for Chem2TextQA.

For every compound, derive a "ground-truth" dictionary from the SMILES using
RDKit. For every Q&A on that compound, run lightweight regex/keyword
extractors over phase1_answer and phase2_answer, emit {verified, contradicted,
not_applicable} verdicts, and write a per-compound JSONL and an aggregate
summary broken down by topic bucket and split.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from rdkit import Chem, RDLogger
from rdkit.Chem import rdMolDescriptors

sys.path.insert(0, str(Path(__file__).parent))
from topic_bucket import bucket_topic  # canonical Chem2TextQA topic bucketer

RDLogger.DisableLog("rdApp.*")


# ------------------------------------------------------------------ SMARTS ---

# Functional-group SMARTS. Each key must match the trigger names below.
FG_SMARTS = {
    # Accept both neutral carboxylic acid (-COOH) and its conjugate base
    # (-COO-) — models routinely call them both "carboxylate" / "carboxylic
    # acid" / "-COOH" and that's chemically reasonable at physiological pH.
    "carboxylic_acid": "[CX3](=O)[OX2H1,OX1H0-]",
    "ester": "[#6][CX3](=O)[OX2][#6]",
    "phosphate_ester": "[PX4](=O)([OX2])[OX2][#6]",
    "amide": "[NX3][CX3](=O)[#6]",
    "nitro": "[NX3+](=O)[O-]",
    "halide_any": "[F,Cl,Br,I]",
    "fluorine": "[F]",
    "chlorine": "[Cl]",
    "bromine": "[Br]",
    "iodine": "[I]",
    "amine": "[NX3;H2,H1,H0;!$(NC=O);!$(N=*);!$([N+])]",
    "hydroxyl": "[OX2H]",
    "sulfonamide": "[SX4](=O)(=O)[NX3]",
    "ketone": "[#6][CX3](=O)[#6]",
    "aldehyde": "[CX3H1](=O)[#6]",
}

# Trigger phrases in answers that assert a group is present. Must align with
# FG_SMARTS keys above. Case-insensitive substring matching on the answer text.
FG_TRIGGERS = {
    "carboxylic_acid": [r"carboxylic\s*acid", r"\b-?cooh\b", r"\bcarboxyl(?:ate)?\b"],
    "ester": [r"\bester\b"],
    "phosphate_ester": [r"\bphosphate\s*ester\b", r"\bphosphodiester\b", r"\bphosphoester\b"],
    "amide": [r"\bamide\b", r"\bamido\b"],
    "nitro": [r"\bnitro\s*group\b", r"\bnitro\b"],
    "halide_any": [r"\bhalide\b", r"\bhalogen(?:ated)?\b"],
    "fluorine": [r"\bfluor(?:ine|o|inate|inated)\b", r"\bfluorin?yl\b"],
    "chlorine": [r"\bchlor(?:ine|o|inate|inated)\b", r"\bchloro\b"],
    "bromine": [r"\bbrom(?:ine|o|inate|inated)\b", r"\bbromo\b"],
    "iodine": [r"\biod(?:ine|o|inate|inated)\b", r"\biodo\b"],
    "amine": [r"\b(?:primary|secondary|tertiary)?\s*amine\b", r"\bamino\s*group\b"],
    "hydroxyl": [r"\bhydroxyl\b", r"\bhydroxy\s*group\b", r"\b-?oh\s*group\b"],
    "sulfonamide": [r"\bsulfonamide\b", r"\bsulphonamide\b"],
    "ketone": [r"\bketone\b"],
    "aldehyde": [r"\baldehyde\b"],
}

# Words in the preceding ~30-char window that disqualify a functional-group
# trigger from being treated as a claim on THIS molecule. These are:
#  - naming other ester-like chemistries (phosphate/poly/thio/sulfo)
#  - prodrug / formulation talk
#  - comparisons to analogs
DISQUALIFIER_BY_GROUP: dict[str, re.Pattern] = {
    # Ester: names of ester subclasses RDKit's strict [#6]-C(=O)-O-[#6] SMARTS
    # doesn't recognize (lactone/cyclic ester, nitrate/sulfate/sulfonate/
    # phosphonate/phosphate/carbamate/carbonate/phosphoramidate esters, aryl
    # sulfate). These are real ester-family groups; suppress the generic
    # "ester" trigger rather than flipping it to contradicted.
    "ester": re.compile(
        r"\b(?:phosphate|phosphodi|phospho|phosphonate|phosphoramidate|"
        r"nitrate|nitrite|sulfate|sulfonate|sulfo|sulphate|thio|poly|hexyl|"
        r"methyl|ethyl|benzyl|acetyl|prodrug|glucurono|glycerol|cholesterol|"
        r"lactone|cyclic|carbamate|carbonate|aryl\s+sulfate|aryl\s+phosphate|"
        r"(?:carbamate|carbonate|phosphate|sulfate|lactone)\s*or\s+|"
        r"unlike|trans)\s*$",
        re.IGNORECASE,
    ),
    # Amide: "sulfonamide/carbamate/carbox-" avoid subword hits. Add
    # "such\s+as" (acceptor comparison) and "carboxamide" framing.
    "amide": re.compile(
        r"\b(?:sulfonamide|carbamate|carbox|such\s+as\s+(?:\w+\s+or\s+)?"
        r"hydroxyl\s+or|cleaves\s+(?:the|an?|this)|"
        r"reactivity\s+for|site\s+for|potential\s+for|"
        r"formation\s+of|unlike)\s*$",
        re.IGNORECASE,
    ),
    # Aldehyde: enzyme/cofactor names (aldehyde dehydrogenase, ALDH,
    # PLP aldehyde, pyridoxal). Don't include bare articles — those are too
    # common in valid descriptions like "an aldehyde and a hydroxyl".
    "aldehyde": re.compile(
        r"\b(?:reactive|PLP|pyridoxal|retinal|ALDH\w*)\s*$",
        re.IGNORECASE,
    ),
    # Carboxylic acid: "carboxylate ester" (subgroup name, not free acid),
    # and "Nx-yy-carboxylate" / position-prefixed carboxylate naming (e.g.
    # "N-methylpyrrole-2-carboxylate ester"). Also "carboxy" inside
    # hyphenated compound names (e.g. "5-COOH-2'-dUrd" is a metabolite name
    # covered by hypothetical context instead).
    "carboxylic_acid": re.compile(
        r"(?:-[12345]-|methyl|ethyl|benzyl|acetyl)\s*$",
        re.IGNORECASE,
    ),
}

# Words in the ~20-char window AFTER a functional-group trigger that
# disqualify it — same idea as the lookback disqualifiers above, but for
# cases where the context that re-labels the group comes after the trigger
# word (e.g. "carboxylate ester", "aldehyde dehydrogenase").
POST_DISQUALIFIER_BY_GROUP: dict[str, re.Pattern] = {
    "carboxylic_acid": re.compile(
        r"^\s*(?:ester|anhydride|amide|metabolite)\b",
        re.IGNORECASE,
    ),
    "aldehyde": re.compile(
        r"^\s*(?:dehydrogenase|oxidase|reductase|reductas|synthase|"
        r"derivatives?|-mediated|-induced|-related|detoxification)\b",
        re.IGNORECASE,
    ),
    "amide": re.compile(
        r"^\s*(?:bond\s+between|protons?|formation|linkage\s+between|"
        r"[,;]\s*(?:urea|carbamate|ester|sulfonamide)\b)",
        re.IGNORECASE,
    ),
    # "ester carbonyl[s]" — talking about the C=O part of an ester subgroup
    # that RDKit's SMARTS might not recognize anyway (rare).
}

# Pre-compile everything once.
FG_SMARTS_MOLS = {k: Chem.MolFromSmarts(v) for k, v in FG_SMARTS.items()}
FG_TRIGGER_REGEX = {
    k: re.compile("|".join(f"(?:{p})" for p in v), re.IGNORECASE)
    for k, v in FG_TRIGGERS.items()
}

# Numeric claims we can verify.
# Each entry: (regex, claim_type, rdkit_key).
NUM_CLAIM_PATTERNS = [
    (re.compile(r"degree[s]?\s+of\s+unsaturation[^\d]{0,20}(?:is|=|:|of)\s*(\d+)", re.IGNORECASE), "degree_of_unsaturation", "dou"),
    (re.compile(r"(?:double[- ]?bond\s+equivalent(?:s)?)[^\d]{0,20}(?:is|=|:|of)\s*(\d+)", re.IGNORECASE), "degree_of_unsaturation", "dou"),
    (re.compile(r"(\d+)\s+(?:aromatic\s+rings?)", re.IGNORECASE), "aromatic_rings", "aromatic_rings"),
    (re.compile(r"(\d+)\s+rotatable\s+bonds?", re.IGNORECASE), "rotatable_bonds", "rotatable_bonds"),
    (re.compile(r"(\d+)\s+(?:hydrogen\s+bond\s+donor|h-?\s*bond\s+donor|hbd)", re.IGNORECASE), "hbd", "hbd"),
    (re.compile(r"(\d+)\s+(?:hydrogen\s+bond\s+acceptor|h-?\s*bond\s+acceptor|hba)", re.IGNORECASE), "hba", "hba"),
    (re.compile(r"(\d+)\s+(?:chiral\s+centers?|stereocenters?|stereogenic\s+centers?)", re.IGNORECASE), "stereocenters", "stereocenters"),
    (re.compile(r"(\d+)\s+heavy\s+atoms?", re.IGNORECASE), "heavy_atoms", "heavy_atoms"),
    (re.compile(r"(\d+)\s+rings?(?![\w-])", re.IGNORECASE), "num_rings", "num_rings"),
]

# Context-based skip list for numeric claims: if one of these tokens is in
# the preceding 60-char window of a numeric match, the "count" is most
# likely a per-substructure DoU breakdown ("1 ring + 3 π bonds"), a size
# descriptor ("5-membered ring"), or a partial-structure mention ("core (4
# rings + 3 aromatic rings)") — not the whole-molecule count. These are
# easy to tell apart from real claims like "contains 4 rings".
NUM_CLAIM_CONTEXT_SKIP = {
    "num_rings": re.compile(
        r"\b(?:contribut\w+|additional|further|core|system|framework|"
        r"architecture|aglycone|backbone|subunit|moiety|portion|"
        r"scaffold|plus\s+\d|\+\s*\d|distributed\s+as|each|per|"
        r"\d+[-]?membered|membered|fused|fusion|cluster)\b",
        re.IGNORECASE,
    ),
}

# Bucketing is delegated to topic_bucket.py (Chem2TextQA canonical helper).
topic_bucket = bucket_topic


# Hedge/range terms that invalidate an exact numeric claim. If any of these
# appear inside the ~40-character window preceding the number, the claim is
# treated as a bound/approximation rather than a specific count.
HEDGE_REGEX = re.compile(
    r"\b(?:fewer\s+than|less\s+than|more\s+than|greater\s+than|at\s+least|"
    r"at\s+most|up\s+to|under|over|about|approximately|roughly|around|"
    r"between|~|≈|≥|≤)\b",
    re.IGNORECASE,
)
RANGE_REGEX = re.compile(r"\b\d+\s*(?:-|to|–|—)\s*\d+\b", re.IGNORECASE)


# ----------------------------------------------------------------- RDKit ---


def mol_facts(smiles: str) -> dict[str, Any] | None:
    try:
        m = Chem.MolFromSmiles(smiles)
    except Exception:
        return None
    if m is None:
        return None
    # Add Hs is not needed — descriptors work on implicit-H graph.
    d: dict[str, Any] = {}
    d["heavy_atoms"] = m.GetNumHeavyAtoms()
    d["num_rings"] = rdMolDescriptors.CalcNumRings(m)
    d["aromatic_rings"] = rdMolDescriptors.CalcNumAromaticRings(m)
    d["rotatable_bonds"] = rdMolDescriptors.CalcNumRotatableBonds(m)
    # Use Lipinski definitions — these match the "count all O/N" convention
    # most LLMs use when asked for HBD/HBA. The stricter CalcNumHBA* variants
    # apply SMARTS exclusions that models don't typically follow.
    d["hbd"] = rdMolDescriptors.CalcNumLipinskiHBD(m)
    d["hba"] = rdMolDescriptors.CalcNumLipinskiHBA(m)
    d["formal_charge"] = Chem.GetFormalCharge(m)
    d["stereocenters"] = len(Chem.FindMolChiralCenters(m, includeUnassigned=True))

    # DoU from molecular formula. RDKit doesn't expose this directly; compute
    # from explicit + implicit H counts.
    counts = Counter()
    for atom in m.GetAtoms():
        counts[atom.GetSymbol()] += 1
    # Add implicit + explicit Hs
    H = sum(a.GetTotalNumHs() for a in m.GetAtoms())
    C = counts.get("C", 0)
    N = counts.get("N", 0)
    X = sum(counts.get(x, 0) for x in ("F", "Cl", "Br", "I"))
    d["dou"] = (2 * C + 2 + N - H - X) // 2

    # Functional-group presence (from SMARTS).
    fg: dict[str, bool] = {}
    for name, q in FG_SMARTS_MOLS.items():
        if q is None:
            continue
        fg[name] = m.HasSubstructMatch(q)
    d["functional_groups"] = fg
    return d


# ----------------------------------------------------------- Verifier core ---


def _in_hedged_context(answer: str, start: int, window: int = 40) -> bool:
    """True if the text just before `start` (within `window` chars) contains a
    hedge term like 'fewer than', 'about', or a numeric range like '2-3'."""
    ctx = answer[max(0, start - window) : start]
    if HEDGE_REGEX.search(ctx):
        return True
    # A range like "2-3 hydrogen bond donors" — check the immediate tail of ctx.
    if RANGE_REGEX.search(ctx[-20:]):
        return True
    return False


def _check_numeric(answer: str, facts: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for pat, claim_type, key in NUM_CLAIM_PATTERNS:
        ctx_skip = NUM_CLAIM_CONTEXT_SKIP.get(claim_type)
        for m in pat.finditer(answer):
            try:
                claimed = int(m.group(1))
            except (ValueError, IndexError):
                continue
            # Skip hedged or range claims — they're not exact counts.
            if _in_hedged_context(answer, m.start(1)):
                continue
            # Skip hypothetical / analog-discussion contexts.
            if _is_hypothetical(answer, m.start(1)):
                continue
            # Skip partial-structure / DoU-breakdown contexts.
            if ctx_skip is not None:
                lookback = answer[max(0, m.start(1) - 60) : m.start(1)]
                if ctx_skip.search(lookback):
                    continue
            ref = facts.get(key)
            if ref is None:
                continue
            status = "verified" if claimed == ref else "contradicted"
            checks.append(
                {
                    "claim_type": claim_type,
                    "claimed": claimed,
                    "rdkit": ref,
                    "status": status,
                }
            )
    return checks


NEGATION_REGEX = re.compile(
    r"\b(?:no|not|without|lack(?:s|ing)?|absen(?:t|ce)(?:\s+of)?|devoid\s+of|"
    r"free\s+of|does\s+not\s+(?:have|contain|possess)|"
    r"doesn'?t\s+(?:have|contain|possess)|"
    r"missing|neither)\b",
    re.IGNORECASE,
)

# Hypothetical / conditional / analog-discussion cues. If any of these appear
# in the sentence containing a functional-group trigger, we don't treat the
# trigger as a claim about *this* compound — the model is talking about
# possible modifications, analogues, or reaction products.
HYPOTHETICAL_REGEX = re.compile(
    r"\b(?:would|could|might|if\s+(?:it|the\s+\w+)\s+(?:were|was)|"
    r"replac(?:e|ing|ement)|substitut(?:e|ing|ion)\s+(?:with|by)|"
    r"analog(?:ue)?s?|derivativ\w*|modification|modified|"
    r"addition\s+of|removal\s+of|adding\s+a|removing\s+a|"
    r"converted\s+(?:to|into)|conversion\s+(?:of|to|into)|"
    r"form(?:s|ing)\s+\w+\s+upon|formation\s+of\s+(?:a|an|the)\s+\w+|"
    r"esterification|halogenation|methylation|oxidation\s+(?:to|into|of)|"
    r"reduction\s+(?:to|into)|reaction\s+with|react\s+with|"
    r"unlike|compared\s+to|in\s+contrast\s+to|versus|such\s+as|"
    r"tri\w*fluoro|per\w*fluoro|labeled\s+version|labeled\s+with|"
    r"catabolite\s+of|metabolite\s+(?:of|to)|"
    r"to\s+(?:an?|the)\s+(?:inactive\s+)?\w+\s+metabolite|"
    r"precursor\s+of|derived\s+from|"
    r"intermediate(?:s)?|byproduct(?:s)?|cleavage\s+to\s+yield|"
    r"cleaves?\s+(?:the|an?|this)|hydrolyz\w+\s+(?:to|into|by|it)|"
    r"hydrolysis\s+(?:of|yields|generates|produces)|"
    r"deamination\s+to|decarboxylation\s+to|"
    r"reducing\s+the|reduce\s+the|oxidizing\s+the|oxidize\s+the|"
    r"upon\s+(?:hydrolysis|reduction|oxidation|cleavage|reaction)|"
    r"the\s+resulting\s+\w+|resulting\s+(?:from|in)|"
    r"oxidized\s+metabolites?|oxidized\s+forms?|"
    r"reduced\s+to|oxidized\s+to|hydrolyzed\s+to|yields?\s+(?:a|an|the)\s+\w+|"
    r"undergoes\s+\w+\s+to\s+form|results?\s+in\s+(?:a|an|the)\s+\w+|"
    r"activates?\s+\w+\s+(?:dehydrogenase|oxidase|reductase|synthase)|"
    r"PLP-dependent|external\s+aldimine)\b",
    re.IGNORECASE,
)

_SENT_SPLIT = re.compile(r"(?<=[.!?;])\s+|\n+")


def _sentence_span(answer: str, idx: int) -> tuple[int, int]:
    """Return (start, end) of the sentence containing character index `idx`."""
    starts = [0]
    for m in _SENT_SPLIT.finditer(answer):
        starts.append(m.end())
    # Find the last start <= idx
    s = 0
    for st in starts:
        if st <= idx:
            s = st
        else:
            break
    # End is next sentence boundary
    e = len(answer)
    for m in _SENT_SPLIT.finditer(answer, idx):
        e = m.start()
        break
    return s, e


def _is_hypothetical(answer: str, idx: int) -> bool:
    s, e = _sentence_span(answer, idx)
    return bool(HYPOTHETICAL_REGEX.search(answer[s:e]))


def _has_negation_before(answer: str, start: int, window: int = 30) -> bool:
    ctx = answer[max(0, start - window) : start]
    return bool(NEGATION_REGEX.search(ctx))


def _check_functional_groups(answer: str, facts: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    fg_ref = facts.get("functional_groups") or {}
    for name, regex in FG_TRIGGER_REGEX.items():
        dq = DISQUALIFIER_BY_GROUP.get(name)
        for m in regex.finditer(answer):
            ref = fg_ref.get(name)
            if ref is None:
                continue
            # Skip hypothetical / analog-discussion contexts.
            if _is_hypothetical(answer, m.start()):
                continue
            # Skip group-specific disqualifier contexts (e.g. "phosphate ester").
            if dq is not None:
                lookback = answer[max(0, m.start() - 30) : m.start()]
                if dq.search(lookback):
                    continue
            # Post-context disqualifiers (e.g. "carboxylate ester",
            # "aldehyde dehydrogenase", "amide bond between X and Y").
            post_dq = POST_DISQUALIFIER_BY_GROUP.get(name)
            if post_dq is not None:
                lookahead = answer[m.end() : m.end() + 30]
                if post_dq.search(lookahead):
                    continue
            negated = _has_negation_before(answer, m.start())
            claimed_present = not negated
            status = "verified" if bool(ref) == claimed_present else "contradicted"
            checks.append(
                {
                    "claim_type": f"{name}_present",
                    "claimed": claimed_present,
                    "rdkit": bool(ref),
                    "status": status,
                }
            )
            break  # first occurrence per group is enough; dedup handles extras
    return checks


def _dedup_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse duplicate (claim_type, claimed) checks; keep the first."""
    seen = set()
    out = []
    for c in checks:
        key = (c["claim_type"], c["claimed"])
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def verify_qa(phase1: str, phase2: str, facts: dict[str, Any]) -> list[dict[str, Any]]:
    # We only score phase2_answer — the final (post-agreement) answer in the
    # dataset pipeline. Phase 1 is an intermediate draft.
    answer = phase2 or ""
    checks = _check_numeric(answer, facts) + _check_functional_groups(answer, facts)
    return _dedup_checks(checks)


# -------------------------------------------------------------------- Main ---


def iterate_source(path: Path):
    with path.open() as f:
        for line in f:
            yield json.loads(line)


def main():
    repo_root = Path(__file__).resolve().parents[1]
    default_input = repo_root / "data" / "dataset_gold.jsonl"
    default_out_dir = repo_root / "tasks" / "task1" / "outputs"

    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(default_input))
    p.add_argument("--out_dir", default=str(default_out_dir))
    p.add_argument("--limit", type=int, default=0, help="0 = no limit")
    args = p.parse_args()

    src = Path(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    per_compound_path = out_dir / "rdkit_verification.jsonl"

    # Running tallies ----------------------------------------------------
    # buckets by (topic_bucket, split, claim_class)
    bucket_totals = defaultdict(
        lambda: Counter({"checkable_qa": 0, "total_qa": 0, "verified_claims": 0, "contradicted_claims": 0, "total_claims": 0})
    )
    by_claim_type = Counter()
    by_claim_type_verified = Counter()

    smiles_parse_fail = 0
    total_compounds = 0
    total_qa = 0

    with per_compound_path.open("w") as fout:
        for i, row in enumerate(iterate_source(src)):
            if args.limit and i >= args.limit:
                break
            total_compounds += 1
            cid = row.get("cid")
            split = row.get("split") or "unknown"
            smiles = row.get("smiles") or ""
            facts = mol_facts(smiles) if smiles else None
            if facts is None:
                smiles_parse_fail += 1
                fout.write(json.dumps({"cid": cid, "smiles_parse_failed": True}) + "\n")
                continue

            qa_verifs = []
            for qa in row.get("qa_pairs") or []:
                total_qa += 1
                topic = qa.get("topic")
                bucket = topic_bucket(topic)
                checks = verify_qa(
                    phase1="",  # we score phase 2 only
                    phase2=qa.get("phase2_answer") or "",
                    facts=facts,
                )
                qa_verifs.append(
                    {
                        "qa_index": qa.get("qa_index"),
                        "topic": topic,
                        "bucket": bucket,
                        "checks": checks,
                    }
                )
                btot = bucket_totals[(bucket, split)]
                btot["total_qa"] += 1
                if checks:
                    btot["checkable_qa"] += 1
                    btot["total_claims"] += len(checks)
                    for c in checks:
                        by_claim_type[c["claim_type"]] += 1
                        if c["status"] == "verified":
                            btot["verified_claims"] += 1
                            by_claim_type_verified[c["claim_type"]] += 1
                        else:
                            btot["contradicted_claims"] += 1

            fout.write(
                json.dumps({"cid": cid, "split": split, "qa_verifications": qa_verifs})
                + "\n"
            )
            if (i + 1) % 1000 == 0:
                print(f"  processed {i+1} compounds ({total_qa} Q&A so far)", flush=True)

    # Write summary ------------------------------------------------------
    summary_path = out_dir / "rdkit_verification_summary.md"
    lines: list[str] = []
    lines.append("# RDKit Deterministic Verification — Summary\n")
    lines.append(
        f"Source: `{src}`  \nCompounds processed: **{total_compounds:,}**  "
        f"(SMILES parse failures: {smiles_parse_fail})  \n"
        f"Total Q&A evaluated: **{total_qa:,}**\n"
    )

    def _coverage_row(vals: Counter):
        total = vals["total_qa"]
        checkable = vals["checkable_qa"]
        verified = vals["verified_claims"]
        contradicted = vals["contradicted_claims"]
        claims = vals["total_claims"]
        cov = checkable / total if total else 0.0
        ver = verified / claims if claims else 0.0
        con = contradicted / claims if claims else 0.0
        return f"{total:,}", f"{checkable:,}", f"{cov:.3%}", f"{claims:,}", f"{ver:.3%}", f"{con:.3%}"

    # Section: overall
    overall = Counter()
    for v in bucket_totals.values():
        overall.update(v)
    lines.append("## Overall\n")
    lines.append("| total Q&A | checkable Q&A | coverage | total claims | verified% | contradicted% |")
    lines.append("|---|---|---|---|---|---|")
    lines.append("| " + " | ".join(_coverage_row(overall)) + " |\n")

    # Section: by topic bucket
    by_bucket = defaultdict(Counter)
    for (bucket, split), v in bucket_totals.items():
        by_bucket[bucket].update(v)
    lines.append("## By topic bucket\n")
    lines.append("| bucket | total Q&A | checkable | coverage | claims | verified% | contradicted% |")
    lines.append("|---|---|---|---|---|---|---|")
    for bucket in sorted(by_bucket.keys()):
        row = _coverage_row(by_bucket[bucket])
        lines.append(f"| {bucket} | " + " | ".join(row) + " |")
    lines.append("")

    # Section: by split
    by_split = defaultdict(Counter)
    for (bucket, split), v in bucket_totals.items():
        by_split[split].update(v)
    lines.append("## By split\n")
    lines.append("| split | total Q&A | checkable | coverage | claims | verified% | contradicted% |")
    lines.append("|---|---|---|---|---|---|---|")
    for split in sorted(by_split.keys()):
        row = _coverage_row(by_split[split])
        lines.append(f"| {split} | " + " | ".join(row) + " |")
    lines.append("")

    # Section: per bucket × split
    lines.append("## Per bucket × split\n")
    lines.append("| bucket | split | total Q&A | checkable | coverage | claims | verified% | contradicted% |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for (bucket, split) in sorted(bucket_totals.keys()):
        row = _coverage_row(bucket_totals[(bucket, split)])
        lines.append(f"| {bucket} | {split} | " + " | ".join(row) + " |")
    lines.append("")

    # Section: per claim type
    lines.append("## Per claim type\n")
    lines.append("| claim_type | total fired | verified | verified% |")
    lines.append("|---|---|---|---|")
    for ct in sorted(by_claim_type.keys()):
        total = by_claim_type[ct]
        ver = by_claim_type_verified[ct]
        rate = ver / total if total else 0.0
        lines.append(f"| {ct} | {total:,} | {ver:,} | {rate:.3%} |")
    lines.append("")

    summary_path.write_text("\n".join(lines))
    print(f"\nWrote:\n  {per_compound_path}\n  {summary_path}")


if __name__ == "__main__":
    main()
