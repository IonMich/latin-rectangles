#!/usr/bin/env python3
"""Compare a candidate against a baseline for the autoresearch objective."""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_SCRIPT = (
    REPO_ROOT / "tools" / "autoresearch" / "benchmark_touchard_cold_start.py"
)


@dataclass(frozen=True)
class Target:
    """A baseline or candidate source tree."""

    label: str
    path: Path
    source: str


def _run_command(
    args: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout_seconds: float | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )


@contextmanager
def _target_from_ref_or_path(raw: str, *, label: str) -> Iterator[Target]:
    """Yield a source tree for a git ref or existing path."""
    path = Path(raw).expanduser()
    if path.exists():
        yield Target(label=label, path=path.resolve(), source="path")
        return

    with tempfile.TemporaryDirectory(prefix=f"latin-rectangles-{label}-") as tmp:
        worktree_path = Path(tmp) / "worktree"
        result = _run_command(
            ["git", "worktree", "add", "--detach", str(worktree_path), raw],
            cwd=REPO_ROOT,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Could not create worktree for {label}={raw!r}: {result.stderr.strip()}"
            )
        try:
            yield Target(label=label, path=worktree_path, source="git-ref")
        finally:
            _run_command(
                ["git", "worktree", "remove", "--force", str(worktree_path)],
                cwd=REPO_ROOT,
            )


def _target_env(target: Target) -> dict[str, str]:
    """Build an environment that imports package code from the target tree."""
    env = os.environ.copy()
    target_paths = [str(target.path / "src"), str(target.path)]
    existing = env.get("PYTHONPATH")
    if existing:
        target_paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(target_paths)
    return env


