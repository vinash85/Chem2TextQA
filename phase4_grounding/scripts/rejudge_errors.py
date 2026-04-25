"""One-shot rejudge for rows that landed in claims_per_qa.errors.jsonl.

Targets two failure modes seen on the 300-item production run:
  * `raw=None` from OpenRouter (refusal / empty content)
  * truncated JSON (provider-side default max_tokens cutoff)

Strategy: re-run primary judging on those rows with an explicit
max_tokens=8000 cap. Successful rejudgments are appended to
claims_per_qa.jsonl; the errors file is rewritten with only items that
still failed after this attempt.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

PHASE4_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHASE4_ROOT.parent))

from phase4_grounding.grounding.judge import JudgeError
from phase4_grounding.grounding.openrouter_client import OpenRouterClient
from phase4_grounding.grounding.parser import ClaimParser
from phase4_grounding.grounding.prompt import PromptBuilder
from phase4_grounding.scripts.judge_claims import (
    _error_to_dict,
    _judged_to_dict,
    row_from_dict,
)
from phase4_grounding.grounding.models import JudgedQA

OUT_DIR = PHASE4_ROOT / "outputs"
SAMPLE = OUT_DIR / "sample.jsonl"
PRIMARY_OUT = OUT_DIR / "claims_per_qa.jsonl"
ERRORS = OUT_DIR / "claims_per_qa.errors.jsonl"
KEY_PATH = Path("~/.openrouter_key").expanduser()
MODEL = "google/gemini-2.5-pro"
MAX_TOKENS = 8000
CONCURRENCY = 4


async def _judge_once(client, prompt_builder, parser, row, model, max_tokens):
    prompt = prompt_builder.build(row)
    attached_ids = {e.id for e in row.evidence_attached}
    first = await client.chat(model=model, prompt=prompt, max_tokens=max_tokens)
    first_parsed = parser.parse(first.text, attached_ids)
    if first_parsed.ok:
        return _make_judged(row, model, first_parsed, [first]), None

    retry_prompt = prompt + (
        "\n\nYour previous output was not valid JSON. Return only the JSON "
        "object — no markdown fences, no commentary."
    )
    second = await client.chat(model=model, prompt=retry_prompt, max_tokens=max_tokens)
    second_parsed = parser.parse(second.text, attached_ids)
    if second_parsed.ok:
        return _make_judged(row, model, second_parsed, [first, second]), None

    err = JudgeError(
        "rejudge: failed JSON parse on both attempts",
        cid=row.cid,
        qa_index=row.qa_index,
        model=model,
        raw=second.text,
        first_error=first_parsed.error,
        second_error=second_parsed.error,
    )
    return None, err


def _make_judged(row, model, parsed, chats) -> JudgedQA:
    return JudgedQA(
        cid=row.cid,
        qa_index=row.qa_index,
        topic=row.topic,
        evidence_ids_nonempty=row.evidence_ids_nonempty,
        num_evidence_attached=len(row.evidence_attached),
        model=model,
        claims=parsed.claims,
        prompt_tokens=sum(c.prompt_tokens for c in chats),
        completion_tokens=sum(c.completion_tokens for c in chats),
        latency_ms=sum(c.latency_ms for c in chats),
        split=row.split,
    )


async def main() -> int:
    error_keys = []
    with ERRORS.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            error_keys.append((d["cid"], d["qa_index"]))

    if not error_keys:
        print("no errored rows — nothing to do")
        return 0

    error_set = set(error_keys)
    print(f"rejudging {len(error_set)} rows: {sorted(error_set)}")

    rows_by_key = {}
    with SAMPLE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            key = (int(d["cid"]), int(d["qa_index"]))
            if key in error_set:
                rows_by_key[key] = row_from_dict(d)

    missing = error_set - rows_by_key.keys()
    if missing:
        print(f"WARNING: {len(missing)} errored rows not in sample.jsonl: {sorted(missing)}")

    rows = [rows_by_key[k] for k in error_set if k in rows_by_key]

    api_key = KEY_PATH.read_text().strip()

    builder = PromptBuilder()
    parser = ClaimParser()
    sem = asyncio.Semaphore(CONCURRENCY)

    successes: list = []
    failures: list = []

    async with OpenRouterClient(api_key=api_key, concurrency=CONCURRENCY, max_usd=2.0) as client:
        async def go(row):
            async with sem:
                return await _judge_once(client, builder, parser, row, MODEL, MAX_TOKENS)

        results = await asyncio.gather(*(go(r) for r in rows), return_exceptions=True)

        for row, result in zip(rows, results):
            if isinstance(result, Exception):
                print(f"  {row.cid}/{row.qa_index}: EXCEPTION {type(result).__name__}: {result}")
                continue
            judged, err = result
            if judged is not None:
                successes.append(judged)
                print(f"  {row.cid}/{row.qa_index}: OK ({len(judged.claims)} claims)")
            else:
                failures.append(err)
                print(f"  {row.cid}/{row.qa_index}: STILL FAILED ({err.first_error}; {err.second_error})")

        print(f"\nrejudge spend: ${client.spend_usd:.4f}")

    if successes:
        with PRIMARY_OUT.open("a") as f:
            for j in successes:
                f.write(json.dumps(_judged_to_dict(j)) + "\n")

    with ERRORS.open("w") as f:
        for err in failures:
            f.write(json.dumps(_error_to_dict(err)) + "\n")

    print(f"\nappended {len(successes)} rows to {PRIMARY_OUT.name}")
    print(f"rewrote {ERRORS.name} with {len(failures)} remaining errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
