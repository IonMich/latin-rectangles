"""Wide two-row extension counts on macOS/Linux, with cold workers and exact checks.

From the repository root run
    uv run --frozen python -m benchmarks.benchmark_wide_two_rows --output wide.json

Pass --repo /path/to/another/checkout to measure another revision using these
same fixtures. The 8-second worker deadline includes interpreter startup.
"""

import argparse
import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
from functools import partial
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter_ns

from benchmarks.references import rows_for_cycles
from tools.autoresearch.benchmark_touchard_cold_start import named_cycle_families

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ("two_equal_cycles", "mostly_16_cycles", "mixed_ladder")
FORMS = ("explicit_rows", "cycle_lengths")
SEEDS = (423, 301, 781)
TIME_MS, MEMORY_MIB, DEADLINE_S = 1_000, 256, 8


def circular_menage_terms(width):
    """Formal M_0, ..., M_n from the four-term circular ménage recurrence."""
    a, b, c, d = 2, -1, 0, 1
    yield from (a, b, c, d)[: width + 1]
    for i in range(4, width + 1):
        a, b, c, d = b, c, d, i * d + 2 * c - (i - 4) * b - a
        yield d


def reference_count(parts):
    """Fold complementary subset sums, independently using descending subset DP."""
    width = sum(parts)
    half = width // 2
    weights = [1] + [0] * half
    reachable = 0
    for length in parts:
        for j in range(min(reachable, half - length), -1, -1):
            weights[j + length] += weights[j]
        reachable += length
    answer = 0
    for i, value in enumerate(circular_menage_terms(width)):
        if (width - i) % 2 == 0:
            weight = weights[(width - i) // 2]
            # At zero the central coefficient has half weight and formal M_0=2.
            answer += weight if i == 0 else weight * value
    return answer


def digest(value):
    return hashlib.sha256(
        value.to_bytes((value.bit_length() + 7) // 8, "big")
    ).hexdigest()


def shuffled_rows(parts, seed):
    first, second = rows_for_cycles(parts)
    labels = list(range(1, len(first) + 1))
    columns = first.copy()
    rng = Random(seed)
    rng.shuffle(labels)
    rng.shuffle(columns)
    return [[0, *(labels[row[j]] for j in columns)] for row in (first, second)]


def worker(repo, family, width, form, seed):
    sys.path.insert(0, str(repo / "src"))
    from latin_rectangles import (
        count_extensions_from_cycle_type,
        count_next_row_extensions,
    )

    parts = named_cycle_families(width)[family]
    if form == "explicit_rows":
        count = partial(count_next_row_extensions, shuffled_rows(parts, seed))
    else:
        count = partial(count_extensions_from_cycle_type, parts)
    start = perf_counter_ns()
    try:
        value = count()
    except (MemoryError, RecursionError) as exc:
        return {"status": type(exc).__name__}
    elapsed_ms = (perf_counter_ns() - start) / 1e6
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "status": "ok",
        "ms": elapsed_ms,
        "peak_mib": peak / (2**20 if sys.platform == "darwin" else 1024),
        "sha256": digest(value),
    }


def measure(repo, family, width, form, expected, previous_ms):
    samples = []
    for seed in SEEDS:
        cmd = [
            sys.executable,
            "-m",
            "benchmarks.benchmark_wide_two_rows",
            "--repo",
            str(repo),
            "--worker",
            family,
            str(width),
            form,
            str(seed),
        ]
        try:
            output = subprocess.check_output(
                cmd,
                cwd=ROOT,
                timeout=DEADLINE_S,
                text=True,
                env={**os.environ, "PYTHONHASHSEED": "23"},
            )
            sample = json.loads(output)
        except subprocess.TimeoutExpired:
            sample = {"status": "timeout"}
        samples.append(sample)
        if sample["status"] != "ok":
            return {"status": sample["status"], "samples": samples}
        if sample["sha256"] != expected:
            raise ValueError(
                f"Incorrect exact count for {form}, {family}, width {width}, seed {seed}"
            )
    ms = median(sample["ms"] for sample in samples)
    peak = max(sample["peak_mib"] for sample in samples)
    return {
        "status": "pass" if ms <= TIME_MS and peak <= MEMORY_MIB else "over budget",
        "median_ms": ms,
        "peak_mib": peak,
        "doubling_ratio": ms / previous_ms if previous_ms else None,
        "samples": samples,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--min-width", type=int, default=1024)
    parser.add_argument("--max-width", type=int, default=65536)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", nargs=4, help=argparse.SUPPRESS)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.worker:
        family, width, form, seed = args.worker
        print(json.dumps(worker(repo, family, int(width), form, int(seed))))
        return
    if (
        args.output is None
        or not (4 <= args.min_width <= args.max_width)
        or args.min_width % 2
    ):
        parser.error(
            "supply --output, an even --min-width >= 4, and --max-width >= --min-width"
        )
    if not (repo / "src" / "latin_rectangles" / "__init__.py").is_file():
        parser.error("--repo must identify a latin-rectangles checkout")
    report = {
        "python": sys.version,
        "platform": platform.platform(),
        "revision": subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip(),
        "time_budget_ms": TIME_MS,
        "memory_budget_mib": MEMORY_MIB,
        "worker_deadline_s": DEADLINE_S,
        "seeds": SEEDS,
        "width_range": [args.min_width, args.max_width],
        "families": {},
    }
    for family in FAMILIES:
        histories = {form: [] for form in FORMS}
        report["families"][family] = histories
        width = args.min_width
        while width <= args.max_width:
            active = [
                form
                for form, rows in histories.items()
                if not rows or rows[-1]["status"] == "pass"
            ]
            if not active:
                break
            expected = digest(reference_count(named_cycle_families(width)[family]))
            for form in active:
                rows = histories[form]
                result = measure(
                    repo,
                    family,
                    width,
                    form,
                    expected,
                    rows[-1]["median_ms"] if rows else None,
                )
                rows.append({"width": width, "expected_sha256": expected, **result})
                print(f"{family} {form} {width}: {result['status']}", flush=True)
            width *= 2
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