def run_pytest_gate(
    target: Target,
    *,
    pytest_args: Sequence[str],
    timeout_seconds: float,
) -> dict[str, Any]:
    """Run a pytest gate in the target tree."""
    result = _run_command(
        ["uv", "run", "pytest", *pytest_args],
        cwd=target.path,
        timeout_seconds=timeout_seconds,
    )
    return {
        "target": target.label,
        "status": "ok" if result.returncode == 0 else "fail",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run_benchmark(
    target: Target,
    *,
    profile: str,
    method: str,
    track_memory: bool,
    output_dir: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Run the cold-start benchmark helper against one target tree."""
    output_path = output_dir / f"{target.label}_benchmark.json"
    args = [
        "uv",
        "run",
        str(BENCHMARK_SCRIPT),
        "--profile",
        profile,
        "--method",
        method,
        "--output",
        str(output_path),
    ]
    if not track_memory:
        args.append("--no-track-memory")

    result = _run_command(
        args,
        cwd=REPO_ROOT,
        env=_target_env(target),
        timeout_seconds=timeout_seconds,
    )
    if result.returncode != 0:
        return {
            "target": target.label,
            "status": "fail",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "output_path": str(output_path),
        }
    return {
        "target": target.label,
        "status": "ok",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "output_path": str(output_path),
        "result": json.loads(output_path.read_text()),
    }


def _workload_rows(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["workload"]: row for row in report["workloads"]}


def score_candidate(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """Score candidate benchmark JSON against baseline benchmark JSON."""
    baseline_rows = _workload_rows(baseline)
    candidate_rows = _workload_rows(candidate)
    missing = sorted(set(baseline_rows) - set(candidate_rows))
    extra = sorted(set(candidate_rows) - set(baseline_rows))
    comparisons: list[dict[str, Any]] = []
    weighted_log_speedup = 0.0
    total_weight = 0.0
    worst_regression = 0.0
    max_memory_ratio = 0.0
    digest_mismatches: list[str] = []

    for name, base_row in baseline_rows.items():
        cand_row = candidate_rows.get(name)
        if cand_row is None:
            continue
        if base_row["result_digest"] != cand_row["result_digest"]:
            digest_mismatches.append(name)

        base_seconds = max(float(base_row["seconds"]), 1e-12)
        cand_seconds = max(float(cand_row["seconds"]), 1e-12)
        speedup = base_seconds / cand_seconds
        clamped_speedup = min(max(speedup, 0.20), 5.00)
        weight = float(base_row.get("weight", 1.0))
        weighted_log_speedup += weight * math.log(clamped_speedup)
        total_weight += weight

        regression = max(0.0, cand_seconds / base_seconds - 1.0)
        worst_regression = max(worst_regression, regression)

        base_memory = float(base_row.get("peak_memory_mb") or 0.0)
        cand_memory = float(cand_row.get("peak_memory_mb") or 0.0)
        memory_ratio = cand_memory / base_memory if base_memory > 0 else 0.0
        max_memory_ratio = max(max_memory_ratio, memory_ratio)

        comparisons.append(
            {
                "workload": name,
                "weight": weight,
                "baseline_seconds": base_seconds,
                "candidate_seconds": cand_seconds,
                "speedup": speedup,
                "baseline_digest": base_row["result_digest"],
                "candidate_digest": cand_row["result_digest"],
                "memory_ratio": memory_ratio,
            }
        )

    if total_weight:
        weighted_log_speedup /= total_weight

    status = "ok"
    hard_failure_reasons: list[str] = []
    if missing:
        hard_failure_reasons.append(f"missing workloads: {', '.join(missing)}")
    if extra:
        hard_failure_reasons.append(f"extra workloads: {', '.join(extra)}")
    if digest_mismatches:
        hard_failure_reasons.append(
            f"digest mismatches: {', '.join(digest_mismatches)}"
        )
    if hard_failure_reasons:
        status = "fail"

    score = -1_000_000.0
    if status == "ok":
        memory_growth = max(0.0, max_memory_ratio - 1.25)
        score = (
            1000.0 * weighted_log_speedup
            - 300.0 * max(0.0, worst_regression - 0.10)
            - 100.0 * memory_growth
        )

    return {
        "status": status,
        "score": score,
        "weighted_log_speedup": weighted_log_speedup,
        "geomean_speedup": math.exp(weighted_log_speedup),
        "worst_regression": worst_regression,
        "max_memory_ratio": max_memory_ratio,
        "hard_failure_reasons": hard_failure_reasons,
        "comparisons": comparisons,
    }


def evaluate(
    *,
    baseline_ref: str,
    candidate_ref: str,
    profile: str,
    method: str,
    output_dir: Path,
    run_tests: bool,
    track_memory: bool,
    benchmark_timeout_seconds: float,
    pytest_timeout_seconds: float,
) -> dict[str, Any]:
    """Evaluate a candidate ref/path against a baseline ref/path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with (
        _target_from_ref_or_path(baseline_ref, label="baseline") as baseline,
        _target_from_ref_or_path(candidate_ref, label="candidate") as candidate,
    ):
        pytest_result = None
        if run_tests:
            pytest_result = run_pytest_gate(
                candidate,
                pytest_args=(),
                timeout_seconds=pytest_timeout_seconds,
            )

        baseline_benchmark = run_benchmark(
            baseline,
            profile=profile,
            method=method,
            track_memory=track_memory,
            output_dir=output_dir,
            timeout_seconds=benchmark_timeout_seconds,
        )
        candidate_benchmark = run_benchmark(
            candidate,
            profile=profile,
            method=method,
            track_memory=track_memory,
            output_dir=output_dir,
            timeout_seconds=benchmark_timeout_seconds,
        )

    score: dict[str, Any] | None = None
    if baseline_benchmark["status"] == "ok" and candidate_benchmark["status"] == "ok":
        score = score_candidate(
            baseline_benchmark["result"],
            candidate_benchmark["result"],
        )

    status = "ok"
    if pytest_result is not None and pytest_result["status"] != "ok":
        status = "fail"
    if baseline_benchmark["status"] != "ok" or candidate_benchmark["status"] != "ok":
        status = "fail"
    if score is not None and score["status"] != "ok":
        status = "fail"

    return {
        "status": status,
        "baseline_ref": baseline_ref,
        "candidate_ref": candidate_ref,
        "profile": profile,
        "method": method,
        "pytest": pytest_result,
        "baseline_benchmark": baseline_benchmark,
        "candidate_benchmark": candidate_benchmark,
        "score": score,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate autoresearch candidate against a baseline."
    )
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--candidate-ref", required=True)
    parser.add_argument(
        "--profile",
        choices=["smoke", "quick", "promotion"],
        default="smoke",
    )
    parser.add_argument(
        "--method",
        choices=["auto", "touchard", "rook", "rook_ntt"],
        default="auto",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_results/autoresearch/evaluation"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--run-tests",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run full pytest gate on the candidate.",
    )
    parser.add_argument(
        "--track-memory",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Track peak memory in benchmark helper.",
    )
    parser.add_argument("--benchmark-timeout-seconds", type=float, default=300.0)
    parser.add_argument("--pytest-timeout-seconds", type=float, default=300.0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = evaluate(
        baseline_ref=args.baseline_ref,
        candidate_ref=args.candidate_ref,
        profile=args.profile,
        method=args.method,
        output_dir=args.output_dir,
        run_tests=args.run_tests,
        track_memory=args.track_memory,
        benchmark_timeout_seconds=args.benchmark_timeout_seconds,
        pytest_timeout_seconds=args.pytest_timeout_seconds,
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
