"""Stratified sampling entry point: writes `sample.jsonl` under --out-dir.

Composes the tested library modules `Sampler` + `EvidenceAttacher`. Output
layout matches PLAN §Step 1 so the judge runner and aggregator can consume
it without reopening the gold dataset.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from phase4_grounding.grounding.evidence import EvidenceAttacher
from phase4_grounding.grounding.models import SampleRow
from phase4_grounding.grounding.sampling import Sampler


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Sample functional QA for grounding audit")
    p.add_argument("--n", type=int, required=True, help="total sample size")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument(
        "--data-path",
        type=Path,
        default=Path("data/dataset_gold.jsonl"),
        help="input dataset (JSONL)",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("phase4_grounding/outputs"),
        help="directory to write sample.jsonl",
    )
    return p


def _index_records(dataset_path: Path) -> dict[int, dict]:
    idx: dict[int, dict] = {}
    with dataset_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            idx[int(rec["cid"])] = rec
    return idx


def _attach_evidence(row: SampleRow, rec: dict) -> SampleRow:
    qa = next(
        (q for q in rec.get("qa_pairs", []) if int(q.get("qa_index")) == row.qa_index),
        None,
    )
    if qa is None:
        raise RuntimeError(
            f"qa_index {row.qa_index} not found in cid={row.cid}"
        )
    attached = EvidenceAttacher.attach(qa, rec)
    return replace(row, evidence_attached=attached)


def row_to_dict(row: SampleRow) -> dict:
    return {
        "cid": row.cid,
        "qa_index": row.qa_index,
        "topic": row.topic,
        "split": row.split,
        "evidence_ids_nonempty": row.evidence_ids_nonempty,
        "compound": {
            "name": row.compound.name,
            "smiles": row.compound.smiles,
            "molecular_formula": row.compound.molecular_formula,
        },
        "question": row.question,
        "phase2_answer": row.phase2_answer,
        "evidence_attached": [
            {"id": e.id, "text": e.text, "pmid": e.pmid, "source": e.source}
            for e in row.evidence_attached
        ],
    }


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    sampler = Sampler(dataset_path=args.data_path, seed=args.seed)
    rows = sampler.sample(args.n)

    records = _index_records(args.data_path)
    attached_rows = [_attach_evidence(row, records[row.cid]) for row in rows]

    out_path = args.out_dir / "sample.jsonl"
    with out_path.open("w") as f:
        for row in attached_rows:
            f.write(json.dumps(row_to_dict(row)) + "\n")

    print(f"wrote {len(attached_rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
