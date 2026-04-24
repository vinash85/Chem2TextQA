"""Emit a per-Q&A JSONL with an RDKit-based label attached.

For every QA in dataset_gold.jsonl we attach:
  - checks:     the raw RDKit verifier checks (claim_type, claimed, rdkit, status)
  - rdkit_label: aggregate verdict
      - verified       : >=1 checkable claim, all verified
      - contradicted   : >=1 claim contradicted (regardless of whether others verified)
      - not_applicable : no RDKit-checkable claim extracted
"""
import argparse
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_GOLD = _REPO_ROOT / "data" / "dataset_gold.jsonl"
_DEFAULT_VERIF = _REPO_ROOT / "tasks" / "task1" / "outputs" / "rdkit_verification.jsonl"
_DEFAULT_OUT = _REPO_ROOT / "tasks" / "task1" / "outputs" / "qa_rdkit_labeled.jsonl"


def aggregate_label(checks):
    if not checks:
        return "not_applicable"
    if any(c.get("status") == "contradicted" for c in checks):
        return "contradicted"
    return "verified"


def main():
    p = argparse.ArgumentParser(
        description="Emit a per-Q&A JSONL with an RDKit-based label attached."
    )
    p.add_argument(
        "--gold",
        default=str(_DEFAULT_GOLD),
        help="Path to dataset_gold.jsonl (default: repo-relative data/dataset_gold.jsonl)",
    )
    p.add_argument(
        "--verif",
        default=str(_DEFAULT_VERIF),
        help="Path to rdkit_verification.jsonl produced by rdkit_verifier.py",
    )
    p.add_argument(
        "--out",
        default=str(_DEFAULT_OUT),
        help="Output path for qa_rdkit_labeled.jsonl",
    )
    args = p.parse_args()

    gold_path = Path(args.gold)
    verif_path = Path(args.verif)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Index verifier output by (cid, qa_index).
    verif_index = {}
    for line in verif_path.open():
        v = json.loads(line)
        if v.get("smiles_parse_failed"):
            continue
        for qa in v.get("qa_verifications") or []:
            verif_index[(v["cid"], qa["qa_index"])] = qa

    n_total = 0
    counts = {"verified": 0, "contradicted": 0, "not_applicable": 0}
    with out_path.open("w") as fout:
        for line in gold_path.open():
            row = json.loads(line)
            cid = row["cid"]
            split = row.get("split")
            smiles = row.get("smiles")
            name = row.get("name")
            for qa in row.get("qa_pairs") or []:
                qa_idx = qa["qa_index"]
                v = verif_index.get((cid, qa_idx)) or {}
                checks = v.get("checks") or []
                label = aggregate_label(checks)
                counts[label] += 1
                n_total += 1
                rec = {
                    "cid": cid,
                    "split": split,
                    "name": name,
                    "smiles": smiles,
                    "qa_index": qa_idx,
                    "topic": qa.get("topic"),
                    "bucket": v.get("bucket"),
                    "question": qa.get("question"),
                    "phase1_answer": qa.get("phase1_answer"),
                    "phase2_answer": qa.get("phase2_answer"),
                    "judge_verdict": qa.get("verdict"),
                    "judge_reasoning": qa.get("judge_reasoning"),
                    "evidence_ids": qa.get("evidence_ids"),
                    "rdkit_checks": checks,
                    "rdkit_label": label,
                }
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {n_total:,} labeled Q&A records to {out_path}")
    for k, v in counts.items():
        print(f"  {k}: {v:,} ({v/n_total:.1%})")


if __name__ == "__main__":
    main()
