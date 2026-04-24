#!/usr/bin/env bash
# Driver: sample -> embed -> score -> summarize.
# Assumes the chem2text_leakage env already exists (run setup_env.sh first).
set -euo pipefail

ENV_NAME=chem2text_leakage
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT=/home/dandreas/chem2text/outputs/leakage
LOG="$OUT/run.log"

mkdir -p "$OUT"

source /opt/anaconda3/etc/profile.d/conda.sh
conda activate "$ENV_NAME"

stamp () { date -u +"[%Y-%m-%dT%H:%M:%SZ]"; }

{
  echo "$(stamp) >>> sample.py"
  python "$HERE/sample.py"

  echo "$(stamp) >>> embed.py"
  python "$HERE/embed.py"

  echo "$(stamp) >>> compute_metrics.py"
  python "$HERE/compute_metrics.py"

  echo "$(stamp) >>> summarize.py"
  python "$HERE/summarize.py"

  echo "$(stamp) >>> done"
} 2>&1 | tee "$LOG"
