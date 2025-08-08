"""Main extension counting algorithm for Latin rectangles."""

import math

from .derangements import find_cycle_decomposition
from .rook_polynomials import (
    get_rook_polynomial_for_cycle,
    multiply_polynomials,
    multiply_polynomials_fft,
)


def count_extensions(permutation: list[int], *, use_fft: bool = False) -> int:
    """
    Calculates the number of ways to extend a 2xn Latin rectangle to a 3xn one.
    This is the most robust and general implementation.

    Args:
        permutation: A list representing the second row, assuming the first row is
                     (1, 2, ..., n). The list should be 1-indexed, so its
                     length is n+1 and permutation[0] can be a dummy value.
                     It must be a derangement.

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
    total_ways = 0
    for k, h_k in enumerate(total_rook_poly):
        term = ((-1) ** k) * h_k * math.factorial(n - k)
        total_ways += term

    return total_ways


__all__ = ["count_extensions"]
