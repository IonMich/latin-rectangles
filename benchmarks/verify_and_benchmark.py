"""Run independent verification, then cache-controlled exact benchmarks.

Run from the repository root:
    uv run --frozen benchmarks/verify_and_benchmark.py
No timing assertions, network access, or optional dependencies are required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from random import Random
from unittest.mock import patch

# Support both direct script execution and module imports in tests.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks.references import (  # noqa: E402
    packed_convolution,
    permanent_count,
    recurrence_count,
    rows_for_cycles,
)
from latin_rectangles import extension_counting as counting  # noqa: E402
from latin_rectangles import rook_polynomials as rook  # noqa: E402

type Result = int | list[int]
type Operation = Callable[[], Result]
SEED = 20260907
COUNT_METHODS: tuple[counting.CycleStructureMethod, ...] = (
    "rook",
    "rook_ntt",
    "touchard",
    "auto",
)


def clear_caches() -> None:
    """Cold means empty library caches, not a fresh interpreter or cold CPU."""
    counting._one_cycle_extension_count.cache_clear()
    rook._ROOK_POLY_CACHE.clear()
    rook._NTT_PRIME_CACHE.clear()
    rook._NTT_SEARCH_CACHE.clear()


def require_equal(actual: Result, expected: Result) -> None:
    # Do not use assert: correctness gates must survive Python's -O mode.
    if actual != expected:
        raise ValueError("Exact correctness check failed; refusing timing output")


def result_digest(result: Result) -> str:
    return hashlib.sha256(json.dumps(result).encode()).hexdigest()


def measure_case(
    name: str,
    inputs: dict[str, object],
    methods: dict[str, Operation],
    expected: Result,
    oracle: str,
    repeats: int,
) -> list[dict[str, object]]:
    """Rotate method order; reset/warm each sample outside the timed region."""
    rows: list[dict[str, object]] = []
    names = list(methods)
    for cache_mode in ("cold", "warm"):
        samples: dict[str, list[int]] = {name: [] for name in names}
        for repeat in range(repeats):
            offset = repeat % len(names)
            for method in names[offset:] + names[:offset]:
                operation = methods[method]
                clear_caches()
                if cache_mode == "warm":
                    require_equal(operation(), expected)
                start = time.perf_counter_ns()
                actual = operation()
                elapsed = time.perf_counter_ns() - start
                require_equal(actual, expected)
                samples[method].append(elapsed)

        baseline_median = statistics.median(samples[names[0]])
        for method in names:
            operation = methods[method]
            clear_caches()
            if cache_mode == "warm":
                require_equal(operation(), expected)
            # Instrument only an untimed replay; observe real modular convolutions.
            with patch.object(
                rook, "_convolve_mod", wraps=rook._convolve_mod
            ) as modular:
                require_equal(operation(), expected)
            transforms = [
                {"size": call.args[2], "modulus": call.args[3]}
                for call in modular.call_args_list
            ]
            median = statistics.median(samples[method])
            rows.append(
                {
                    "case": name,
                    "inputs": inputs,
                    "oracle": oracle,
                    "method": method,
                    "baseline": names[0],
                    "cache_mode": cache_mode,
                    "samples_ns": samples[method],
                    "median_ns": median,
                    "min_ns": min(samples[method]),
                    "max_ns": max(samples[method]),
                    "baseline_median_over_method_median": baseline_median / median,
                    "modular_convolutions_untimed": transforms,
                    "result_sha256": result_digest(expected),
                    "correctness": "exact equality on every measured call and warmup",
                }
            )
    return rows


def run_benchmarks(repeats: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    # Include overhead-dominated, transform-friendly, skinny, and CRT-budget cases.
    for index, (left_size, right_size, bits) in enumerate(
        [
            (64, 64, 20),
            (129, 129, 20),
            (1024, 1024, 8),
            (512, 512, 80),
            (31, 1024, 20),
            (129, 129, 160),
        ]
    ):
        seed = SEED + index
        rng = Random(seed)
        left, right = [
            [rng.randrange(-(1 << bits), 1 << bits) for _ in range(size)]
            for size in (left_size, right_size)
        ]
        name = f"convolution_{left_size}x{right_size}_{bits}bit"
        print(f"Checking and timing {name}", flush=True)
        rows.extend(
            measure_case(
                name,
                {
                    "lengths": [left_size, right_size],
                    "coefficient_bits": bits,
                    "seed": seed,
                    "input_sha256": result_digest([*left, *right]),
                },
                {
                    "schoolbook": partial(rook.multiply_polynomials, left, right),
                    "ntt_crt": partial(rook.multiply_polynomials_fft, left, right),
                },
                packed_convolution(left, right),
                "signed integer packing (Kronecker substitution)",
                repeats,
            )
        )

    cases = {
        "mixed_n16": [2, 2, 3, 4, 5],
        "transpositions_n64": [2] * 32,
        "odd_n65": [3] + [2] * 31,
        "two_cycles_n256": [128, 128],
        "dense_n258": [3, 5] + [2] * 125,
        "two_cycles_n512": [256, 256],
    }
    for name, lengths in cases.items():
        print(f"Checking and timing {name}", flush=True)
        expected = recurrence_count(lengths)
        oracle = "path-matching recurrence + integer packing + inclusion-exclusion"
        if sum(lengths) <= 16:
            require_equal(permanent_count(rows_for_cycles(lengths)), expected)
            oracle += "; also independent allowed-board permanent"
        methods: dict[str, Operation] = {
            method: partial(
                counting.count_extensions_from_cycle_type, lengths, method=method
            )
            for method in COUNT_METHODS
        }
        rows.extend(
            measure_case(
                name, {"cycle_lengths": lengths}, methods, expected, oracle, repeats
            )
        )
    return rows


def command_output(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def metadata() -> dict[str, object]:
    files = [ROOT / "pyproject.toml", ROOT / "uv.lock"]
    for directory in ("src", "benchmarks", "tests"):
        files.extend(sorted((ROOT / directory).rglob("*.py")))
    cpu = platform.processor()
    memory = None
    if sys.platform == "darwin":
        cpu = (
            command_output(["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"])
            or cpu
        )
        memory = command_output(["/usr/sbin/sysctl", "-n", "hw.memsize"])
    elif sys.platform.startswith("linux"):
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
        memory = str(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": cpu or "unavailable",
        "logical_cpus": os.cpu_count(),
        "physical_memory_bytes": int(memory) if memory else None,
        "uv": command_output(["uv", "--version"]),
        "git_head": command_output(["git", "rev-parse", "HEAD"]),
        "git_status": command_output(["git", "status", "--short"]),
        "source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
        "timer": vars(time.get_clock_info("perf_counter")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument(
        "--output", type=Path, default=Path("benchmark_results/verification.json")
    )
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    print("Running the complete test suite before recording timings", flush=True)
    verification = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-cov"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(verification.stdout, end="", flush=True)
    if verification.returncode:
        print(verification.stderr, file=sys.stderr)
        raise SystemExit(verification.returncode)
    run_metadata = metadata()
    measurements = run_benchmarks(args.repeats)
    report = {
        "schema_version": 1,
        "metadata": run_metadata,
        "protocol": {
            "command": "uv run --frozen benchmarks/verify_and_benchmark.py "
            f"--repeats {args.repeats} --output {args.output}",
            "seed": SEED,
            "repeats": args.repeats,
            "cold": "Clear all four library caches before each sample; import excluded.",
            "warm": "Clear caches then call the same method once before each sample.",
            "timed": "One call; setup, validation, hashing and instrumentation excluded.",
            "ordering": "Rotate method order each repetition, separately per cache mode.",
            "ratio": "Baseline median / method median; above 1 means method was faster.",
            "limitations": "One process/host; no CPU pinning or frequency control; "
            "GC stays enabled; no memory benchmark or complexity proof.",
        },
        "verification": {
            "returncode": verification.returncode,
            "stdout": verification.stdout,
            "stderr": verification.stderr,
        },
        "measurements": measurements,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n")
    temporary.replace(args.output)
    print(f"Wrote {len(measurements)} checked measurements to {args.output}")


if __name__ == "__main__":
    main()
