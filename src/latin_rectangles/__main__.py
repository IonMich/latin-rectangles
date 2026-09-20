"""Entry point for running the latin_rectangles package as a script."""

import argparse
import math
import sys

from .derangements import (
    find_cycle_decomposition,
    generate_random_derangement,
)
from .extension_counting import (
    count_extensions_from_cycle_type as count_extensions_from_cycle_type_lengths,
)
from .extension_counting import (
    count_extensions_from_derangement,
)
from .total_counting import count_latin_rectangles

_COUNT_SUMMARY_MODULUS = 1_000_000_007
_DEFAULT_MAX_OUTPUT_DIGITS = 1_000
_SUMMARY_EDGE_DIGITS = 24


def _positive_int(raw: str) -> int:
    """Parse a positive CLI integer."""
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Expected an integer, got {raw!r}") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("Expected a positive integer")
    return value


def _non_negative_int(raw: str) -> int:
    """Parse a non-negative CLI integer."""
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Expected an integer, got {raw!r}") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("Expected a non-negative integer")
    return value


def _row_label(count: int) -> str:
    return "row" if count == 1 else "rows"


def _group_decimal_text(text: str) -> str:
    """Add thousands separators to a decimal string."""
    sign = ""
    if text.startswith("-"):
        sign = "-"
        text = text[1:]
    groups: list[str] = []
    while text:
        groups.append(text[-3:])
        text = text[:-3]
    return sign + ",".join(reversed(groups))


def _decimal_digit_count(value: int) -> int:
    """Return the exact number of decimal digits without converting to str."""
    value = abs(value)
    if value < 10:
        return 1

    digits = int((value.bit_length() - 1) * math.log10(2)) + 1
    if value >= 10**digits:
        digits += 1
    elif value < 10 ** (digits - 1):
        digits -= 1
    return digits


def _allow_full_integer_output() -> None:
    """Disable Python's decimal int conversion guard for explicit full output."""
    if hasattr(sys, "set_int_max_str_digits"):
        sys.set_int_max_str_digits(0)


def _allow_integer_output_digits(digits: int) -> None:
    """Raise Python's decimal int conversion guard when the CLI opted in."""
    if not hasattr(sys, "get_int_max_str_digits"):
        return
    current_limit = sys.get_int_max_str_digits()
    if current_limit == 0 or digits <= current_limit:
        return
    sys.set_int_max_str_digits(max(digits, 640))


def _format_extension_count(value: int, *, max_digits: int, full_output: bool) -> str:
    """Format an integer count safely for CLI output."""
    if full_output:
        _allow_full_integer_output()
        return f"{value:,}"

    digits = _decimal_digit_count(value)
    if digits <= max_digits:
        _allow_integer_output_digits(digits)
        return f"{value:,}"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""
    edge_digits = min(_SUMMARY_EDGE_DIGITS, digits)
    leading = abs_value // 10 ** (digits - edge_digits)
    trailing = abs_value % (10**edge_digits)
    leading_text = _group_decimal_text(str(leading))
    trailing_text = _group_decimal_text(str(trailing).zfill(edge_digits))

    return (
        f"{digits:,} decimal digits "
        f"(bits={value.bit_length():,}; "
        f"leading={sign}{leading_text}; "
        f"trailing={trailing_text}; "
        f"mod {_COUNT_SUMMARY_MODULUS:,}={value % _COUNT_SUMMARY_MODULUS:,}; "
        "use --full-output to print all digits)"
    )


def count_random_extensions(
    n: int, *, rows_to_add: int = 1
) -> tuple[int, list[int], int]:
    """
    Generate a random derangement and count its extensions.

    Args:
        n: Size of the derangement
        rows_to_add: Number of further rows to add.

    Returns:
        Tuple of (n, cycle_lengths, extensions_count)
    """
    if n <= 1:
        raise ValueError("n must be greater than 1 for derangements to exist")

    random_p = generate_random_derangement(n)
    random_cycles = find_cycle_decomposition(random_p)
    cycle_lengths = sorted([len(c) for c in random_cycles])
    extensions = count_extensions_from_derangement(
        random_p,
        rows_to_add=rows_to_add,
    )

    return n, cycle_lengths, extensions


