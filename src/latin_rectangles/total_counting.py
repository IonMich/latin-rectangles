"""Exact totals of labeled, row-ordered Latin rectangles.

For four or more rows, use generalized Doyle inclusion-exclusion as proved in
Stones, Lin, Liu and Wang, *On Computing the Number of Latin Rectangles*,
Graphs and Combinatorics 32 (2016), Theorem 2:
https://doi.org/10.1007/s00373-015-1643-1

With h = rows - 1, population s[S] counts objects forbidden in the subset S of
the h noninitial rows. Sum over populations totaling n. A term is

    (-1)**sum(|S|*s[S]) * n!/prod(s[S]!) * prod(g(s-e_S)**s[S]),

where g counts injections by Mobius inversion on set partitions of [h]. This
counts rectangles with identity first row; multiply by n! for labeled totals.
There is no floating-point arithmetic or persistent population cache.
"""

from collections.abc import Iterator
from math import factorial, prod


def count_latin_rectangles(rows: int, columns: int) -> int:
    """Count all ``rows x columns`` Latin rectangles on ``1..columns``.

    Rows, columns and symbols are labeled: no first row or first column is
    fixed, and row order matters. An empty dimension gives one empty array;
    more rows than a positive number of columns gives zero.

    One, two and three rows use factorial/derangement/Riordan recurrences.
    Larger heights use exact generalized Doyle inclusion-exclusion with row
    symmetry. Its unreduced population count is
    ``comb(columns + 2**(rows-1) - 1, 2**(rows-1) - 1)``: polynomial in width
    at fixed height, but with a rapidly increasing degree. Large heights are
    consequently expensive; arbitrary precision arithmetic adds further cost.
    The final row of a square is forced, so squares use one fewer row.

    Raises:
        TypeError: A dimension is not an integer (booleans are rejected).
        ValueError: A dimension is negative.

    Examples:
        >>> count_latin_rectangles(4, 4)
        576
        >>> count_latin_rectangles(4, 6)
        283046400
    """
    for name, value in (("rows", rows), ("columns", columns)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    if rows == 0 or columns == 0:
        return 1
    if rows > columns:
        return 0
    if rows == columns and rows > 1:
        rows -= 1

    first_rows = factorial(columns)
    if rows == 1:
        return first_rows
    if rows == 2:
        derangements = 1
        for n in range(1, columns + 1):
            derangements = n * derangements + (-1 if n % 2 else 1)
        return first_rows * derangements
    if rows == 3:
        return first_rows * _three_row_normalized(columns)
    if rows == 4:
        return first_rows * _four_row_normalized(columns)
    return first_rows * _doyle_normalized(rows - 1, columns)


def _three_row_normalized(columns: int) -> int:
    """Riordan's recurrence, equations (3)-(4) of the cited paper."""
    previous, second, third = 1, 0, 0  # K(0), K(-1), K(-2)
    auxiliary = 1
    for n in range(1, columns + 1):
        auxiliary = -n * auxiliary - (n - 1) * (1 << n)
        current = (
            n * n * previous
            + n * (n - 1) * second
            + 2 * n * (n - 1) * (n - 2) * third
            + auxiliary
        )
        previous, second, third = current, previous, second
    return previous


def _weighted_populations(height: int, columns: int) -> Iterator[tuple[list[int], int]]:
    """Yield a reused population buffer and signed multinomial/orbit weight.

    Only singleton-mask populations are sorted. Permuting the h row labels
    acts transitively on their distinct orderings, and the sum over all other
    populations is invariant under that action. Thus each sorted slice has
    weight h!/prod(multiplicity!). Equal singleton values retain their whole
    stabilizer slice; we do not incorrectly multiply every term by h!.
    """
    size = 1 << height
    populations = [0] * size
    singletons = [1 << bit for bit in range(height)]
    remaining_masks = [mask for mask in range(size) if mask.bit_count() != 1]
    facts = [1]
    for n in range(1, max(columns, height) + 1):
        facts.append(facts[-1] * n)
    numerator = facts[columns]

    def remaining(
        position: int, left: int, denominator: int, parity: int, orbit: int
    ) -> Iterator[tuple[list[int], int]]:
        mask = remaining_masks[position]
        odd = mask.bit_count() % 2
        if position == len(remaining_masks) - 1:
            populations[mask] = left
            weight = numerator // (denominator * facts[left]) * orbit
            if (parity + odd * left) % 2:
                weight = -weight
            yield populations, weight
            return
        for count in range(left + 1):
            populations[mask] = count
            yield from remaining(
                position + 1,
                left - count,
                denominator * facts[count],
                parity + odd * count,
                orbit,
            )

    def ordered_singletons(
        position: int, left: int, minimum: int, denominator: int
    ) -> Iterator[tuple[list[int], int]]:
        if position == height:
            stabilizer = 1
            run = 1
            for index in range(1, height):
                if populations[singletons[index]] == populations[singletons[index - 1]]:
                    run += 1
                else:
                    stabilizer *= facts[run]
                    run = 1
            stabilizer *= facts[run]
            orbit = facts[height] // stabilizer
            yield from remaining(0, left, denominator, columns - left, orbit)
            return
        for count in range(minimum, left // (height - position) + 1):
            populations[singletons[position]] = count
            yield from ordered_singletons(
                position + 1, left - count, count, denominator * facts[count]
            )

    yield from ordered_singletons(0, columns, 0, 1)


def _four_row_normalized(columns: int) -> int:
    """Doyle with the five partition terms for h=3 expanded once per state."""
    total = 0
    for populations, term in _weighted_populations(3, columns):
        s0, s1, s2, s3, s4, s5, s6, _ = populations
        # f(B) is the sum of populations whose masks are disjoint from B.
        a = s0 + s2 + s4 + s6  # f({1})
        b = s0 + s1 + s4 + s5  # f({2})
        c = s0 + s1 + s2 + s3  # f({3})
        d, e, f = s0 + s4, s0 + s2, s0 + s1
        ab, ac, bc = a * b, a * c, b * c
        g = a * bc - a * f - b * e - c * d + 2 * s0
        # g(s-e_S): decrement precisely the f(B) with B disjoint from S.
        injections = (
            g - ab - ac - bc + 2 * (a + b + c) + d + e + f - 6,
            g - ab - ac + 2 * a + d + e,
            g - ab - bc + 2 * b + d + f,
            g - ab + d,
            g - ac - bc + 2 * c + e + f,
            g - ac + e,
            g - bc + f,
            g,
        )
        for count, ways in zip(populations, injections, strict=True):
            if count:
                if ways == 0:
                    break
                term *= ways**count
        else:
            total += term
    return total


def _partitions(height: int) -> Iterator[tuple[int, ...]]:
    """Set partitions with blocks represented by bit masks, without a cache."""
    if height == 0:
        yield ()
        return
    bit = 1 << (height - 1)
    for partition in _partitions(height - 1):
        yield (*partition, bit)
        for index, block in enumerate(partition):
            yield (*partition[:index], block | bit, *partition[index + 1 :])


def _doyle_normalized(height: int, columns: int) -> int:
    """General partition-Mobius formula; height excludes the fixed first row."""
    size = 1 << height
    full = size - 1
    terms = [
        (
            prod(
                (-1) ** (block.bit_count() - 1) * factorial(block.bit_count() - 1)
                for block in partition
            ),
            partition,
        )
        for partition in _partitions(height)
    ]
    total = 0
    for populations, term in _weighted_populations(height, columns):
        # Subset zeta transform: f(B) = sum_{S subset of complement(B)} s[S].
        subset_sums = populations.copy()
        for bit_index in range(height):
            bit = 1 << bit_index
            for mask in range(size):
                if mask & bit:
                    subset_sums[mask] += subset_sums[mask ^ bit]
        for mask, count in enumerate(populations):
            if count == 0:
                continue
            ways = 0
            for coefficient, partition in terms:
                product = coefficient
                for block in partition:
                    product *= subset_sums[full ^ block] - (not (mask & block))
                ways += product
            if ways == 0:
                break
            term *= ways**count
        else:
            total += term
    return total
