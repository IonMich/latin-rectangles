"""Tests for benchmark and plotting helpers."""

import time
from pathlib import Path

import pytest

from benchmarks import benchmark_cycle_type_methods as bench
from benchmarks import diagnose_scaling as diagnose
from benchmarks import plot_cycle_type_methods as plots


def test_cycle_type_counts_match_known_values() -> None:
    """Partitions with no 1-parts have known small values."""
    expected = {
        0: 0,
        1: 0,
        2: 1,
        3: 1,
        4: 2,
        5: 2,
        6: 4,
        7: 4,
        8: 7,
    }
    for n, count in expected.items():
        assert bench.count_cycle_types(n) == count
        assert len(list(bench.iter_cycle_types(n))) == count


@pytest.mark.parametrize("target_part", [3, 8, 16])
def test_near_uniform_cycle_types_have_no_fixed_points(target_part: int) -> None:
    """Named cycle families must always sum to n and avoid 1-cycles."""
    for n in range(2, 60):
        cycle_type = bench.near_uniform_cycle_type(n, target_part)
        assert cycle_type is not None
        assert sum(cycle_type) == n
        assert all(part >= 2 for part in cycle_type)


def test_all_named_cycle_families_have_valid_cycle_types() -> None:
    """Every generated family should describe a derangement cycle type."""
    for n in [3, 64, 128, 1024]:
        families = bench.named_cycle_families(n)
        assert "single_cycle" in families
        if n % 2 == 0:
            assert "two_equal_cycles" in families
        if n % 4 == 0:
            assert "four_equal_cycles" in families
        assert "mixed_ladder" in families
        for cycle_type in families.values():
            assert sum(cycle_type) == n
            assert all(part >= 2 for part in cycle_type)


def test_benchmark_writes_agreement_checked_csvs(tmp_path: Path) -> None:
    """Small benchmarks should write rows after checking method equality."""
    methods = [
        bench.METHODS["signed_sum"],
        bench.METHODS["rook_schoolbook"],
        bench.METHODS["rook_ntt"],
    ]
    family_path = tmp_path / "cycle_families.csv"
    all_cycle_path = tmp_path / "all_cycle_types.csv"

    family_count = bench.write_rows(
        family_path,
        bench.family_rows(
            [4],
            {"single_cycle", "transpositions"},
            methods,
            repeats=1,
            track_memory=True,
        ),
    )
    all_cycle_count = bench.write_rows(
        all_cycle_path,
        bench.all_cycle_type_rows(
            [6],
            methods,
            repeats=1,
            track_memory=True,
            max_cycle_types=100,
            allow_large_all_cycle_types=False,
        ),
    )

    assert family_count == 6
    assert all_cycle_count == bench.count_cycle_types(6) * len(methods)
    assert "signed_sum" in family_path.read_text()
    assert "rook_ntt" in all_cycle_path.read_text()


def test_all_cycle_type_guard_blocks_unintended_large_runs() -> None:
    """The exhaustive suite should refuse unexpectedly large cycle-type counts."""
    rows = bench.all_cycle_type_rows(
        [30],
        [bench.METHODS["signed_sum"]],
        repeats=1,
        track_memory=False,
        max_cycle_types=10,
        allow_large_all_cycle_types=False,
    )
    with pytest.raises(ValueError, match="cycle types"):
        next(rows)


def test_timeout_writes_timeout_row() -> None:
    """Timed-out methods should not block the whole benchmark run."""

    def slow_method(_cycle_lengths: list[int]) -> int:
        time.sleep(1)
        return 0

    rows = bench.benchmark_case(
        bench.BenchmarkCase(
            suite="families",
            family="slow",
            n=4,
            cycle_lengths=[4],
        ),
        [bench.Method("slow", slow_method)],
        repeats=1,
        track_memory=True,
        timeout_seconds=0.01,
    )

    assert rows[0]["status"] == "timeout"
    assert rows[0]["time_seconds_median"] == ""


def test_signed_sum_diagnostics_reports_cache_misses() -> None:
    """Signed-sum diagnostics should expose subset and M-cache work."""
    case = diagnose.DiagnosticCase("known", 8, [2, 2, 4])
    cold = diagnose.signed_sum_diagnostics(
        case,
        mode="cold",
        timeout_seconds=1,
    )
    warm = diagnose.signed_sum_diagnostics(
        case,
        mode="warm",
        timeout_seconds=1,
    )

    assert cold["status"] == "ok"
    assert cold["result_mod_1000000007"] == "4744"
    assert int(cold["reachable_subset_sums"]) > 0
    assert int(cold["m_cache_misses_delta"]) > 0
    assert warm["status"] == "ok"
    assert warm["result_mod_1000000007"] == "4744"
    assert warm["m_cache_misses_delta"] == "0"


def test_rook_strategy_diagnostics_agree_on_small_case() -> None:
    """Sequential and tree rook strategies should compute the same result."""
    case = diagnose.DiagnosticCase("known", 8, [2, 2, 4])
    summaries = []
    for strategy_name in [
        "schoolbook_sequential",
        "ntt_sequential",
        "schoolbook_tree",
        "ntt_tree",
    ]:
        summary, steps = diagnose.rook_strategy_diagnostics(
            case,
            diagnose.ROOK_STRATEGIES[strategy_name],
            timeout_seconds=1,
        )
        summaries.append(summary)
        assert summary["status"] == "ok"
        assert len(steps) > 0

    assert {summary["result_mod_1000000007"] for summary in summaries} == {"4744"}


def test_rook_step_timeout_is_recorded() -> None:
    """A timed-out multiplication should appear in step diagnostics."""
    left = [1] * 10_000
    right = [1] * 10_000
    result, row = diagnose.multiply_with_step_diagnostics(
        left,
        right,
        use_ntt=False,
        timeout_seconds=0.01,
    )

    assert result is None
    assert row["status"] == "timeout"


def test_plotter_creates_separate_svg_files(tmp_path: Path) -> None:
    """The plotter should produce standalone SVGs from benchmark CSVs."""
    methods = [
        bench.METHODS["signed_sum"],
        bench.METHODS["rook_schoolbook"],
    ]
    input_dir = tmp_path / "results"
    output_dir = tmp_path / "plots"
    bench.write_rows(
        input_dir / "cycle_families.csv",
        bench.family_rows(
            [4, 6],
            {"single_cycle"},
            methods,
            repeats=1,
            track_memory=True,
        ),
    )
    bench.write_rows(
        input_dir / "all_cycle_types.csv",
        bench.all_cycle_type_rows(
            [4],
            methods,
            repeats=1,
            track_memory=True,
            max_cycle_types=100,
            allow_large_all_cycle_types=False,
        ),
    )

    written = plots.create_plots(input_dir, output_dir)
    names = {path.name for path in written}

    assert "runtime_family_single_cycle.svg" in names
    assert "runtime_all_cycle_types_n_4.svg" in names
    assert "runtime_vs_cycle_count_n_4.svg" in names
    assert all(path.exists() for path in written)
