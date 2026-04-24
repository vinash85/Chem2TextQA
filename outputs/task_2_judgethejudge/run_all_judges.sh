#!/usr/bin/env bash
# Run chemqa_multijudge_parallel.py three times — once per new judge — over
# the 1000-row stratified sample. Each judge writes to its own shards_dir so
# runs can proceed in parallel (just launch in separate shells) and can be
# resumed independently by re-running the same command.
set -euo pipefail

cd "$(dirname "$0")"

INPUT="outputs/multi_judge/samples_input.jsonl"
OUT_DIR="outputs/multi_judge"
KEYS="../../api_keys.txt"
N_PROC="${N_PROC:-25}"   # 4 keys * 25 = 100 workers per judge

mkdir -p "$OUT_DIR"

if [ ! -f "$INPUT" ]; then
  echo "missing $INPUT — run sample_stratified.py first" >&2
  exit 1
fi

JUDGES=(
  "sonnet46:anthropic/claude-sonnet-4.6"
  "gpt5:openai/gpt-5"
  "gemini25pro:google/gemini-2.5-pro"
  "gpt54pro:openai/gpt-5.4-pro"
  "deepseekv4pro:deepseek/deepseek-v4-pro"
)

# Optional: filter by tag via `./run_all_judges.sh sonnet46 gpt5`
if [ "$#" -gt 0 ]; then
  WANTED=("$@")
else
  WANTED=(sonnet46 gpt5 gemini25pro)
fi

for spec in "${JUDGES[@]}"; do
  tag="${spec%%:*}"
  model="${spec#*:}"

  # skip if not in WANTED list
  match=0
  for w in "${WANTED[@]}"; do [ "$w" = "$tag" ] && match=1; done
  [ "$match" -eq 1 ] || continue

  echo
  echo "===== judge: $tag  ($model) ====="
  python3 chemqa_multijudge_parallel.py \
    --input_file   "$INPUT" \
    --output_file  "$OUT_DIR/final_judged_${tag}.jsonl" \
    --shards_dir   "$OUT_DIR/shards_${tag}/" \
    --model        "$model" \
    --api_keys_file "$KEYS" \
    --n_process    "$N_PROC" \
    --merge_output
done
