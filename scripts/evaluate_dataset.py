#!/usr/bin/env python3
"""
Benchmark and Evaluation Dataset Tool.
Calculates Confusion Matrix, Precision, Recall, F1 and reports False Negatives
across three stages:
  1. deterministic_gate (rule-based pre-AI filter)
  2. ai_stage (LLM evaluation on jobs that passed the deterministic gate)
  3. end_to_end (combined pipeline outcome)
Supports stratified sampling across the evaluation ledger (passed, rejected at gate, rejected by AI).
Zero emojis strictly enforced.
"""
import argparse
import json
import os
import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.job_policy import deterministic_filter
from src.state_manager import save_state_atomic

_EMOJI_STRIP_RE = re.compile(
    "[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b00-\u2bff\ufe0f\u200d]",
    flags=re.UNICODE,
)


def _strip_emojis(text: str) -> str:
    return _EMOJI_STRIP_RE.sub("", str(text or ""))


def compute_metrics(eval_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    tp = sum(1 for r in eval_results if r["predicted"] == "relevant" and r["expected"] == "relevant")
    fp = sum(1 for r in eval_results if r["predicted"] == "relevant" and r["expected"] == "irrelevant")
    tn = sum(1 for r in eval_results if r["predicted"] == "irrelevant" and r["expected"] == "irrelevant")
    fn = sum(1 for r in eval_results if r["predicted"] == "irrelevant" and r["expected"] == "relevant")

    precision: Optional[float] = tp / (tp + fp) if (tp + fp) > 0 else None
    recall: Optional[float] = tp / (tp + fn) if (tp + fn) > 0 else None

    if precision is not None and recall is not None:
        f1: Optional[float] = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    else:
        f1 = None

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
        "false_negatives": false_negatives,
    }


def _load_ledger_index(ledger_path: Optional[str] = None) -> Tuple[Dict[str, Dict[str, Any]], Dict[Tuple[str, str], Dict[str, Any]]]:
    """Load evaluation_state.json indexed by link and by (company_lower, title_lower)."""
    target = Path(ledger_path) if ledger_path else (ROOT_DIR / "data" / "evaluation_state.json")
    by_link: Dict[str, Dict[str, Any]] = {}
    by_pair: Dict[Tuple[str, str], Dict[str, Any]] = {}
    if not target.exists():
        return by_link, by_pair
    try:
        with open(target, "r", encoding="utf-8") as f:
            raw = json.load(f)
        jobs_map = raw.get("jobs", {}) if isinstance(raw, dict) else {}
        for link, entry in jobs_map.items():
            job = entry.get("job", {}) if isinstance(entry, dict) else {}
            if not isinstance(job, dict):
                continue
            by_link[str(link).strip()] = job
            comp = str(job.get("company") or "").strip().casefold()
            title = str(job.get("title") or "").strip().casefold()
            if comp or title:
                by_pair[(comp, title)] = job
    except Exception:
        pass
    return by_link, by_pair


def _resolve_ai_decision(sample: Dict[str, Any], by_link: Dict[str, Dict[str, Any]], by_pair: Dict[Tuple[str, str], Dict[str, Any]]) -> Tuple[Optional[str], str]:
    """
    Determine AI stage prediction ('relevant' | 'irrelevant' | None) for a sample.
    Checks explicit sample fields first, then falls back to the evaluation ledger.
    """
    explicit_status = str(sample.get("ai_status") or sample.get("pipeline_status") or "").upper()
    explicit_source = str(sample.get("evaluation_source") or "").lower()
    if explicit_status in ("QUALIFIED", "RELEVANT") and explicit_source != "deterministic":
        return "relevant", f"AI stage qualified (score={sample.get('match_score', 'N/A')})"
    if explicit_status in ("DISQUALIFIED", "IRRELEVANT") and explicit_source in ("gemini", "groq", "ai"):
        return "irrelevant", f"AI stage disqualified: {sample.get('disqualification_reason') or sample.get('ai_reason') or 'role_fit'}"

    link = str(sample.get("link") or "").strip()
    comp = str(sample.get("company") or "").strip().casefold()
    title = str(sample.get("title") or "").strip().casefold()

    ledger_job = by_link.get(link) if link else None
    if ledger_job is None and (comp or title):
        ledger_job = by_pair.get((comp, title))

    if ledger_job:
        ev_source = str(ledger_job.get("evaluation_source") or "").lower()
        status = str(ledger_job.get("status") or "").upper()
        if ev_source in ("gemini", "groq"):
            if status == "QUALIFIED":
                return "relevant", f"AI ({ev_source}) qualified (score={ledger_job.get('match_score', 0)})"
            if status == "DISQUALIFIED":
                return "irrelevant", f"AI ({ev_source}) disqualified: {ledger_job.get('disqualification_reason', 'role_fit')}"

    return None, "No AI stage record"


