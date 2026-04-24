import json
from collections import defaultdict
import os

def compute_agree_rates(file_path):
    stats = defaultdict(lambda: {"agree": 0, "total": 0})

    with open(file_path, "r") as f:
        for line in f:
            data = json.loads(line)

            for qa in data.get("qa_pairs", []):
                topic = qa.get("topic")
                verdict = qa.get("verdict")

                if topic is None or verdict is None:
                    continue

                stats[topic]["total"] += 1
                if verdict == "agree":
                    stats[topic]["agree"] += 1

    # compute rates
    result = {}
    for topic, v in stats.items():
        total = v["total"]
        agree = v["agree"]
        rate = agree / total if total > 0 else 0

        result[topic] = {
            "agree": agree,
            "total": total,
            "agree_rate": round(rate, 4)
        }

    return result


# === paths ===
main_path = "dataset_gold.jsonl"
canary_path = "dataset_final.jsonl"

main_stats = compute_agree_rates(main_path)
canary_stats = compute_agree_rates(canary_path)

# merge results
all_topics = set(main_stats) | set(canary_stats)

output = {}

for topic in all_topics:
    main = main_stats.get(topic, {"agree": 0, "total": 0, "agree_rate": 0})
    canary = canary_stats.get(topic, {"agree": 0, "total": 0, "agree_rate": 0})

    output[topic] = {
        "main": main,
        "canary": canary,
        "delta": round(main["agree_rate"] - canary["agree_rate"], 4),
        "difference": round(main["agree_rate"] - canary["agree_rate"], 4),
        "delta_pp": round((main["agree_rate"] - canary["agree_rate"]) * 100, 2)
    }

sorted_output = dict(
    sorted(output.items(), key=lambda x: x[1]["delta"], reverse=True)
)

# save
os.makedirs("canary_analysiscanary_analysis", exist_ok=True)

with open("canary_analysiscanary_analysis/per_bucket_agree_rates.json", "w") as f:
    json.dump(sorted_output, f, indent=2)

print("Saved to canary_analysiscanary_analysis/per_bucket_agree_rates.json")