"""Judge runner entry point: decomposes each sampled phase2 answer into claims.

Reads `sample.jsonl`, judges each row via `ClaimJudge`, writes successful
rows to `claims_per_qa.jsonl` (resumable) and parse failures to
`claims_per_qa.errors.jsonl`. Aborts on budget-cap violation, preserving
partial output so a re-run picks up where it left off.

`run_judge_pass` is the testable core — `main` just wires up the live
OpenRouterClient.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Protocol

from phase4_grounding.grounding.judge import ClaimJudge, JudgeError
from phase4_grounding.grounding.models import (
    ChatResult,
    Compound,
    EvidenceItem,
    SampleRow,
)
from phase4_grounding.grounding.openrouter_client import BudgetExceeded, OpenRouterClient
from phase4_grounding.grounding.prompt import PromptBuilder


class _ChatClientLike(Protocol):
    spend_usd: float

    async def chat(self, *, model: str, prompt: str, **kwargs: object) -> ChatResult: ...


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Judge sampled QA for grounding audit")
    p.add_argument("--api-key-file", type=Path, default=Path("~/.openrouter_key"))
    p.add_argument("--primary-model", default="anthropic/claude-sonnet-4.6")
    p.add_argument("--cross-check-model", default="google/gemini-2.5-pro")
    p.add_argument("--skip-cross-check", action="store_true")
    p.add_argument("--cross-check-n", type=int, default=30)
    p.add_argument("--max-usd", type=float, default=15.0)
    p.add_argument("--concurrency", type=int, default=5)
    p.add_argument("--out-dir", type=Path, default=Path("phase4_grounding/outputs"))
    return p


def row_from_dict(d: dict) -> SampleRow:
    return SampleRow(
        cid=int(d["cid"]),
        qa_index=int(d["qa_index"]),
        topic=d["topic"],
        split=d["split"],
        evidence_ids_nonempty=bool(d["evidence_ids_nonempty"]),
        compound=Compound(
            cid=int(d["cid"]),
            name=d["compound"]["name"],
            smiles=d["compound"]["smiles"],
            molecular_formula=d["compound"]["molecular_formula"],
        ),
        question=d["question"],
        phase2_answer=d["phase2_answer"],
        evidence_attached=tuple(
            EvidenceItem(
                id=int(e["id"]),
                text=e["text"],
                pmid=e.get("pmid"),
                source=e.get("source"),
            )
            for e in d["evidence_attached"]
        ),
    )


def load_sample(path: Path) -> list[SampleRow]:
    rows: list[SampleRow] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(row_from_dict(json.loads(line)))
    return rows


def already_judged(path: Path) -> set[tuple[int, int]]:
    if not path.exists():
        return set()
    done: set[tuple[int, int]] = set()
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                d = json.loads(line)
                done.add((int(d["cid"]), int(d["qa_index"])))
    return done


def _judged_to_dict(judged) -> dict:
    return {
        "cid": judged.cid,
        "qa_index": judged.qa_index,
        "topic": judged.topic,
        "split": judged.split,
        "evidence_ids_nonempty": judged.evidence_ids_nonempty,
        "num_evidence_attached": judged.num_evidence_attached,
        "model": judged.model,
        "claims": [
            {
                "claim": c.claim,
                "label": c.label,
                "evidence_id": c.evidence_id,
                "rationale": c.rationale,
            }
            for c in judged.claims
        ],
        "usage": {
            "prompt_tokens": judged.prompt_tokens,
            "completion_tokens": judged.completion_tokens,
        },
        "latency_ms": judged.latency_ms,
    }


def _error_to_dict(exc: JudgeError) -> dict:
    return {
        "cid": exc.cid,
        "qa_index": exc.qa_index,
        "model": exc.model,
        "raw": exc.raw,
        "first_error": exc.first_error,
        "second_error": exc.second_error,
    }


async def run_judge_pass(
    rows: list[SampleRow],
    judge: ClaimJudge,
    client: _ChatClientLike,
    *,
    model: str,
    out_path: Path,
    err_path: Path,
    concurrency: int,
) -> int:
    """Judge each row and append its record to out_path (or err_path on parse failure).

    Returns the number of successfully judged rows. Raises `BudgetExceeded` if
    the client refuses a call because the cumulative spend cap was crossed;
    rows already written before the abort are preserved on disk.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    err_path.parent.mkdir(parents=True, exist_ok=True)

    sem = asyncio.Semaphore(concurrency)
    lock = asyncio.Lock()
    success = 0

    with out_path.open("a") as out_f, err_path.open("a") as err_f:

        async def run_one(row: SampleRow) -> None:
            nonlocal success
            async with sem:
                try:
                    judged = await judge.judge(row, model=model)
                except JudgeError as exc:
                    async with lock:
                        err_f.write(json.dumps(_error_to_dict(exc)) + "\n")
                        err_f.flush()
                    return
                async with lock:
                    out_f.write(json.dumps(_judged_to_dict(judged)) + "\n")
                    out_f.flush()
                    success += 1
                    if success % 25 == 0:
                        print(
                            f"judged {success} rows | spend ${client.spend_usd:.4f}"
                        )

        await asyncio.gather(*(run_one(r) for r in rows))

    return success


async def _run(args: argparse.Namespace) -> int:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    sample_path = args.out_dir / "sample.jsonl"
    primary_out = args.out_dir / "claims_per_qa.jsonl"
    primary_err = args.out_dir / "claims_per_qa.errors.jsonl"

    all_rows = load_sample(sample_path)
    done = already_judged(primary_out)
    pending = [r for r in all_rows if (r.cid, r.qa_index) not in done]
    print(
        f"primary pass: {len(pending)} pending / {len(all_rows)} total "
        f"(model: {args.primary_model})"
    )

    api_key = Path(args.api_key_file).expanduser().read_text().strip()
    async with OpenRouterClient(
        api_key=api_key,
        concurrency=args.concurrency,
        max_usd=args.max_usd,
    ) as client:
        judge = ClaimJudge(client, PromptBuilder())
        try:
            await run_judge_pass(
                pending,
                judge,
                client,
                model=args.primary_model,
                out_path=primary_out,
                err_path=primary_err,
                concurrency=args.concurrency,
            )
        except BudgetExceeded as exc:
            print(f"aborting primary pass: {exc}")

        if not args.skip_cross_check:
            xcheck_out = args.out_dir / "claims_per_qa.gemini.jsonl"
            xcheck_err = args.out_dir / "claims_per_qa.gemini.errors.jsonl"
            done_x = already_judged(xcheck_out)
            subset_head = all_rows[: args.cross_check_n]
            pending_x = [r for r in subset_head if (r.cid, r.qa_index) not in done_x]
            print(
                f"cross-check pass: {len(pending_x)} pending / {len(subset_head)} "
                f"(model: {args.cross_check_model})"
            )
            try:
                await run_judge_pass(
                    pending_x,
                    judge,
                    client,
                    model=args.cross_check_model,
                    out_path=xcheck_out,
                    err_path=xcheck_err,
                    concurrency=args.concurrency,
                )
            except BudgetExceeded as exc:
                print(f"aborting cross-check pass: {exc}")

        print(f"final spend: ${client.spend_usd:.4f}")

    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
