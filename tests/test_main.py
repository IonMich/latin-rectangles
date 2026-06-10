"""Tests for Latin rectangles extension counting algorithms."""

import pytest

from latin_rectangles import (
    count_extensions,
    count_extensions_k,
    find_cycle_decomposition,
    generate_random_derangement,
)


class TestGenerateRandomDerangement:
    """Test the random derangement generation function."""

    def test_derangement_size_0(self) -> None:
        """Test derangement for n=0."""
        result = generate_random_derangement(0)
        assert result == [0]

    def test_derangement_size_1_raises_error(self) -> None:
        """Test that n=1 raises ValueError."""
        with pytest.raises(ValueError, match="No derangements exist for n=1"):
            generate_random_derangement(1)

    def test_negative_n_raises_error(self) -> None:
        """Test that negative n raises ValueError."""
        with pytest.raises(ValueError, match="n must be non-negative"):
            generate_random_derangement(-1)

    def test_derangement_valid_for_n_2(self) -> None:
        """Test derangement for n=2."""
        result = generate_random_derangement(2)
        assert len(result) == 3  # [0, p1, p2]
        assert result[0] == 0  # 0-index is dummy
        assert result[1] != 1  # Not a fixed point
        assert result[2] != 2  # Not a fixed point
        assert set(result[1:]) == {1, 2}  # Valid permutation

    def test_derangement_valid_for_n_5(self) -> None:
        """Test derangement for n=5."""
        result = generate_random_derangement(5)
        assert len(result) == 6  # [0, p1, p2, p3, p4, p5]
        assert result[0] == 0  # 0-index is dummy

        # Check it's a valid derangement
        for i in range(1, 6):
            assert result[i] != i  # No fixed points

        # Check it's a valid permutation
        assert set(result[1:]) == {1, 2, 3, 4, 5}

    def test_derangement_repeated_calls(self) -> None:
        """Test that repeated calls produce valid derangements."""
        for _ in range(10):
            result = generate_random_derangement(4)
            assert len(result) == 5
            assert result[0] == 0
            for i in range(1, 5):
                assert result[i] != i
            assert set(result[1:]) == {1, 2, 3, 4}


class TestFindCycleDecomposition:
    """Test the cycle decomposition function."""

    def test_single_cycle(self) -> None:
        """Test a single cycle permutation."""
        p = [0, 2, 3, 4, 1]  # (1 2 3 4)
        cycles = find_cycle_decomposition(p)
        assert len(cycles) == 1
        assert cycles[0] == [1, 2, 3, 4]

    def test_two_cycles(self) -> None:
        """Test a permutation with two cycles."""
        p = [0, 2, 1, 4, 3]  # (1 2)(3 4)
        cycles = find_cycle_decomposition(p)
        assert len(cycles) == 2
        # Sort cycles by first element for consistent testing
        cycles.sort(key=lambda x: x[0])
        assert cycles[0] == [1, 2]
        assert cycles[1] == [3, 4]

    def test_identity_permutation(self) -> None:
        """Test the identity permutation (all 1-cycles)."""
        p = [0, 1, 2, 3, 4]  # Identity
        cycles = find_cycle_decomposition(p)
        assert len(cycles) == 4
        expected_cycles = [[1], [2], [3], [4]]
        cycles.sort(key=lambda x: x[0])
        assert cycles == expected_cycles

    def test_complex_permutation(self) -> None:
        """Test a more complex permutation."""
        p = [0, 3, 1, 5, 6, 4, 2]  # (1 3 5 4 6 2)
        cycles = find_cycle_decomposition(p)
        assert len(cycles) == 1
        assert cycles[0] == [1, 3, 5, 4, 6, 2]


