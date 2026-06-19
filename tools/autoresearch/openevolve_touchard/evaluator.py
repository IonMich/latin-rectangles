"""OpenEvolve evaluator for the Latin-rectangles Touchard objective."""

# ruff: noqa: E402

from __future__ import annotations

import importlib.util
import json
import os
import statistics
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from latin_rectangles import count_extensions_from_cycle_type as _reference_count
from latin_rectangles.extension_counting import (
    _count_extensions_from_cycle_type_touchard,
)
from tools.autoresearch import benchmark_touchard_cold_start as bench
from tools.autoresearch.evaluate_candidate import score_candidate

try:
    from openevolve.evaluation_result import EvaluationResult
except ImportError:  # Allows dry checks without installing OpenEvolve.
    EvaluationResult = None  # type: ignore[assignment]

_BASELINE_CACHE: dict[tuple[str, str, bool, int], dict[str, Any]] = {}


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return max(1, parsed)


def _load_candidate(program_path: str | Path) -> ModuleType:
    path = Path(program_path).resolve()
    module_name = f"latin_rectangles_candidate_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load candidate from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _candidate_counter(
    candidate: ModuleType,
) -> Any:
    if not hasattr(candidate, "count_cycle_type"):
        raise AttributeError(
            "Candidate must define count_cycle_type(cycle_type, method)"
        )

    def clear_cache() -> None:
        if hasattr(candidate, "clear_candidate_cache"):
            candidate.clear_candidate_cache()
            return
        for value in vars(candidate).values():
            cache_clear = getattr(value, "cache_clear", None)
            if callable(cache_clear):
                cache_clear()

    def counter(cycle_type: bench.Sequence[int], method: bench.MethodName) -> int:
        return int(candidate.count_cycle_type(tuple(cycle_type), method=method))

    counter.clear_cache = clear_cache  # type: ignore[attr-defined]
    return counter


def _direct_reference_counter(
    cycle_type: bench.Sequence[int],
    method: bench.MethodName,
) -> int:
    """Call the same lean Touchard path candidates are trying to improve."""
    if method == "touchard":
        return _count_extensions_from_cycle_type_touchard(list(cycle_type))
    return _reference_count(list(cycle_type), method=method)


def _run_profile_once_with_counter(
    profile: bench.ProfileName,
    method: bench.MethodName,
    *,
    track_memory: bool,
    counter: Any,
) -> dict[str, Any]:
    workloads = bench.build_workloads(profile)
    return {
        "metadata": {
            "profile": profile,
            "method": method,
            "track_memory": track_memory,
            "runner": "openevolve_touchard",
        },
        "workloads": [
            bench.run_workload(
                workload,
                method=method,
                track_memory=track_memory,
                counter=counter,
            )
            for workload in workloads
        ],
    }


