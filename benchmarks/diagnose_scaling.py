#!/usr/bin/env python3
"""Diagnose scaling behavior of the 2-row extension-counting methods.

This script is intentionally more invasive than the benchmark runner: it
decomposes the signed-sum and rook-polynomial methods into internal work units
so slow cases can be explained before choosing implementation changes.
"""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import csv
import heapq
import math
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmarks.benchmark_cycle_type_methods import (
    MODULUS_FOR_CSV,
    MethodTimeoutError,
    format_cycle_type,
    format_cycle_type_preview,
    method_timeout,
    named_cycle_families,
    parse_int_list,
)
from latin_rectangles.extension_counting import (
    _apply_inclusion_exclusion,
    _one_cycle_extension_count,
    _validate_cycle_lengths,
)
from latin_rectangles.rook_polynomials import (
    _NTT_MAX_CRT_PRIMES,
    _NTT_MIN_POLY_LEN,
    _NTT_SCHOOLBOOK_THRESHOLD,
    _convolve_mod,
    _estimate_crt_prime_count,
    _next_power_of_two,
    get_rook_polynomial_for_cycle,
    multiply_polynomials,
    multiply_polynomials_fft,
)


@dataclass(frozen=True)
class DiagnosticCase:
    """One named cycle type to diagnose."""

    family: str
    n: int
    cycle_lengths: list[int]


@dataclass(frozen=True)
class RookStrategy:
    """A rook-polynomial multiplication strategy."""

    name: str
    use_ntt: bool
    use_product_tree: bool


ROOK_STRATEGIES: dict[str, RookStrategy] = {
    "schoolbook_sequential": RookStrategy(
        "schoolbook_sequential", use_ntt=False, use_product_tree=False
    ),
    "ntt_sequential": RookStrategy(
        "ntt_sequential", use_ntt=True, use_product_tree=False
    ),
    "schoolbook_tree": RookStrategy(
        "schoolbook_tree", use_ntt=False, use_product_tree=True
    ),
    "ntt_tree": RookStrategy("ntt_tree", use_ntt=True, use_product_tree=True),
}


SIGNED_SUM_COLUMNS = [
    "family",
    "n",
    "cycle_count",
    "largest_cycle",
    "cycle_gcd",
    "cycle_type",
    "mode",
    "status",
    "error",
    "subset_dp_seconds",
    "accumulation_seconds",
    "total_seconds",
    "reachable_subset_sums",
    "unique_m_values",
    "m_value_min",
    "m_value_max",
    "m_cache_hits_delta",
    "m_cache_misses_delta",
    "result_bits",
    "result_mod_1000000007",
]

ROOK_STEP_COLUMNS = [
    "family",
    "n",
    "strategy",
    "step",
    "len_left",
    "len_right",
    "output_len",
    "len_ratio",
    "product_size",
    "predicted_path",
    "ntt_size",
    "coefficient_bound_bits",
    "ntt_prime_calls",
    "elapsed_seconds",
    "status",
    "error",
]

ROOK_SUMMARY_COLUMNS = [
    "family",
    "n",
    "cycle_count",
    "largest_cycle",
    "cycle_gcd",
    "cycle_type",
    "strategy",
    "status",
    "error",
    "steps_completed",
    "schoolbook_steps",
    "ntt_steps",
    "scalar_steps",
    "total_ntt_prime_calls",
    "multiply_seconds",
    "inclusion_seconds",
    "total_seconds",
    "result_bits",
    "result_mod_1000000007",
]


def parse_csv_names(raw: str) -> list[str]:
    """Parse a comma-separated list of names."""
    names = [part.strip() for part in raw.split(",") if part.strip()]
    if not names:
        raise argparse.ArgumentTypeError("Expected at least one name")
    return names


def parse_rook_strategies(raw: str) -> list[RookStrategy]:
    """Parse selected rook diagnostic strategies."""
    names = parse_csv_names(raw)
    unknown = sorted(set(names) - set(ROOK_STRATEGIES))
    if unknown:
        valid = ", ".join(sorted(ROOK_STRATEGIES))
        raise argparse.ArgumentTypeError(
            f"Unknown rook strategy: {', '.join(unknown)}. Valid strategies: {valid}"
        )
    return [ROOK_STRATEGIES[name] for name in names]


