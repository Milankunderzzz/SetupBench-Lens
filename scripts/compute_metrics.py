from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path

from common import ROOT


ANNOTATIONS = ROOT / "dataset" / "annotations"
OUTPUT = ROOT / "analysis" / "metrics.json"


def rows(name: str):
    with (ANNOTATIONS / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def metric(tp: int, fp: int, fn: int):
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def main() -> None:
    conditions = rows("ground_truth_conditions.csv")
    reviews = rows("finding_reviews.csv")
    matches = rows("condition_matches.csv")
    humans = rows("human_trials.csv")
    blockers = []
    if not conditions:
        blockers.append("No independently annotated ground-truth conditions")
    if not reviews:
        blockers.append("No SetupLens finding reviews")
    if not matches:
        blockers.append("No adjudicated condition matches")
    if not humans:
        blockers.append("No real blinded human-inspection trials")
    if any(row.get("review_status") != "adjudicated" for row in conditions + reviews):
        blockers.append("Some condition or finding labels are not adjudicated")
    if blockers:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps({"status": "blocked", "blockers": blockers}, indent=2) + "\n", encoding="utf-8")
        raise SystemExit("Metrics blocked:\n- " + "\n- ".join(blockers))

    tp = sum(row["outcome"] == "true_positive" for row in matches)
    fn = sum(row["outcome"] == "false_negative" for row in matches)
    matched_reviews = {row["review_id"] for row in matches if row["review_id"]}
    fp = sum(row["verdict"] == "false_positive" and row["review_id"] not in matched_reviews for row in reviews)
    result = {"status": "complete", "primary": metric(tp, fp, fn)}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

