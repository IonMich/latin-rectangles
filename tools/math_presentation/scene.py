"""Build and independently check the shared mathematical presentation scene."""

# Mathematical multiplication signs are intentional in the presentation text.
# ruff: noqa: RUF001

import hashlib
import json
import math
from collections import Counter
from itertools import combinations, permutations, product
from pathlib import Path

source = Path("docs/assets/math-readme/scene.json")
original = json.loads(source.read_text())
pi = original["pi"]
edges = [(i + 1, s) for i, p in enumerate(pi) for s in (i + 1, p)]
selected = [(1, 1), (3, 4)]


def nonattacking(placement: tuple[tuple[int, int], ...]) -> bool:
    return (
        len({c for c, _ in placement})
        == len(placement)
        == len({s for _, s in placement})
    )


coefficients = [sum(nonattacking(p) for p in combinations(edges, j)) for j in range(9)]
assert coefficients == original["rook_coefficients"]
histogram: Counter[int] = Counter()
pair_completions = 0
example = (1, 3, 4, 2, 7, 8, 5, 6)
for row in permutations(range(1, 9)):
    violations = {(i + 1, s) for i, s in enumerate(row) if (i + 1, s) in edges}
    histogram[len(violations)] += 1
    pair_completions += set(selected) <= violations
    if row == example:
        assert violations == set(selected)
assert histogram[0] == 4744
assert pair_completions == math.factorial(6) == 720
for j in range(9):
    assert coefficients[j] * math.factorial(8 - j) == sum(
        math.comb(t, j) * count for t, count in histogram.items() if t >= j
    )
terms = [(-1) ** j * r * math.factorial(8 - j) for j, r in enumerate(coefficients)]
assert sum(terms) == 4744
pairs = list(combinations(edges, 2))
assert len(pairs) == 120
assert sum(a[0] == b[0] for a, b in pairs) == 8
assert sum(a[1] == b[1] for a, b in pairs) == 8

distributions = [(2, 0, 0), (0, 2, 0), (0, 0, 2), (1, 1, 0), (1, 0, 1), (0, 1, 1)]
groups = [{1, 2}, {3, 4}, {5, 6, 7, 8}]
options = []
for distribution in distributions:
    choices = [
        [
            p
            for p in combinations([e for e in edges if e[0] in group], j)
            if nonattacking(p)
        ]
        for group, j in zip(groups, distribution, strict=True)
    ]
    counts = [len(p) for p in choices]
    count = math.prod(counts)
    combined = list(product(*choices))
    assert len(combined) == count
    assert all(nonattacking(tuple(e for p in choice for e in p)) for choice in combined)
    options.append(
        {
            "distribution": distribution,
            "count": count,
            "example": [e for p in combined[0] for e in p],
            "explanation": f"The component choices multiply: {counts[0]} × {counts[1]} × {counts[2]} = {count}.",
        }
    )
assert [o["count"] for o in options] == [2, 2, 20, 16, 32, 32]

data = {
    **original,
    "source_scene_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "selected_bad_assignments": selected,
    "permutation_with_exactly_those_two_violations": example,
    "inclusion_exclusion_terms": terms,
    "factorials": [math.factorial(i) for i in range(9)],
    "component_options": options,
    "violation_histogram": dict(sorted(histogram.items())),
    "pair_completions": pair_completions,
    "all_weighted_terms_checked_against_permutation_enumeration": True,
}
output = Path("docs/evidence/math-presentation/scene.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(data, indent=2) + "\n")
print(
    json.dumps(
        {
            "legal_rows": histogram[0],
            "pair_completions": pair_completions,
            "signed_terms": terms,
        }
    )
)
