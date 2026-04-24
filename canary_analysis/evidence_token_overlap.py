import json
import os
import re
from collections import defaultdict

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")

def tokenize(text):
    return TOKEN_RE.findall((text or "").lower())

def safe_rate(num, den):
    return num / den if den else 0.0

def compute_file_stats(path):
    overall = {"overlap_tokens": 0, "answer_tokens": 0, "num_qas": 0}
    by_topic = defaultdict(lambda: {"overlap_tokens": 0, "answer_tokens": 0, "num_qas": 0})

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            row = json.loads(line)

            evidence_text = " ".join(
                ev.get("text", "")
                for ev in row.get("evidence_sentences", [])
            )
            evidence_vocab = set(tokenize(evidence_text))

            for qa in row.get("qa_pairs", []):
                topic = qa.get("topic", "UNKNOWN")
                answer_tokens = tokenize(qa.get("phase1_answer", ""))

                if not answer_tokens:
                    continue

                overlap = sum(1 for tok in answer_tokens if tok in evidence_vocab)
                total = len(answer_tokens)

                overall["overlap_tokens"] += overlap
                overall["answer_tokens"] += total
                overall["num_qas"] += 1

                by_topic[topic]["overlap_tokens"] += overlap
                by_topic[topic]["answer_tokens"] += total
                by_topic[topic]["num_qas"] += 1

    overall["token_overlap_rate"] = safe_rate(
        overall["overlap_tokens"], overall["answer_tokens"]
    )

    by_topic_out = {}
    for topic, stats in by_topic.items():
        stats = dict(stats)
        stats["token_overlap_rate"] = safe_rate(
            stats["overlap_tokens"], stats["answer_tokens"]
        )
        by_topic_out[topic] = stats

    return overall, by_topic_out

def pp(x):
    return 100 * x

def main():
    main_path = "dataset_gold.jsonl"
    canary_path = "dataset_final.jsonl"
    output_path = "canary_analysis/evidence_token_overlap.json"

    main_overall, main_by_topic = compute_file_stats(main_path)
    canary_overall, canary_by_topic = compute_file_stats(canary_path)

    all_topics = sorted(set(main_by_topic) | set(canary_by_topic))

    output = {
        "overall": {
            "main": main_overall,
            "canary": canary_overall,
            "delta_main_minus_canary": (
                main_overall["token_overlap_rate"]
                - canary_overall["token_overlap_rate"]
            ),
            "delta_main_minus_canary_pp": pp(
                main_overall["token_overlap_rate"]
                - canary_overall["token_overlap_rate"]
            ),
        },
        "by_topic": {},
    }

    empty = {
        "overlap_tokens": 0,
        "answer_tokens": 0,
        "num_qas": 0,
        "token_overlap_rate": 0.0,
    }

    for topic in all_topics:
        m = main_by_topic.get(topic, empty)
        c = canary_by_topic.get(topic, empty)

        output["by_topic"][topic] = {
            "main": m,
            "canary": c,
            "delta_main_minus_canary": (
                m["token_overlap_rate"] - c["token_overlap_rate"]
            ),
            "delta_main_minus_canary_pp": pp(
                m["token_overlap_rate"] - c["token_overlap_rate"]
            ),
        }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Saved to {output_path}")

if __name__ == "__main__":
    main()