def selected_cases(
    ns: Sequence[int], family_names: Sequence[str]
) -> list[DiagnosticCase]:
    """Build diagnostic cases from named families."""
    cases: list[DiagnosticCase] = []
    for n in ns:
        families = named_cycle_families(n)
        unknown = sorted(set(family_names) - set(families))
        if unknown:
            valid = ", ".join(sorted(families))
            raise ValueError(
                f"n={n} does not support family name(s): {', '.join(unknown)}. "
                f"Valid families: {valid}"
            )
        for family in family_names:
            cases.append(DiagnosticCase(family, n, families[family]))
    return cases


def cycle_gcd(cycle_lengths: Sequence[int]) -> int:
    """Return gcd of all cycle lengths."""
    result = 0
    for length in cycle_lengths:
        result = math.gcd(result, length)
    return result


def base_case_row(case: DiagnosticCase) -> dict[str, str]:
    """Return shared CSV columns for one diagnostic case."""
    return {
        "family": case.family,
        "n": str(case.n),
        "cycle_count": str(len(case.cycle_lengths)),
        "largest_cycle": str(max(case.cycle_lengths)),
        "cycle_gcd": str(cycle_gcd(case.cycle_lengths)),
        "cycle_type": format_cycle_type(case.cycle_lengths),
    }


def signed_sum_diagnostics(
    case: DiagnosticCase,
    *,
    mode: str,
    timeout_seconds: float,
) -> dict[str, str]:
    """Return one diagnostic row for the signed-sum method."""
    if mode not in {"cold", "warm"}:
        raise ValueError(f"Unknown signed-sum mode {mode!r}")

    lengths = tuple(case.cycle_lengths)
    _validate_cycle_lengths(lengths)
    if mode == "cold":
        _one_cycle_extension_count.cache_clear()

    total_started = time.perf_counter()
    row = base_case_row(case)
    row.update({"mode": mode, "status": "ok", "error": ""})
    cache_before = _one_cycle_extension_count.cache_info()

    try:
        with method_timeout(timeout_seconds):
            subset_started = time.perf_counter()
            subset_counts = [0] * (case.n + 1)
            subset_counts[0] = 1
            max_subset_sum = 0
            for cycle_length in lengths:
                for subset_sum in range(max_subset_sum, -1, -1):
                    count = subset_counts[subset_sum]
                    if count:
                        subset_counts[subset_sum + cycle_length] += count
                max_subset_sum += cycle_length
            subset_seconds = time.perf_counter() - subset_started

            reachable = [
                (subset_sum, multiplicity)
                for subset_sum, multiplicity in enumerate(subset_counts)
                if multiplicity
            ]
            m_values = {abs(2 * subset_sum - case.n) for subset_sum, _ in reachable}
            row.update(
                {
                    "subset_dp_seconds": f"{subset_seconds:.12g}",
                    "reachable_subset_sums": str(len(reachable)),
                    "unique_m_values": str(len(m_values)),
                    "m_value_min": str(min(m_values) if m_values else ""),
                    "m_value_max": str(max(m_values) if m_values else ""),
                }
            )

            cache_before = _one_cycle_extension_count.cache_info()
            accumulation_started = time.perf_counter()
            signed_total = 0
            for subset_sum, multiplicity in reachable:
                signed_total += multiplicity * _one_cycle_extension_count(
                    abs(2 * subset_sum - case.n)
                )
            accumulation_seconds = time.perf_counter() - accumulation_started
            cache_after = _one_cycle_extension_count.cache_info()

            if signed_total % 2 != 0:
                raise AssertionError("Signed-sum total should be even")
            result = signed_total // 2

            row.update(
                {
                    "accumulation_seconds": f"{accumulation_seconds:.12g}",
                    "total_seconds": f"{time.perf_counter() - total_started:.12g}",
                    "m_cache_hits_delta": str(cache_after.hits - cache_before.hits),
                    "m_cache_misses_delta": str(
                        cache_after.misses - cache_before.misses
                    ),
                    "result_bits": str(result.bit_length()),
                    "result_mod_1000000007": str(result % MODULUS_FOR_CSV),
                }
            )
    except MethodTimeoutError as exc:
        cache_after = _one_cycle_extension_count.cache_info()
        row.update(
            {
                "status": "timeout",
                "error": str(exc),
                "total_seconds": f"{time.perf_counter() - total_started:.12g}",
                "m_cache_hits_delta": str(cache_after.hits - cache_before.hits),
                "m_cache_misses_delta": str(cache_after.misses - cache_before.misses),
            }
        )

    for column in SIGNED_SUM_COLUMNS:
        row.setdefault(column, "")
    return row


