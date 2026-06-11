#!/usr/bin/env python3
"""Benchmark 2-row extension-counting methods on cycle-type inputs.

The script writes CSV data for two benchmark suites:

* named fixed cycle families over many values of n, suitable for probing n in
  the hundreds or thousands;
* exhaustive derangement cycle types for selected fixed n, suitable for
  structural sensitivity studies.

Every benchmarked case checks that all selected methods return the same count.
"""

from __future__ import annotations

import argparse
import csv
import gc
import signal
import statistics
import time
import tracemalloc
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from latin_rectangles import (
    count_cycle_structure_extensions,
    count_extensions,
    create_cycle_structure,
)

MODULUS_FOR_CSV = 1_000_000_007


@dataclass(frozen=True)
class Method:
    """A named counting method used by the benchmark harness."""

    name: str
    func: Callable[[list[int]], int]


@dataclass(frozen=True)
class Measurement:
    """Timing and memory summary for one method on one cycle type."""

    result: int
    median_seconds: float
    min_seconds: float
    peak_memory_mb: float


class MethodTimeoutError(TimeoutError):
    """Raised when one benchmark method exceeds its configured timeout."""


@dataclass(frozen=True)
class BenchmarkCase:
    """One cycle-type input to benchmark."""

    suite: str
    family: str
    n: int
    cycle_lengths: list[int]
    cycle_type_index: int | None = None
    total_cycle_types_for_n: int | None = None


def _count_touchard(cycle_lengths: list[int]) -> int:
    return count_cycle_structure_extensions(cycle_lengths, method="touchard")


def _count_cycle_auto(cycle_lengths: list[int]) -> int:
    return count_cycle_structure_extensions(cycle_lengths, method="auto")


def _count_rook_schoolbook(cycle_lengths: list[int]) -> int:
    return count_extensions(create_cycle_structure(cycle_lengths), use_fft=False)


def _count_rook_ntt(cycle_lengths: list[int]) -> int:
    return count_extensions(create_cycle_structure(cycle_lengths), use_fft=True)


METHODS: dict[str, Method] = {
    "cycle_auto": Method("cycle_auto", _count_cycle_auto),
    "touchard": Method("touchard", _count_touchard),
    "rook_schoolbook": Method("rook_schoolbook", _count_rook_schoolbook),
    "rook_ntt": Method("rook_ntt", _count_rook_ntt),
}


def parse_int_list(raw: str) -> list[int]:
    """Parse a comma-separated list of positive integers."""
    try:
        values = [int(part.strip()) for part in raw.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Expected comma-separated integers, got {raw!r}"
        ) from exc

    if not values:
        raise argparse.ArgumentTypeError("Expected at least one integer")
    if any(value <= 0 for value in values):
        raise argparse.ArgumentTypeError("All values must be positive integers")
    return values


def parse_methods(raw: str) -> list[Method]:
    """Parse a comma-separated method list."""
    names = [part.strip() for part in raw.split(",") if part.strip()]
    if not names:
        raise argparse.ArgumentTypeError("Expected at least one method")

    unknown = sorted(set(names) - set(METHODS))
    if unknown:
        valid = ", ".join(sorted(METHODS))
        raise argparse.ArgumentTypeError(
            f"Unknown method(s): {', '.join(unknown)}. Valid methods: {valid}"
        )
    return [METHODS[name] for name in names]


def format_cycle_type(cycle_lengths: Sequence[int]) -> str:
    """Format a cycle type compactly for CSV output."""
    return "+".join(str(length) for length in cycle_lengths)


def format_cycle_type_preview(
    cycle_lengths: Sequence[int], *, max_parts: int = 12
) -> str:
    """Format a cycle type for progress logs without flooding the terminal."""
    if len(cycle_lengths) <= max_parts:
        return str(list(cycle_lengths))
    head_count = max_parts // 2
    tail_count = max_parts - head_count
    head = ", ".join(str(part) for part in cycle_lengths[:head_count])
    tail = ", ".join(str(part) for part in cycle_lengths[-tail_count:])
    return f"[{head}, ..., {tail}]"


@contextmanager
def method_timeout(seconds: float) -> Iterator[None]:
    """Interrupt a benchmark method after ``seconds`` on Unix-like systems."""
    if seconds <= 0:
        yield
        return

    def handle_timeout(_signum: int, _frame: object) -> None:
        raise MethodTimeoutError(f"method exceeded {seconds:g} seconds")

    old_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, handle_timeout)
    old_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
        if old_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, old_timer[0], old_timer[1])


def iter_cycle_types(n: int) -> Iterator[list[int]]:
    """Yield all partitions of n with every part at least 2."""

    def rec(remaining: int, min_part: int, current: list[int]) -> Iterator[list[int]]:
        if remaining == 0:
            yield current.copy()
            return
        for part in range(min_part, remaining + 1):
            if remaining - part == 1:
                continue
            current.append(part)
            yield from rec(remaining - part, part, current)
            current.pop()

    if n <= 1:
        return
    yield from rec(n, 2, [])


