"""Build the v1 fixture file from published totals and independent reference code."""

import argparse
import json
import sys
from itertools import permutations
from math import factorial
from pathlib import Path
from random import Random


def cyclic(n, shifts):
    return [[(col + shift) % n for col in range(n)] for shift in shifts]


def legal_next(rows, candidates):
    blocked = [set(col) for col in zip(*rows)]
    return [
        row for row in candidates if all(x not in col for x, col in zip(row, blocked))
    ]


def two_disjoint_rows(rows):
    # At degree three, any such pair also forces the final row.
    rows_left = legal_next(rows, permutations(range(len(rows[0]))))
    return sum(
        all(a != b for a, b in zip(left, right))
        for left in rows_left
        for right in rows_left
    )


def get_type(p):
    seen = set()
    lengths = []
    for i in range(len(p)):
        if i not in seen:
            j, length = i, 0
            while j not in seen:
                seen.add(j)
                length += 1
                j = p[j]
            lengths.append(length)
    return sorted(lengths)


def sampled_types(n, count, seed):
    rng = Random(seed)
    result = []
    while len(result) < count:
        p = list(range(n))
        rng.shuffle(p)
        if all(i != v for i, v in enumerate(p)):
            result.append(get_type(p))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(args.repo.resolve()))
    from benchmarks.references import cycle_types, permanent_count, recurrence_count

    cases = []

    def add(key, family, op, data, expected, source, mode="cold"):
        cases.append(
            dict(
                id=key,
                family=family,
                op=op,
                data=data,
                expected=expected,
                oracle=source,
                mode=mode,
            )
        )

    for key, types, mode in [
        ("cycles-long", [[256, 256]], "cold"),
        ("cycles-mixed-cold", [[3, 5] + [2] * 125], "cold"),
        ("cycles-mixed-warm", [[3, 5] + [2] * 125], "warm"),
        ("cycles-fixed-width-batch", list(cycle_types(18)), "batch"),
        ("cycles-sampled-batch", sampled_types(32, 32, 233), "batch"),
    ]:
        add(
            key,
            "Cycle types",
            "cycles",
            types,
            [recurrence_count(t) for t in types],
            "Path matching recurrence and packed multiplication in benchmarks.references",
            mode,
        )

    for key, rows in [
        ("next-two-explicit", cyclic(14, [4, 5])),
        ("next-connected", cyclic(12, [0, 1, 4])),
        ("next-four-components", cyclic(12, [0, 4, 8])),
        ("next-forced", cyclic(9, range(1, 9))),
        ("next-full", cyclic(9, range(9))),
    ]:
        add(
            key,
            "Explicit next row",
            "next",
            rows,
            permanent_count(rows),
            "Allowed-board subset permanent",
        )

    rng = Random(2331)
    irregular = [tuple(range(9))]
    candidates = list(permutations(range(9)))
    while len(irregular) < 6:
        irregular.append(rng.choice(legal_next(irregular, candidates)))
    add(
        "next-irregular",
        "Explicit next row",
        "next",
        irregular[:4],
        permanent_count(irregular[:4]),
        "Allowed-board subset permanent",
    )
    ordinary_two = [list(range(7)), [1, 2, 0, 4, 5, 6, 3]]
    for key, rows, count, expected, oracle in [
        (
            "ordered-one-plus-two",
            cyclic(7, [3]),
            2,
            5411750400 // factorial(7),
            "McKay–Wanless labeled 3×7 total divided by 7!",
        ),
        (
            "ordered-last-two",
            cyclic(9, [1, 2, 4, 5, 6, 7, 8]),
            2,
            8,
            "Permutations for the first row, then a forced last row",
        ),
        (
            "ordered-two-plus-two",
            ordinary_two,
            2,
            two_disjoint_rows(ordinary_two),
            "Ordered pairs of disjoint rows from direct permutation enumeration",
        ),
        (
            "ordered-last-three",
            irregular,
            3,
            two_disjoint_rows(irregular),
            "Ordered pairs of disjoint, directly enumerated legal next rows",
        ),
    ]:
        if key == "ordered-last-two" and expected != len(legal_next(rows, candidates)):
            raise ValueError("Final-two fixture disagrees with enumeration")
        add(key, "Ordered extensions", "multi", [rows, count], expected, oracle)

    for k, n, expected in [
        (3, 7, 5411750400),
        (4, 10, 269169718618593283276800),
        (5, 6, 812851200),
    ]:
        add(
            f"total-{k}x{n}",
            "Labeled totals",
            "total",
            [k, n],
            expected,
            "McKay and Wanless, On the number of Latin squares, Table 1, converted to labeled counts",
        )

    # Lin, Liu, Stones and Wang's reduced four-row counts, OEIS A000573.
    reduced = {
        8: 420909504,
        10: 147174521059584,
        12: 188237563987982390784,
        14: 695457005987768649183581184,
        16: 6314083806394358817244705266941952,
        18: 125151207879107507418595651580525408108544,
        20: 4946695754673063706940982976280298177634970763264,
        22: 362953223623178176928985853358776023561076140898585411584,
        24: 46646364890123254950981334346141630039665836277086889810449137664,
        26: 10007844722789723474949164515246755752126297615867851579087218636333514752,
        28: 3442323233447644574634006660322435995886430762756321172680356416748961150464425984,
    }
    for n, value in reduced.items():
        add(
            f"capacity-{n}",
            "Capacity",
            "total",
            [4, n],
            value * factorial(n) * factorial(n - 1) // factorial(n - 4),
            "Lin, Liu, Stones and Wang, A000573, adjusted for labeled rows, columns and symbols",
        )
    args.output.write_text(json.dumps({"version": 1, "cases": cases}, indent=2) + "\n")


if __name__ == "__main__":
    main()
