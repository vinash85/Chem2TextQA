#!/usr/bin/env python3
"""Parallel multi-judge runner for Task 2 (ChemQA multi-judge panel).

Forked from ../../LLMasJudge_openrouter_parallel.py. Keeps the same
sharding / resume / merge skeleton (multiprocessing, round-robin across API
keys, per-shard JSONL for resumability, optional final merge), and swaps out
the QAProt 5-criteria prompt for the Chem2TextQA Phase-3 verdict prompt
(JUDGE_SYSTEM_PROMPT, copied verbatim from judge.py).

Input rows (from sample_stratified.py) look like:
    {"cid":..., "qa_index":..., "question":..., "phase1_answer":...,
     "phase2_answer":..., "gemma_verdict":..., ...}

Output rows:
    {cid, qa_index, key, model, verdict, reasoning, error?, llm_response,
     full_response, ...input fields...}

The judge is called at temperature=0 with reasoning disabled, matching the
settings used by the original Phase-3 Gemma run.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from multiprocessing import Process, current_process
from pathlib import Path

import requests
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Judge prompt — copied verbatim from judge.py to avoid the chem2textqa
# package dependency chain. Keep in sync if JUDGE_SYSTEM_PROMPT ever changes.
# ---------------------------------------------------------------------------
JUDGE_SYSTEM_PROMPT = """You are a judge evaluating whether two independent \
answers to the same question about a chemical compound agree with each other.

Both answers were produced blind to each other — they never saw each other's \
reply. Your job is to classify the agreement level as agree, disagree, or \
unclear.

Use:
  "agree"    — both answers reach the same substantive conclusion on the main \
claim, even if phrased differently or with different levels of detail. Minor \
wording differences, partial overlap on supplementary details, or one answer \
being more concise than the other still counts as agree.
  "disagree" — the answers contradict each other on the main claim (e.g., one \
says yes and the other says no; one says 3 rings and the other says 1 ring).
  "unclear"  — the two answers address different aspects of the question, one \
says "N/A" / "cannot determine", or both are so vague that comparing them is \
not meaningful.

WORKED EXAMPLES:

Example A (agree):
  QUESTION: How many rotatable bonds does the compound have?
  ANSWER 1: Approximately 5 rotatable bonds, located in the aliphatic chain \
and the ester linkage.
  ANSWER 2: The compound has about 5 rotatable bonds, primarily in the side chain.
  → {"verdict": "agree", "reasoning": "Both report the same count (~5) and \
attribute it to the same flexible region; wording differs but substance matches."}

Example B (disagree):
  QUESTION: Does the compound contain a nitro group?
  ANSWER 1: Yes, there is a nitro group attached to the aromatic ring.
  ANSWER 2: No, the compound has no nitro functionality; the nitrogen is part \
of an amine.
  → {"verdict": "disagree", "reasoning": "Direct contradiction on whether a \
nitro group is present."}

Example C (unclear):
  QUESTION: What is the aromaticity pattern of the compound?
  ANSWER 1: The molecule contains one aromatic benzene ring.
  ANSWER 2: N/A — the question cannot be answered without 3D coordinates.
  → {"verdict": "unclear", "reasoning": "One answer addresses the question, \
the other declines to answer, so they cannot be compared."}