class TestCountExtensions:
    """Test the extension counting function."""

    def test_invalid_not_derangement(self) -> None:
        """Test that non-derangements raise ValueError."""
        p = [0, 1, 2, 3, 4]  # Identity (has fixed points)
        with pytest.raises(ValueError, match="Input permutation must be a derangement"):
            count_extensions(p)

    def test_single_2_cycle(self) -> None:
        """Test a simple 2-cycle derangement."""
        p = [0, 2, 1]  # (1 2)
        result = count_extensions(p)
        assert result == 0  # Known result for 2-cycle

    def test_two_2_cycles(self) -> None:
        """Test two 2-cycles."""
        p = [0, 2, 1, 4, 3]  # (1 2)(3 4)
        result = count_extensions(p)
        assert result == 4  # Actual result from algorithm

    def test_3_cycle(self) -> None:
        """Test a 3-cycle."""
        p = [0, 2, 3, 1]  # (1 2 3)
        result = count_extensions(p)
        assert result == 1  # Actual result from algorithm

    def test_4_cycle(self) -> None:
        """Test a 4-cycle."""
        p = [0, 2, 3, 4, 1]  # (1 2 3 4)
        result = count_extensions(p)
        assert result == 2  # Actual result from algorithm

    def test_known_8_cycle_result(self) -> None:
        """Test the known result for an 8-cycle."""
        p = [0, 2, 3, 4, 5, 6, 7, 8, 1]  # 8-cycle
        result = count_extensions(p)
        assert result == 4738  # Actual result from algorithm

    def test_known_6_2_cycles_result(self) -> None:
        """Test the known result for (6,2)-cycles."""
        p = [0, 2, 3, 4, 5, 6, 1, 8, 7]  # (1 2 3 4 5 6)(7 8)
        result = count_extensions(p)
        assert result == 4740  # Actual result from algorithm

    def test_known_4_4_cycles_result(self) -> None:
        """Test the known result for (4,4)-cycles."""
        p = [0, 2, 3, 4, 1, 6, 7, 8, 5]  # (1 2 3 4)(5 6 7 8)
        result = count_extensions(p)
        assert result == 4740  # Actual result from algorithm

    def test_known_four_2_cycles_result(self) -> None:
        """Test the known result for four 2-cycles."""
        p = [0, 2, 1, 4, 3, 6, 5, 8, 7]  # (1 2)(3 4)(5 6)(7 8)
        result = count_extensions(p)
        assert result == 4752  # Actual result from algorithm

    def test_result_is_non_negative(self) -> None:
        """Test that results are always non-negative."""
        # Test various derangements
        test_cases = [
            [0, 2, 3, 1],  # 3-cycle
            [0, 3, 1, 2],  # 3-cycle (different)
            [0, 2, 4, 1, 3],  # (1 2 4 3)
            [0, 3, 4, 1, 2],  # (1 3)(2 4)
        ]

        for p in test_cases:
            result = count_extensions(p)
            assert result >= 0, f"Negative result for permutation {p}"

    # CLI behavior is covered in tests/test_cli.py


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_random_derangement_can_be_counted(self) -> None:
        """Test that randomly generated derangements can be counted."""
        for n in [3, 4, 5, 6]:
            derangement = generate_random_derangement(n)
            # Should not raise an exception
            result = count_extensions(derangement)
            assert isinstance(result, int)
            assert result >= 0

    def test_cycle_decomposition_of_derangement(self) -> None:
        """Test that cycle decomposition works on generated derangements."""
        for n in [3, 4, 5, 6]:
            derangement = generate_random_derangement(n)
            cycles = find_cycle_decomposition(derangement)

            # All elements should appear exactly once across all cycles
            all_elements = []
            for cycle in cycles:
                all_elements.extend(cycle)

            assert set(all_elements) == set(range(1, n + 1))
            assert len(all_elements) == n

    def test_general_k_matches_two_row_case(self) -> None:
        """For two existing rows (id + derangement), general method matches specialized."""
        # Build rows: first identity, second is a derangement p
        p = [0, 2, 3, 1]  # 3-cycle
        rows = [[0, 1, 2, 3], p]
        general = count_extensions_k(rows)
        specialized = count_extensions(p)
        assert general == specialized

    def test_general_k_consistency_multiple_derangements(self) -> None:
        """Consistency with 2→3 method across a few small derangements."""
        cases: list[list[int]] = [
            [0, 2, 3, 1],  # (1 2 3)
            [0, 2, 1, 4, 3],  # (1 2)(3 4)
            [0, 2, 3, 4, 1],  # (1 2 3 4)
        ]
        for p in cases:
            n = len(p) - 1
            id_row = [0, *list(range(1, n + 1))]
            assert count_extensions_k([id_row, p]) == count_extensions(p)

    def test_general_k_small_examples(self) -> None:
        """Check small n and k against a direct permanent for sanity."""

        def permanent_of_allowed(rows: list[list[int]]) -> int:
            # Build A[i,j] = 1 if i not in {rows[r][j] for r}
            n = len(rows[0]) - 1
            used: list[set[int]] = [set() for _ in range(n + 1)]
            for r in rows:
                for j in range(1, n + 1):
                    used[j].add(r[j])
            # brute-force sum over permutations of [1..n]
            ans = 0
            from itertools import permutations

            for perm in permutations(range(1, n + 1)):
                ok = True
                for j, i in enumerate(perm, start=1):
                    if i in used[j]:
                        ok = False
                        break
                ans += int(ok)
            return ans

        # n=3, k=2 (two rows: id and a 3-cycle derangement)
        rows = [[0, 1, 2, 3], [0, 2, 3, 1]]
        assert count_extensions_k(rows) == permanent_of_allowed(rows)

        # n=4, k=3 (three rows): id, (1 2)(3 4), and (1 3)(2 4)
        rows2 = [
            [0, 1, 2, 3, 4],
            [0, 2, 1, 4, 3],
            [0, 3, 4, 1, 2],
        ]
        assert count_extensions_k(rows2) == permanent_of_allowed(rows2)

    def test_general_k_one_row_counts_derangements(self) -> None:
        """With one existing row, extensions are exactly derangements."""
        known_derangements = {
            0: 1,
            1: 0,
            2: 1,
            3: 2,
            4: 9,
            5: 44,
            6: 265,
            7: 1854,
            8: 14833,
        }
        for n, expected in known_derangements.items():
            identity = [0, *list(range(1, n + 1))]
            assert count_extensions_k([identity]) == expected
            assert count_extensions_k([identity], use_fft=True) == expected

    def test_general_k_one_row_large_n_fast_path(self) -> None:
        """A one-row input should not enter the exponential component DP."""
        identity = [0, *list(range(1, 101))]
        assert count_extensions_k([identity]).bit_length() == 524

    def test_n_minus_1_rows_unique_extension(self) -> None:
        """With k=n-1 rows formed by powers of an n-cycle, there is exactly one extension."""

        def power_cycle_perm(n: int, power: int) -> list[int]:
            # 1-indexed: i -> ((i-1 + power) % n) + 1
            return [0] + [((i - 1 + power) % n) + 1 for i in range(1, n + 1)]

        for n in [3, 4, 5]:
            # rows: π^0, π^1, ..., π^{n-2}; unique allowed symbol per column is π^{n-1}
            rows = [power_cycle_perm(n, r) for r in range(n - 1)]
            assert count_extensions_k(rows) == 1