def evaluate_dataset_file(
    filepath: str,
    include_borderline: bool = False,
    ledger_path: Optional[str] = None,
) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data.get("samples", [])
    by_link, by_pair = _load_ledger_index(ledger_path)

    gate_results: List[Dict[str, Any]] = []
    ai_results: List[Dict[str, Any]] = []
    end_to_end_results: List[Dict[str, Any]] = []

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
            "snippet": s.get("snippet", ""),
        }

        rejection = deterministic_filter(job_dict)
        if rejection:
            gate_pred = "irrelevant"
            gate_reason = f"Deterministic filter: {rejection.get('disqualification_reason')}"
        else:
            gate_pred = "relevant"
            gate_reason = "Passed deterministic gate"

        base_entry = {
            "sample_id": s.get("sample_id"),
            "title": s.get("title"),
            "company": s.get("company"),
            "expected": expected,
            "user_notes": s.get("user_notes", ""),
        }

        gate_results.append({
            **base_entry,
            "predicted": gate_pred,
            "reason": gate_reason,
            "stage": "deterministic_gate",
        })

        ai_pred, ai_reason = _resolve_ai_decision(s, by_link, by_pair)
        if gate_pred == "relevant" and ai_pred is not None:
            ai_results.append({
                **base_entry,
                "predicted": ai_pred,
                "reason": ai_reason,
                "stage": "ai_stage",
            })
            e2e_pred = ai_pred
            e2e_reason = ai_reason
        else:
            e2e_pred = gate_pred
            e2e_reason = gate_reason

        end_to_end_results.append({
            **base_entry,
            "predicted": e2e_pred,
            "reason": e2e_reason,
            "stage": "end_to_end",
        })

    gate_metrics = compute_metrics(gate_results)
    ai_metrics = compute_metrics(ai_results)
    e2e_metrics = compute_metrics(end_to_end_results)

    return {
        **e2e_metrics,
        "stages": {
            "deterministic_gate": gate_metrics,
            "ai_stage": ai_metrics,
            "end_to_end": e2e_metrics,
        },
    }


