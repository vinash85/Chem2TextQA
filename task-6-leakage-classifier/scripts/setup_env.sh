#!/usr/bin/env bash
# Creates the chem2text_leakage conda env.
# Idempotent: skips create if the env already exists, still runs pip to fill gaps.
set -euo pipefail

ENV_NAME=chem2text_leakage
PY_VER=3.11

source /opt/anaconda3/etc/profile.d/conda.sh

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo ">>> Env '$ENV_NAME' already exists; skipping create."
else
  echo ">>> Creating conda env '$ENV_NAME' (python=$PY_VER)."
  conda create -y -n "$ENV_NAME" "python=$PY_VER" pip
fi

conda activate "$ENV_NAME"

echo ">>> Installing PyTorch (cu128)."
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cu128

echo ">>> Installing sentence-transformers, tqdm, numpy."
# Pin transformers<5 — transformers 5.x breaks sentence-transformers 5.x
# (ModuleNotFoundError: PreTrainedModel). 4.57.x is the last compatible series.
pip install "sentence-transformers>=3,<6" "transformers<5" "tqdm>=4.66" "numpy<2"

echo ">>> Sanity check."
python -c "import torch, sentence_transformers, numpy, tqdm; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), '| st', sentence_transformers.__version__, '| numpy', numpy.__version__)"

echo ">>> Done. Activate with: conda activate $ENV_NAME"
