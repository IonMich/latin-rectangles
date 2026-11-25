"""Cold first-valid-row benchmark on macOS/Linux, separate from exact counting.

    uv run --frozen python -m benchmarks.benchmark_find_next_row --output find.json

Use --method legacy --repo OLD_CHECKOUT to measure the previous permutation
search on the same fixtures. The worker deadline includes startup, fixture
construction and verification. Reported latency covers the finder call only.
"""

import argparse
import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
from array import array
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter_ns

from benchmarks.benchmark_wide_two_rows import (
    DEADLINE_S,
    MEMORY_MIB,
    ROOT,
    SEEDS,
    TIME_MS,
)

MAX_WIDTH = {
    "two_irregular": 65536,
    "half_full": 2048,
    "two_remaining": 2048,
    "forced": 2048,
}
# An explicit prefix stores one pointer per cell. Share the symbol objects and
# cap the cells even when a larger custom ceiling is requested.
MAX_CELLS = 4 * 1024**2


def height(family, width):
    return {
        "two_irregular": 2,
        "half_full": width // 2,
        "two_remaining": width - 2,
        "forced": width - 1,
    }[family]


def fixture(family, width, seed):
    rng = Random(seed)
    symbols = list(range(1, width + 1))
    rng.shuffle(symbols)
    columns = list(range(width))
    rng.shuffle(columns)
    if family == "two_irregular":
        permutation = list(range(width))
        while True:
            rng.shuffle(permutation)
            if all(i != j for i, j in enumerate(permutation)):
                break
        return [
            [0, *(symbols[j] for j in columns)],
            [0, *(symbols[permutation[j]] for j in columns)],
        ]
    # In an even cyclic square, row shifts r,r+n/2 and columns j,j+n/2
    # form a 2-by-2 intercalate. Swapping its symbols preserves the square.
    # These blocks are disjoint: vary the trades before taking a random
    # row subset. Odd widths use the relabelled cyclic square directly.
    shifts = rng.sample(range(width), height(family, width))
    half = width // 2
    trades = {}
    if width % 2 == 0:
        for r in sorted({shift % half for shift in shifts}):
            trades[r] = rng.randbytes((half + 7) // 8)
    rows = []
    for shift in shifts:
        flips = trades.get(shift % half)
        row = [0]
        for column in columns:
            value = (shift + column) % width
            j = column % half
            if flips and flips[j // 8] & (1 << (j % 8)):
                value = (value + half) % width
            row.append(symbols[value])
        rows.append(row)
    return rows


def fingerprint(rows):
    digest = hashlib.sha256()
    for row in rows:
        digest.update(len(row).to_bytes(8, "big"))
        digest.update(array("I", row))
    return digest.digest()


def valid_witness(rows, witness):
    width = len(rows[0]) - 1
    return (
        isinstance(witness, list)
        and len(witness) == width + 1
        and witness[0] == 0
        and set(witness[1:]) == set(range(1, width + 1))
        and all(row[j] != witness[j] for row in rows for j in range(1, width + 1))
    )


def worker(repo, method, family, width, seed):
    sys.path.insert(0, str(repo / "src"))
    if method == "public":
        from latin_rectangles import find_next_row as find
    else:
        from latin_rectangles.general_extensions import _iter_valid_next_rows

        def find(rows):
            return next(_iter_valid_next_rows(rows), None)

    if width * height(family, width) > MAX_CELLS:
        return {"status": "fixture cell limit"}
    rows = fixture(family, width, seed)
    snapshot = fingerprint(rows)
    start = perf_counter_ns()
    try:
        witness = find(rows)
    except (MemoryError, RecursionError) as exc:
        return {"status": type(exc).__name__}
    ms = (perf_counter_ns() - start) / 1e6
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    mib = peak / (1024**2 if sys.platform == "darwin" else 1024)
    if fingerprint(rows) != snapshot:
        return {"status": "mutated input"}
    if not valid_witness(rows, witness):
        return {"status": "invalid witness"}
    return {"status": "ok", "ms": ms, "peak_mib": mib}


def sample(repo, method, family, width, seed):
    cmd = [
        sys.executable,
        "-m",
        "benchmarks.benchmark_find_next_row",
        "--repo",
        str(repo),
        "--method",
        method,
        "--worker",
        family,
        str(width),
        str(seed),
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            timeout=DEADLINE_S,
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONHASHSEED": "23"},
        )
    except subprocess.TimeoutExpired:
        return {"status": "worker timeout"}
    except subprocess.CalledProcessError as exc:
        return {
            "status": "worker error",
            "returncode": exc.returncode,
            "detail": exc.stderr.strip()[-800:],
        }
    return json.loads(completed.stdout)


def ladder(repo, method, family, start, ceiling):
    rungs = []
    previous = None
    width = start
    stop = "ceiling reached"
    while width <= ceiling:
        row_count = height(family, width)
        if width * row_count > MAX_CELLS:
            stop = "fixture cell limit"
            break
        samples = []
        for seed in SEEDS:
            trial = sample(repo, method, family, width, seed)
            samples.append({"seed": seed, **trial})
            if trial["status"] != "ok":
                break
        rung = {"width": width, "height": row_count, "samples": samples}
        if trial["status"] == "ok":
            ms = median(t["ms"] for t in samples)
            mib = max(t["peak_mib"] for t in samples)
            status = "pass" if ms <= TIME_MS and mib <= MEMORY_MIB else "over budget"
            rung.update(
                median_ms=ms,
                peak_mib=mib,
                doubling_ratio=ms / previous if previous else None,
            )
            previous = ms
        else:
            status = trial["status"]
        rungs.append({**rung, "status": status})
        print(
            f"{method} {family} {row_count}x{width} {status}",
            file=sys.stderr,
            flush=True,
        )
        if status != "pass":
            stop = status
            break
        width *= 2
    return {
        "requested_ceiling": ceiling,
        "last_passing_width": max(
            (r["width"] for r in rungs if r["status"] == "pass"), default=None
        ),
        "stop": stop,
        "right_censored": stop in ("ceiling reached", "fixture cell limit"),
        "first_untested_width": width
        if stop in ("ceiling reached", "fixture cell limit")
        else None,
        "rungs": rungs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--method", choices=("public", "legacy"), default="public")
    parser.add_argument(
        "--families", nargs="+", choices=MAX_WIDTH, default=list(MAX_WIDTH)
    )
    parser.add_argument("--min-width", type=int, default=8)
    parser.add_argument("--max-width", type=int, help="override the per-family ceiling")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", nargs=3, help=argparse.SUPPRESS)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.worker:
        family, width, seed = args.worker
        print(json.dumps(worker(repo, args.method, family, int(width), int(seed))))
        return
    if not (repo / "src/latin_rectangles/__init__.py").is_file():
        parser.error("--repo must identify a latin-rectangles checkout")
    if args.output is None or args.min_width < 4:
        parser.error("supply --output and --min-width >= 4")
    ceilings = {
        f: args.max_width if args.max_width is not None else MAX_WIDTH[f]
        for f in args.families
    }
    if min(ceilings.values()) < args.min_width:
        parser.error("each ceiling must be at least --min-width")
    revision = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True
    )
    report = {
        "method": args.method,
        "revision": revision.stdout.strip() or None,
        "platform": platform.platform(),
        "python": sys.version,
        "seeds": SEEDS,
        "min_width": args.min_width,
        "time_budget_ms": TIME_MS,
        "peak_budget_mib": MEMORY_MIB,
        "worker_deadline_s": DEADLINE_S,
        "fixture_cell_limit": MAX_CELLS,
        "families": {},
    }
    for family, ceiling in ceilings.items():
        report["families"][family] = ladder(
            repo, args.method, family, args.min_width, ceiling
        )
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    if any(
        r["stop"] in ("invalid witness", "mutated input", "worker error")
        for r in report["families"].values()
    ):
        raise SystemExit(
            "Benchmark correctness or worker failure. See the JSON report."
        )


if __name__ == "__main__":
    main()
