#!/usr/bin/env bash
# Eval the 6 model x variant combos on dataset_final (canary split).
# Mirrors run_full_vllm.sh but adapted for: local repo path, conda python310 env,
# 4 GPUs (vs original 6) so 6 jobs run as wave 4 + wave 2.
set -euo pipefail

REPO=/data/yue/Luis_data/ChemQA
export HF_HOME=/home/yue/.cache/huggingface
export TOKENIZERS_PARALLELISM=false
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH

source /data/yue/anaconda3/etc/profile.d/conda.sh
conda activate python310

RAW=/data/yue/Luis_data/dataset_final.jsonl
TEST=$REPO/data/processed/dataset_final_flat.jsonl
N=${N:-1000000}
MAX_NEW=${MAX_NEW:-256}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-1024}
GPU_UTIL=${GPU_UTIL:-0.95}
OUT_ROOT=$REPO/eval/results_dataset_final
mkdir -p $OUT_ROOT

# 1) Flatten qa_pairs -> {prompt, response}
python3 $REPO/eval/scripts/prep_dataset_final.py \
  --input_file "$RAW" --output_file "$TEST"

run () {
  local gpu=$1 tag=$2 base=$3 adapter=$4
  local out=$OUT_ROOT/$tag.jsonl
  local log=$OUT_ROOT/$tag.log
  mkdir -p "$(dirname "$out")"
  local ADAPTER_ARG=""
  [ -n "$adapter" ] && ADAPTER_ARG="--adapter_dir $adapter"
  echo ">>> [gpu=$gpu] $tag"
  CUDA_VISIBLE_DEVICES=$gpu python3 $REPO/eval/scripts/generate_vllm.py \
    --base_model "$base" $ADAPTER_ARG \
    --input_file "$TEST" --output_file "$out" \
    --num_samples $N --max_new_tokens $MAX_NEW \
    --max_model_len $MAX_MODEL_LEN \
    --gpu_memory_utilization $GPU_UTIL \
    > "$log" 2>&1
}

# Wave 1: Qwen + Llama (base + ft) on GPUs 0-3
run 0 qwen2_5_14b/base_chemqa   Qwen/Qwen2.5-14B-Instruct       "" &
run 1 qwen2_5_14b/ft_chemqa     Qwen/Qwen2.5-14B-Instruct       $REPO/checkpoints/qwen2_5_14b_chemqa/final &
run 2 llama3_1_8b/base_chemqa   meta-llama/Llama-3.1-8B-Instruct "" &
run 3 llama3_1_8b/ft_chemqa     meta-llama/Llama-3.1-8B-Instruct $REPO/checkpoints/llama3_1_8b_chemqa/final &
wait
echo ">>> wave 1 (qwen + llama) done"

# Wave 2: Gemma (base + ft) on GPUs 0-1
run 0 gemma3_12b/base_chemqa    unsloth/gemma-3-12b-it          "" &
run 1 gemma3_12b/ft_chemqa      unsloth/gemma-3-12b-it          $REPO/checkpoints/gemma3_12b_chemqa/final &
wait
echo ">>> wave 2 (gemma) done"

# Score every predictions file (skip ones already scored)
for p in $OUT_ROOT/*/*.jsonl; do
  [ -f "${p%.jsonl}.metrics.json" ] && continue
  python3 $REPO/eval/scripts/score.py --pred_file "$p"
done

# Summary table — CIDEr / BLEU-1 / BLEU-4 / ROUGE-L
RESULTS_DIR=$OUT_ROOT python3 - <<'PY' > $OUT_ROOT/summary.md
import os, json
from pathlib import Path
ROOT = Path(os.environ['RESULTS_DIR'])
rows = []
for p in sorted(ROOT.rglob('*.metrics.json')):
    m = json.loads(p.read_text())
    tag = p.relative_to(ROOT).with_suffix('').as_posix().replace('.metrics','')
    model, cond = tag.split('/', 1)
    variant = 'base' if cond.startswith('base') else 'finetuned'
    rows.append((model, variant, m.get('n'), m.get('CIDEr'), m.get('BLEU-1'),
                 m.get('BLEU-4'), m.get('ROUGE-L')))
print('# dataset_final Evaluation Results\n')
print('Flattened from `dataset_final.jsonl` (compound-level QA pairs); reference = `phase2_answer`.\n')
print('| model | variant | n | CIDEr | BLEU-1 | BLEU-4 | ROUGE-L |')
print('|---|---|---|---|---|---|---|')
for model, variant, n, cider, b1, b4, rl in sorted(rows):
    print(f'| {model} | {variant} | {n} | {cider:.4f} | {b1:.4f} | {b4:.4f} | {rl:.4f} |')
PY
echo ">>> summary -> $OUT_ROOT/summary.md"
cat $OUT_ROOT/summary.md
