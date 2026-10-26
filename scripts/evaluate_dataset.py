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


def sample_from_archive(output_path="data/benchmark_samples_to_label.json", count=30):
    archive_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "weekly_archive.json")
    if not os.path.exists(archive_path):
        print(f"Archive not found at {archive_path}")
        return
    with open(archive_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    samples = []
    for idx, j in enumerate(jobs[:count], 1):
        samples.append({
            "sample_id": f"SMP-{idx:03d}",
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "snippet": j.get("snippet", "")[:300],
            "expected_label": "TODO: relevant / irrelevant / borderline",
            "user_notes": ""
        })
    result = {
        "description": "Ground-truth benchmark dataset for manual candidate evaluation",
        "instructions": "Mark each expected_label as 'relevant', 'irrelevant', or 'borderline'",
        "samples": samples
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[+] Successfully exported {len(samples)} samples to {output_path} for manual labeling.")


def main():
    parser = argparse.ArgumentParser(description="Evaluate ground-truth benchmark dataset")
    parser.add_argument("--dataset", default="data/evaluation_benchmark_template.json", help="Path to benchmark JSON")
    parser.add_argument("--include-borderline", action="store_true", help="Include borderline samples as relevant")
    parser.add_argument("--sample-archive", action="store_true", help="Export samples from weekly archive for manual labeling")
    parser.add_argument("--output-sample", default="data/benchmark_samples_to_label.json", help="Destination path for sampled benchmark")
    args = parser.parse_args()

    if args.sample_archive:
        sample_from_archive(args.output_sample)
        return

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
