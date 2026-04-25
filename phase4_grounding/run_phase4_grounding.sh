#!/usr/bin/env bash
# Phase 4 grounding-audit orchestrator.
#
# Three-step pipeline (resumable; safe to re-run):
#   1. sample_qa.py
#   2. judge_claims.py
#   3. aggregate.py
#
# Usage:
#   bash phase4_grounding/run_phase4_grounding.sh \
#       --n 300 \
#       --api-key-file ~/.openrouter_key \
#       [--skip-cross-check] \
#       [--data-path data/dataset_gold.jsonl] \
#       [--out-dir phase4_grounding/outputs] \
#       [--primary-model anthropic/claude-sonnet-4.6] \
#       [--cross-check-model google/gemini-2.5-pro] \
#       [--cross-check-n 30] \
#       [--max-usd 15] \
#       [--concurrency 5] \
#       [--seed 0]
set -euo pipefail

N=""
API_KEY_FILE="$HOME/.openrouter_key"
DATA_PATH="data/dataset_gold.jsonl"
OUT_DIR="phase4_grounding/outputs"
PRIMARY_MODEL="anthropic/claude-sonnet-4.6"
CROSS_CHECK_MODEL="google/gemini-2.5-pro"
CROSS_CHECK_N=30
MAX_USD=15
CONCURRENCY=5
SEED=0
SKIP_CROSS_CHECK=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --n) N="$2"; shift 2 ;;
    --api-key-file) API_KEY_FILE="$2"; shift 2 ;;
    --data-path) DATA_PATH="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --primary-model) PRIMARY_MODEL="$2"; shift 2 ;;
    --cross-check-model) CROSS_CHECK_MODEL="$2"; shift 2 ;;
    --cross-check-n) CROSS_CHECK_N="$2"; shift 2 ;;
    --max-usd) MAX_USD="$2"; shift 2 ;;
    --concurrency) CONCURRENCY="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --skip-cross-check) SKIP_CROSS_CHECK=1; shift ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$N" ]]; then
  echo "error: --n is required" >&2
  exit 2
fi

mkdir -p "$OUT_DIR"

echo "==> [1/3] sample_qa.py --n $N --seed $SEED"
python -m phase4_grounding.scripts.sample_qa \
  --n "$N" \
  --seed "$SEED" \
  --data-path "$DATA_PATH" \
  --out-dir "$OUT_DIR"

echo "==> [2/3] judge_claims.py"
xcheck_flag=()
if [[ "$SKIP_CROSS_CHECK" -eq 1 ]]; then
  xcheck_flag+=(--skip-cross-check)
fi
python -m phase4_grounding.scripts.judge_claims \
  --api-key-file "$API_KEY_FILE" \
  --primary-model "$PRIMARY_MODEL" \
  --cross-check-model "$CROSS_CHECK_MODEL" \
  --cross-check-n "$CROSS_CHECK_N" \
  --max-usd "$MAX_USD" \
  --concurrency "$CONCURRENCY" \
  --out-dir "$OUT_DIR" \
  "${xcheck_flag[@]}"

echo "==> [3/3] aggregate.py"
python -m phase4_grounding.scripts.aggregate --out-dir "$OUT_DIR"

echo "==> done. Outputs under: $OUT_DIR"
