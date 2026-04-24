"""Flatten dataset_final.jsonl (compound-level, with nested qa_pairs) into the
flat {cid, smiles, qa_index, topic, prompt, response} schema used by
generate_vllm.py / score.py.

prompt = "{smiles}\n{question}"  (matches data/processed/test.jsonl format)
response = qa_pairs[i].phase2_answer
"""
from __future__ import annotations
import argparse, json
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input_file", default="/data/yue/Luis_data/dataset_final.jsonl")
    p.add_argument("--output_file",
                   default="/data/yue/Luis_data/ChemQA/data/processed/dataset_final_flat.jsonl")
    return p.parse_args()


def main():
    args = parse_args()
    out_path = Path(args.output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_compounds = 0
    n_qa = 0
    n_skipped = 0
    with open(args.input_file) as fin, open(out_path, "w") as fout:
        for line in fin:
            rec = json.loads(line)
            n_compounds += 1
            smiles = rec.get("smiles", "")
            cid = rec.get("cid")
            for qa in rec.get("qa_pairs", []):
                question = qa.get("question", "").strip()
                answer = qa.get("phase2_answer", "").strip()
                if not question or not answer:
                    n_skipped += 1
                    continue
                fout.write(json.dumps({
                    "cid": cid,
                    "smiles": smiles,
                    "qa_index": qa.get("qa_index"),
                    "topic": qa.get("topic"),
                    "prompt": f"{smiles}\n{question}",
                    "response": answer,
                }, ensure_ascii=False) + "\n")
                n_qa += 1
    print(f"[prep] compounds={n_compounds} qa_written={n_qa} skipped={n_skipped} -> {out_path}")


if __name__ == "__main__":
    main()