def count_extensions_for_cycle_type(
    cycle_structure: str,
    *,
    rows_to_add: int = 1,
) -> tuple[int, list[int], int]:
    """
    Create a derangement with specific cycle structure and count its extensions.

    Args:
        cycle_structure: Comma-separated cycle lengths (e.g., "2,2,4")
        rows_to_add: Number of further rows to add.

    Returns:
        Tuple of (n, cycle_lengths, extensions_count)
    """
    try:
        cycle_lengths = [int(x.strip()) for x in cycle_structure.split(",")]
    except ValueError as exc:
        raise ValueError("Cycle structure must be comma-separated integers") from exc
    if not cycle_lengths:
        raise ValueError("Cycle structure cannot be empty")

    n = sum(cycle_lengths)
    if n <= 1:
        raise ValueError("Total size must be greater than 1")

    extensions = count_extensions_from_cycle_type_lengths(
        cycle_lengths,
        rows_to_add=rows_to_add,
    )

    return n, sorted(cycle_lengths), extensions


def generate_all_cycle_structures(n: int) -> list[list[int]]:
    """
    Generate all valid cycle structures (partitions) for a derangement of size n.
    Only includes partitions where all parts are ≥ 2 (no 1-cycles).

    Args:
        n: Size of the derangement

    Returns:
        List of cycle structures, each as a sorted list of cycle lengths
    """

    def partitions_with_min_part(
        target: int, min_part: int, current: list[int]
    ) -> list[list[int]]:
        """Generate partitions of target where all parts are >= min_part."""
        if target == 0:
            return [current[:]]

        if target < min_part:
            return []

        result = []
        for part_size in range(min_part, target + 1):
            current.append(part_size)
            result.extend(
                partitions_with_min_part(target - part_size, part_size, current)
            )
            current.pop()

        return result

    if n <= 1:
        return []

    # Generate all partitions where each part is at least 2
    partitions = partitions_with_min_part(n, 2, [])

    # Sort each partition for consistent output
    return [sorted(partition) for partition in partitions]


def enumerate_all_extensions(
    n: int, *, rows_to_add: int = 1
) -> list[tuple[list[int], int]]:
    """
    Enumerate all possible cycle structures for n and count their extensions.

    Args:
        n: Size of the derangement
        rows_to_add: Number of further rows to add.

    Returns:
        List of tuples (cycle_structure, extensions_count) sorted by extensions_count
    """
    structures = generate_all_cycle_structures(n)
    results = []

    for cycle_lengths in structures:
        extensions = count_extensions_from_cycle_type_lengths(
            cycle_lengths,
            rows_to_add=rows_to_add,
        )
        results.append((cycle_lengths, extensions))

    # Sort by extensions count (descending), then by cycle structure
    results.sort(key=lambda x: (-x[1], x[0]))
    return results


