"""Exhaustive workflow checks independent of rook and Touchard arithmetic."""

import json
from collections import Counter
from collections.abc import Callable
from fractions import Fraction
from itertools import permutations, product

import pytest

import latin_rectangles as api
import latin_rectangles.__main__ as cli
import latin_rectangles.derangements as generation
from latin_rectangles.general_extensions import _iter_valid_next_rows

type PropertyRecorder = Callable[[str, object], None]


def _compatible(rows: list[tuple[int, ...]]) -> bool:
    """A candidate tuple is Latin exactly when each column has distinct symbols."""
    return all(len(set(column)) == len(rows) for column in zip(*rows, strict=True))


def _indexed(rows: list[tuple[int, ...]]) -> list[list[int]]:
    return [[0, *row] for row in rows]


@pytest.mark.parametrize("n", range(2, 7))
def test_every_shuffle_proposal_accepts_exactly_derangements(
    n: int, monkeypatch: pytest.MonkeyPatch, record_property: PropertyRecorder
) -> None:
    """Exhaust the rejection predicate rather than use a flaky frequency test."""
    proposals = list(permutations(range(1, n + 1)))
    identity = proposals[0]
    accepted = [p for p in proposals if _compatible([identity, p])]
    calls = 0
    pending = iter([accepted[0]])

    def deterministic_shuffle(values: list[int]) -> None:
        nonlocal calls
        calls += 1
        values[:] = next(pending)

    monkeypatch.setattr(generation.random, "shuffle", deterministic_shuffle)
    returned = set()
    for proposal in proposals:
        # An invalid proposal must be rejected before the known-valid fallback.
        pending = iter([proposal, accepted[0]])
        calls = 0
        result = api.generate_random_derangement(n)
        if proposal in accepted:
            assert calls == 1
            assert result == [0, *proposal]
            returned.add(tuple(result[1:]))
        else:
            assert calls == 2
            assert result == [0, *accepted[0]]
        assert result[0] == 0 and sorted(result[1:]) == list(identity)
        assert _compatible([identity, tuple(result[1:])])
    assert returned == set(accepted)
    record_property("proposal_count", len(proposals))
    record_property("accepted_derangements", len(accepted))
    record_property(
        "uniform_probability_given_uniform_shuffle", str(Fraction(1, len(accepted)))
    )


@pytest.mark.parametrize("n", range(2, 6))
def test_all_normalized_prefixes_and_next_row_outputs(
    n: int, record_property: PropertyRecorder
) -> None:
    candidates = list(permutations(range(1, n + 1)))
    frontier = [[candidates[0]]]
    sizes = []
    for _ in range(n):
        sizes.append(len(frontier))
        following: list[list[tuple[int, ...]]] = []
        for rows in frontier:
            legal = [p for p in candidates if _compatible([*rows, p])]
            indexed = _indexed(rows)
            expected = len(legal)
            assert api.count_extensions(indexed) == expected
            assert api.count_next_row_extensions(indexed, use_fft=True) == expected
            assert list(_iter_valid_next_rows(indexed)) == _indexed(legal)
            # Independently relabel columns and symbols, and change the first row.
            relabelled = [tuple(v % n + 1 for v in row[::-1]) for row in rows[::-1]]
            assert api.count_extensions(_indexed(relabelled)) == expected
            following.extend([*rows, candidate] for candidate in legal)
        frontier = following
    assert not frontier
    record_property("prefixes_by_existing_row_count", json.dumps(sizes))
    record_property("explicit_boards_checked", sum(sizes))


@pytest.mark.parametrize("n", [4, 5])
def test_every_two_row_start_against_full_ordered_pair_candidates(
    n: int, record_property: PropertyRecorder
) -> None:
    candidates = list(permutations(range(1, n + 1)))
    identity = candidates[0]
    total = 0
    starts = [p for p in candidates if _compatible([identity, p])]
    for second in starts:
        rows = [identity, second]
        expected = sum(
            _compatible([*rows, *pair]) for pair in product(candidates, repeat=2)
        )
        assert api.count_extensions(_indexed(rows), rows_to_add=2) == expected
        assert (
            api.count_extensions_from_derangement([0, *second], rows_to_add=2)
            == expected
        )
        total += expected
    record_property("two_row_starts", len(starts))
    record_property("ordered_four_row_rectangles_first_row_fixed", total)


def test_random_count_workflow_and_distribution_units(
    monkeypatch: pytest.MonkeyPatch, record_property: PropertyRecorder
) -> None:
    """Random starts, equally weighted cycle types, and completions differ."""
    candidates = list(permutations(range(1, 5)))
    identity = candidates[0]
    classes: Counter[tuple[int, ...]] = Counter()
    histogram: Counter[int] = Counter()
    next_start = candidates[0]

    def proposal(values: list[int]) -> None:
        values[:] = next_start

    monkeypatch.setattr(generation.random, "shuffle", proposal)
    for second in candidates:
        if not _compatible([identity, second]):
            continue
        next_start = second
        expected = sum(_compatible([identity, second, third]) for third in candidates)
        assert api.count_random_extensions(4) == expected
        n, lengths, actual = cli.count_random_extensions(4)
        assert n == 4 and actual == expected
        assert api.count_extensions_from_cycle_type(lengths) == expected
        assert api.create_cycle_structure(lengths)[0] == 0
        classes[tuple(lengths)] += 1
        histogram[expected] += 1

    assert classes == {(2, 2): 3, (4,): 6}
    assert histogram == {4: 3, 2: 6}
    all_types = cli.enumerate_all_extensions(4)
    assert {tuple(parts): count for parts, count in all_types} == {
        (2, 2): 4,
        (4,): 2,
    }
    uniform_type_mean = Fraction(sum(count for _, count in all_types), len(all_types))
    uniform_start_mean = Fraction(
        sum(k * v for k, v in histogram.items()), sum(histogram.values())
    )
    assert uniform_type_mean == 3
    assert uniform_start_mean == Fraction(8, 3)
    # If a caller then chose a legal third row uniformly, rectangle probabilities
    # would be 1/(9*4) and 1/(9*2), rather than the uniform target 1/24.
    assert {Fraction(1, 9 * count) for count in histogram} == {
        Fraction(1, 36),
        Fraction(1, 18),
    }
    record_property(
        "cycle_type_class_sizes", json.dumps({str(k): v for k, v in classes.items()})
    )
    record_property("uniform_cycle_type_mean_extensions", str(uniform_type_mean))
    record_property("uniform_derangement_mean_extensions", str(uniform_start_mean))
    record_property(
        "normalized_three_row_rectangles", sum(k * v for k, v in histogram.items())
    )


@pytest.mark.parametrize("interface", ["rows", "derangement", "cycle_type"])
def test_zero_width_extensions_do_not_depend_on_recursion_depth(interface: str) -> None:
    """Any number of ordered empty rows still has exactly one arrangement."""
    calls = {
        "rows": lambda: api.count_extensions([[0]], rows_to_add=10_000),
        "derangement": lambda: api.count_extensions_from_derangement(
            [0], rows_to_add=10_000
        ),
        "cycle_type": lambda: api.count_extensions_from_cycle_type(
            [], rows_to_add=10_000
        ),
    }
    assert calls[interface]() == 1
