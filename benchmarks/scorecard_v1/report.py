"""Print the full Markdown scorecard for a completed v1 comparison."""

import argparse
import hashlib
import json
from pathlib import Path

FIXTURES = Path(__file__).with_name("fixtures.json")
RUNNER = Path(__file__).with_name("scorecard.py")


def read_report(path, protocol):
    data = json.loads(path.read_text())
    if data["version"] != 1 or data["protocol"] != protocol:
        raise ValueError(f"{path} must be a v1 {protocol} report")
    for field, source in (("runner_sha256", RUNNER), ("fixtures_sha256", FIXTURES)):
        if (
            data["metadata"].get(field)
            != hashlib.sha256(source.read_bytes()).hexdigest()
        ):
            raise ValueError(f"{path} does not match the frozen {source.name}")
    return data


def table(headers, rows):
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        print("| " + " | ".join(row) + " |")
    print()


def comparison(data, fixtures):
    cases = data["cases"]
    expected_ids = [fixture["id"] for fixture in fixtures]
    by_id = {case["id"]: case for case in cases}
    if len(cases) != len(expected_ids) or set(by_id) != set(expected_ids):
        raise ValueError("The comparison must contain all 18 frozen workloads")
    ordered = [by_id[key] for key in expected_ids]
    pairs = 0
    answers = 0
    for fixture, case in zip(fixtures, ordered, strict=True):
        samples = case["samples"]
        if len(samples) != 9 or any(
            set(pair) != {"base", "candidate"} for pair in samples
        ):
            raise ValueError(f"Incomplete paired samples for {case['id']}")
        pairs += len(samples)
        counts = len(fixture["expected"]) if fixture["op"] == "cycles" else 1
        calls = 2 if fixture["mode"] == "warm" else 1
        answers += len(samples) * 2 * counts * calls

    print("# Performance scorecard v1\n")
    print(
        f"Baseline `{data['base']['commit'][:12]}` → candidate `{data['candidate']['commit'][:12]}`.\n"
    )
    metadata = data["metadata"]
    print(
        f"{metadata['cpu']} · {metadata['platform']} · Python {metadata['python'].split()[0]}\n"
    )
    print(
        f"{len(ordered)} workloads, {pairs} paired samples and {answers:,} exact "
        "integer answers checked, including batch members and warm-ups. "
        f"{sum(c['time_alert'] for c in ordered)} time alerts and "
        f"{sum(c['memory_alert'] for c in ordered)} memory alerts.\n"
    )
    print("## Families\n")
    print("Time ratios divide candidate time by baseline time. Below 1 is faster.\n")
    family_rows = []
    for name in dict.fromkeys(c["family"] for c in ordered):
        info = data["families"][name]
        family_rows.append(
            [
                name,
                f"{info['geometric_mean_candidate_over_base']:.5g}",
                info["worst_case"],
                f"{info['worst_candidate_over_base']:.5g}",
            ]
        )
    table(
        ["Family", "Geometric mean time ratio", "Worst workload", "Worst time ratio"],
        family_rows,
    )
    print("## Workloads\n")
    rows = []
    for case in ordered:
        alerts = [
            label
            for key, label in (("time_alert", "Time"), ("memory_alert", "RSS"))
            if case[key]
        ]
        rows.append(
            [
                case["id"],
                case["mode"],
                f"{case['base_ms']:.4g} → {case['candidate_ms']:.4g}",
                f"{case['candidate_over_base']:.5g}",
                f"{case['base_peak_rss_mib']:.2f} → {case['candidate_peak_rss_mib']:.2f}",
                ", ".join(alerts) or "—",
            ]
        )
    table(
        [
            "Workload",
            "Mode",
            "Median ms, base → candidate",
            "Paired time ratio",
            "Peak RSS MiB, base → candidate",
            "Alerts",
        ],
        rows,
    )
    print("## Batch throughput\n")
    table(
        ["Workload", "Baseline counts/s", "Candidate counts/s"],
        (
            [case["id"], f"{rate['base']:,.0f}", f"{rate['candidate']:,.0f}"]
            for case in ordered
            if (rate := case["counts_per_second"]) is not None
        ),
    )


def describe_rung(rung):
    if rung["status"] == "worker timeout":
        return f"{rung['width']} columns, 8 s worker timeout"
    return f"{rung['width']} columns, {rung['median_ms']:.4g} ms, {rung['max_peak_rss_mib']:.2f} MiB"


def capacity_row(side, path, comparison_report):
    label = {"base": "Baseline", "candidate": "Candidate"}[side]
    if path is None:
        return [label, "—", "No report supplied", "—"]
    report = read_report(path, "capacity")
    if report["revision"] != comparison_report[side]:
        raise ValueError(
            f"{path} does not match the {side} revision and checkout status"
        )
    for field in ("platform", "cpu", "python", "hash_seed"):
        if report["metadata"][field] != comparison_report["metadata"][field]:
            raise ValueError(
                f"{path} has different {field} metadata from the comparison"
            )
    passed = [rung for rung in report["rungs"] if rung["status"] == "pass"]
    miss = next((rung for rung in report["rungs"] if rung["status"] != "pass"), None)
    return [
        label,
        report["revision"]["commit"][:12],
        describe_rung(passed[-1]) if passed else "No passing width recorded",
        describe_rung(miss) if miss else "No miss among measured widths",
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("comparison", type=Path)
    parser.add_argument("--base-capacity", type=Path)
    parser.add_argument("--candidate-capacity", type=Path)
    args = parser.parse_args()
    fixtures = [
        c
        for c in json.loads(FIXTURES.read_bytes())["cases"]
        if c["family"] != "Capacity"
    ]
    try:
        data = read_report(args.comparison, "compare")
        capacities = [
            capacity_row("base", args.base_capacity, data),
            capacity_row("candidate", args.candidate_capacity, data),
        ]
    except ValueError as exc:
        parser.error(str(exc))
    comparison(data, fixtures)
    print("## Labeled four-row capacity\n")
    print("Budgets are a one-second median and 256 MiB peak RSS.\n")
    table(["Revision", "Commit", "Last passing width", "First miss"], capacities)


if __name__ == "__main__":
    main()
