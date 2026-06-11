"""Main extension counting algorithm for Latin rectangles."""

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from .derangements import create_cycle_structure, find_cycle_decomposition
from .general_extensions import count_extensions
from .rook_polynomials import (
    get_rook_polynomial_for_cycle,
    multiply_polynomials,
    multiply_polynomials_fft,
)

CycleStructureMethod = Literal["auto", "touchard", "rook", "rook_ntt"]
_TOUCHARD_FOLDED_MAX_N = 64


@dataclass(frozen=True)
class _OneCycleCacheInfo:
    """Cache statistics matching the small subset of functools.cache_info used."""

    hits: int
    misses: int
    maxsize: None
    currsize: int


class _OneCycleExtensionCounter:
    """Callable cache for the formal one-cycle Touchard values M_s."""

    def __init__(self) -> None:
        self._cache: dict[int, int] = {}
        self._hits = 0
        self._misses = 0

    def __call__(self, cycle_length: int) -> int:
        if cycle_length in self._cache:
            self._hits += 1
            return self._cache[cycle_length]

        self._misses += 1
        value = self._compute(cycle_length)
        self._cache[cycle_length] = value
        return value

    def _compute(self, cycle_length: int) -> int:
        if cycle_length < 0:
            raise ValueError("Cycle length must be non-negative")
        if cycle_length == 0:
            return 2
        if cycle_length == 1:
            return -1
        return _apply_inclusion_exclusion(
            get_rook_polynomial_for_cycle(cycle_length),
            cycle_length,
        )

    def cache_clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def cache_info(self) -> _OneCycleCacheInfo:
        return _OneCycleCacheInfo(
            hits=self._hits,
            misses=self._misses,
            maxsize=None,
            currsize=len(self._cache),
        )

    def missing_values(self, values: Iterable[int]) -> set[int]:
        return {value for value in values if value not in self._cache}


def _apply_inclusion_exclusion(rook_poly: list[int], n: int) -> int:
    """Apply the rook-polynomial inclusion-exclusion functional."""
    total_ways = 0
    for k, h_k in enumerate(rook_poly):
        term = ((-1) ** k) * h_k * math.factorial(n - k)
        total_ways += term
    return total_ways


_one_cycle_extension_count = _OneCycleExtensionCounter()


def _validate_cycle_lengths(cycle_lengths: tuple[int, ...]) -> None:
    if any(cycle_length < 2 for cycle_length in cycle_lengths):
        raise ValueError("Cycle structure parts must be at least 2")


def _validate_rows_to_add(rows_to_add: int) -> None:
    if rows_to_add < 0:
        raise ValueError("rows_to_add must be non-negative")


def _validate_derangement(permutation: list[int]) -> int:
    n = len(permutation) - 1
    if n < 0 or not permutation or permutation[0] != 0:
        raise ValueError("Input permutation must be 1-indexed with permutation[0] == 0")
    if set(permutation[1:]) != set(range(1, n + 1)):
        raise ValueError("Input permutation must be a valid permutation of 1..n")
    if any(i == val for i, val in enumerate(permutation[1:], 1)):
        raise ValueError("Input permutation must be a derangement (p(i) != i).")
    return n


def _identity_row(n: int) -> list[int]:
    return [0, *range(1, n + 1)]


def _touchard_subset_counts(cycle_lengths: tuple[int, ...]) -> list[int]:
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


def _touchard_m_values(cycle_lengths: tuple[int, ...]) -> set[int]:
    """Return the formal one-cycle indices M_s needed by Touchard's formula."""
    n = sum(cycle_lengths)
    return {
        abs(2 * subset_sum - n)
        for subset_sum, multiplicity in enumerate(
            _touchard_subset_counts(cycle_lengths)
        )
        if multiplicity
    }


