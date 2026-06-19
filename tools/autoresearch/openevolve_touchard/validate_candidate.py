#!/usr/bin/env python3
"""Paired validation for an OpenEvolve Touchard candidate."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from tools.autoresearch import benchmark_touchard_cold_start as bench
from tools.autoresearch.evaluate_candidate import score_candidate
from tools.autoresearch.openevolve_touchard import evaluator as oe_evaluator


def _empty_report(
    *,
    profile: bench.ProfileName,
    method: bench.MethodName,
    track_memory: bool,
    label: str,
) -> dict[str, Any]:
    return {
        "metadata": {
            "profile": profile,
            "method": method,
            "track_memory": track_memory,
            "runner": "openevolve_touchard_paired_validator",
            "target": label,
        },
        "workloads": [],
    }


def _aggregate_repeated_reports(reports: list[dict[str, Any]]) -> dict[str, Any]:
    if not reports:
        raise ValueError("At least one benchmark report is required")

    aggregated = json.loads(json.dumps(reports[0]))
    aggregated["metadata"]["timing_repetitions"] = len(reports)
    aggregated["metadata"]["timing_aggregate"] = (
        "single" if len(reports) == 1 else "median"
    )

    if len(reports) == 1:
        return aggregated

    for row_index, row in enumerate(aggregated["workloads"]):
        matching_rows = [report["workloads"][row_index] for report in reports]
        workload_names = {candidate_row["workload"] for candidate_row in matching_rows}
        if workload_names != {row["workload"]}:
            raise ValueError("Repeated benchmark reports have different workload order")

        seconds = [float(candidate_row["seconds"]) for candidate_row in matching_rows]
        row["seconds_repetitions"] = seconds
        row["seconds"] = statistics.median(seconds)
        row["seconds_min"] = min(seconds)
        row["seconds_max"] = max(seconds)
        row["seconds_stdev"] = statistics.stdev(seconds) if len(seconds) > 1 else 0.0
        row["peak_memory_mb"] = max(
            float(candidate_row.get("peak_memory_mb") or 0.0)
            for candidate_row in matching_rows
        )

        statuses = {
            candidate_row.get("status", "ok") for candidate_row in matching_rows
        }
        digests = {
            candidate_row.get("result_digest", "") for candidate_row in matching_rows
        }
        if len(statuses) > 1 or statuses != {"ok"}:
            row["status"] = "error"
            row["error"] = "inconsistent repeated benchmark status"
        if len(digests) > 1:
            row["status"] = "error"
            row["error"] = "inconsistent repeated benchmark digest"

    return aggregated


def _total_seconds(report: dict[str, Any]) -> float:
    return sum(float(row["seconds"]) for row in report["workloads"])


def _weighted_seconds(report: dict[str, Any]) -> float:
    rows = report["workloads"]
    total_weight = sum(float(row.get("weight", 1.0)) for row in rows)
    if total_weight == 0:
        return _total_seconds(report)
    return (
        sum(float(row.get("weight", 1.0)) * float(row["seconds"]) for row in rows)
        / total_weight
    )


def _inputs_per_second(report: dict[str, Any]) -> float:
    total_inputs = sum(
        float(row.get("count_inputs", 0.0)) for row in report["workloads"]
    )
    total_seconds = _total_seconds(report)
    return total_inputs / total_seconds if total_seconds > 0 else 0.0


def _comparison_rows(score: dict[str, Any]) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for comparison in score.get("comparisons", []):
        rows.append(
            {
                "workload": str(comparison["workload"]),
                "weight": float(comparison["weight"]),
                "baseline_seconds": float(comparison["baseline_seconds"]),
                "candidate_seconds": float(comparison["candidate_seconds"]),
                "speedup": float(comparison["speedup"]),
            }
        )
    return rows


def validate(
    candidate_path: Path,
    *,
    profile: bench.ProfileName,
    method: bench.MethodName,
    repetitions: int,
    track_memory: bool,
) -> dict[str, Any]:
    """Run baseline and candidate in alternating order for each workload."""
    candidate_module = oe_evaluator._load_candidate(candidate_path)
    candidate_counter = oe_evaluator._candidate_counter(candidate_module)
    workloads = bench.build_workloads(profile)
    baseline_reports: list[dict[str, Any]] = []
    candidate_reports: list[dict[str, Any]] = []
    started = time.perf_counter()

    for repetition in range(repetitions):
        baseline_report = _empty_report(
            profile=profile,
            method=method,
            track_memory=track_memory,
            label="baseline",
        )
        candidate_report = _empty_report(
            profile=profile,
            method=method,
            track_memory=track_memory,
            label="candidate",
        )

        for workload_index, workload in enumerate(workloads):
            run_baseline_first = (repetition + workload_index) % 2 == 0
            if run_baseline_first:
                baseline_row = bench.run_workload(
                    workload,
                    method=method,
                    track_memory=track_memory,
                    counter=oe_evaluator._direct_reference_counter,
                )
                candidate_row = bench.run_workload(
                    workload,
                    method=method,
                    track_memory=track_memory,
                    counter=candidate_counter,
                )
            else:
                candidate_row = bench.run_workload(
                    workload,
                    method=method,
                    track_memory=track_memory,
                    counter=candidate_counter,
                )
                baseline_row = bench.run_workload(
                    workload,
                    method=method,
                    track_memory=track_memory,
                    counter=oe_evaluator._direct_reference_counter,
                )
            baseline_report["workloads"].append(baseline_row)
            candidate_report["workloads"].append(candidate_row)

        baseline_reports.append(baseline_report)
        candidate_reports.append(candidate_report)

    baseline = _aggregate_repeated_reports(baseline_reports)
    candidate = _aggregate_repeated_reports(candidate_reports)
    score = score_candidate(baseline, candidate)
    baseline_total_seconds = _total_seconds(baseline)
    candidate_total_seconds = _total_seconds(candidate)

    return {
        "status": score["status"],
        "candidate_path": str(candidate_path),
        "profile": profile,
        "method": method,
        "repetitions": repetitions,
        "elapsed_seconds": time.perf_counter() - started,
        "weighted_geomean_speedup": score["geomean_speedup"],
        "weighted_log_speedup": score["weighted_log_speedup"],
        "worst_regression": score["worst_regression"],
        "baseline_total_seconds": baseline_total_seconds,
        "candidate_total_seconds": candidate_total_seconds,
        "total_wall_speedup": (
            baseline_total_seconds / candidate_total_seconds
            if candidate_total_seconds > 0
            else 0.0
        ),
        "baseline_weighted_seconds": _weighted_seconds(baseline),
        "candidate_weighted_seconds": _weighted_seconds(candidate),
        "candidate_inputs_per_second": _inputs_per_second(candidate),
        "hard_failure_reasons": score["hard_failure_reasons"],
        "comparisons": _comparison_rows(score),
        "baseline_report": baseline,
        "candidate_report": candidate,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run paired validation for an OpenEvolve Touchard candidate."
    )
    parser.add_argument("candidate_path", type=Path)
    parser.add_argument(
        "--profile",
        choices=["smoke", "quick", "promotion"],
        default="promotion",
    )
    parser.add_argument(
        "--method",
        choices=["auto", "touchard", "rook", "rook_ntt"],
        default="touchard",
    )
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--track-memory", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate(
        args.candidate_path,
        profile=args.profile,
        method=args.method,
        repetitions=max(1, args.repetitions),
        track_memory=args.track_memory,
    )
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{text}\n")
    print(text)
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
