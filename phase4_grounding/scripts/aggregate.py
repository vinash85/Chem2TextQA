"""Aggregate `claims_per_qa.jsonl` into the dual grounding-summary markdown files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from phase4_grounding.grounding.aggregator import Aggregator
from phase4_grounding.grounding.models import Claim, JudgedQA
from phase4_grounding.grounding.reporter import Reporter


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Aggregate judged claims into summaries")
    p.add_argument("--out-dir", type=Path, default=Path("phase4_grounding/outputs"))
    p.add_argument(
        "--claims-file",
        type=str,
        default="claims_per_qa.jsonl",
        help="filename inside --out-dir to read",
    )
    return p


def load_judged(path: Path) -> list[JudgedQA]:
    judged: list[JudgedQA] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            judged.append(_judged_from_dict(d))
    return judged


def _judged_from_dict(d: dict) -> JudgedQA:
    claims = tuple(
        Claim(
            claim=c["claim"],
            label=c["label"],
            evidence_id=c.get("evidence_id"),
            rationale=c.get("rationale", ""),
        )
        for c in d.get("claims", [])
    )
    usage = d.get("usage") or {}
    return JudgedQA(
        cid=int(d["cid"]),
        qa_index=int(d["qa_index"]),
        topic=d["topic"],
        evidence_ids_nonempty=bool(d.get("evidence_ids_nonempty", False)),
        num_evidence_attached=int(d.get("num_evidence_attached", 0)),
        model=d.get("model", ""),
        claims=claims,
        prompt_tokens=int(usage.get("prompt_tokens", 0)),
        completion_tokens=int(usage.get("completion_tokens", 0)),
        latency_ms=int(d.get("latency_ms", 0)),
        split=d.get("split", ""),
    )


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    claims_path = args.out_dir / args.claims_file
    judged = load_judged(claims_path)

    aggregator = Aggregator(judged)
    metrics_keep = aggregator.compute("keep")
    metrics_drop = aggregator.compute("drop")

    reporter = Reporter(metrics_keep, metrics_drop, judged)
    keep_path, drop_path = reporter.write(args.out_dir)

    print(f"wrote {keep_path}")
    print(f"wrote {drop_path}")
    print(
        f"keep-view UNSUPPORTED rate: {metrics_keep.unsupported_rate * 100:.2f}% "
        f"(n_claims={metrics_keep.total_claims})"
    )
    print(
        f"drop-view UNSUPPORTED rate: {metrics_drop.unsupported_rate * 100:.2f}% "
        f"(n_claims={metrics_drop.total_claims})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