Output JSON only, matching exactly this shape:
{
  "verdict": "agree" | "disagree" | "unclear",
  "reasoning": "<one or two sentences>"
}"""


def _judge_user_prompt(question: str, a1: str, a2: str) -> str:
    return (
        f"QUESTION: {question}\n\n"
        f"ANSWER 1: {a1}\n\n"
        f"ANSWER 2: {a2}\n\n"
        f"Do the two answers agree? Output JSON only."
    )


def _extract_json(response: str) -> dict | None:
    if not response:
        return None
    text = response.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                return None
        return None


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------
def load_rows(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith(".jsonl"):
            return [json.loads(line) for line in f if line.strip()]
        return json.load(f)


def read_api_keys(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def safe_model_tag(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_") or "model"


def ensure_parent(p: str) -> None:
    d = os.path.dirname(os.path.abspath(p))
    if d:
        os.makedirs(d, exist_ok=True)


def record_key(row: dict) -> str:
    cid = row.get("cid")
    qi = row.get("qa_index")
    return f"{cid}:{qi}"


# ---------------------------------------------------------------------------
# OpenRouter wrapper
# ---------------------------------------------------------------------------
class OpenRouter:
    """Per-worker client. Reads OPENROUTER_APIKEY from env."""

    URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, timeout: float = 300.0, max_tokens: int = 2000):
        self.api_key = os.getenv("OPENROUTER_APIKEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_APIKEY environment variable not set")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.timeout = timeout
        self.max_tokens = max_tokens

    def judge(self, model: str, question: str, a1: str, a2: str) -> dict:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": _judge_user_prompt(question, a1, a2)},
            ],
            "temperature": 0.0,
            "max_tokens": self.max_tokens,
            # NOTE: do NOT send {"reasoning": {"enabled": False}} — GPT-5 and
            # Gemini 2.5 Pro reject that over OpenRouter ("reasoning is
            # mandatory"). Default reasoning on those judges is fine; the
            # verdict is determined by the final JSON, not the reasoning.
        }
        r = requests.post(
            self.URL, headers=self.headers,
            data=json.dumps(payload), timeout=self.timeout,
        )
        return r.json()


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------
def process_chunk(
    items: list[dict],
    model_name: str,
    shard_path: str,
    api_key: str,
    max_tokens: int = 2000,
) -> None:
    os.environ["OPENROUTER_APIKEY"] = api_key
    router = OpenRouter(max_tokens=max_tokens)

    processed: set[str] = set()
    if os.path.exists(shard_path):
        with open(shard_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    j = json.loads(line)
                    if "key" in j:
                        processed.add(j["key"])
                except json.JSONDecodeError:
                    continue

    ensure_parent(shard_path)
    with open(shard_path, "a", encoding="utf-8") as out_f:
        pbar = tqdm(items, desc=f"{current_process().name} {model_name}")
        for row in pbar:
            key = record_key(row)
            if key in processed:
                continue

            q = (row.get("question") or "").strip()
            a1 = (row.get("phase1_answer") or "").strip()
            a2 = (row.get("phase2_answer") or "").strip()

            if not (q and a1 and a2):
                out_f.write(json.dumps({
                    **row, "key": key, "model": model_name,
                    "verdict": None, "reasoning": "",
                    "error": "missing question / phase1_answer / phase2_answer",
                }, ensure_ascii=False) + "\n")
                out_f.flush()
                continue

            try:
                rsp = router.judge(model_name, q, a1, a2)
                if "error" in rsp and "choices" not in rsp:
                    raise RuntimeError(str(rsp["error"]))

                content = (
                    rsp.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                parsed = _extract_json(content or "")
                verdict: str | None = None
                reasoning = ""
                err: str | None = None
                if parsed is None:
                    err = "could not parse JSON"
                else:
                    v = (parsed.get("verdict") or "").strip().lower()
                    reasoning = parsed.get("reasoning", "") or ""
                    if v in ("agree", "disagree", "unclear"):
                        verdict = v
                    else:
                        err = f"invalid verdict: {v!r}"

                record_out = {
                    **row,
                    "key": key,
                    "model": model_name,
                    "verdict": verdict,
                    "reasoning": reasoning,
                    "llm_response": content,
                    "full_response": rsp,
                }
                if err:
                    record_out["error"] = err

            except Exception as exc:  # noqa: BLE001
                record_out = {
                    **row, "key": key, "model": model_name,
                    "verdict": None, "reasoning": "",
                    "error": str(exc),
                }

            out_f.write(json.dumps(record_out, ensure_ascii=False) + "\n")
            out_f.flush()


# ---------------------------------------------------------------------------
# Merge shards
# ---------------------------------------------------------------------------
def merge_shards(shard_paths: list[str], merged_output: str) -> None:
    ensure_parent(merged_output)
    rows: list[dict] = []
    seen: set[str] = set()
    for p in shard_paths:
        if not os.path.exists(p):
            continue
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                k = r.get("key")
                if k in seen:
                    continue
                if k is not None:
                    seen.add(k)
                rows.append(r)
    rows.sort(key=lambda x: (x.get("cid") or 0, x.get("qa_index") or 0))
    with open(merged_output, "w", encoding="utf-8") as out_f:
        for r in rows:
            out_f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    here = Path(__file__).resolve().parent
    default_keys = here.parent.parent / "api_keys.txt"

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input_file", required=True,
                    help="JSONL from sample_stratified.py")
    ap.add_argument("--output_file", required=True,
                    help="Merged output JSONL (written only with --merge_output)")
    ap.add_argument("--model", required=True,
                    help="OpenRouter model ID (e.g. anthropic/claude-sonnet-4.6)")
    ap.add_argument("--api_keys_file", default=str(default_keys),
                    help="One OpenRouter API key per line (default: repo-root api_keys.txt)")
    ap.add_argument("--n_process", type=int, default=25,
                    help="Processes per API key")
    ap.add_argument("--shards_dir", default=None,
                    help="Where to write shard JSONLs (default: dir of --output_file)")
    ap.add_argument("--merge_output", action="store_true",
                    help="Merge all shard files into --output_file after completion")
    ap.add_argument("--max_tokens", type=int, default=2000,
                    help="OpenRouter max_tokens (raise for reasoning-heavy models)")
    args = ap.parse_args()

    rows = load_rows(args.input_file)
    api_keys = read_api_keys(args.api_keys_file)
    if not api_keys:
        print(f"ERROR: no API keys in {args.api_keys_file}", file=sys.stderr)
        return 1

    total_proc = max(1, len(api_keys) * max(1, args.n_process))
    chunk_size = max(1, math.ceil(len(rows) / total_proc))

    base_out = os.path.splitext(os.path.abspath(args.output_file))[0]
    shards_dir = (
        os.path.abspath(args.shards_dir) if args.shards_dir
        else os.path.dirname(base_out)
    )
    os.makedirs(shards_dir, exist_ok=True)
    model_tag = safe_model_tag(args.model)

    procs: list[Process] = []
    shard_paths: list[str] = []
    for idx in range(total_proc):
        start = idx * chunk_size
        end = min((idx + 1) * chunk_size, len(rows))
        chunk = rows[start:end]
        if not chunk:
            continue
        api_key = api_keys[idx % len(api_keys)]
        shard_path = os.path.join(
            shards_dir,
            f"{os.path.basename(base_out)}_{model_tag}_part{idx}.jsonl",
        )
        shard_paths.append(shard_path)
        p = Process(
            target=process_chunk,
            args=(chunk, args.model, shard_path, api_key, args.max_tokens),
            name=f"Proc-{idx}",
        )
        p.start()
        procs.append(p)

    for p in procs:
        p.join()

    print(f"Completed {len(shard_paths)} shard(s) for model {args.model}.")

    if args.merge_output:
        print("Merging shards...")
        merge_shards(shard_paths, args.output_file)
        print(f"Merged output written to: {args.output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
