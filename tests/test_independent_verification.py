"""Independent arithmetic/enumeration checks, including real route execution."""

from itertools import permutations
from random import Random
from unittest.mock import patch

import pytest

from benchmarks.references import (
    cycle_matching_coefficients,
    cycle_types,
    enumerate_extensions,
    packed_convolution,
    permanent_count,
    recurrence_count,
    rows_for_cycles,
)
from latin_rectangles import (
    count_extensions,
    count_extensions_from_cycle_type,
    count_extensions_from_derangement,
    count_next_row_extensions,
    create_cycle_structure,
)
from latin_rectangles import extension_counting as counting
from latin_rectangles import rook_polynomials as rook


def one_indexed(rows: list[list[int]]) -> list[list[int]]:
    return [[0, *(symbol + 1 for symbol in row)] for row in rows]


@pytest.mark.parametrize("size", [2, 4, 8, 16])
def test_ntt_matches_direct_modular_dft(size: int) -> None:
    """A round trip alone could hide matching forward/inverse mistakes."""
    modulus = 17
    root = pow(3, 16 // size, modulus)
    values = [(i * i + 3 * i - 7) % modulus for i in range(size)]
    expected = [
        sum(value * pow(root, i * j, modulus) for i, value in enumerate(values))
        % modulus
        for j in range(size)
    ]
    transformed = values.copy()
    rook._ntt(transformed, root, modulus, invert=False)
    assert transformed == expected
    rook._ntt(transformed, root, modulus, invert=True)
    assert transformed == values


@pytest.mark.parametrize("bits", [1, 20, 60, 110])
@pytest.mark.parametrize("lengths", [(128, 129), (129, 129), (257, 131)])
def test_real_ntt_crt_matches_integer_packing(
    bits: int, lengths: tuple[int, int]
) -> None:
    rng = Random(901 + bits)
    left, right = [
        [rng.randrange(-(1 << bits), 1 << bits) for _ in range(length)]
        for length in lengths
    ]
    originals = left.copy(), right.copy()
    with patch.object(rook, "_convolve_mod", wraps=rook._convolve_mod) as modular:
        assert rook.multiply_polynomials_fft(left, right) == packed_convolution(
            left, right
        )
    assert modular.call_count >= (2 if bits >= 20 else 1)
    moduli = [call.args[3] for call in modular.call_args_list]
    assert len(set(moduli)) == len(moduli)
    assert (left, right) == originals


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ([], []),
        ([], [1, 2, 3]),
        ([1, 2, 3], []),
        ([0], [-7]),
        ([-3], [1, -2, 0]),
        ([0] * 140, [2] * 140),
        ([1, *([0] * 127), -1], [-1, *([0] * 127), 1]),
        ([1 << 160] * 129, [-(1 << 160)] * 129),
    ],
)
def test_convolution_edge_cases(left: list[int], right: list[int]) -> None:
    expected = packed_convolution(left, right)
    assert rook.multiply_polynomials(left, right) == expected
    assert rook.multiply_polynomials_fft(left, right) == expected


@pytest.mark.parametrize(
    ("left_size", "right_size", "uses_ntt"),
    [(128, 128, False), (31, 600, False), (32, 512, False), (32, 513, True)],
)
def test_transform_dispatch_boundaries(
    left_size: int, right_size: int, uses_ntt: bool
) -> None:
    left = [1] * left_size
    right = [-1] * right_size
    with patch.object(rook, "_convolve_mod", wraps=rook._convolve_mod) as modular:
        assert rook.multiply_polynomials_fft(left, right) == packed_convolution(
            left, right
        )
    assert bool(modular.call_count) == uses_ntt