def sample_from_archive(
    output_path: str = "data/benchmark_samples_to_label.json",
    count: int = 30,
    ledger_path: Optional[str] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Stratified sampling from the evaluation ledger across three pipeline strata:
      1. passed_pipeline (QUALIFIED)
      2. rejected_gate (DISQUALIFIED by deterministic gate)
      3. rejected_ai (DISQUALIFIED by Gemini/Groq AI evaluation)
    Falls back to weekly_archive.json only if evaluation_state.json is unavailable.
    """
    rng = random.Random(seed)
    target_ledger = Path(ledger_path) if ledger_path else (ROOT_DIR / "data" / "evaluation_state.json")

    passed_pool: List[Dict[str, Any]] = []
    rejected_gate_pool: List[Dict[str, Any]] = []
    rejected_ai_pool: List[Dict[str, Any]] = []

    if target_ledger.exists():
        with open(target_ledger, "r", encoding="utf-8") as f:
            raw = json.load(f)
        jobs_map = raw.get("jobs", {}) if isinstance(raw, dict) else {}
        for link, entry in jobs_map.items():
            job = entry.get("job", {}) if isinstance(entry, dict) else {}
            if not isinstance(job, dict):
                continue
            status = str(job.get("status") or "").upper()
            ev_source = str(job.get("evaluation_source") or "").lower()
            item = {**job, "link": job.get("link") or link}
            if status == "QUALIFIED":
                passed_pool.append(item)
            elif status == "DISQUALIFIED" and ev_source == "deterministic":
                rejected_gate_pool.append(item)
            elif status == "DISQUALIFIED" and ev_source in ("gemini", "groq"):
                rejected_ai_pool.append(item)

    if not (passed_pool or rejected_gate_pool or rejected_ai_pool):
        archive_path = ROOT_DIR / "data" / "weekly_archive.json"
        if archive_path.exists():
            with open(archive_path, "r", encoding="utf-8") as f:
                jobs = json.load(f)
            if isinstance(jobs, list):
                passed_pool = list(jobs)

    rng.shuffle(passed_pool)
    rng.shuffle(rejected_gate_pool)
    rng.shuffle(rejected_ai_pool)

    per_stratum = max(1, count // 3)
    s_passed = passed_pool[:per_stratum]
    s_gate = rejected_gate_pool[:per_stratum]
    remaining = max(0, count - len(s_passed) - len(s_gate))
    s_ai = rejected_ai_pool[:remaining]

    combined: List[Tuple[str, Dict[str, Any]]] = (
        [("passed_pipeline", j) for j in s_passed]
        + [("rejected_gate", j) for j in s_gate]
        + [("rejected_ai", j) for j in s_ai]
    )

    # Top up from whichever pool still has items if total < count
    if len(combined) < count:
        used_links = {j.get("link") for _, j in combined if j.get("link")}
        for stratum_name, pool in (
            ("rejected_ai", rejected_ai_pool),
            ("rejected_gate", rejected_gate_pool),
            ("passed_pipeline", passed_pool),
        ):
            for j in pool:
                if len(combined) >= count:
                    break
                if j.get("link") not in used_links:
                    used_links.add(j.get("link"))
                    combined.append((stratum_name, j))

    samples: List[Dict[str, Any]] = []
    for idx, (stratum, j) in enumerate(combined[:count], 1):
        samples.append({
            "sample_id": f"SMP-{idx:03d}",
            "stratum": stratum,
            "link": j.get("link", ""),
            "title": _strip_emojis(j.get("title", "")),
            "company": _strip_emojis(j.get("company", "")),
            "snippet": _strip_emojis(j.get("snippet", ""))[:300],
            "pipeline_status": j.get("status", "QUALIFIED" if stratum == "passed_pipeline" else "DISQUALIFIED"),
            "evaluation_source": j.get("evaluation_source", "unknown"),
            "match_score": j.get("match_score", 0),
            "disqualification_reason": j.get("disqualification_reason", ""),
            "expected_label": "PENDING_LABEL: relevant / irrelevant / borderline",
            "user_notes": "",
        })

    strata_counts = {
        "passed_pipeline": sum(1 for s in samples if s["stratum"] == "passed_pipeline"),
        "rejected_gate": sum(1 for s in samples if s["stratum"] == "rejected_gate"),
        "rejected_ai": sum(1 for s in samples if s["stratum"] == "rejected_ai"),
    }

    result = {
        "description": "Stratified ground-truth benchmark dataset sampled from evaluation ledger",
        "instructions": "Mark each expected_label as 'relevant', 'irrelevant', or 'borderline'",
        "strata_counts": strata_counts,
        "samples": samples,
    }
    save_state_atomic(output_path, result)
    print(
        f"[OK] Exported {len(samples)} stratified samples to {output_path} "
        f"(passed={strata_counts['passed_pipeline']}, gate_rejected={strata_counts['rejected_gate']}, ai_rejected={strata_counts['rejected_ai']})."
    )
    return result


def _format_metric(val: Optional[float]) -> str:
    return f"{val:.2%}" if val is not None else "N/A"


def main():
    parser = argparse.ArgumentParser(description="Evaluate ground-truth benchmark dataset across pipeline stages")
    parser.add_argument("--dataset", default="data/evaluation_benchmark_template.json", help="Path to benchmark JSON")
    parser.add_argument("--include-borderline", action="store_true", help="Include borderline samples as relevant")
    parser.add_argument("--sample-archive", action="store_true", help="Export stratified samples from evaluation ledger")
    parser.add_argument("--output-sample", default="data/benchmark_samples_to_label.json", help="Destination path for sampled benchmark")
    parser.add_argument("--count", type=int, default=30, help="Number of stratified samples to export")
    args = parser.parse_args()

    if args.sample_archive:
        sample_from_archive(args.output_sample, count=args.count)
        return

    try:
        metrics = evaluate_dataset_file(args.dataset, include_borderline=args.include_borderline)
    except Exception as e:
        print(f"Error evaluating dataset: {e}", file=sys.stderr)
        sys.exit(1)

    print("=== BENCHMARK EVALUATION REPORT (END-TO-END) ===")
    print(f"Total Evaluated: {metrics['total_samples']}")
    print(f"Confusion Matrix: TP={metrics['tp']}, FP={metrics['fp']}, TN={metrics['tn']}, FN={metrics['fn']}")
    print(f"Precision: {_format_metric(metrics['precision'])}")
    print(f"Recall:    {_format_metric(metrics['recall'])}")
    print(f"F1 Score:  {_format_metric(metrics['f1'])}")

    stages = metrics.get("stages", {})
    for stage_key, label in (
        ("deterministic_gate", "STAGE 1: DETERMINISTIC GATE"),
        ("ai_stage", "STAGE 2: AI EVALUATION"),
    ):
        sm = stages.get(stage_key)
        if sm and sm["total_samples"] > 0:
            print(f"\n--- {label} (n={sm['total_samples']}) ---")
            print(f"Confusion Matrix: TP={sm['tp']}, FP={sm['fp']}, TN={sm['tn']}, FN={sm['fn']}")
            print(
                f"Precision: {_format_metric(sm['precision'])} | "
                f"Recall: {_format_metric(sm['recall'])} | "
                f"F1: {_format_metric(sm['f1'])}"
            )

    if metrics["false_negatives"]:
        print("\n=== FALSE NEGATIVES (Missed Opportunities) ===")
        for fn in metrics["false_negatives"]:
            print(f"- [{fn['sample_id']}] {fn['company']} - {fn['title']} ({fn.get('stage', 'end_to_end')})")
            print(f"  Reason: {fn['reason']}")
            print(f"  User Notes: {fn['user_notes']}")
    else:
        print("\nZero False Negatives detected.")


if __name__ == "__main__":
    main()
