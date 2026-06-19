#!/usr/bin/env python3
"""Repeated validation for a candidate source tree against a baseline ref."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from tools.autoresearch.evaluate_candidate import (
    _target_from_ref_or_path,
    run_benchmark,
    score_candidate,
)
from tools.autoresearch.openevolve_touchard.evaluator import _aggregate_repeated_reports


def _total_seconds(report: dict[str, Any]) -> float:
    return sum(float(row["seconds"]) for row in report["workloads"])


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
    *,
    baseline_ref: str,
    candidate_ref: str,
    profile: str,
    method: str,
    output_dir: Path,
    repetitions: int,
    track_memory: bool,
    benchmark_timeout_seconds: float,
) -> dict[str, Any]:
    """Run repeated benchmark comparisons with alternating target order."""
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    baseline_reports: list[dict[str, Any]] = []
    candidate_reports: list[dict[str, Any]] = []
    run_errors: list[dict[str, Any]] = []

    with (
        _target_from_ref_or_path(baseline_ref, label="baseline") as baseline,
        _target_from_ref_or_path(candidate_ref, label="candidate") as candidate,
    ):
        for repetition in range(repetitions):
            rep_dir = output_dir / f"rep_{repetition + 1:02d}"
            run_baseline_first = repetition % 2 == 0
            ordered_targets = (
                (baseline, candidate) if run_baseline_first else (candidate, baseline)
            )

            results = []
            for target in ordered_targets:
                result = run_benchmark(
                    target,
                    profile=profile,  # type: ignore[arg-type]
                    method=method,  # type: ignore[arg-type]
                    track_memory=track_memory,
                    output_dir=rep_dir,
                    timeout_seconds=benchmark_timeout_seconds,
                )
                results.append(result)
                if result["status"] != "ok":
                    run_errors.append(
                        {
                            "repetition": repetition + 1,
                            "target": target.label,
                            "returncode": result.get("returncode"),
                            "stderr": result.get("stderr", ""),
                        }
                    )

            by_label = {result["target"]: result for result in results}
            if by_label.get("baseline", {}).get("status") == "ok":
                baseline_reports.append(by_label["baseline"]["result"])
            if by_label.get("candidate", {}).get("status") == "ok":
                candidate_reports.append(by_label["candidate"]["result"])

    status = "ok"
    score: dict[str, Any] | None = None
    baseline_report: dict[str, Any] | None = None
    candidate_report: dict[str, Any] | None = None

    if (
        run_errors
        or len(baseline_reports) != repetitions
        or len(candidate_reports) != repetitions
    ):
        status = "fail"
    else:
        baseline_report = _aggregate_repeated_reports(baseline_reports)
        candidate_report = _aggregate_repeated_reports(candidate_reports)
        score = score_candidate(baseline_report, candidate_report)
        if score["status"] != "ok":
            status = "fail"

    payload: dict[str, Any] = {
        "status": status,
        "baseline_ref": baseline_ref,
        "candidate_ref": candidate_ref,
        "profile": profile,
        "method": method,
        "repetitions": repetitions,
        "track_memory": track_memory,
        "elapsed_seconds": time.perf_counter() - started,
        "run_errors": run_errors,
    }
    if (
        score is not None
        and baseline_report is not None
        and candidate_report is not None
    ):
        baseline_total = _total_seconds(baseline_report)
        candidate_total = _total_seconds(candidate_report)
        payload.update(
            {
                "weighted_geomean_speedup": score["geomean_speedup"],
                "weighted_log_speedup": score["weighted_log_speedup"],
                "worst_regression": score["worst_regression"],
                "baseline_total_seconds": baseline_total,
                "candidate_total_seconds": candidate_total,
                "total_wall_speedup": (
                    baseline_total / candidate_total if candidate_total > 0 else 0.0
                ),
                "hard_failure_reasons": score["hard_failure_reasons"],
                "comparisons": _comparison_rows(score),
                "baseline_report": baseline_report,
                "candidate_report": candidate_report,
            }
        )
    return payload


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repeatedly validate a source-tree candidate against a baseline."
    )
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--candidate-ref", required=True)
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
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_results/autoresearch/source_validation"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument(
        "--track-memory",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument("--benchmark-timeout-seconds", type=float, default=300.0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = validate(
        baseline_ref=args.baseline_ref,
        candidate_ref=args.candidate_ref,
        profile=args.profile,
        method=args.method,
        output_dir=args.output_dir,
        repetitions=max(1, args.repetitions),
        track_memory=args.track_memory,
        benchmark_timeout_seconds=args.benchmark_timeout_seconds,
    )
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.output is None:
        print(payload)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{payload}\n")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
