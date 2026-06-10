"""Tests for the 2-row signed-sum cycle-structure formula."""

from latin_rectangles import count_extensions
from latin_rectangles.__main__ import generate_all_cycle_structures
from latin_rectangles.derangements import create_cycle_structure
from latin_rectangles.extension_counting import (
    _choose_cycle_structure_method,
    _count_cycle_structure_extensions_signed,
    _one_cycle_extension_count,
    count_cycle_structure_extensions,
)


def test_formal_one_cycle_values() -> None:
    """M_0 and M_1 are formal Chebyshev correction terms."""
    assert _one_cycle_extension_count(0) == 2
    assert _one_cycle_extension_count(1) == -1
    assert _one_cycle_extension_count(2) == 0
    assert _one_cycle_extension_count(7) == 579


def test_signed_sum_research_note_examples() -> None:
    """Preserve the examples from the stored research note."""
    assert _count_cycle_structure_extensions_signed([3, 4]) == (
        _one_cycle_extension_count(7) + _one_cycle_extension_count(1)
    )
    assert _count_cycle_structure_extensions_signed([3, 4]) == 578

    assert _count_cycle_structure_extensions_signed([2, 2, 2, 2]) == (
        _one_cycle_extension_count(8)
        + 4 * _one_cycle_extension_count(4)
        + 3 * _one_cycle_extension_count(0)
    )
    assert _count_cycle_structure_extensions_signed([2, 2, 2, 2]) == 4752


def test_signed_sum_matches_rook_polynomial_for_small_cycle_structures() -> None:
    """Cross-check the signed-sum path against the original rook product path."""
    for n in range(2, 13):
        for cycle_lengths in generate_all_cycle_structures(n):
            p = create_cycle_structure(cycle_lengths)
            assert _count_cycle_structure_extensions_signed(cycle_lengths) == (
                count_extensions(p)
            )


def test_cycle_structure_auto_method_routes_cold_dense_large_cases() -> None:
    """Cold dense high-n cases should not force many uncached M_s computations."""
    _one_cycle_extension_count.cache_clear()
    dense_cycle_type = [2] * 300

    assert _choose_cycle_structure_method(tuple(dense_cycle_type)) == "rook"
    assert count_cycle_structure_extensions(
        dense_cycle_type, method="auto"
    ) == count_cycle_structure_extensions(dense_cycle_type, method="rook")


def test_cycle_structure_auto_method_uses_warm_signed_cache() -> None:
    """When every needed M_s is cached, auto should use the signed path."""
    _one_cycle_extension_count.cache_clear()
    cycle_type = [2, 2, 4]

    assert count_cycle_structure_extensions(cycle_type, method="signed") == 4744
    assert _choose_cycle_structure_method(tuple(cycle_type)) == "signed"
    assert count_cycle_structure_extensions(cycle_type, method="auto") == 4744
