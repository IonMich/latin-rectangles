"""Tests for autoresearch benchmark and evaluator scaffolding."""

import json
from pathlib import Path

from tools.autoresearch import benchmark_touchard_cold_start as bench
from tools.autoresearch import evaluate_candidate as evaluator
from tools.autoresearch import plot_openevolve_progress as plot_progress
from tools.autoresearch.openevolve_touchard import evaluator as openevolve_evaluator


def test_smoke_workloads_are_valid_cycle_types() -> None:
    """Smoke profile should contain deterministic no-fixed-point cycle types."""
    workloads = bench.build_workloads("smoke")

    assert {workload.name for workload in workloads} == {
        "all_cycle_types_n_8",
        "named_families_n_64",
        "dense_touchard_n_128",
    }
    for workload in workloads:
        assert workload.cycle_types
        for cycle_type in workload.cycle_types:
            assert sum(cycle_type) >= 2
            assert all(part >= 2 for part in cycle_type)


def test_autoresearch_workloads_do_not_exceed_n_1024() -> None:
    """Autoresearch profiles should stay within the agreed Touchard size cap."""
    for profile in ("smoke", "quick", "promotion"):
        for workload in bench.build_workloads(profile):
            for cycle_type in workload.cycle_types:
                assert sum(cycle_type) <= 1024


def test_run_workload_records_digest_and_cache_fields() -> None:
    """A workload run should emit stable scoring fields."""
    workload = bench.Workload(
        name="fake",
        kind="unit",
        cycle_types=((2, 2), (4,)),
        weight=1.0,
        description="unit test workload",
    )

    def fake_counter(cycle_type: bench.Sequence[int], _method: bench.MethodName) -> int:
        return sum(cycle_type) + len(cycle_type)

    row = bench.run_workload(
        workload,
        method="auto",
        track_memory=False,
        counter=fake_counter,
    )

    assert row["status"] == "ok"
    assert row["count_inputs"] == 2
    assert row["result_digest"].startswith("sha256:")
    assert row["result_mod_sum_1000000007"] == 11
    assert row["cache_before"] is None or set(row["cache_before"]) == {
        "hits",
        "misses",
        "currsize",
    }


def test_result_digest_handles_large_integers() -> None:
    """Digesting huge exact counts should not depend on decimal string limits."""
    digest = bench._result_digest([((1024,), 10**5000)])

    assert digest.startswith("sha256:")


def test_run_workload_clears_candidate_cache_hook() -> None:
    """Candidate-local caches should be cleared for each cold workload."""
    workload = bench.Workload(
        name="fake",
        kind="unit",
        cycle_types=((2, 2),),
        weight=1.0,
        description="unit test workload",
    )
    clears = 0

    def fake_counter(cycle_type: bench.Sequence[int], _method: bench.MethodName) -> int:
        return sum(cycle_type)

    def clear_cache() -> None:
        nonlocal clears
        clears += 1

    fake_counter.clear_cache = clear_cache  # type: ignore[attr-defined]

    row = bench.run_workload(
        workload,
        method="auto",
        track_memory=False,
        counter=fake_counter,
    )

    assert row["status"] == "ok"
    assert clears == 1


def test_score_candidate_rewards_broad_speedup() -> None:
    """Candidate score should reflect weighted geometric speedup."""
    baseline = {
        "workloads": [
            {
                "workload": "a",
                "weight": 0.75,
                "seconds": 4.0,
                "peak_memory_mb": 10.0,
                "result_digest": "sha256:same-a",
            },
            {
                "workload": "b",
                "weight": 0.25,
                "seconds": 2.0,
                "peak_memory_mb": 5.0,
                "result_digest": "sha256:same-b",
            },
        ]
    }
    candidate = {
        "workloads": [
            {
                "workload": "a",
                "weight": 0.75,
                "seconds": 2.0,
                "peak_memory_mb": 10.0,
                "result_digest": "sha256:same-a",
            },
            {
                "workload": "b",
                "weight": 0.25,
                "seconds": 1.0,
                "peak_memory_mb": 5.0,
                "result_digest": "sha256:same-b",
            },
        ]
    }

    score = evaluator.score_candidate(baseline, candidate)

    assert score["status"] == "ok"
    assert score["geomean_speedup"] == 2.0
    assert score["score"] > 0


