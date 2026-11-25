"""Independent checks for a single legal next row of a Latin rectangle."""

from itertools import permutations

import pytest

from latin_rectangles import find_next_row


def test_find_next_row_on_all_order_four_prefixes_with_fixed_first_row() -> None:
    # This includes disconnected allowed graphs, forced final rows and full
    # squares. Starting with a nonidentity row checks the returned symbol labels.
    candidates = [[0, *p] for p in permutations(range(1, 5))]
    frontier = [[[0, 2, 1, 4, 3]]]
    while frontier:
        rows = frontier.pop()
        legal = [
            p
            for p in candidates
            if all(p[j] != row[j] for row in rows for j in range(1, 5))
        ]
        original = [row.copy() for row in rows]
        result = find_next_row(rows)
        assert rows == original
        if legal:
            assert result in legal
        else:
            assert result is None
        frontier.extend([*rows, candidate] for candidate in legal)


def test_find_next_row_can_reassign_a_greedy_choice() -> None:
    # Taking the smallest unused legal symbol in every column chooses
    # 4, 3, 1, 2. The last remaining symbol, 5, is forbidden in column 5.
    rows = [[0, 1, 2, 3, 4, 5], [0, 2, 1, 4, 5, 3], [0, 3, 4, 5, 1, 2]]
    result = find_next_row(rows)
    assert result is not None
    assert result[0] == 0 and sorted(result[1:]) == [1, 2, 3, 4, 5]
    assert all(result[j] != row[j] for row in rows for j in range(1, 6))


def test_find_next_row_on_wide_input() -> None:
    n = 1025
    rows = [[0, *range(1, n + 1)], [0, *range(2, n + 1), 1]]
    result = find_next_row(rows)
    assert result is not None
    assert result[0] == 0 and sorted(result[1:]) == list(range(1, n + 1))
    assert all(result[j] != row[j] for row in rows for j in range(1, n + 1))


def test_find_next_row_at_zero_width() -> None:
    assert find_next_row([[0]]) == [0]


@pytest.mark.parametrize(
    "rows",
    [[], [[]], [[1, 2, 3]], [[0, 1, 1]], [[0, 1], [0, 2, 1]], [[0, 1], [0, 1]]],
    ids=["no-rows", "empty-list-row", "sentinel", "permutation", "width", "column"],
)
def test_find_next_row_rejects_invalid_prefix(rows: list[list[int]]) -> None:
    with pytest.raises(ValueError):
        find_next_row(rows)
