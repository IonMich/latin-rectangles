# EVOLVE-BLOCK-START
"""OpenEvolve seed program for exact Touchard cycle-type counting.

The evaluator imports this file and calls ``count_cycle_type(cycle_type, method)``.
Keep exact integer arithmetic. The evolved code may add private helpers, caches,
or routing logic, but it must preserve the public function below.
"""

from __future__ import annotations

from collections.abc import Sequence

from latin_rectangles import count_extensions_from_cycle_type as _reference_count
from latin_rectangles.extension_counting import _one_cycle_extension_count

_TOUCHARD_FOLDED_MAX_N = 64


def _subset_counts(cycle_lengths: tuple[int, ...]) -> list[int]:
    """Return subset-sum multiplicities for cycle lengths."""
    n = sum(cycle_lengths)
    subset_counts = [0] * (n + 1)
    subset_counts[0] = 1
    max_subset_sum = 0

    for cycle_length in cycle_lengths:
        for subset_sum in range(max_subset_sum, -1, -1):
            count = subset_counts[subset_sum]
            if count:
                subset_counts[subset_sum + cycle_length] += count
        max_subset_sum += cycle_length

    return subset_counts


def _touchard_count(cycle_lengths: tuple[int, ...]) -> int:
    """Count exact N_1(lambda) via Touchard's formula."""
    n = sum(cycle_lengths)
    if n <= _TOUCHARD_FOLDED_MAX_N:
        subset_counts = _subset_counts(cycle_lengths)
        total = 0
        for subset_sum in range((n + 1) // 2):
            multiplicity = subset_counts[subset_sum]
            if multiplicity:
                total += multiplicity * _one_cycle_extension_count(n - 2 * subset_sum)
        if n % 2 == 0:
            total += subset_counts[n // 2]
        return total

    touchard_total = 0
    for subset_sum, multiplicity in enumerate(_subset_counts(cycle_lengths)):
        if multiplicity:
            touchard_total += multiplicity * _one_cycle_extension_count(
                abs(2 * subset_sum - n)
            )
    if touchard_total % 2 != 0:
        raise AssertionError("Touchard total should be even")
    return touchard_total // 2


def count_cycle_type(cycle_type: Sequence[int], method: str = "touchard") -> int:
    """Return exact N_1(lambda) for a derangement cycle type.

    ``method="touchard"`` is the main evolved path. Other methods may delegate
    to the package reference implementation so OpenEvolve candidates can focus
    on the Touchard cold-start objective first.
    """
    lengths = tuple(sorted(int(part) for part in cycle_type))
    if any(part < 2 for part in lengths):
        raise ValueError("Cycle structure parts must be at least 2")

    if method == "touchard":
        return _touchard_count(lengths)
    if method == "auto":
        if sum(lengths) <= 256:
            return _touchard_count(lengths)
        return _reference_count(list(lengths), method="auto")
    if method in {"rook", "rook_ntt"}:
        return _reference_count(list(lengths), method=method)
    raise ValueError(f"Unknown method: {method}")


def candidate_info() -> dict[str, str]:
    """Optional metadata surfaced in evaluator artifacts."""
    return {"kind": "seed_touchard_subset_dp"}


# EVOLVE-BLOCK-END


if __name__ == "__main__":
    print(count_cycle_type([2, 2, 4], method="touchard"))
