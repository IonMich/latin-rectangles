#!/usr/bin/env python3
"""Benchmark cold-start exact cycle-type extension counting.

This helper is intentionally framework-neutral. OpenEvolve, Codex, or a custom
script can call it and consume the JSON output.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import time
import tracemalloc
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

MODULUS_FOR_DIGEST = 1_000_000_007
MethodName = Literal["auto", "touchard", "rook", "rook_ntt"]
ProfileName = Literal["smoke", "quick", "promotion"]


@dataclass(frozen=True)
class Workload:
    """A deterministic group of cycle types measured from a cold cache."""

    name: str
    kind: str
    cycle_types: tuple[tuple[int, ...], ...]
    weight: float
    description: str


def _count_from_cycle_type(cycle_type: Sequence[int], method: MethodName) -> int:
    """Call the current or historical cycle-type API."""
    import latin_rectangles as lr

    if hasattr(lr, "count_extensions_from_cycle_type"):
        return lr.count_extensions_from_cycle_type(list(cycle_type), method=method)
    if hasattr(lr, "count_cycle_structure_extensions"):
        return lr.count_cycle_structure_extensions(list(cycle_type), method=method)
    raise AttributeError("No supported cycle-type counting API found")


def _clear_touchard_cache() -> dict[str, int] | None:
    """Clear the private Touchard one-cycle cache when available."""
    try:
        from latin_rectangles.extension_counting import _one_cycle_extension_count
    except ImportError:
        return None

    if not hasattr(_one_cycle_extension_count, "cache_clear"):
        return None
    _one_cycle_extension_count.cache_clear()
    return _cache_info()


def _cache_info() -> dict[str, int] | None:
    """Return private Touchard cache stats when available."""
    try:
        from latin_rectangles.extension_counting import _one_cycle_extension_count
    except ImportError:
        return None

    if not hasattr(_one_cycle_extension_count, "cache_info"):
        return None
    info = _one_cycle_extension_count.cache_info()
    return {
        "hits": int(info.hits),
        "misses": int(info.misses),
        "currsize": int(info.currsize),
    }


def _clear_counter_cache(
    counter: Callable[[Sequence[int], MethodName], int],
) -> None:
    """Clear candidate-local caches when the evaluator exposes a hook."""
    clear_cache = getattr(counter, "clear_cache", None)
    if callable(clear_cache):
        clear_cache()


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


def near_uniform_cycle_type(n: int, target_part: int) -> list[int] | None:
    """Return a no-1 cycle type mostly made of ``target_part`` parts."""
    if n < 2 or target_part < 2:
        return None

    count, remainder = divmod(n, target_part)
    parts = [target_part] * count
    if remainder == 0:
        return parts
    if remainder == 1:
        if not parts:
            return None
        parts[-1] += 1
        return sorted(parts)
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
        candidate = min(ladder[index % len(ladder)], remaining)
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
    """Build deterministic high-n cycle families."""
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
        name: cycle_type
        for name, cycle_type in candidates.items()
        if cycle_type is not None
        and sum(cycle_type) == n
        and all(part >= 2 for part in cycle_type)
    }


def _dedupe_cycle_types(
    cycle_types: Iterable[Sequence[int]],
) -> tuple[tuple[int, ...], ...]:
    seen: set[tuple[int, ...]] = set()
    deduped: list[tuple[int, ...]] = []
    for cycle_type in cycle_types:
        normalized = tuple(sorted(cycle_type))
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return tuple(deduped)


def _sample_cycle_types(n: int, limit: int) -> tuple[tuple[int, ...], ...]:
    """Return a deterministic structural sample of no-1 partitions of n."""
    all_types = sorted(
        (tuple(cycle_type) for cycle_type in iter_cycle_types(n)),
        key=lambda cycle_type: (len(cycle_type), max(cycle_type), cycle_type),
    )
    if len(all_types) <= limit:
        return tuple(all_types)

    selected: list[tuple[int, ...]] = []
    for index in range(limit):
        source_index = round(index * (len(all_types) - 1) / (limit - 1))
        selected.append(all_types[source_index])
    selected.extend(tuple(v) for v in named_cycle_families(n).values())
    return _dedupe_cycle_types(selected)


def _workload(
    name: str,
    kind: str,
    cycle_types: Iterable[Sequence[int]],
    *,
    weight: float,
    description: str,
) -> Workload:
    return Workload(
        name=name,
        kind=kind,
        cycle_types=_dedupe_cycle_types(cycle_types),
        weight=weight,
        description=description,
    )


def build_workloads(profile: ProfileName) -> list[Workload]:
    """Build the deterministic workload suite for a profile."""
    if profile == "smoke":
        return [
            _workload(
                "all_cycle_types_n_8",
                "fixed_n_batch",
                iter_cycle_types(8),
                weight=0.45,
                description="Tiny fixed-n batch for smoke tests.",
            ),
            _workload(
                "named_families_n_64",
                "named_families",
                named_cycle_families(64).values(),
                weight=0.35,
                description="Small named-family cold starts.",
            ),
            _workload(
                "dense_touchard_n_128",
                "dense_touchard",
                [mixed_ladder_cycle_type(128) or [128]],
                weight=0.20,
                description="Small dense mixed-ladder stress case.",
            ),
        ]

    if profile == "quick":
        fixed_n_types: list[Sequence[int]] = []
        fixed_n_types.extend(iter_cycle_types(20))
        fixed_n_types.extend(_sample_cycle_types(30, 2_000))
        fixed_n_types.extend(_sample_cycle_types(40, 400))

        named_types: list[Sequence[int]] = []
        for n in (256, 512, 1024):
            named_types.extend(named_cycle_families(n).values())

        dense_types: list[Sequence[int]] = []
        for n in (1024,):
            mixed = mixed_ladder_cycle_type(n)
            if mixed is not None:
                dense_types.append(mixed)
        dense_types.extend(
            [
                [2] * 256,
                [3] * 340 + [4],
                [512, 512],
                [256, 256, 256, 256],
            ]
        )

        return [
            _workload(
                "fixed_n_batches",
                "fixed_n_batch",
                fixed_n_types,
                weight=0.45,
                description="Many exact N_1(lambda) values for fixed n.",
            ),
            _workload(
                "named_high_n_families",
                "named_families",
                named_types,
                weight=0.30,
                description="High-n named cold-start families.",
            ),
            _workload(
                "dense_touchard_stress",
                "dense_touchard",
                dense_types,
                weight=0.20,
                description="Dense or repeated cycle types that stress Touchard.",
            ),
        ]

    if profile == "promotion":
        named_types: list[Sequence[int]] = []
        for n in (256, 512, 768, 1024):
            named_types.extend(named_cycle_families(n).values())
        return [
            _workload(
                "fixed_n_batches_promotion",
                "fixed_n_batch",
                [
                    *_sample_cycle_types(30, 2_000),
                    *_sample_cycle_types(40, 1_000),
                    *_sample_cycle_types(50, 1_000),
                ],
                weight=0.50,
                description="Held-out fixed-n batch suite.",
            ),
            _workload(
                "named_high_n_promotion",
                "named_families",
                named_types,
                weight=0.35,
                description="Held-out high-n named families.",
            ),
            _workload(
                "dense_touchard_promotion",
                "dense_touchard",
                [
                    mixed_ladder_cycle_type(768) or [768],
                    mixed_ladder_cycle_type(1024) or [1024],
                    [512, 512],
                    [256, 256, 256, 256],
                    [2] * 512,
                    [3] * 340 + [4],
                ],
                weight=0.15,
                description="Held-out dense stress suite.",
            ),
        ]

    raise ValueError(f"Unknown profile: {profile}")


def _format_cycle_type(cycle_type: Sequence[int]) -> str:
    return "+".join(str(part) for part in cycle_type)


def _int_digest_bytes(value: int) -> bytes:
    """Return a stable integer byte encoding without decimal string conversion."""
    if value == 0:
        return b"+\0"
    sign = b"-" if value < 0 else b"+"
    magnitude = abs(value)
    byte_count = (magnitude.bit_length() + 7) // 8
    return sign + magnitude.to_bytes(byte_count, byteorder="big")


def _result_digest(results: Sequence[tuple[tuple[int, ...], int]]) -> str:
    digest = hashlib.sha256()
    for cycle_type, result in results:
        digest.update(_format_cycle_type(cycle_type).encode())
        digest.update(b":")
        digest.update(_int_digest_bytes(result))
        digest.update(b"\n")
    return f"sha256:{digest.hexdigest()}"


def run_workload(
    workload: Workload,
    *,
    method: MethodName,
    track_memory: bool,
    counter: Callable[[Sequence[int], MethodName], int] = _count_from_cycle_type,
) -> dict[str, Any]:
    """Run one workload from a cold cache and return a JSON-serializable row."""
    gc.collect()
    cache_before = _clear_touchard_cache()
    _clear_counter_cache(counter)

    if track_memory:
        tracemalloc.start()

    started = time.perf_counter()
    results: list[tuple[tuple[int, ...], int]] = []
    status = "ok"
    error = ""
    try:
        for cycle_type in workload.cycle_types:
            results.append((cycle_type, counter(cycle_type, method)))
    except Exception as exc:  # pragma: no cover - exercised by framework runs
        status = "error"
        error = f"{type(exc).__name__}: {exc}"
    seconds = time.perf_counter() - started

    peak_memory_mb = 0.0
    if track_memory:
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_memory_mb = peak_bytes / (1024 * 1024)

    cache_after = _cache_info()
    mod_sum = sum(result % MODULUS_FOR_DIGEST for _, result in results)
    max_bits = max((result.bit_length() for _, result in results), default=0)

    return {
        "workload": workload.name,
        "kind": workload.kind,
        "description": workload.description,
        "method": method,
        "weight": workload.weight,
        "status": status,
        "error": error,
        "count_inputs": len(workload.cycle_types),
        "seconds": seconds,
        "peak_memory_mb": peak_memory_mb,
        "result_digest": _result_digest(results),
        "result_mod_sum_1000000007": mod_sum % MODULUS_FOR_DIGEST,
        "result_max_bits": max_bits,
        "cache_before": cache_before,
        "cache_after": cache_after,
    }


def run_profile(
    profile: ProfileName,
    *,
    method: MethodName,
    track_memory: bool,
) -> dict[str, Any]:
    """Run all workloads for a profile."""
    workloads = build_workloads(profile)
    rows = [
        run_workload(workload, method=method, track_memory=track_memory)
        for workload in workloads
    ]
    return {
        "metadata": {
            "profile": profile,
            "method": method,
            "track_memory": track_memory,
            "pythonpath": os.environ.get("PYTHONPATH", ""),
        },
        "workloads": rows,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark cold-start exact N_1(lambda) cycle-type batches."
    )
    parser.add_argument(
        "--profile",
        choices=["smoke", "quick", "promotion"],
        default="smoke",
        help="Workload profile to run.",
    )
    parser.add_argument(
        "--method",
        choices=["auto", "touchard", "rook", "rook_ntt"],
        default="auto",
        help="Counting method to benchmark.",
    )
    parser.add_argument(
        "--track-memory",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Track peak memory with tracemalloc.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. If omitted, JSON is printed to stdout.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_profile(
        args.profile,
        method=args.method,
        track_memory=args.track_memory,
    )
    has_error = any(row["status"] != "ok" for row in result["workloads"])
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(payload)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{payload}\n")
    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
