"""Rook polynomial calculations for Latin rectangles."""

import math

# Memoization cache for rook polynomials to avoid re-computation
_ROOK_POLY_CACHE: dict[int, list[int]] = {}
_NTT_PRIME_CACHE: dict[int, list[tuple[int, int]]] = {}
_NTT_SEARCH_CACHE: dict[int, int] = {}

_NTT_MAX_PRIME = (1 << 31) - 1
_NTT_SCHOOLBOOK_THRESHOLD = 16_384
_NTT_MIN_POLY_LEN = 32


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


def _is_prime(n: int) -> bool:
    """Deterministic Miller-Rabin primality test for the 32-bit range used here."""
    if n < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False

    d = n - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2

    for a in (2, 3, 5, 7, 11, 13, 17):
        if a >= n:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _find_power_of_two_root(modulus: int, size: int) -> int:
    """Find an element of exact order ``size`` modulo ``modulus``."""
    exponent = (modulus - 1) // size
    base = 2
    while True:
        root = pow(base, exponent, modulus)
        if root != 1 and pow(root, size >> 1, modulus) != 1:
            return root
        base += 1


def _next_ntt_prime(size: int) -> tuple[int, int]:
    """Return the next cached/generated NTT prime and size-th root."""
    cached = _NTT_PRIME_CACHE.setdefault(size, [])
    search_k = _NTT_SEARCH_CACHE.get(size, (_NTT_MAX_PRIME - 1) // size)

    while search_k > 0:
        candidate = search_k * size + 1
        search_k -= 1
        if _is_prime(candidate):
            root = _find_power_of_two_root(candidate, size)
            cached.append((candidate, root))
            _NTT_SEARCH_CACHE[size] = search_k
            return candidate, root

    raise RuntimeError(f"Could not find enough NTT primes for transform size {size}")


def _ntt(values: list[int], root: int, modulus: int, *, invert: bool) -> None:
    """In-place iterative NTT. ``root`` has order len(values)."""
    n = len(values)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            values[i], values[j] = values[j], values[i]

    if invert:
        root = pow(root, -1, modulus)

    length = 2
    while length <= n:
        wlen = pow(root, n // length, modulus)
        for i in range(0, n, length):
            w = 1
            half = length >> 1
            for j in range(i, i + half):
                u = values[j]
                v = values[j + half] * w % modulus
                values[j] = (u + v) % modulus
                values[j + half] = (u - v) % modulus
                w = w * wlen % modulus
        length <<= 1

    if invert:
        inv_n = pow(n, -1, modulus)
        for i, value in enumerate(values):
            values[i] = value * inv_n % modulus


def _convolve_mod(
    poly1: list[int], poly2: list[int], size: int, modulus: int, root: int
) -> list[int]:
    """Convolve two integer polynomials modulo one NTT prime."""
    a = [0] * size
    b = [0] * size
    for i, value in enumerate(poly1):
        a[i] = value % modulus
    for i, value in enumerate(poly2):
        b[i] = value % modulus

    _ntt(a, root, modulus, invert=False)
    _ntt(b, root, modulus, invert=False)
    for i in range(size):
        a[i] = a[i] * b[i] % modulus
    _ntt(a, root, modulus, invert=True)
    return a[: len(poly1) + len(poly2) - 1]


def multiply_polynomials_fft(poly1: list[int], poly2: list[int]) -> list[int]:
    """
    Multiply integer polynomials exactly using NTT primes and CRT.

    Args:
        poly1: Coefficients of first polynomial (low to high degree)
        poly2: Coefficients of second polynomial (low to high degree)

    Returns:
        List[int]: Coefficients of the product polynomial.

    Notes:
        This is an exact transform-based convolution, not a floating-point FFT.
        It uses enough 31-bit NTT primes to reconstruct every coefficient by
        CRT, and falls back to schoolbook multiplication for small or skinny
        products where transform overhead dominates.
    """
    n1, n2 = len(poly1), len(poly2)
    if n1 == 0 or n2 == 0:
        return []
    if n1 == 1:
        return [poly1[0] * c for c in poly2]
    if n2 == 1:
        return [poly2[0] * c for c in poly1]
    if min(n1, n2) < _NTT_MIN_POLY_LEN or n1 * n2 <= _NTT_SCHOOLBOOK_THRESHOLD:
        return multiply_polynomials(poly1, poly2)

    max_abs_1 = max(abs(value) for value in poly1)
    max_abs_2 = max(abs(value) for value in poly2)
    coefficient_bound = min(n1, n2) * max_abs_1 * max_abs_2
    if coefficient_bound == 0:
        return [0] * (n1 + n2 - 1)

    size = _next_power_of_two(n1 + n2 - 1)
    modulus_product = 1
    combined: list[int] | None = None
    prime_index = 0

    while modulus_product <= 2 * coefficient_bound:
        cached = _NTT_PRIME_CACHE.setdefault(size, [])
        if prime_index < len(cached):
            modulus, root = cached[prime_index]
        else:
            modulus, root = _next_ntt_prime(size)

        residues = _convolve_mod(poly1, poly2, size, modulus, root)
        if combined is None:
            combined = residues
            modulus_product = modulus
        else:
            inv_modulus_product = pow(modulus_product % modulus, -1, modulus)
            for i, value in enumerate(combined):
                correction = (residues[i] - value) % modulus
                correction = correction * inv_modulus_product % modulus
                combined[i] = value + modulus_product * correction
            modulus_product *= modulus

        prime_index += 1

    if combined is None:
        return []

    half_modulus = modulus_product // 2
    return [
        value - modulus_product if value > half_modulus else value for value in combined
    ]


__all__ = [
    "get_rook_polynomial_for_cycle",
    "multiply_polynomials",
    "multiply_polynomials_fft",
]
