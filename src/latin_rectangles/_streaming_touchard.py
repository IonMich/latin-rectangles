"""Touchard's exact two-row count with streamed subset and ménage coefficients."""

from collections import Counter
from collections.abc import Callable, Iterator
from math import comb, gcd


def _folded_weights(lengths: tuple[int, ...], n: int) -> Iterator[tuple[int, int]]:
    """Yield (2s - n, [x^s] product(1 + x^length)) for s >= n/2."""
    counts = Counter(lengths)
    if len(counts) == 1:
        length, count = counts.popitem()
        j = (count + 1) // 2
        weight = comb(count, j)
        while j <= count:
            yield 2 * j * length - n, weight
            weight = weight * (count - j) // (j + 1)
            j += 1
        return

    # Work in powers of x^step. For P(x) = product (1+x^d)^m, put
    # Q_d = x^d P/(1+x^d). Logarithmic differentiation gives
    # x P' = sum(m*d*Q_d), while Q_d = x^d(P-Q_d).
    # A ring of d coefficients per distinct d implements this last delay.
    step = gcd(*counts)
    delays = [
        (length // step * count, [0] * (length // step))
        for length, count in counts.items()
    ]
    for s in range(n // step + 1):
        weight = (
            sum(factor * delay[s % len(delay)] for factor, delay in delays) // s
            if s
            else 1
        )
        index = 2 * s * step - n
        if index >= 0 and weight:
            yield index, weight
        for _, delay in delays:
            slot = s % len(delay)
            delay[slot] = weight - delay[slot]


def _count_streaming_touchard(
    lengths: tuple[int, ...], *, cached_value: Callable[[int], int | None] | None = None
) -> int:
    """Count legal third rows from previously validated relative cycle lengths."""
    if not lengths:
        return 1

    # Complementary subsets have the same weight and same absolute index.
    # At the center, Touchard's factor 1/2 turns the formal M_0 = 2 into 1.
    # M_1 = -1. For s >= 2 the circular ménage number is M_s = A_s - A_(s-1),
    # where A_s is the straight ménage number with A_0 = 1, A_1 = A_2 = 0.
    a, b, c = 1, 0, 0
    s = 2
    result = 0
    for index, weight in _folded_weights(lengths, sum(lengths)):
        if index == 0:
            result += weight
        elif index == 1:
            result -= weight
        else:
            value = cached_value(index) if cached_value is not None else None
            if value is None:
                while s < index:
                    s += 1
                    a, b, c = b, c, (s - 1) * (c + b) + a
                value = c - b
            result += weight * value
    return result
