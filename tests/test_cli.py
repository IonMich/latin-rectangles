"""CLI path coverage tests for latin_rectangles.__main__.

These tests call main([...]) with explicit argv to exercise CLI code paths
without interfering with pytest's own arguments.
"""

import pytest

import latin_rectangles.__main__ as cli
from latin_rectangles.__main__ import (
    _decimal_digit_count,
    _format_extension_count,
    main,
)


def test_cli_random_derangement(capsys: pytest.CaptureFixture[str]) -> None:
    main(["--n", "4"])  # random derangement for n=4
    out = capsys.readouterr().out
    assert "Generated Random Derangement for n=4" in out
    assert "Cycle structure:" in out
    assert "Number of extensions after adding 1 row:" in out


def test_cli_specific_cycle(capsys: pytest.CaptureFixture[str]) -> None:
    main(["--c", "2,2"])  # specific cycle structure (n=4)
    out = capsys.readouterr().out
    assert "Specific Cycle Structure for n=4" in out
    assert "Cycle structure:" in out
    assert "Number of extensions after adding 1 row:" in out


def test_cli_specific_cycle_two_added_rows(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["--c", "3,4", "--rows-to-add", "2"])
    out = capsys.readouterr().out
    assert "Specific Cycle Structure for n=7" in out
    assert "Number of extensions after adding 2 rows:" in out
    assert "83,328" in out


def test_cli_enumerate_all(capsys: pytest.CaptureFixture[str]) -> None:
    main(["--n", "4", "--all"])  # enumerate for n=4
    out = capsys.readouterr().out
    assert "All Cycle Structures for n=4" in out
    assert "Found" in out


def test_format_extension_count_summarizes_large_values() -> None:
    huge_value = 10**500 + 123

    formatted = _format_extension_count(
        huge_value,
        max_digits=50,
        full_output=False,
    )

    assert _decimal_digit_count(huge_value) == 501
    assert "501 decimal digits" in formatted
    assert "leading=100" in formatted
    assert "trailing=000,000,000,000,000,000,000,123" in formatted
    assert "use --full-output" in formatted


def test_format_extension_count_honors_large_max_digits() -> None:
    huge_value = 10**5000 + 123

    formatted = _format_extension_count(
        huge_value,
        max_digits=5001,
        full_output=False,
    )

    assert formatted.startswith("100,000")
    assert formatted.endswith("123")
    assert "use --full-output" not in formatted


def test_cli_random_large_result_uses_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    huge_value = 10**500 + 123

    def fake_count_random_extensions(
        n: int, *, rows_to_add: int = 1
    ) -> tuple[int, list[int], int]:
        assert rows_to_add == 1
        return n, [2, n - 2], huge_value

    monkeypatch.setattr(cli, "count_random_extensions", fake_count_random_extensions)

    main(["--n", "1700", "--max-digits", "50"])
    out = capsys.readouterr().out

    assert "Generated Random Derangement for n=1700" in out
    assert "501 decimal digits" in out
    assert "use --full-output" in out