def _aggregate_repeated_reports(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate repeated benchmark reports with median seconds per workload."""
    if not reports:
        raise ValueError("At least one benchmark report is required")
    if len(reports) == 1:
        report = json.loads(json.dumps(reports[0]))
        report["metadata"]["timing_repetitions"] = 1
        report["metadata"]["timing_aggregate"] = "single"
        return report

    first = reports[0]
    aggregated = json.loads(json.dumps(first))
    aggregated["metadata"]["timing_repetitions"] = len(reports)
    aggregated["metadata"]["timing_aggregate"] = "median"

    for row_index, row in enumerate(aggregated["workloads"]):
        matching_rows = [report["workloads"][row_index] for report in reports]
        workload_names = {candidate_row["workload"] for candidate_row in matching_rows}
        if workload_names != {row["workload"]}:
            raise ValueError("Repeated benchmark reports have different workload order")

        row["seconds_repetitions"] = [
            float(candidate_row["seconds"]) for candidate_row in matching_rows
        ]
        row["seconds"] = statistics.median(row["seconds_repetitions"])
        row["seconds_min"] = min(row["seconds_repetitions"])
        row["seconds_max"] = max(row["seconds_repetitions"])
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


def _run_profile_with_counter(
    profile: bench.ProfileName,
    method: bench.MethodName,
    *,
    track_memory: bool,
    counter: Any,
    repetitions: int,
) -> dict[str, Any]:
    reports = [
        _run_profile_once_with_counter(
            profile,
            method,
            track_memory=track_memory,
            counter=counter,
        )
        for _ in range(repetitions)
    ]
    return _aggregate_repeated_reports(reports)


def _baseline_report(
    profile: bench.ProfileName,
    method: bench.MethodName,
    track_memory: bool,
    repetitions: int,
) -> dict[str, Any]:
    key = (profile, method, track_memory, repetitions)
    if key not in _BASELINE_CACHE:
        _BASELINE_CACHE[key] = _run_profile_with_counter(
            profile,
            method=method,
            track_memory=track_memory,
            counter=_direct_reference_counter,
            repetitions=repetitions,
        )
    return _BASELINE_CACHE[key]


def _sanitize_metric_name(name: str) -> str:
    return (
        name.replace("-", "_")
        .replace("+", "_")
        .replace(" ", "_")
        .replace("/", "_")
        .lower()
    )


def _candidate_timing_metrics(report: dict[str, Any]) -> dict[str, float]:
    """Return absolute candidate timing metrics for plotting and comparison."""
    rows = report["workloads"]
    total_seconds = sum(float(row["seconds"]) for row in rows)
    total_weight = sum(float(row.get("weight", 1.0)) for row in rows)
    weighted_seconds = sum(
        float(row.get("weight", 1.0)) * float(row["seconds"]) for row in rows
    )
    total_inputs = sum(float(row.get("count_inputs", 0.0)) for row in rows)
    return {
        "candidate_total_seconds": total_seconds,
        "candidate_weighted_seconds": (
            weighted_seconds / total_weight if total_weight else total_seconds
        ),
        "candidate_inputs_per_second": (
            total_inputs / total_seconds if total_seconds > 0 else 0.0
        ),
    }


def evaluate(program_path: str) -> Any:
    """Evaluate an evolved candidate program.

    OpenEvolve calls this function with the path to a temporary candidate file.
    The returned ``combined_score`` is maximized by OpenEvolve.
    """
    started = time.perf_counter()
    profile = os.environ.get("LATIN_AUTORESEARCH_PROFILE", "smoke")
    method = os.environ.get("LATIN_AUTORESEARCH_METHOD", "touchard")
    track_memory = _bool_env("LATIN_AUTORESEARCH_TRACK_MEMORY", False)
    repetitions = _int_env("LATIN_AUTORESEARCH_REPETITIONS", 3)

    try:
        candidate = _load_candidate(program_path)
        counter = _candidate_counter(candidate)
        baseline = _baseline_report(
            profile,  # type: ignore[arg-type]
            method,  # type: ignore[arg-type]
            track_memory,
            repetitions,
        )
        candidate_report = _run_profile_with_counter(
            profile,  # type: ignore[arg-type]
            method,  # type: ignore[arg-type]
            track_memory=track_memory,
            counter=counter,
            repetitions=repetitions,
        )
        score = score_candidate(baseline, candidate_report)
        elapsed = time.perf_counter() - started

        correctness = 1.0 if score["status"] == "ok" else 0.0
        geomean_speedup = float(score.get("geomean_speedup", 0.0))
        worst_regression = float(score.get("worst_regression", 0.0))
        regression_penalty = max(0.0, worst_regression - 0.10)
        combined_score = (
            max(0.0, geomean_speedup - 0.25 * regression_penalty)
            if correctness
            else 0.0
        )

        candidate_lines = Path(program_path).read_text().count("\n") + 1
        metrics: dict[str, float] = {
            "combined_score": float(combined_score),
            "correctness": correctness,
            "geomean_speedup": geomean_speedup if correctness else 0.0,
            "weighted_log_speedup": float(score.get("weighted_log_speedup", 0.0)),
            "worst_regression": worst_regression,
            "max_memory_ratio": float(score.get("max_memory_ratio", 0.0)),
            "candidate_lines": float(candidate_lines),
            "evaluation_seconds": float(elapsed),
            "timing_repetitions": float(repetitions),
        }
        metrics.update(_candidate_timing_metrics(candidate_report))

        for comparison in score.get("comparisons", []):
            metric_name = _sanitize_metric_name(f"{comparison['workload']}_speedup")
            metrics[metric_name] = float(comparison["speedup"])
            seconds_name = _sanitize_metric_name(
                f"{comparison['workload']}_candidate_seconds"
            )
            metrics[seconds_name] = float(comparison["candidate_seconds"])

        candidate_info = {}
        if hasattr(candidate, "candidate_info"):
            try:
                candidate_info = candidate.candidate_info()
            except Exception as exc:  # pragma: no cover - model-generated code path
                candidate_info = {"candidate_info_error": str(exc)}

        artifacts = {
            "summary": json.dumps(
                {
                    "profile": profile,
                    "method": method,
                    "baseline": "direct_private_touchard"
                    if method == "touchard"
                    else "public_reference",
                    "timing_repetitions": repetitions,
                    "timing_aggregate": "median" if repetitions > 1 else "single",
                    "status": score["status"],
                    "hard_failure_reasons": score["hard_failure_reasons"],
                    "candidate_info": candidate_info,
                    "comparisons": score["comparisons"],
                },
                indent=2,
                sort_keys=True,
            ),
        }
        if EvaluationResult is not None:
            return EvaluationResult(metrics=metrics, artifacts=artifacts)
        return metrics
    except Exception as exc:
        try:
            candidate_lines = Path(program_path).read_text().count("\n") + 1
        except OSError:
            candidate_lines = 0
        metrics = {
            "combined_score": 0.0,
            "correctness": 0.0,
            "geomean_speedup": 0.0,
            "candidate_lines": float(candidate_lines),
            "evaluation_seconds": float(time.perf_counter() - started),
            "error": 1.0,
        }
        artifacts = {"error": f"{type(exc).__name__}: {exc}"}
        if EvaluationResult is not None:
            return EvaluationResult(metrics=metrics, artifacts=artifacts)
        return metrics


if __name__ == "__main__":
    target = (
        sys.argv[1]
        if len(sys.argv) > 1
        else str(Path(__file__).with_name("initial_program.py"))
    )
    result = evaluate(target)
    if hasattr(result, "metrics"):
        print(json.dumps(result.metrics, indent=2, sort_keys=True))
        if getattr(result, "artifacts", None):
            print(json.dumps(result.artifacts, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
