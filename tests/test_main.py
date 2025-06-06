"""Tests for Latin rectangles extension counting algorithms."""

import pytest

from latin_rectangles import (
    count_extensions,
    find_cycle_decomposition,
    generate_random_derangement,
)
from latin_rectangles.__main__ import main


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


class TestMainFunction:
    """Test the main demonstration function."""

    def test_main_runs_without_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that main function runs without error and produces output."""
        main()
        captured = capsys.readouterr()
        assert "Latin Rectangles Extension Counter" in captured.out
        assert "Verifying results for n=8" in captured.out
        assert "Number of extensions:" in captured.out


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