def count_cycle_types(n: int) -> int:
    """Count partitions of n with no part equal to 1."""
    if n <= 1:
        return 0

    counts = [0] * (n + 1)
    counts[0] = 1
    for part in range(2, n + 1):
        for total in range(part, n + 1):
            counts[total] += counts[total - part]
    return counts[n]


def near_uniform_cycle_type(n: int, target_part: int) -> list[int] | None:
    """Return a no-1 cycle type that is mostly made of ``target_part`` parts."""
    if n < 2 or target_part < 2:
        return None

    count, remainder = divmod(n, target_part)
    parts = [target_part] * count
    if remainder == 0:
        return parts
    if remainder == 1:
        if parts:
            parts[-1] += 1
            return sorted(parts)
        return None
    parts.append(remainder)
    return sorted(parts)


def mixed_ladder_cycle_type(n: int) -> list[int] | None:
    """Return a deterministic mixed-size no-1 cycle type."""
    if n < 2:
        return None
    if n == 3:
        return [3]

    ladder = [2, 3, 5, 8, 13, 21, 34]
    parts: list[int] = []
    remaining = n
    index = 0
    while remaining >= 2:
        candidate = ladder[index % len(ladder)]
        if candidate > remaining:
            candidate = remaining
        if remaining - candidate == 1:
            candidate -= 1
        if candidate < 2:
            if not parts:
                return None
            parts[-1] += remaining
            break
        parts.append(candidate)
        remaining -= candidate
        index += 1
    return sorted(parts)