def test_score_candidate_rejects_digest_mismatch() -> None:
    """Wrong exact answers should hard-fail the candidate."""
    baseline = {
        "workloads": [
            {
                "workload": "a",
                "weight": 1.0,
                "seconds": 1.0,
                "peak_memory_mb": 1.0,
                "result_digest": "sha256:baseline",
            }
        ]
    }
    candidate = {
        "workloads": [
            {
                "workload": "a",
                "weight": 1.0,
                "seconds": 0.5,
                "peak_memory_mb": 1.0,
                "result_digest": "sha256:candidate",
            }
        ]
    }

    score = evaluator.score_candidate(baseline, candidate)

    assert score["status"] == "fail"
    assert score["score"] == -1_000_000.0
    assert "digest mismatches: a" in score["hard_failure_reasons"]


def test_openevolve_evaluator_uses_median_repeated_timings() -> None:
    """Repeated evaluator reports should use median seconds per workload."""
    reports = [
        {
            "metadata": {"runner": "unit"},
            "workloads": [
                {
                    "workload": "a",
                    "status": "ok",
                    "seconds": seconds,
                    "peak_memory_mb": peak,
                    "result_digest": "sha256:same",
                }
            ],
        }
        for seconds, peak in ((0.3, 1.0), (0.1, 3.0), (0.2, 2.0))
    ]

    aggregate = openevolve_evaluator._aggregate_repeated_reports(reports)
    row = aggregate["workloads"][0]

    assert aggregate["metadata"]["timing_repetitions"] == 3
    assert aggregate["metadata"]["timing_aggregate"] == "median"
    assert row["seconds"] == 0.2
    assert row["seconds_repetitions"] == [0.3, 0.1, 0.2]
    assert row["seconds_min"] == 0.1
    assert row["seconds_max"] == 0.3
    assert row["peak_memory_mb"] == 3.0


def test_plot_openevolve_progress_renders_svg(tmp_path: Path) -> None:
    """OpenEvolve checkpoints should render into a progress SVG."""
    programs = tmp_path / "checkpoints" / "checkpoint_2" / "programs"
    programs.mkdir(parents=True)
    for index, seconds in enumerate((0.3, 0.5, 0.2), start=1):
        (programs / f"program-{index}.json").write_text(
            json.dumps(
                {
                    "id": f"program-{index}",
                    "iteration_found": index,
                    "metadata": {
                        "changes": (
                            "Change 1: Replace:\n"
                            "  def old_name() -> None:\n"
                            "with:\n"
                            "  def improved_name() -> None:\n"
                        )
                        if seconds == 0.2
                        else ""
                    },
                    "metrics": {
                        "combined_score": 1.0 / seconds,
                        "correctness": 0.0 if seconds == 0.5 else 1.0,
                        "candidate_lines": 80 + index,
                    },
                    "artifacts_json": json.dumps(
                        {
                            "summary": json.dumps(
                                {
                                    "comparisons": [
                                        {
                                            "workload": "unit",
                                            "weight": 1.0,
                                            "candidate_seconds": seconds,
                                        }
                                    ]
                                }
                            )
                        },
                    ),
                }
            )
        )

    checkpoint = plot_progress.resolve_checkpoint(tmp_path)
    reference_report = tmp_path / "head_benchmark.json"
    reference_report.write_text(
        json.dumps(
            {
                "workloads": [
                    {
                        "status": "ok",
                        "seconds": 0.4,
                        "weight": 1.0,
                        "count_inputs": 1,
                    }
                ]
            }
        )
    )
    reference = plot_progress.load_reference_attempt(
        reference_report,
        metric_name="candidate_weighted_seconds",
        label="HEAD",
    )
    attempts = plot_progress.load_attempts(
        checkpoint,
        "candidate_weighted_seconds",
        lower_is_better=True,
    )
    attempts = plot_progress._mark_improvements(
        [reference, *attempts],
        lower_is_better=True,
    )
    svg = plot_progress.render_svg(
        attempts,
        metric_name="candidate_weighted_seconds",
        lower_is_better=True,
    )

    assert checkpoint == programs.parent
    assert [attempt.is_improvement for attempt in attempts] == [True, True, False, True]
    assert svg.startswith("<svg")
    assert "OpenEvolve Attempts" in svg
    assert "Iteration" in svg
    assert "HEAD" in svg
    assert "candidate_weighted_seconds = sum" in svg
    assert "changed old_name + improved_name" in svg


def test_openevolve_seed_program_evaluates_without_api_calls() -> None:
    """The OpenEvolve problem should have a dry evaluator path."""
    program_path = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "autoresearch"
        / "openevolve_touchard"
        / "initial_program.py"
    )

    result = openevolve_evaluator.evaluate(str(program_path))
    metrics = result.metrics if hasattr(result, "metrics") else result

    assert metrics["correctness"] == 1.0
    assert 0.5 < metrics["combined_score"] < 2.0
    assert 0.5 < metrics["geomean_speedup"] < 2.0
    assert metrics["timing_repetitions"] == 3.0