def predicted_ntt_path(poly1: list[int], poly2: list[int]) -> str:
    """Predict the branch used by ``multiply_polynomials_fft``."""
    n1, n2 = len(poly1), len(poly2)
    if n1 == 0 or n2 == 0:
        return "zero"
    if n1 == 1 or n2 == 1:
        return "scalar"
    if min(n1, n2) < _NTT_MIN_POLY_LEN or n1 * n2 <= _NTT_SCHOOLBOOK_THRESHOLD:
        return "schoolbook_fallback"
    if _estimate_crt_prime_count(coefficient_bound(poly1, poly2)) > _NTT_MAX_CRT_PRIMES:
        return "crt_prime_fallback"
    return "ntt"


def coefficient_bound(poly1: list[int], poly2: list[int]) -> int:
    """Return the transform coefficient bound."""
    if not poly1 or not poly2:
        return 0
    return min(len(poly1), len(poly2)) * max(map(abs, poly1)) * max(map(abs, poly2))


def coefficient_bound_bits(poly1: list[int], poly2: list[int]) -> int:
    """Return the bit length of the transform coefficient bound."""
    return coefficient_bound(poly1, poly2).bit_length()


def ntt_size_for(poly1: list[int], poly2: list[int]) -> int:
    """Return the transform size that NTT would use."""
    return _next_power_of_two(len(poly1) + len(poly2) - 1)


def remaining_timeout(deadline: float | None) -> float:
    """Return seconds left before a deadline, or 0 for no timeout."""
    if deadline is None:
        return 0.0
    remaining = deadline - time.perf_counter()
    if remaining <= 0:
        raise MethodTimeoutError("strategy exceeded its timeout")
    return remaining


def multiply_with_step_diagnostics(
    poly1: list[int],
    poly2: list[int],
    *,
    use_ntt: bool,
    timeout_seconds: float,
) -> tuple[list[int] | None, dict[str, str]]:
    """Multiply two polynomials and return diagnostic fields for the step."""
    predicted_path = predicted_ntt_path(poly1, poly2) if use_ntt else "schoolbook"
    ntt_prime_calls = 0
    started = time.perf_counter()
    status = "ok"
    error = ""
    result: list[int] | None = None

    original_convolve: Callable[..., list[int]] = _convolve_mod

    def counting_convolve(*args: Any, **kwargs: Any) -> list[int]:
        nonlocal ntt_prime_calls
        ntt_prime_calls += 1
        return original_convolve(*args, **kwargs)

    try:
        with method_timeout(timeout_seconds):
            if use_ntt:
                import latin_rectangles.rook_polynomials as rook_polynomials

                rook_polynomials._convolve_mod = counting_convolve
                try:
                    result = multiply_polynomials_fft(poly1, poly2)
                finally:
                    rook_polynomials._convolve_mod = original_convolve
            else:
                result = multiply_polynomials(poly1, poly2)
    except MethodTimeoutError as exc:
        status = "timeout"
        error = str(exc)
    finally:
        elapsed = time.perf_counter() - started

    len1 = len(poly1)
    len2 = len(poly2)
    min_len = min(len1, len2)
    max_len = max(len1, len2)
    row = {
        "len_left": str(len1),
        "len_right": str(len2),
        "output_len": str(len1 + len2 - 1),
        "len_ratio": f"{(max_len / min_len if min_len else 0):.12g}",
        "product_size": str(len1 * len2),
        "predicted_path": predicted_path,
        "ntt_size": str(ntt_size_for(poly1, poly2) if predicted_path == "ntt" else ""),
        "coefficient_bound_bits": str(coefficient_bound_bits(poly1, poly2)),
        "ntt_prime_calls": str(ntt_prime_calls),
        "elapsed_seconds": f"{elapsed:.12g}",
        "status": status,
        "error": error,
    }
    return result, row


