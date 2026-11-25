"""Run a paired performance comparison or a four-row capacity ladder, on macOS/Linux."""

import argparse
import hashlib
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from time import perf_counter_ns


HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures.json"
ROUNDS = 9
MIB = 1024**2
CAPACITY_NS = 1_000_000_000
CAPACITY_BYTES = 256 * MIB


def load_cases():
    return json.loads(FIXTURES.read_text())["cases"]


def index_rows(rows):
    return [[0, *(symbol + 1 for symbol in row)] for row in rows]


def check_answer(actual, case):
    values = actual if isinstance(actual, list) else [actual]
    if actual != case["expected"] or any(type(value) is not int for value in values):
        raise ValueError(f"Exact integer result mismatch for {case['id']}")


def worker(repo, case_id):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repo.resolve() / "src"))
    import latin_rectangles as lr

    case = next(c for c in load_cases() if c["id"] == case_id)
    data = case["data"]
    if case["op"] == "total":
        run = partial(lr.count_latin_rectangles, *data)
    elif case["op"] == "next":
        run = partial(lr.count_next_row_extensions, index_rows(data))
    elif case["op"] == "multi":
        rows, count = data
        run = partial(lr.count_extensions, index_rows(rows), rows_to_add=count)
    elif case["op"] == "cycles":

        def run():
            return [lr.count_extensions_from_cycle_type(lengths) for lengths in data]
    else:
        raise ValueError(case["op"])

    if case["mode"] == "warm":
        check_answer(run(), case)
    started = perf_counter_ns()
    actual = run()
    elapsed = perf_counter_ns() - started
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    check_answer(actual, case)
    print(
        json.dumps(
            {
                "ns": elapsed,
                "rss_bytes": rss if sys.platform == "darwin" else rss * 1024,
            }
        )
    )


def sample(repo, case, timeout=60):
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "_worker",
            str(repo),
            case["id"],
        ],
        env={**os.environ, "PYTHONHASHSEED": "23", "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode:
        raise RuntimeError(f"{case['id']} failed on {repo}: {result.stderr}")
    return json.loads(result.stdout)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def revision(repo):
    return {
        "commit": git(repo, "rev-parse", "HEAD"),
        "status": git(repo, "status", "--porcelain"),
    }


def metadata():
    if sys.platform == "darwin":
        cpu = subprocess.check_output(
            ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"], text=True
        ).strip()
    else:
        cpu = platform.processor() or platform.machine()
    return {
        "started_utc": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "cpu": cpu,
        "hash_seed": 23,
        "fixtures_sha256": hashlib.sha256(FIXTURES.read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def compare(base, candidate):
    cases = [c for c in load_cases() if c["family"] != "Capacity"]
    report = {
        "version": 1,
        "protocol": "compare",
        "metadata": metadata(),
        "base": revision(base),
        "candidate": revision(candidate),
    }
    rows = {c["id"]: [] for c in cases}
    for j in range(ROUNDS):
        for i in range(len(cases)):
            c = cases[(i + j) % len(cases)]
            pair = {}
            order = [("base", base), ("candidate", candidate)]
            if (cases.index(c) + j) % 2:
                order.reverse()
            for label, repo in order:
                pair[label] = sample(repo, c)
            rows[c["id"]].append(pair)
        print(f"Paired round {j + 1}/{ROUNDS} complete", file=sys.stderr, flush=True)
    summaries = []
    for c in cases:
        pairs = rows[c["id"]]
        old = [p["base"]["ns"] for p in pairs]
        new = [p["candidate"]["ns"] for p in pairs]
        ratios = [b / a for a, b in zip(old, new)]
        deltas = [b - a for a, b in zip(old, new)]
        ratio = statistics.median(ratios)
        old_rss = statistics.median(p["base"]["rss_bytes"] for p in pairs)
        new_rss = statistics.median(p["candidate"]["rss_bytes"] for p in pairs)
        throughput = None
        if c["mode"] == "batch":
            throughput = {
                s: len(c["data"]) * 1e9 / statistics.median(t)
                for s, t in (("base", old), ("candidate", new))
            }
        summaries.append(
            {
                "id": c["id"],
                "family": c["family"],
                "mode": c["mode"],
                "base_ms": statistics.median(old) / 1e6,
                "candidate_ms": statistics.median(new) / 1e6,
                "candidate_over_base": ratio,
                "slower_pairs": sum(d > 0 for d in deltas),
                "time_alert": ratio > 1.1
                and statistics.median(deltas) > 50_000
                and sum(d > 0 for d in deltas) >= 8,
                "base_peak_rss_mib": old_rss / MIB,
                "candidate_peak_rss_mib": new_rss / MIB,
                "memory_alert": new_rss > old_rss * 1.2 and new_rss - old_rss > 8 * MIB,
                "counts_per_second": throughput,
                "samples": pairs,
            }
        )
    report["cases"] = summaries
    families = {}
    for family in dict.fromkeys(s["family"] for s in summaries):
        group = [s for s in summaries if s["family"] == family]
        worst = max(group, key=lambda s: s["candidate_over_base"])
        families[family] = {
            "geometric_mean_candidate_over_base": statistics.geometric_mean(
                s["candidate_over_base"] for s in group
            ),
            "worst_case": worst["id"],
            "worst_candidate_over_base": worst["candidate_over_base"],
        }
    report["families"] = families
    return report


def capacity(repo):
    report = {
        "version": 1,
        "protocol": "capacity",
        "metadata": metadata(),
        "revision": revision(repo),
        "latency_budget_ns": CAPACITY_NS,
        "rss_budget_bytes": CAPACITY_BYTES,
        "last_passing_width": None,
        "rungs": [],
    }
    for c in (c for c in load_cases() if c["family"] == "Capacity"):
        samples = []
        try:
            for _ in range(3):
                samples.append(sample(repo, c, timeout=8))
        except subprocess.TimeoutExpired:
            report["rungs"].append(
                {"width": c["data"][1], "status": "worker timeout", "samples": samples}
            )
            break
        median = statistics.median(x["ns"] for x in samples)
        peak = max(x["rss_bytes"] for x in samples)
        passed = median <= CAPACITY_NS and peak <= CAPACITY_BYTES
        report["rungs"].append(
            {
                "width": c["data"][1],
                "median_ms": median / 1e6,
                "max_peak_rss_mib": peak / MIB,
                "status": "pass" if passed else "over budget",
                "samples": samples,
            }
        )
        if not passed:
            break
        report["last_passing_width"] = c["data"][1]
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    comparison = commands.add_parser("compare")
    comparison.add_argument("base", type=Path)
    comparison.add_argument("candidate", type=Path)
    comparison.add_argument("--output", type=Path, required=True)
    reach = commands.add_parser("capacity")
    reach.add_argument("repo", type=Path)
    reach.add_argument("--output", type=Path, required=True)
    one = commands.add_parser("_worker")
    one.add_argument("repo", type=Path)
    one.add_argument("case")
    args = p.parse_args()
    if args.command == "_worker":
        worker(args.repo, args.case)
        return
    report = (
        compare(args.base, args.candidate)
        if args.command == "compare"
        else capacity(args.repo)
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
