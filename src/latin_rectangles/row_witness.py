"""Construct a legal next row for an explicit Latin rectangle."""

from collections import deque

from .general_extensions import _validate_latin_rows


def _repair_permutation(rows: list[list[int]], n: int) -> list[int]:
    """Repair conflicts by swapping with one of the first 2k columns."""
    k = len(rows)
    pivots = [{row[j] for row in rows} for j in range(1, 2 * k + 1)]
    result = list(range(n + 1))
    for column in range(1, n + 1):
        forbidden = (
            pivots[column - 1] if column <= 2 * k else {row[column] for row in rows}
        )
        symbol = result[column]
        if symbol not in forbidden:
            continue
        # k columns hold symbols forbidden here, and k forbid this symbol.
        # Both sets contain this column, so at most 2k-1 pivots fail.
        other = next(
            j
            for j, blocked in enumerate(pivots, 1)
            if result[j] not in forbidden and symbol not in blocked
        )
        result[column], result[other] = result[other], symbol
    return result


def _match_allowed(rows: list[list[int]], n: int) -> list[int]:
    """Find a perfect matching of the sparse allowed column-symbol graph."""
    symbols = range(1, n + 1)
    allowed: list[list[int]] = [[]]
    result = [0] * (n + 1)
    owner = [0] * (n + 1)
    for column in range(1, n + 1):
        forbidden = {row[column] for row in rows}
        neighbors = [symbol for symbol in symbols if symbol not in forbidden]
        allowed.append(neighbors)
        for symbol in neighbors:
            if not owner[symbol]:
                result[column] = symbol
                owner[symbol] = column
                break

    for root in range(1, n + 1):
        if result[root]:
            continue
        # Find an alternating path from this column to a free symbol. Hall's
        # theorem guarantees one because the graph is regular of positive degree.
        reached_from = [0] * (n + 1)
        queue = deque([root])
        free = 0
        while not free:
            column = queue.popleft()
            for symbol in allowed[column]:
                if reached_from[symbol]:
                    continue
                reached_from[symbol] = column
                if not owner[symbol]:
                    free = symbol
                    break
                queue.append(owner[symbol])
        # Flip the path. The previous match at the root is the zero sentinel.
        while free:
            column = reached_from[free]
            owner[free] = column
            result[column], free = free, result[column]
    return result


def find_next_row(rows: list[list[int]]) -> list[int] | None:
    """Construct a deterministic legal next row for a validated k x n rectangle.

    Rows and the returned permutation use a leading zero. A positive-width
    full square returns None, and a zero-width input returns the empty row [0].
    Invalid inputs raise ValueError under the same rules as count_extensions.

    For k <= n/2, swaps take O(nk) time with O(n + k^2) auxiliary space.
    For k > n/2, augmenting paths in the allowed graph of degree d = n-k
    take O(nk + n^2 d) time with O(n + nd) auxiliary space.
    """
    n = _validate_latin_rows(rows)
    if n == 0:
        return [0]
    k = len(rows)
    if k == n:
        return None
    if 2 * k <= n:
        return _repair_permutation(rows, n)
    return _match_allowed(rows, n)