def record_multiply_step(
    step_rows: list[dict[str, str]],
    case: DiagnosticCase,
    strategy: RookStrategy,
    step_number: int,
    step_data: dict[str, str],
) -> None:
    """Append one rook multiplication step row."""
    row = {
        "family": case.family,
        "n": str(case.n),
        "strategy": strategy.name,
        "step": str(step_number),
    }
    row.update(step_data)
    for column in ROOK_STEP_COLUMNS:
        row.setdefault(column, "")
    step_rows.append(row)


def multiply_sequential(
    polynomials: Sequence[list[int]],
    case: DiagnosticCase,
    strategy: RookStrategy,
    *,
    deadline: float | None,
    step_rows: list[dict[str, str]],
) -> tuple[list[int], int]:
    """Multiply polynomials in input order."""
    total = [1]
    step_number = 0
    for polynomial in polynomials:
        step_number += 1
        total, step_data = multiply_with_step_diagnostics(
            total,
            polynomial,
            use_ntt=strategy.use_ntt,
            timeout_seconds=remaining_timeout(deadline),
        )
        record_multiply_step(step_rows, case, strategy, step_number, step_data)
        if total is None:
            raise MethodTimeoutError(step_data["error"])
    return total, step_number


def multiply_product_tree(
    polynomials: Sequence[list[int]],
    case: DiagnosticCase,
    strategy: RookStrategy,
    *,
    deadline: float | None,
    step_rows: list[dict[str, str]],
) -> tuple[list[int], int]:
    """Multiply polynomials by repeatedly pairing the two shortest products."""
    heap: list[tuple[int, int, list[int]]] = []
    next_id = 0
    for polynomial in polynomials:
        heapq.heappush(heap, (len(polynomial), next_id, polynomial))
        next_id += 1

    step_number = 0
    while len(heap) > 1:
        _, _, left = heapq.heappop(heap)
        _, _, right = heapq.heappop(heap)
        step_number += 1
        product, step_data = multiply_with_step_diagnostics(
            left,
            right,
            use_ntt=strategy.use_ntt,
            timeout_seconds=remaining_timeout(deadline),
        )
        record_multiply_step(step_rows, case, strategy, step_number, step_data)
        if product is None:
            raise MethodTimeoutError(step_data["error"])
        heapq.heappush(heap, (len(product), next_id, product))
        next_id += 1

    if not heap:
        return [1], 0
    return heap[0][2], step_number


