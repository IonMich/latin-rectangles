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


def _next_power_of_two(n: int) -> int:
    """Return the next power of two >= n."""
    p = 1
    while p < n:
        p <<= 1
    return p


def multiply_polynomials_fft(poly1: list[int], poly2: list[int]) -> list[int]:
    """
    Multiply two integer polynomials using Cooley-Tukey FFT.

    Args:
        poly1: Coefficients of first polynomial (low to high degree)
        poly2: Coefficients of second polynomial (low to high degree)

    Returns:
        List[int]: Coefficients of the product polynomial.

    Notes:
        - Runs in O(n log n) where n is padded length (power of two ≥ len1+len2-1).
        - Coefficients are rounded to nearest integers to handle floating error.
    """
    n1, n2 = len(poly1), len(poly2)
    if n1 == 0 or n2 == 0:
        return []
    if n1 == 1:
        return [poly1[0] * c for c in poly2]
    if n2 == 1:
        return [poly2[0] * c for c in poly1]

    size = _next_power_of_two(n1 + n2 - 1)

    # Prepare complex arrays
    a = [0j] * size
    b = [0j] * size
    for i, v in enumerate(poly1):
        a[i] = complex(v, 0.0)
    for i, v in enumerate(poly2):
        b[i] = complex(v, 0.0)

    def fft(arr: list[complex], invert: bool) -> None:
        n = len(arr)
        j = 0
        # Bit-reversal permutation
        for i in range(1, n):
            bit = n >> 1
            while j & bit:
                j ^= bit
                bit >>= 1
            j ^= bit
            if i < j:
                arr[i], arr[j] = arr[j], arr[i]

        length = 2
        while length <= n:
            ang = 2 * math.pi / length * (-1 if invert else 1)
            wlen = complex(math.cos(ang), math.sin(ang))
            for i in range(0, n, length):
                w = 1 + 0j
                half = length // 2
                for k in range(i, i + half):
                    u = arr[k]
                    v = arr[k + half] * w
                    arr[k] = u + v
                    arr[k + half] = u - v
                    w *= wlen
            length <<= 1
        if invert:
            inv_n = 1.0 / n
            for i in range(n):
                arr[i] *= inv_n

    # FFT, pointwise multiply, inverse FFT
    fft(a, invert=False)
    fft(b, invert=False)
    for i in range(size):
        a[i] *= b[i]
    fft(a, invert=True)

    # Round to nearest integers and trim
    result_len = n1 + n2 - 1
    result = [round(a[i].real) for i in range(result_len)]
    return result


__all__ = [
    "get_rook_polynomial_for_cycle",
    "multiply_polynomials",
    "multiply_polynomials_fft",
]
