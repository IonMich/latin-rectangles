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


@pytest.mark.parametrize(("n", "rows_to_add"), [(2, 1), (3, 2), (4, 3)])
def test_cli_all_reports_zero_when_no_extensions_exist(
    n: int, rows_to_add: int, capsys: pytest.CaptureFixture[str]
) -> None:
    """There cannot be more than n rows in a nonempty Latin rectangle."""
    main(["--n", str(n), "--all", "--rows-to-add", str(rows_to_add)])
    output = capsys.readouterr().out
    assert "Found 0 possible structures with non-zero extensions" in output
    assert "→" not in output


def test_cli_all_zero_added_rows_still_has_one_empty_extension(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["--n", "2", "--all", "--rows-to-add", "0"])
    output = capsys.readouterr().out
    assert "Found 1 possible structures" in output
    assert "[2] → 1 extensions" in output


@pytest.mark.parametrize(
    "argv",
    [["--n", "0", "--c", "2,2"], ["--n", "4", "--c", ""], ["--c", "", "--all"]],
)
def test_cli_conflicts_are_based_on_option_presence(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as error:
        main(argv)
    assert error.value.code == 1
    captured = capsys.readouterr()
    assert "Cannot" in captured.err
    assert captured.out == ""


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


@pytest.mark.parametrize(
    ("rows", "columns", "expected"),
    [(0, 0, 1), (0, 3, 1), (3, 0, 1), (4, 3, 0), (2, 3, 12), (4, 4, 576)],
)
def test_cli_total_counts_labeled_rectangles(
    rows: int, columns: int, expected: int, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["total", "-r", str(rows), "-c", str(columns)])
    captured = capsys.readouterr()
    assert captured.out == (
        f"Latin rectangles: {rows} rows, {columns} columns\n"
        f"Total labeled count: {expected:,}\n"
    )
    assert captured.err == ""


def test_cli_total_passes_requested_dimensions(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def count_total(rows: int, columns: int) -> int:
        assert (rows, columns) == (4, 20)
        return 1_234_567

    monkeypatch.setattr(cli, "count_latin_rectangles", count_total)
    main(["total", "--rows", "4", "--columns", "20"])
    assert "Total labeled count: 1,234,567" in capsys.readouterr().out


@pytest.mark.parametrize(
    "argv", [["total"], ["total", "-r", "2"], ["total", "-c", "3"]]
)
def test_cli_total_requires_both_dimensions(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as error:
        main(argv)
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert "required" in captured.err
    assert captured.out == ""


@pytest.mark.parametrize(
    ("rows", "columns"),
    [("-1", "3"), ("2", "-1"), ("1.5", "3"), ("2", "2,2"), ("four", "20")],
)
def test_cli_total_rejects_invalid_dimensions(
    rows: str, columns: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as error:
        main(["total", "-r", rows, "-c", columns])
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert "integer" in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == ""


@pytest.mark.parametrize(
    "legacy_options",
    [["--n", "4"], ["--c", "4"], ["--all"], ["--rows-to-add", "1"]],
)
@pytest.mark.parametrize("before_command", [False, True])
def test_cli_total_rejects_legacy_options(
    legacy_options: list[str],
    before_command: bool,
    capsys: pytest.CaptureFixture[str],
) -> None:
    total_options = ["total", "-r", "2", "-c", "4"]
    argv = (
        legacy_options + total_options
        if before_command
        else total_options + legacy_options
    )
    with pytest.raises(SystemExit) as error:
        main(argv)
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert captured.out == ""


@pytest.mark.parametrize("before_command", [False, True])
@pytest.mark.parametrize("full_output", [False, True])
def test_cli_total_uses_shared_output_controls(
    before_command: bool,
    full_output: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    huge_value = 10**500 + 123
    monkeypatch.setattr(cli, "count_latin_rectangles", lambda rows, columns: huge_value)
    output_options = ["--max-digits", "50"]
    if full_output:
        output_options.append("--full-output")
    total_options = ["total", "-r", "4", "-c", "20"]
    argv = (
        output_options + total_options
        if before_command
        else total_options + output_options
    )
    main(argv)
    output = capsys.readouterr().out
    if full_output:
        assert f"Total labeled count: {huge_value:,}\n" in output
        assert "decimal digits" not in output
    else:
        assert "Total labeled count: 501 decimal digits" in output
        assert "use --full-output" in output


def test_cli_total_reports_counting_errors_cleanly(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def count_total(rows: int, columns: int) -> int:
        raise ValueError("Unsupported counting regime")

    monkeypatch.setattr(cli, "count_latin_rectangles", count_total)
    with pytest.raises(SystemExit) as error:
        main(["total", "-r", "4", "-c", "20"])
    assert error.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Unsupported counting regime" in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == ""


@pytest.mark.parametrize("argv", [["--help"], ["total", "--help"]])
def test_cli_help_describes_total(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as error:
        main(argv)
    assert error.value.code == 0
    output = capsys.readouterr().out
    assert "total" in output
    assert "labeled" in output
    if argv[0] == "total":
        assert "--rows" in output
        assert "--columns" in output
        assert "--max-digits" in output
        assert "--full-output" in output


@pytest.mark.parametrize("argv", [["--n", "1"], ["--c", "total"]])
def test_cli_legacy_validation_preserves_error_exit(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as error:
        main(argv)
    assert error.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert captured.out == ""


def test_cli_no_arguments_preserves_help_exit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as error:
        main([])
    assert error.value.code == 1
    captured = capsys.readouterr()
    assert "usage:" in captured.out
    assert captured.err == ""