def rook_strategy_diagnostics(
    case: DiagnosticCase,
    strategy: RookStrategy,
    *,
    timeout_seconds: float,
) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Return a summary row and step rows for one rook strategy."""
    started = time.perf_counter()
    step_rows: list[dict[str, str]] = []
    summary = base_case_row(case)
    summary.update({"strategy": strategy.name, "status": "ok", "error": ""})
    polynomials = [
        get_rook_polynomial_for_cycle(length) for length in case.cycle_lengths
    ]
    deadline = started + timeout_seconds if timeout_seconds > 0 else None

    try:
        if strategy.use_product_tree:
            total_rook_poly, steps_completed = multiply_product_tree(
                polynomials,
                case,
                strategy,
                deadline=deadline,
                step_rows=step_rows,
            )
        else:
            total_rook_poly, steps_completed = multiply_sequential(
                polynomials,
                case,
                strategy,
                deadline=deadline,
                step_rows=step_rows,
            )

        multiply_seconds = time.perf_counter() - started
        inclusion_started = time.perf_counter()
        result = _apply_inclusion_exclusion(total_rook_poly, case.n)
        inclusion_seconds = time.perf_counter() - inclusion_started
        total_seconds = time.perf_counter() - started
        summary.update(
            {
                "steps_completed": str(steps_completed),
                "multiply_seconds": f"{multiply_seconds:.12g}",
                "inclusion_seconds": f"{inclusion_seconds:.12g}",
                "total_seconds": f"{total_seconds:.12g}",
                "result_bits": str(result.bit_length()),
                "result_mod_1000000007": str(result % MODULUS_FOR_CSV),
            }
        )
    except MethodTimeoutError as exc:
        summary.update(
            {
                "status": "timeout",
                "error": str(exc),
                "steps_completed": str(len(step_rows)),
                "total_seconds": f"{time.perf_counter() - started:.12g}",
            }
        )

    schoolbook_steps = 0
    ntt_steps = 0
    scalar_steps = 0
    ntt_prime_calls = 0
    for row in step_rows:
        predicted_path = row["predicted_path"]
        if predicted_path in {
            "schoolbook",
            "schoolbook_fallback",
            "crt_prime_fallback",
        }:
            schoolbook_steps += 1
        elif predicted_path == "ntt":
            ntt_steps += 1
        elif predicted_path == "scalar":
            scalar_steps += 1
        ntt_prime_calls += int(row["ntt_prime_calls"] or "0")

    summary.update(
        {
            "schoolbook_steps": str(schoolbook_steps),
            "ntt_steps": str(ntt_steps),
            "scalar_steps": str(scalar_steps),
            "total_ntt_prime_calls": str(ntt_prime_calls),
        }
    )
    for column in ROOK_SUMMARY_COLUMNS:
        summary.setdefault(column, "")
    return summary, step_rows


def write_csv(
    path: Path, columns: Sequence[str], rows: Sequence[dict[str, str]]
) -> None:
    """Write rows to a CSV path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Diagnose internal scaling behavior of 2-row counting methods."
    )
    parser.add_argument(
        "--ns",
        type=parse_int_list,
        default=parse_int_list("2048"),
        help="Comma-separated n values.",
    )
    parser.add_argument(
        "--families",
        type=parse_csv_names,
        default=parse_csv_names(
            "single_cycle,two_equal_cycles,four_equal_cycles,mostly_16_cycles,mixed_ladder"
        ),
        help="Comma-separated named cycle families.",
    )
    parser.add_argument(
        "--signed-modes",
        type=parse_csv_names,
        default=parse_csv_names("cold,warm"),
        help="Comma-separated signed-sum modes: cold,warm.",
    )
    parser.add_argument(
        "--rook-strategies",
        type=parse_rook_strategies,
        default=parse_rook_strategies(
            "schoolbook_sequential,ntt_sequential,schoolbook_tree,ntt_tree"
        ),
        help="Comma-separated rook strategies.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="Per signed-sum or multiplication-step timeout.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_results/diagnostics"),
        help="Directory for diagnostic CSVs.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Run diagnostics and write CSV reports."""
    args = parse_args(argv)
    cases = selected_cases(args.ns, args.families)
    signed_rows: list[dict[str, str]] = []
    rook_summary_rows: list[dict[str, str]] = []
    rook_step_rows: list[dict[str, str]] = []

    for case in cases:
        print(
            f"case n={case.n} family={case.family} "
            f"cycle_count={len(case.cycle_lengths)} "
            f"largest={max(case.cycle_lengths)} "
            f"gcd={cycle_gcd(case.cycle_lengths)} "
            f"cycle_type={format_cycle_type_preview(case.cycle_lengths)}",
            flush=True,
        )
        for mode in args.signed_modes:
            print(f"  signed_sum mode={mode}", flush=True)
            row = signed_sum_diagnostics(
                case,
                mode=mode,
                timeout_seconds=args.timeout_seconds,
            )
            signed_rows.append(row)
            print(
                f"    status={row['status']} total={row['total_seconds']}s "
                f"reachable={row['reachable_subset_sums']} "
                f"m_misses={row['m_cache_misses_delta']}",
                flush=True,
            )

        for strategy in args.rook_strategies:
            print(f"  rook strategy={strategy.name}", flush=True)
            summary, steps = rook_strategy_diagnostics(
                case,
                strategy,
                timeout_seconds=args.timeout_seconds,
            )
            rook_summary_rows.append(summary)
            rook_step_rows.extend(steps)
            print(
                f"    status={summary['status']} total={summary['total_seconds']}s "
                f"steps={summary['steps_completed']} "
                f"ntt_steps={summary['ntt_steps']} "
                f"prime_calls={summary['total_ntt_prime_calls']}",
                flush=True,
            )

    write_csv(
        args.output_dir / "signed_sum_diagnostics.csv",
        SIGNED_SUM_COLUMNS,
        signed_rows,
    )
    write_csv(
        args.output_dir / "rook_strategy_summary.csv",
        ROOK_SUMMARY_COLUMNS,
        rook_summary_rows,
    )
    write_csv(
        args.output_dir / "rook_multiply_steps.csv",
        ROOK_STEP_COLUMNS,
        rook_step_rows,
    )
    print(f"Wrote diagnostics to {args.output_dir}")


if __name__ == "__main__":
    main()
