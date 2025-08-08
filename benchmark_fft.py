#!/usr/bin/env python3
"""Benchmark naive vs FFT polynomial multiplication paths.

Two parts:
1) Direct polynomial convolution benchmark (synthetic), which isolates the
    asymptotics: naive O(n^2) vs FFT O(n log n).
2) Controlled algorithm-internal benchmark using a single n-cycle permutation,
    which performs one convolution of degree n inside count_extensions.
"""

from __future__ import annotations

import math
import random
import time
from statistics import mean

from latin_rectangles import count_extensions
from latin_rectangles.rook_polynomials import (
    multiply_polynomials,
    multiply_polynomials_fft,
)


def fit_power(x: list[float], y: list[float]) -> float:
    # Returns exponent b from linear fit of log y vs log x
    lx = [math.log(v) for v in x]
    ly = [math.log(v) for v in y]
    n = len(x)
    x_mean = sum(lx) / n
    y_mean = sum(ly) / n
    num = sum((lx[i] - x_mean) * (ly[i] - y_mean) for i in range(n))
    den = sum((lx[i] - x_mean) ** 2 for i in range(n))
    return num / den if den else 0.0


def bench_polymul(
    ns: list[int], repeats: int = 3
) -> tuple[list[int], list[float], list[float]]:
    """Benchmark naive vs FFT on random polynomial pairs of equal length n."""
    times_naive: list[float] = []
    times_fft: list[float] = []
    for n in ns:
        random.seed(42 + n)
        a = [random.randint(0, 1000) for _ in range(n)]
        b = [random.randint(0, 1000) for _ in range(n)]

        run_naive: list[float] = []
        run_fft: list[float] = []
        for _ in range(repeats):
            t0 = time.perf_counter()
            _ = multiply_polynomials(a, b)
            run_naive.append(time.perf_counter() - t0)

            t1 = time.perf_counter()
            _ = multiply_polynomials_fft(a, b)
            run_fft.append(time.perf_counter() - t1)

        times_naive.append(mean(run_naive))
        times_fft.append(mean(run_fft))
    return ns, times_naive, times_fft


def bench_single_cycle(
    ns: list[int], repeats: int = 3
) -> tuple[list[int], list[float], list[float]]:
    """Benchmark count_extensions on a single n-cycle to isolate one convolution."""

    def single_cycle_perm(n: int) -> list[int]:
        # [0, 2, 3, ..., n, 1]
        return [0, *list(range(2, n + 1)), 1]

    times_naive: list[float] = []
    times_fft: list[float] = []
    for n in ns:
        p = single_cycle_perm(n)
        r_naive = []
        r_fft = []
        for _ in range(repeats):
            t0 = time.perf_counter()
            _ = count_extensions(p, use_fft=False)
            r_naive.append(time.perf_counter() - t0)

            t1 = time.perf_counter()
            _ = count_extensions(p, use_fft=True)
            r_fft.append(time.perf_counter() - t1)
        times_naive.append(mean(r_naive))
        times_fft.append(mean(r_fft))
    return ns, times_naive, times_fft


def main() -> None:
    # Modest sizes for quick runs; adjust if needed
    ns_poly = [64, 128, 256, 384, 512]
    ns_cycle = [64, 96, 128, 160, 192, 224, 256]

    print("=== Direct polynomial multiplication ===")
    n1, t1_naive, t1_fft = bench_polymul(ns_poly)
    b1_naive = fit_power([float(n) for n in n1], t1_naive)
    b1_fft = fit_power([float(n) for n in n1], t1_fft)
    print("n:", n1)
    print("naive(s):", [f"{t:.3e}" for t in t1_naive])
    print("fft  (s):", [f"{t:.3e}" for t in t1_fft])
    print(f"Observed exponent naive ~ n^{b1_naive:.2f}")
    print(f"Observed exponent fft   ~ n^{b1_fft:.2f}")
    print("(Targets: ~2.00 naive, ~1.00 for n log n over moderate ranges)\n")

    print("=== Single-cycle count_extensions (one convolution) ===")
    n2, t2_naive, t2_fft = bench_single_cycle(ns_cycle)
    b2_naive = fit_power([float(n) for n in n2], t2_naive)
    b2_fft = fit_power([float(n) for n in n2], t2_fft)
    print("n:", n2)
    print("naive(s):", [f"{t:.3e}" for t in t2_naive])
    print("fft  (s):", [f"{t:.3e}" for t in t2_fft])
    print(f"Observed exponent naive ~ n^{b2_naive:.2f}")
    print(f"Observed exponent fft   ~ n^{b2_fft:.2f}")
    print("(Note: includes inclusion-exclusion overhead ~O(n))")


if __name__ == "__main__":
    main()
