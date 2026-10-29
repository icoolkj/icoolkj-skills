#!/usr/bin/env python3
"""Evaluate predictions against a human-labelled JSONL set.

Each line contains: {"id", "facts_supported": [...], "topic_pairs_independent": [...],
"risks_detected": [...]}. Predictions use the same keys. This is an evaluation
instrument, not a substitute for human adjudication.
"""
import argparse
import json


def f1(expected, actual):
    expected, actual = set(expected), set(actual)
    if not expected and not actual: return 1.0, 1.0, 1.0
    if not actual: return 0.0, 0.0, 0.0
    precision = len(expected & actual) / len(actual)
    recall = len(expected & actual) / len(expected) if expected else 0.0
    return precision, recall, 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def evaluate(gold_path, prediction_path):
    with open(gold_path, encoding="utf-8") as handle:
        gold = {row["id"]: row for row in map(json.loads, handle) if row.get("id")}
    with open(prediction_path, encoding="utf-8") as handle:
        predicted = {row["id"]: row for row in map(json.loads, handle) if row.get("id")}
    metrics = {}
    for field in ("facts_supported", "topic_pairs_independent", "risks_detected"):
        scores = [f1(gold[item].get(field, []), predicted.get(item, {}).get(field, [])) for item in gold if item in predicted]
        if scores:
            metrics[field] = {name: round(sum(score[i] for score in scores) / len(scores), 3) for i, name in enumerate(("precision", "recall", "f1"))}
    return {"items": len(gold), "predicted_items": len(predicted), "metrics": metrics,
            "note": "指标只反映与人工标注的一致性；语义裁决仍需复核。"}


def main():
    parser = argparse.ArgumentParser(description="评估事实支持、选题独立性和风险识别")
    parser.add_argument("--gold", required=True)
    parser.add_argument("--predictions", required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.gold, args.predictions), ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
