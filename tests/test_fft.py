"""Tests for FFT-based polynomial multiplication and integration."""

import random

from latin_rectangles import count_extensions, generate_random_derangement
from latin_rectangles.rook_polynomials import (
    multiply_polynomials,
    multiply_polynomials_fft,
)


def test_fft_poly_matches_naive_small_cases() -> None:
    random.seed(42)
    for _ in range(10):
        a = [random.randint(0, 5) for _ in range(random.randint(1, 6))]
        b = [random.randint(0, 5) for _ in range(random.randint(1, 6))]
        naive = multiply_polynomials(a, b)
        fft = multiply_polynomials_fft(a, b)
        assert fft == naive


def test_count_extensions_fft_equals_naive() -> None:
    # Verify that enabling FFT yields the same result as naive for a few n
    for n in [3, 4, 5, 6, 8]:
        random.seed(123 + n)
        p = generate_random_derangement(n)
        naive = count_extensions(p, use_fft=False)
        fast = count_extensions(p, use_fft=True)
        assert naive == fast
