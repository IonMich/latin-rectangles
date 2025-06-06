"""Rook polynomial calculations for Latin rectangles."""

import math

# Memoization cache for rook polynomials to avoid re-computation
_ROOK_POLY_CACHE: dict[int, list[int]] = {}


def get_rook_polynomial_for_cycle(k: int) -> list[int]:
    """
    Calculates the rook polynomial for the forbidden board of a k-cycle.
    The formula for the j-th coefficient is taken from the Menage problem:
    r_j(k) = (2k / (2k - j)) * C(2k - j, j)
    where C is the binomial coefficient "n-choose-k".

    Args:
        k: The cycle length.

    Returns:
        List of coefficients for the rook polynomial.
    """
    if k in _ROOK_POLY_CACHE:
        return _ROOK_POLY_CACHE[k]

    # The rook polynomial has degree k, so it has k+1 coefficients.
    coeffs = [0] * (k + 1)

    # r_0 is always 1
    coeffs[0] = 1

    for j in range(1, k + 1):
        # This handles the case j=2k, where the denominator would be zero.
        # In that situation, the binomial coefficient C(0, 2k) is 0 anyway.
        if (2 * k - j) < j:
            # C(n, k) is 0 if k > n
            coeffs[j] = 0
            continue

        numerator = 2 * k
        denominator = 2 * k - j

        # We use integer division `//` as the result is always an integer.
        # This keeps calculations exact and avoids floating point issues.
        term1 = (numerator * math.comb(denominator, j)) // denominator
        coeffs[j] = term1

    _ROOK_POLY_CACHE[k] = coeffs
    return coeffs


def multiply_polynomials(poly1: list[int], poly2: list[int]) -> list[int]:
    """
    Multiplies two polynomials given as lists of coefficients.

    Args:
        poly1: First polynomial as list of coefficients.
        poly2: Second polynomial as list of coefficients.

    Returns:
        Product polynomial as list of coefficients.
    """
    len1, len2 = len(poly1), len(poly2)
    new_len = len1 + len2 - 1
    result_poly = [0] * new_len
    for i in range(len1):
        for j in range(len2):
            result_poly[i + j] += poly1[i] * poly2[j]
    return result_poly


__all__ = ["get_rook_polynomial_for_cycle", "multiply_polynomials"]