def _count_extensions_from_cycle_type_touchard(cycle_lengths: list[int]) -> int:
    """Count 2-row extensions from cycle lengths via Touchard's formula.

    The repo's rook polynomials store positive matching numbers r_j. The
    research note instead uses signed, reversed cycle polynomials
    q_l(t) = sum_j (-1)^j r_j t^(l-j), then applies F(t^d) = d!. For one
    cycle this gives M_l = F(q_l), exactly the inclusion-exclusion value above.

    This is Touchard's 1934 discordant-permutation formula in the h=0
    Latin-rectangle specialization. Chebyshev multiplication rederives
        product_l q_l = 1/2 * sum_epsilon q_|sum epsilon_l l|,
    so the full count is the same average over formal one-cycle values M_s. We
    compute the sign-vector multiplicities with subset-sum DP: choosing the
    positive side of cycles with total a gives signed sum 2a - n.
    """
    lengths = tuple(cycle_lengths)
    _validate_cycle_lengths(lengths)

    n = sum(lengths)
    if n <= _TOUCHARD_FOLDED_MAX_N:
        subset_counts = _touchard_subset_counts(lengths)
        total = 0

        # Complementary subsets with sums a and n-a contribute the same M_s and
        # are paired by the 1/2 in Touchard's all-sign formula.
        for subset_sum in range((n + 1) // 2):
            multiplicity = subset_counts[subset_sum]
            if multiplicity:
                total += multiplicity * _one_cycle_extension_count(n - 2 * subset_sum)

        # The central sum, when present, has M_0 = 2 and is also divided by 2.
        if n % 2 == 0:
            total += subset_counts[n // 2]

        return total

    touchard_total = 0
    for subset_sum, multiplicity in enumerate(_touchard_subset_counts(lengths)):
        if multiplicity:
            touchard_total += multiplicity * _one_cycle_extension_count(
                abs(2 * subset_sum - n)
            )

    # Complementary subsets are paired by the 1/2 in Touchard's all-sign form.
    if touchard_total % 2 != 0:
        raise AssertionError("Touchard total should be even")
    return touchard_total // 2


def _count_extensions_from_cycle_type_rook(
    cycle_lengths: list[int], *, use_fft: bool = False
) -> int:
    """Count 2-row extensions from cycle lengths via rook polynomial products."""
    lengths = tuple(cycle_lengths)
    _validate_cycle_lengths(lengths)

    total_rook_poly = [1]
    for cycle_length in lengths:
        cycle_rook_poly = get_rook_polynomial_for_cycle(cycle_length)
        if use_fft:
            total_rook_poly = multiply_polynomials_fft(total_rook_poly, cycle_rook_poly)
        else:
            total_rook_poly = multiply_polynomials(total_rook_poly, cycle_rook_poly)
    return _apply_inclusion_exclusion(total_rook_poly, sum(lengths))


def _choose_cycle_structure_method(
    cycle_lengths: tuple[int, ...],
) -> Literal["touchard", "rook"]:
    """Choose the default exact method for a cycle-structure request.

    Touchard is excellent when its required one-cycle values are already
    cached, or when only a few new values are needed. Cold dense high-n cycle
    types can ask for hundreds or thousands of new M_s values, and the
    schoolbook rook product is then a better default.
    """
    m_values = _touchard_m_values(cycle_lengths)
    missing_values = _one_cycle_extension_count.missing_values(m_values)
    if not missing_values:
        return "touchard"
    if len(missing_values) <= 8:
        return "touchard"
    if sum(cycle_lengths) <= 256:
        return "touchard"
    return "rook"


def _count_extensions_from_cycle_type_auto(cycle_lengths: list[int]) -> int:
    """Count cycle-structure extensions using the routed default method."""
    lengths = tuple(cycle_lengths)
    _validate_cycle_lengths(lengths)
    if _choose_cycle_structure_method(lengths) == "touchard":
        return _count_extensions_from_cycle_type_touchard(cycle_lengths)
    return _count_extensions_from_cycle_type_rook(cycle_lengths, use_fft=False)


def count_extensions_from_cycle_type(
    cycle_lengths: list[int],
    *,
    rows_to_add: int = 1,
    method: CycleStructureMethod = "auto",
) -> int:
    """Count ordered extensions from a normalized 2 x n start by cycle type."""
    _validate_rows_to_add(rows_to_add)
    lengths = tuple(cycle_lengths)
    _validate_cycle_lengths(lengths)

    if rows_to_add == 0:
        return 1
    if rows_to_add > 1:
        if method != "auto":
            raise ValueError("method is only supported when rows_to_add == 1")
        return count_extensions_from_derangement(
            create_cycle_structure(cycle_lengths),
            rows_to_add=rows_to_add,
        )

    if method == "auto":
        return _count_extensions_from_cycle_type_auto(cycle_lengths)
    if method == "touchard":
        return _count_extensions_from_cycle_type_touchard(cycle_lengths)
    if method == "rook":
        return _count_extensions_from_cycle_type_rook(cycle_lengths, use_fft=False)
    if method == "rook_ntt":
        return _count_extensions_from_cycle_type_rook(cycle_lengths, use_fft=True)
    raise ValueError(f"Unknown cycle-structure method: {method}")


def count_extensions_from_derangement(
    permutation: list[int], *, rows_to_add: int = 1, use_fft: bool = False
) -> int:
    """
    Count ordered extensions from a normalized 2 x n Latin rectangle.

    Args:
        permutation: A list representing the second row, assuming the first row is
                     (1, 2, ..., n). The list should be 1-indexed, so its
                     length is n+1 and permutation[0] can be a dummy value.
                     It must be a derangement.
        rows_to_add: Number of further rows to add. ``0`` returns ``1``.
        use_fft: Use exact NTT/CRT convolution for one-row subproblems.

    Returns:
        The integer number of ordered extensions by ``rows_to_add`` rows.

    Raises:
        ValueError: If the input permutation is not a derangement.
    """
    _validate_rows_to_add(rows_to_add)
    n = _validate_derangement(permutation)
    if rows_to_add == 0:
        return 1
    if rows_to_add > 1:
        return count_extensions(
            [_identity_row(n), permutation],
            rows_to_add=rows_to_add,
            use_fft=use_fft,
        )

    # 1. Find the cycle decomposition of the permutation
    cycles = find_cycle_decomposition(permutation)

    # 2. Get the total rook polynomial by multiplying the polynomials of the sub-problems
    total_rook_poly = [1]  # Start with the polynomial "1"
    for cycle in cycles:
        k = len(cycle)
        cycle_rook_poly = get_rook_polynomial_for_cycle(k)
        if use_fft:
            total_rook_poly = multiply_polynomials_fft(total_rook_poly, cycle_rook_poly)
        else:
            total_rook_poly = multiply_polynomials(total_rook_poly, cycle_rook_poly)

    # 3. Apply the Principle of Inclusion-Exclusion to get the final count.
    return _apply_inclusion_exclusion(total_rook_poly, n)


__all__ = ["count_extensions_from_cycle_type", "count_extensions_from_derangement"]
