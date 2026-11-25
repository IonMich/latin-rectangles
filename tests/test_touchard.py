"""Tests for the 2-row Touchard cycle-structure formula."""

from typing import Literal
from unittest.mock import patch

import pytest

from latin_rectangles import count_extensions_from_derangement
from latin_rectangles import extension_counting as counting
from latin_rectangles.__main__ import generate_all_cycle_structures
from latin_rectangles.derangements import create_cycle_structure
from latin_rectangles.extension_counting import (
    _choose_cycle_structure_method,
    _count_extensions_from_cycle_type_touchard,
    _one_cycle_extension_count,
    count_extensions_from_cycle_type,
)


def test_formal_one_cycle_values() -> None:
    """M_0 and M_1 are formal Chebyshev correction terms."""
    assert _one_cycle_extension_count(0) == 2
    assert _one_cycle_extension_count(1) == -1
    assert _one_cycle_extension_count(2) == 0
    assert _one_cycle_extension_count(7) == 579


def test_touchard_research_note_examples() -> None:
    """Preserve the examples from the stored research note."""
    assert _count_extensions_from_cycle_type_touchard([3, 4]) == (
        _one_cycle_extension_count(7) + _one_cycle_extension_count(1)
    )
    assert _count_extensions_from_cycle_type_touchard([3, 4]) == 578

    assert _count_extensions_from_cycle_type_touchard([2, 2, 2, 2]) == (
        _one_cycle_extension_count(8)
        + 4 * _one_cycle_extension_count(4)
        + 3 * _one_cycle_extension_count(0)
    )
    assert _count_extensions_from_cycle_type_touchard([2, 2, 2, 2]) == 4752


def test_touchard_folds_complementary_subset_sums_before_m_lookup() -> None:
    """Complementary subset sums should share the same one-cycle value."""
    _one_cycle_extension_count.cache_clear()

    assert _count_extensions_from_cycle_type_touchard([2, 2, 2, 2]) == 4752

    info = _one_cycle_extension_count.cache_info()
    assert info.misses == 2
    assert info.hits == 0


def test_touchard_matches_rook_polynomial_for_small_cycle_structures() -> None:
    """Cross-check the Touchard path against the original rook product path."""
    for n in range(2, 13):
        for cycle_lengths in generate_all_cycle_structures(n):
            p = create_cycle_structure(cycle_lengths)
            assert _count_extensions_from_cycle_type_touchard(cycle_lengths) == (
                count_extensions_from_derangement(p)
            )


def test_cycle_structure_auto_method_routes_cold_dense_large_cases() -> None:
    """Cold dense high-n cases should not force many uncached M_s computations."""
    _one_cycle_extension_count.cache_clear()
    dense_cycle_type = [2] * 300

    assert _choose_cycle_structure_method(tuple(dense_cycle_type)) == "rook"
    assert count_extensions_from_cycle_type(
        dense_cycle_type, method="auto"
    ) == count_extensions_from_cycle_type(dense_cycle_type, method="rook")


def test_cycle_structure_auto_method_uses_warm_touchard_cache() -> None:
    """When every needed M_s is cached, auto should use the Touchard path."""
    _one_cycle_extension_count.cache_clear()
    cycle_type = [2, 2, 4]

    assert count_extensions_from_cycle_type(cycle_type, method="touchard") == 4744
    assert _choose_cycle_structure_method(tuple(cycle_type)) == "touchard"
    assert count_extensions_from_cycle_type(cycle_type, method="auto") == 4744


def test_old_signed_method_name_is_not_supported() -> None:
    """The canonical method name is Touchard; old signed names are removed."""
    with pytest.raises(ValueError, match="Unknown cycle-structure method"):
        count_extensions_from_cycle_type(  # type: ignore[arg-type]
            [2, 2], method="signed"
        )


def test_wide_cycle_type_rejects_fractional_length() -> None:
    with pytest.raises(TypeError):
        count_extensions_from_cycle_type([1024.5])  # type: ignore[list-item]


@pytest.mark.parametrize(("width", "warm_with"), [(4096, "auto"), (1024, "touchard")])
def test_wide_sparse_types_reuse_the_same_one_cycle_value(
    width: int, warm_with: Literal["auto", "touchard"]
) -> None:
    _one_cycle_extension_count.cache_clear()
    single = count_extensions_from_cycle_type([width], method=warm_with)
    with patch.object(
        counting, "_count_streaming_touchard", side_effect=AssertionError
    ):
        assert count_extensions_from_cycle_type([width]) == single
        # The equal pair uses M_width and the formal M_0 = 2.
        assert count_extensions_from_cycle_type([width // 2] * 2) == single + 2
