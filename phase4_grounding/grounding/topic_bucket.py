"""Re-export `bucket_topic` from the repo's `scripts/topic_bucket.py` without depending
on `scripts/` being an importable package.

A single source of truth avoids drift between phase4_grounding and the rest of the
pipeline. The loader uses importlib so this module works whether or not the project
is installed in editable mode.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "topic_bucket.py"

_spec = importlib.util.spec_from_file_location("_topic_bucket_repo", _SCRIPT_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load topic_bucket from {_SCRIPT_PATH}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

bucket_topic = _module.bucket_topic
