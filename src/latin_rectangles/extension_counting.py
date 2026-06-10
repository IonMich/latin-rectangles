"""Main extension counting algorithm for Latin rectangles."""

import math
from functools import cache

from .derangements import find_cycle_decomposition
from .rook_polynomials import (
    get_rook_polynomial_for_cycle,
    multiply_polynomials,
    multiply_polynomials_fft,
)


def _apply_inclusion_exclusion(rook_poly: list[int], n: int) -> int:
    """Apply the rook-polynomial inclusion-exclusion functional."""
    total_ways = 0
    for k, h_k in enumerate(rook_poly):
        term = ((-1) ** k) * h_k * math.factorial(n - k)
        total_ways += term
    return total_ways


@cache
def _one_cycle_extension_count(cycle_length: int) -> int:
    """Return the formal one-cycle value M_s used by the signed-sum formula.

    For s >= 2 this is the genuine extension count for a single s-cycle. The
    values M_0 = 2 and M_1 = -1 are formal correction terms from the Chebyshev
    product identity, not Latin rectangle extension counts.
    """
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


def _validate_cycle_lengths(cycle_lengths: tuple[int, ...]) -> None:
    if any(cycle_length < 2 for cycle_length in cycle_lengths):
        raise ValueError("Cycle structure parts must be at least 2")


def _count_cycle_structure_extensions_signed(cycle_lengths: list[int]) -> int:
    """Count 2-row extensions from cycle lengths via signed subset sums.

    The repo's rook polynomials store positive matching numbers r_j. The
    research note instead uses signed, reversed cycle polynomials
    q_l(t) = sum_j (-1)^j r_j t^(l-j), then applies F(t^d) = d!. For one
    cycle this gives M_l = F(q_l), exactly the inclusion-exclusion value above.

    Chebyshev multiplication gives
        product_l q_l = 1/2 * sum_epsilon q_|sum epsilon_l l|,
    so the full count is the same average over formal one-cycle values M_s. We
    compute the sign-vector multiplicities with subset-sum DP: choosing the
    positive side of cycles with total a gives signed sum 2a - n.
    """
    lengths = tuple(cycle_lengths)
    _validate_cycle_lengths(lengths)

    n = sum(lengths)
    subset_counts = [0] * (n + 1)
    subset_counts[0] = 1
    max_subset_sum = 0

    for cycle_length in lengths:
        for subset_sum in range(max_subset_sum, -1, -1):
            count = subset_counts[subset_sum]
            if count:
                subset_counts[subset_sum + cycle_length] += count
        max_subset_sum += cycle_length

    signed_total = 0
    for subset_sum, multiplicity in enumerate(subset_counts):
        if multiplicity:
            signed_total += multiplicity * _one_cycle_extension_count(
                abs(2 * subset_sum - n)
            )

    # Complementary subsets are paired by the 1/2 in the Chebyshev identity.
    if signed_total % 2 != 0:
        raise AssertionError("Signed-sum total should be even")
    return signed_total // 2


def count_extensions(permutation: list[int], *, use_fft: bool = False) -> int:
    """
    Calculates the number of ways to extend a 2xn Latin rectangle to a 3xn one.
    This is the most robust and general implementation.

    Args:
        permutation: A list representing the second row, assuming the first row is
                     (1, 2, ..., n). The list should be 1-indexed, so its
                     length is n+1 and permutation[0] can be a dummy value.
                     It must be a derangement.
        use_fft: Use exact NTT/CRT convolution for large polynomial products.

    Returns:
        The integer number of possible third rows.

    Raises:
        ValueError: If the input permutation is not a derangement.
    """
    n = len(permutation) - 1
    if any(i == val for i, val in enumerate(permutation[1:], 1)):
        raise ValueError("Input permutation must be a derangement (p(i) != i).")

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


__all__ = ["count_extensions"]
