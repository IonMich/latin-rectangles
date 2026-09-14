"""Small, independent exact oracles; deliberately import no production code.

These routines favor transparent checks over performance. Polynomial packing
uses Python integer multiplication, and counting uses explicit permutations or
an allowed-board permanent, not the library's forbidden-board decomposition.
"""

from collections.abc import Iterator
from itertools import permutations, product
from math import factorial


def packed_convolution(left: list[int], right: list[int]) -> list[int]:
    """Kronecker substitution with balanced digits, including signed inputs.

    Each coefficient has absolute value <= B = min(m,n) max|a| max|b|.
    A power-of-two base strictly greater than 2B makes signed decoding unique.
    """
    if not left or not right:
        return []
    bound = min(len(left), len(right)) * max(map(abs, left)) * max(map(abs, right))
    width = max(1, (2 * bound).bit_length())
    base = 1 << width
    packed = sum(value << (width * i) for i, value in enumerate(left)) * sum(
        value << (width * i) for i, value in enumerate(right)
    )
    result = []
    for _ in range(len(left) + len(right) - 1):
        digit = packed % base
        if digit >= base // 2:
            digit -= base
        result.append(digit)
        packed = (packed - digit) // base
    if packed:
        raise AssertionError("Polynomial packing overflow")
    return result


def cycle_types(n: int, minimum: int = 2) -> Iterator[list[int]]:
    """Partitions with no fixed points, including the empty partition."""
    if n == 0:
        yield []
    for part in range(minimum, n + 1):
        for tail in cycle_types(n - part, part):
            yield [part, *tail]


def rows_for_cycles(lengths: list[int]) -> list[list[int]]:
    """Construct zero-indexed explicit rows without library permutation helpers."""
    identity = list(range(sum(lengths)))
    second = []
    offset = 0
    for length in lengths:
        block = identity[offset : offset + length]
        second.extend([*block[1:], block[0]])
        offset += length
    return [identity, second]


def enumerate_extensions(rows: list[list[int]], rows_to_add: int = 1) -> int:
    """Count full candidate tuples directly; factorial cost, small inputs only."""
    n = len(rows[0])
    return sum(
        all(
            len({row[column] for row in [*rows, *extra]}) == len(rows) + rows_to_add
            for column in range(n)
        )
        for extra in product(permutations(range(n)), repeat=rows_to_add)
    )


def permanent_count(rows: list[list[int]]) -> int:
    """Allowed-board permanent via subset DP, O(n 2^n), with no rook formula."""
    n = len(rows[0])
    ways = [0] * (1 << n)
    ways[0] = 1
    for mask in range(1, 1 << n):
        column = mask.bit_count() - 1
        ways[mask] = sum(
            ways[mask ^ (1 << symbol)]
            for symbol in range(n)
            if mask & (1 << symbol) and all(row[column] != symbol for row in rows)
        )
    return ways[-1]


def cycle_matching_coefficients(length: int) -> list[int]:
    """Matchings of C_(2 length) by deleting/including its closing edge.

    For a path on v vertices, P_v = P_(v-1) + x P_(v-2). A cycle is
    P_(2 length) + x P_(2 length-2). No binomial coefficient formula is used.
    """
    paths = [[1], [1]]
    for _ in range(2, 2 * length + 1):
        current = [*paths[-1], 0]
        for degree, count in enumerate(paths[-2]):
            current[degree + 1] += count
        while current[-1] == 0:
            current.pop()
        paths.append(current)
    result = paths[-1].copy()
    for degree, count in enumerate(paths[-3]):
        result[degree + 1] += count
    return result


def recurrence_count(lengths: list[int]) -> int:
    """Independent arithmetic implementation, still using the rook theorem.

    This extends checks beyond feasible permanent sizes; it is not a second
    proof of the inclusion-exclusion identity itself.
    """
    polynomial = [1]
    for length in lengths:
        polynomial = packed_convolution(polynomial, cycle_matching_coefficients(length))
    n = sum(lengths)
    return sum(
        (-1) ** degree * count * factorial(n - degree)
        for degree, count in enumerate(polynomial)
    )