def _add_output_arguments(
    parser: argparse.ArgumentParser, *, inherit_defaults: bool = False
) -> None:
    """Share output controls without replacing values parsed before a subcommand."""
    parser.add_argument(
        "--max-digits",
        type=_positive_int,
        default=(argparse.SUPPRESS if inherit_defaults else _DEFAULT_MAX_OUTPUT_DIGITS),
        help=(
            "Maximum decimal digits to print exactly before summarizing a count "
            f"(default: {_DEFAULT_MAX_OUTPUT_DIGITS})"
        ),
    )
    parser.add_argument(
        "--full-output",
        action="store_true",
        default=argparse.SUPPRESS if inherit_defaults else False,
        help="Print the full decimal count even when it has thousands of digits",
    )


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments and run. If argv is None, use sys.argv[1:]."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Latin Rectangles Counter: total labeled counts and extensions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s total -r 4 -c 20  # Count all labeled 4-row, 20-column Latin rectangles
  %(prog)s --n 42             # Generate random derangement for n=42
  %(prog)s --c "2,2,4"        # Use specific cycle structure: two 2-cycles and one 4-cycle
  %(prog)s --c "3,4" --rows-to-add 2
  %(prog)s --c "8"            # Single 8-cycle
  %(prog)s --c "2,2,2,2"      # Four 2-cycles
  %(prog)s --n 8 --all        # Enumerate all possible cycle structures for n=8
        """,
    )
    parser.add_argument("--n", type=int, help="Size of the derangement (must be > 1)")
    parser.add_argument(
        "--c",
        type=str,
        help="Cycle structure as comma-separated integers (e.g., '2,2,4' for two 2-cycles and one 4-cycle)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Enumerate all possible cycle structures for given n (use with --n)",
    )
    parser.add_argument(
        "--rows-to-add",
        type=_non_negative_int,
        default=None,
        help="Number of further rows to add to the starting 2 x n rectangle",
    )
    _add_output_arguments(parser)
    subcommands = parser.add_subparsers(dest="command")
    total_parser = subcommands.add_parser(
        "total",
        allow_abbrev=False,
        help="Count all labeled Latin rectangles of the given dimensions",
        description=(
            "Count all Latin rectangles with ordered rows, labeled columns, and "
            "symbols 1 through the number of columns. Dimensions are non-negative; "
            "an empty rectangle has count 1."
        ),
    )
    total_parser.add_argument(
        "-r", "--rows", type=_non_negative_int, required=True, help="Number of rows"
    )
    total_parser.add_argument(
        "-c",
        "--columns",
        type=_non_negative_int,
        required=True,
        help="Number of columns and available symbols",
    )
    _add_output_arguments(total_parser, inherit_defaults=True)

    args = parser.parse_args(argv)

    if args.command == "total":
        if (
            args.n is not None
            or args.c is not None
            or args.all
            or args.rows_to_add is not None
        ):
            parser.error(
                "total cannot be combined with --n, --c, --all, or --rows-to-add"
            )
        try:
            count = count_latin_rectangles(args.rows, args.columns)
        except ValueError as exc:
            print(f"❌ Error: {exc}", file=sys.stderr)
            sys.exit(1)
        formatted_count = _format_extension_count(
            count, max_digits=args.max_digits, full_output=args.full_output
        )
        print(f"Latin rectangles: {args.rows} rows, {args.columns} columns")
        print(f"Total labeled count: {formatted_count}")
        return

    if args.rows_to_add is None:
        args.rows_to_add = 1

    if args.n is not None and args.c is not None:
        print("❌ Error: Cannot specify both --n and --c arguments", file=sys.stderr)
        sys.exit(1)

    if args.c is not None and args.all:
        print(
            "❌ Error: Cannot use --all with --c (use --all with --n)", file=sys.stderr
        )
        sys.exit(1)

    if args.n is None and args.c is None:
        parser.print_help()
        sys.exit(1)

    try:
        if args.n is not None and args.all:
            # Enumerate all cycle structures mode
            results = enumerate_all_extensions(
                args.n,
                rows_to_add=args.rows_to_add,
            )
            if not results:
                print(f"❌ No valid cycle structures found for n={args.n}")
                sys.exit(1)

            print(f"🔍 All Cycle Structures for n={args.n}")
            positive_count = sum(extensions > 0 for _, extensions in results)
            print(
                f"📊 Found {positive_count} possible structures with non-zero extensions "
                f"after adding {args.rows_to_add} {_row_label(args.rows_to_add)}:"
            )
            print()

            for i, (cycle_structure, extensions) in enumerate(results, 1):
                if extensions > 0:  # Only show structures with non-zero extensions
                    formatted_extensions = _format_extension_count(
                        extensions,
                        max_digits=args.max_digits,
                        full_output=args.full_output,
                    )
                    print(
                        f"{i:2d}. {cycle_structure} → {formatted_extensions} extensions"
                    )

        elif args.n is not None:
            # Generate random derangement mode
            n_val, cycle_lengths, extensions = count_random_extensions(
                args.n,
                rows_to_add=args.rows_to_add,
            )
            print(f"🎲 Generated Random Derangement for n={n_val}")
            print(f"📊 Cycle structure: {cycle_lengths}")
            print(
                f"🔢 Number of extensions after adding {args.rows_to_add} "
                f"{_row_label(args.rows_to_add)}: "
                f"{_format_extension_count(extensions, max_digits=args.max_digits, full_output=args.full_output)}"
            )
        elif args.c is not None:
            # Specific cycle structure mode
            n_val, cycle_lengths, extensions = count_extensions_for_cycle_type(
                args.c,
                rows_to_add=args.rows_to_add,
            )
            print(f"⚙️  Specific Cycle Structure for n={n_val}")
            print(f"📊 Cycle structure: {cycle_lengths}")
            print(
                f"🔢 Number of extensions after adding {args.rows_to_add} "
                f"{_row_label(args.rows_to_add)}: "
                f"{_format_extension_count(extensions, max_digits=args.max_digits, full_output=args.full_output)}"
            )
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