@pytest.mark.parametrize("n", range(9))
def test_all_small_cycle_types_against_permutation_enumeration(n: int) -> None:
    for lengths in cycle_types(n):
        rows = rows_for_cycles(lengths)
        expected = enumerate_extensions(rows)
        assert permanent_count(rows) == expected
        assert recurrence_count(lengths) == expected
        for method in ("auto", "touchard", "rook", "rook_ntt"):
            assert count_extensions_from_cycle_type(lengths, method=method) == expected
        indexed = one_indexed(rows)
        assert count_extensions_from_derangement(indexed[1]) == expected
        assert count_next_row_extensions(indexed) == expected


def test_all_small_derangements_and_relabelled_general_boards() -> None:
    for n in range(2, 6):
        identity = list(range(n))
        for second in permutations(identity):
            if any(i == symbol for i, symbol in enumerate(second)):
                continue
            rows = [identity, list(second)]
            expected = enumerate_extensions(rows)
            assert count_extensions_from_derangement(one_indexed(rows)[1]) == expected
            # Independent column permutation and symbol relabelling, plus row swap.
            relabelled = [[(v + 1) % n for v in row[::-1]] for row in rows[::-1]]
            for use_fft in (False, True):
                assert (
                    count_next_row_extensions(one_indexed(relabelled), use_fft=use_fft)
                    == expected
                )


@pytest.mark.parametrize("lengths", [[], [2], [3], [2, 2], [2, 3]])
@pytest.mark.parametrize("rows_to_add", [0, 1, 2])
def test_ordered_multiple_rows_against_full_candidate_tuples(
    lengths: list[int], rows_to_add: int
) -> None:
    rows = rows_for_cycles(lengths)
    expected = enumerate_extensions(rows, rows_to_add)
    assert (
        count_extensions_from_cycle_type(lengths, rows_to_add=rows_to_add) == expected
    )
    assert count_extensions(one_indexed(rows), rows_to_add=rows_to_add) == expected


def test_every_normalized_latin_square_prefix_of_order_four() -> None:
    """Cover arbitrary 3-row forbidden graphs, complete and overfull boards."""
    frontier = [[[0, 1, 2, 3]]]
    for _ in range(4):
        next_frontier = []
        for rows in frontier:
            expected = enumerate_extensions(rows)
            assert count_next_row_extensions(one_indexed(rows)) == expected
            for candidate in permutations(range(4)):
                if all(candidate[c] not in [r[c] for r in rows] for c in range(4)):
                    next_frontier.append([*rows, list(candidate)])
        frontier = next_frontier
    assert not frontier


@pytest.mark.parametrize("n", [63, 64, 65, 66, 255, 256, 257, 258])
def test_touchard_fold_and_router_boundaries_against_recurrence(n: int) -> None:
    lengths = [2] * (n // 2) if n % 2 == 0 else [3] + [2] * ((n - 3) // 2)
    expected = recurrence_count(lengths)
    counting._one_cycle_extension_count.cache_clear()
    rook._ROOK_POLY_CACHE.clear()
    cold = count_extensions_from_cycle_type(lengths)
    assert cold == expected
    assert count_extensions_from_cycle_type(lengths, method="touchard") == expected
    assert count_extensions_from_cycle_type(lengths) == expected


@pytest.mark.parametrize("length", [2, 3, 4, 7, 32, 65, 129])
def test_rook_cycle_coefficients_against_path_matchings(length: int) -> None:
    assert rook.get_rook_polynomial_for_cycle(length) == cycle_matching_coefficients(
        length
    )


def test_callers_cannot_corrupt_the_rook_cache() -> None:
    rook._ROOK_POLY_CACHE.clear()
    first = rook.get_rook_polynomial_for_cycle(3)
    first[1] = -123
    second = rook.get_rook_polynomial_for_cycle(3)
    assert second == [1, 6, 9, 2]
    second.append(99)
    assert count_extensions_from_cycle_type([3], method="rook") == 1


@pytest.mark.parametrize("lengths", [[0], [-2], [2, -2], [2, 0], [1]])
def test_cycle_constructor_rejects_non_derangement_parts(lengths: list[int]) -> None:
    with pytest.raises(ValueError):
        create_cycle_structure(lengths)
