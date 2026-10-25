#!/usr/bin/env python3
"""
Benchmark and Evaluation Dataset Tool.
Calculates Confusion Matrix, Precision, Recall, F1 and reports False Negatives
against ground-truth labeled samples.
"""
import argparse
import json
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.job_policy import deterministic_filter


def compute_metrics(eval_results):
    tp = sum(1 for r in eval_results if r["predicted"] == "relevant" and r["expected"] == "relevant")
    fp = sum(1 for r in eval_results if r["predicted"] == "relevant" and r["expected"] == "irrelevant")
    tn = sum(1 for r in eval_results if r["predicted"] == "irrelevant" and r["expected"] == "irrelevant")
    fn = sum(1 for r in eval_results if r["predicted"] == "irrelevant" and r["expected"] == "relevant")

    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall and (precision + recall) > 0) else None

    false_negatives = [r for r in eval_results if r["predicted"] == "irrelevant" and r["expected"] == "relevant"]

    return {
        "total_samples": len(eval_results),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_negatives": false_negatives
    }


def evaluate_dataset_file(filepath, include_borderline=False):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data.get("samples", [])
    results = []

    for s in samples:
        expected = s.get("expected_label")
        if expected == "borderline":
            if not include_borderline:
                continue
            expected = "relevant"

        if expected not in ("relevant", "irrelevant"):
            continue

        job_dict = {
            "title": s.get("title", ""),
            "company": s.get("company", ""),
            "snippet": s.get("snippet", "")
        }

        # Apply deterministic gating rules
        rejection = deterministic_filter(job_dict)
        if rejection:
            predicted = "irrelevant"
            pred_reason = f"Deterministic filter: {rejection.get('disqualification_reason')}"
        else:
            # Passes deterministic stage
            predicted = "relevant"
            pred_reason = "Passed deterministic gate"

        results.append({
            "sample_id": s.get("sample_id"),
            "title": s.get("title"),
            "company": s.get("company"),
            "expected": expected,
            "predicted": predicted,
            "reason": pred_reason,
            "user_notes": s.get("user_notes", "")
        })

    return compute_metrics(results)


def main():
    parser = argparse.ArgumentParser(description="Evaluate ground-truth benchmark dataset")
    parser.add_argument("--dataset", default="data/evaluation_benchmark_template.json", help="Path to benchmark JSON")
    parser.add_argument("--include-borderline", action="store_true", help="Include borderline samples as relevant")
    args = parser.parse_args()

    try:
        metrics = evaluate_dataset_file(args.dataset, include_borderline=args.include_borderline)
    except Exception as e:
        print(f"Error evaluating dataset: {e}", file=sys.stderr)
        sys.exit(1)

    print("=== BENCHMARK EVALUATION REPORT ===")
    print(f"Total Evaluated: {metrics['total_samples']}")
    print(f"Confusion Matrix: TP={metrics['tp']}, FP={metrics['fp']}, TN={metrics['tn']}, FN={metrics['fn']}")
    p_str = f"{metrics['precision']:.2%}" if metrics['precision'] is not None else "N/A"
    r_str = f"{metrics['recall']:.2%}" if metrics['recall'] is not None else "N/A"
    f1_str = f"{metrics['f1']:.2%}" if metrics['f1'] is not None else "N/A"
    print(f"Precision: {p_str}")
    print(f"Recall:    {r_str}")
    print(f"F1 Score:  {f1_str}")

    if metrics["false_negatives"]:
        print("\n=== FALSE NEGATIVES (Missed Opportunities) ===")
        for fn in metrics["false_negatives"]:
            print(f"- [{fn['sample_id']}] {fn['company']} - {fn['title']}")
            print(f"  Reason: {fn['reason']}")
            print(f"  User Notes: {fn['user_notes']}")
    else:
        print("\nZero False Negatives detected.")


if __name__ == "__main__":
    main()
