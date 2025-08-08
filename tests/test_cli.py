"""CLI path coverage tests for latin_rectangles.__main__.

These tests call main([...]) with explicit argv to exercise CLI code paths
without interfering with pytest's own arguments.
"""

import pytest

from latin_rectangles.__main__ import main


def test_cli_random_derangement(capsys: pytest.CaptureFixture[str]) -> None:
    main(["--n", "4"])  # random derangement for n=4
    out = capsys.readouterr().out
    assert "Generated Random Derangement for n=4" in out
    assert "Cycle structure:" in out
    assert "Number of extensions:" in out


def test_cli_specific_cycle(capsys: pytest.CaptureFixture[str]) -> None:
    main(["--c", "2,2"])  # specific cycle structure (n=4)
    out = capsys.readouterr().out
    assert "Specific Cycle Structure for n=4" in out
    assert "Cycle structure:" in out
    assert "Number of extensions:" in out


def test_cli_enumerate_all(capsys: pytest.CaptureFixture[str]) -> None:
    main(["--n", "4", "--all"])  # enumerate for n=4
    out = capsys.readouterr().out
    assert "All Cycle Structures for n=4" in out
    assert "Found" in out