def named_cycle_families(n: int) -> dict[str, list[int]]:
    """Build the standard cycle families for a given n."""
    candidates: dict[str, list[int] | None] = {
        "single_cycle": [n] if n >= 2 else None,
        "two_equal_cycles": [n // 2, n // 2] if n >= 4 and n % 2 == 0 else None,
        "four_equal_cycles": [n // 4] * 4 if n >= 8 and n % 4 == 0 else None,
        "transpositions": [2] * (n // 2) if n >= 2 and n % 2 == 0 else None,
        "mostly_3_cycles": near_uniform_cycle_type(n, 3),
        "mostly_8_cycles": near_uniform_cycle_type(n, 8),
        "mostly_16_cycles": near_uniform_cycle_type(n, 16),
        "mixed_ladder": mixed_ladder_cycle_type(n),
    }
    return {
        name: cycle_lengths
        for name, cycle_lengths in candidates.items()
        if cycle_lengths is not None
        and sum(cycle_lengths) == n
        and 1 not in cycle_lengths
    }


def benchmark_method(
    method: Method,
    cycle_lengths: list[int],
    *,
    repeats: int,
    track_memory: bool,
    timeout_seconds: float = 0,
) -> Measurement:
    """Benchmark one method on one cycle type."""
    if repeats <= 0:
        raise ValueError("repeats must be positive")

    times: list[float] = []
    peaks_mb: list[float] = []
    expected_result: int | None = None

    for _ in range(repeats):
        gc.collect()
        if track_memory:
            tracemalloc.start()

        started = time.perf_counter()
        try:
            with method_timeout(timeout_seconds):
                result = method.func(cycle_lengths)
            elapsed = time.perf_counter() - started
        finally:
            peak_mb = 0.0
            if track_memory:
                _, peak_bytes = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                peak_mb = peak_bytes / (1024 * 1024)

        if expected_result is None:
            expected_result = result
        elif result != expected_result:
            raise AssertionError(
                f"{method.name} returned inconsistent results for "
                f"{format_cycle_type(cycle_lengths)}"
            )

        times.append(elapsed)
        peaks_mb.append(peak_mb)

    if expected_result is None:
        raise AssertionError("benchmark loop did not run")

    return Measurement(
        result=expected_result,
        median_seconds=statistics.median(times),
        min_seconds=min(times),
        peak_memory_mb=max(peaks_mb),
    )


def benchmark_case(
    case: BenchmarkCase,
    methods: Sequence[Method],
    *,
    repeats: int,
    track_memory: bool,
    timeout_seconds: float = 0,
    progress: str = "case",
) -> list[dict[str, str]]:
    """Benchmark all methods for one case and assert method agreement."""
    rows: list[dict[str, str]] = []
    reference: int | None = None
    for method in methods:
        if progress == "method":
            print(f"  method={method.name} start", flush=True)
        started = time.perf_counter()
        try:
            measurement = benchmark_method(
                method,
                case.cycle_lengths,
                repeats=repeats,
                track_memory=track_memory,
                timeout_seconds=timeout_seconds,
            )
        except MethodTimeoutError as exc:
            elapsed = time.perf_counter() - started
            if progress == "method":
                print(
                    f"  method={method.name} timeout after {elapsed:.3f}s", flush=True
                )
            rows.append(
                {
                    "suite": case.suite,
                    "family": case.family,
                    "n": str(case.n),
                    "cycle_type": format_cycle_type(case.cycle_lengths),
                    "cycle_type_index": ""
                    if case.cycle_type_index is None
                    else str(case.cycle_type_index),
                    "total_cycle_types_for_n": ""
                    if case.total_cycle_types_for_n is None
                    else str(case.total_cycle_types_for_n),
                    "cycle_count": str(len(case.cycle_lengths)),
                    "largest_cycle": str(max(case.cycle_lengths)),
                    "method": method.name,
                    "status": "timeout",
                    "error": str(exc),
                    "repeats": str(repeats),
                    "time_seconds_median": "",
                    "time_seconds_min": "",
                    "peak_memory_mb": "",
                    "result_bits": "",
                    "result_mod_1000000007": "",
                }
            )
            continue

        elapsed = time.perf_counter() - started
        if progress == "method":
            print(f"  method={method.name} ok in {elapsed:.3f}s", flush=True)
        if reference is None:
            reference = measurement.result
        elif measurement.result != reference:
            raise AssertionError(
                f"Method mismatch for {format_cycle_type(case.cycle_lengths)}: "
                f"{method.name} returned {measurement.result}, expected {reference}"
            )

        rows.append(
            {
                "suite": case.suite,
                "family": case.family,
                "n": str(case.n),
                "cycle_type": format_cycle_type(case.cycle_lengths),
                "cycle_type_index": ""
                if case.cycle_type_index is None
                else str(case.cycle_type_index),
                "total_cycle_types_for_n": ""
                if case.total_cycle_types_for_n is None
                else str(case.total_cycle_types_for_n),
                "cycle_count": str(len(case.cycle_lengths)),
                "largest_cycle": str(max(case.cycle_lengths)),
                "method": method.name,
                "status": "ok",
                "error": "",
                "repeats": str(repeats),
                "time_seconds_median": f"{measurement.median_seconds:.12g}",
                "time_seconds_min": f"{measurement.min_seconds:.12g}",
                "peak_memory_mb": f"{measurement.peak_memory_mb:.12g}",
                "result_bits": str(measurement.result.bit_length()),
                "result_mod_1000000007": str(measurement.result % MODULUS_FOR_CSV),
            }
        )
    return rows


CSV_COLUMNS = [
    "suite",
    "family",
    "n",
    "cycle_type",
    "cycle_type_index",
    "total_cycle_types_for_n",
    "cycle_count",
    "largest_cycle",
    "method",
    "status",
    "error",
    "repeats",
    "time_seconds_median",
    "time_seconds_min",
    "peak_memory_mb",
    "result_bits",
    "result_mod_1000000007",
]


def write_rows(path: Path, rows: Iterable[dict[str, str]]) -> int:
    """Write benchmark rows to a CSV file and return the number written."""
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def family_rows(
    ns: Sequence[int],
    selected_families: set[str] | None,
    methods: Sequence[Method],
    *,
    repeats: int,
    track_memory: bool,
    timeout_seconds: float = 0,
    progress: str = "case",
) -> Iterator[dict[str, str]]:
    """Yield CSV rows for the fixed-family suite."""
    for n in ns:
        families = named_cycle_families(n)
        for family, cycle_lengths in families.items():
            if selected_families is not None and family not in selected_families:
                continue
            if progress in {"case", "method"}:
                print(
                    f"family n={n} {family} "
                    f"cycle_count={len(cycle_lengths)} "
                    f"largest={max(cycle_lengths)} "
                    f"cycle_type={format_cycle_type_preview(cycle_lengths)}",
                    flush=True,
                )
            yield from benchmark_case(
                BenchmarkCase(
                    suite="families",
                    family=family,
                    n=n,
                    cycle_lengths=cycle_lengths,
                ),
                methods,
                repeats=repeats,
                track_memory=track_memory,
                timeout_seconds=timeout_seconds,
                progress=progress,
            )


def all_cycle_type_rows(
    ns: Sequence[int],
    methods: Sequence[Method],
    *,
    repeats: int,
    track_memory: bool,
    max_cycle_types: int,
    allow_large_all_cycle_types: bool,
    timeout_seconds: float = 0,
    progress: str = "case",
) -> Iterator[dict[str, str]]:
    """Yield CSV rows for exhaustive fixed-n cycle-type suites."""
    for n in ns:
        total = count_cycle_types(n)
        if total > max_cycle_types and not allow_large_all_cycle_types:
            raise ValueError(
                f"n={n} has {total:,} cycle types. Increase --max-cycle-types "
                "or pass --allow-large-all-cycle-types if this is intentional."
            )

        cycle_types = sorted(
            iter_cycle_types(n),
            key=lambda cycle_type: (len(cycle_type), max(cycle_type), cycle_type),
        )
        for index, cycle_lengths in enumerate(cycle_types, start=1):
            if progress in {"case", "method"}:
                print(
                    f"all-cycle-types n={n} {index}/{total} "
                    f"cycle_count={len(cycle_lengths)} "
                    f"largest={max(cycle_lengths)} "
                    f"cycle_type={format_cycle_type_preview(cycle_lengths)}",
                    flush=True,
                )
            yield from benchmark_case(
                BenchmarkCase(
                    suite="all_cycle_types",
                    family=f"all_cycle_types_n_{n}",
                    n=n,
                    cycle_lengths=cycle_lengths,
                    cycle_type_index=index,
                    total_cycle_types_for_n=total,
                ),
                methods,
                repeats=repeats,
                track_memory=track_memory,
                timeout_seconds=timeout_seconds,
                progress=progress,
            )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Benchmark Latin-rectangle 2-row extension-counting methods."
    )
    parser.add_argument(
        "--suite",
        choices=["families", "all-cycle-types", "both"],
        default="both",
        help="Benchmark suite to run.",
    )
    parser.add_argument(
        "--family-ns",
        type=parse_int_list,
        default=parse_int_list("64,128,256,512,1024"),
        help="Comma-separated n values for fixed cycle families.",
    )
    parser.add_argument(
        "--all-cycle-ns",
        type=parse_int_list,
        default=parse_int_list("30"),
        help="Comma-separated n values for exhaustive all-cycle-type benchmarks.",
    )
    parser.add_argument(
        "--families",
        default="",
        help=(
            "Optional comma-separated subset of families. Valid names are "
            "single_cycle, two_equal_cycles, four_equal_cycles, transpositions, "
            "mostly_3_cycles, mostly_8_cycles, mostly_16_cycles, mixed_ladder."
        ),
    )
    parser.add_argument(
        "--methods",
        type=parse_methods,
        default=parse_methods("touchard,rook_schoolbook,rook_ntt"),
        help="Comma-separated methods: cycle_auto, touchard, rook_schoolbook, rook_ntt.",
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=0.0,
        help=(
            "Optional per-method timeout. A timed-out method writes a timeout "
            "row and is excluded from equality checks for that case."
        ),
    )
    parser.add_argument(
        "--progress",
        choices=["none", "case", "method"],
        default="case",
        help="How much progress to print while benchmarking.",
    )
    parser.add_argument(
        "--track-memory",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Track peak memory with tracemalloc.",
    )
    parser.add_argument(
        "--max-cycle-types",
        type=int,
        default=50_000,
        help="Safety guard for exhaustive all-cycle-type benchmarks.",
    )
    parser.add_argument(
        "--allow-large-all-cycle-types",
        action="store_true",
        help="Allow exhaustive all-cycle-type runs above --max-cycle-types.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_results/scaling"),
        help="Directory for CSV output.",
    )
    return parser.parse_args(argv)


def selected_family_names(raw: str) -> set[str] | None:
    """Parse the optional family filter."""
    if not raw.strip():
        return None
    families = {part.strip() for part in raw.split(",") if part.strip()}
    valid = set(named_cycle_families(64))
    unknown = families - valid
    if unknown:
        raise ValueError(
            f"Unknown family name(s): {', '.join(sorted(unknown))}. "
            f"Valid names: {', '.join(sorted(valid))}"
        )
    return families


def main(argv: Sequence[str] | None = None) -> None:
    """Run the selected benchmark suites."""
    args = parse_args(argv)
    families = selected_family_names(args.families)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.suite in {"families", "both"}:
        family_path = args.output_dir / "cycle_families.csv"
        count = write_rows(
            family_path,
            family_rows(
                args.family_ns,
                families,
                args.methods,
                repeats=args.repeats,
                track_memory=args.track_memory,
                timeout_seconds=args.timeout_seconds,
                progress=args.progress,
            ),
        )
        print(f"Wrote {count} rows to {family_path}")

    if args.suite in {"all-cycle-types", "both"}:
        all_cycle_path = args.output_dir / "all_cycle_types.csv"
        count = write_rows(
            all_cycle_path,
            all_cycle_type_rows(
                args.all_cycle_ns,
                args.methods,
                repeats=args.repeats,
                track_memory=args.track_memory,
                max_cycle_types=args.max_cycle_types,
                allow_large_all_cycle_types=args.allow_large_all_cycle_types,
                timeout_seconds=args.timeout_seconds,
                progress=args.progress,
            ),
        )
        print(f"Wrote {count} rows to {all_cycle_path}")


if __name__ == "__main__":
    main()
