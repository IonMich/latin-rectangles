"""Tests for FFT-based polynomial multiplication and integration."""

import random

from latin_rectangles import count_extensions, generate_random_derangement
from latin_rectangles.derangements import create_cycle_structure
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


def test_fft_poly_matches_naive_large_coefficients() -> None:
    """Force the exact NTT/CRT path, including multi-prime reconstruction."""
    random.seed(99)
    a = [random.randint(-(1 << 80), 1 << 80) for _ in range(200)]
    b = [random.randint(-(1 << 80), 1 << 80) for _ in range(180)]
    naive = multiply_polynomials(a, b)
    fft = multiply_polynomials_fft(a, b)
    assert fft == naive


def test_count_extensions_fft_equals_naive() -> None:
    for n in [3, 4, 5, 6, 8]:
        random.seed(123 + n)
        p = generate_random_derangement(n)
        naive = count_extensions(p, use_fft=False)
        fast = count_extensions(p, use_fft=True)
        assert naive == fast


def test_count_extensions_fft_regression_all_2_cycles_n_40() -> None:
    """This input exposed floating FFT rounding errors before exact NTT/CRT."""
    p = create_cycle_structure([2] * 20)
    naive = count_extensions(p, use_fft=False)
    fast = count_extensions(p, use_fft=True)
    assert fast == naive


def test_count_extensions_fft_two_large_cycles() -> None:
    """Force transform multiplication inside the rook-product extension path."""
    p = create_cycle_structure([200, 200])
    naive = count_extensions(p, use_fft=False)
    fast = count_extensions(p, use_fft=True)
    assert fast == naive
