"""Independent enumeration and published totals for labeled rectangles."""

from itertools import permutations
from math import factorial
from typing import cast

import pytest

from latin_rectangles import count_latin_rectangles
from latin_rectangles.total_counting import _doyle_normalized


def _brute_labeled_counts(columns: int) -> list[int]:
    """Enumerate ordered rows, retaining every labeling and fixing no row."""
    counts = [0] * (columns + 1)
    used: list[set[int]] = [set() for _ in range(columns)]
    possible_rows = list(permutations(range(columns)))

    def visit(rows: int) -> None:
        counts[rows] += 1
        if rows == columns:
            return
        for row in possible_rows:
            if any(symbol in used[column] for column, symbol in enumerate(row)):
                continue
            for column, symbol in enumerate(row):
                used[column].add(symbol)
            visit(rows + 1)
            for column, symbol in enumerate(row):
                used[column].remove(symbol)

    visit(0)
    return counts


@pytest.mark.parametrize("columns", range(1, 5))
def test_against_independent_labeled_enumeration(columns: int) -> None:
    for rows, expected in enumerate(_brute_labeled_counts(columns)):
        assert count_latin_rectangles(rows, columns) == expected


# R(k,n) in McKay and Wanless, On the number of Latin squares, Table 1:
# https://users.cecs.anu.edu.au/~bdm/papers/ls11.pdf
# Converted using L(k,n) = n! (n-1)! R(k,n) / (n-k)!.
@pytest.mark.parametrize(
    ("rows", "columns", "expected"),
    [
        (2, 6, 190800),
        (3, 5, 66240),
        (3, 6, 15321600),
        (3, 7, 5411750400),
        (4, 4, 576),
        (4, 5, 161280),
        (4, 6, 283046400),
        (4, 7, 782137036800),
        (4, 8, 3563924952268800),
        (4, 9, 25315180943034286080),
        (4, 10, 269169718618593283276800),
        (4, 11, 4137679434467601752260608000),
        (5, 5, 161280),
        (5, 6, 812851200),
        (5, 7, 20449013760000),
        (6, 6, 812851200),
    ],
)
def test_published_labeled_totals(rows: int, columns: int, expected: int) -> None:
    assert count_latin_rectangles(rows, columns) == expected


@pytest.mark.parametrize("rows", (2, 3, 4))
def test_general_doyle_matches_independent_enumeration(rows: int) -> None:
    # Exercise the general partition formula rather than the public fast paths.
    columns = 4
    expected = _brute_labeled_counts(columns)[rows]
    assert factorial(columns) * _doyle_normalized(rows - 1, columns) == expected


@pytest.mark.parametrize("height", (4, 5))
def test_general_doyle_cancellation_when_too_many_rows(height: int) -> None:
    # One object's available positions cannot accommodate this many rows.
    assert _doyle_normalized(height, 3) == 0


@pytest.mark.parametrize(("rows", "columns"), [(0, 0), (0, 20), (20, 0)])
def test_empty_dimensions(rows: int, columns: int) -> None:
    assert count_latin_rectangles(rows, columns) == 1


@pytest.mark.parametrize(("rows", "columns"), [(2, 1), (4, 3), (21, 20)])
def test_more_rows_than_symbols(rows: int, columns: int) -> None:
    assert count_latin_rectangles(rows, columns) == 0


def test_one_row_counts_every_symbol_permutation() -> None:
    assert count_latin_rectangles(1, 20) == factorial(20)


@pytest.mark.parametrize(("rows", "columns"), [(-1, 4), (4, -1), (0, -1), (-1, 0)])
def test_negative_dimensions(rows: int, columns: int) -> None:
    with pytest.raises(ValueError, match="must be non-negative"):
        count_latin_rectangles(rows, columns)


@pytest.mark.parametrize("value", [True, False, 3.0, "3", None])
def test_non_integer_dimensions(value: object) -> None:
    with pytest.raises(TypeError, match="rows must be an integer"):
        count_latin_rectangles(cast(int, value), 4)
    with pytest.raises(TypeError, match="columns must be an integer"):
        count_latin_rectangles(4, cast(int, value))
