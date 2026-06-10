"""Entry point for running the latin_rectangles package as a script."""

import argparse
import math
import sys

from .derangements import (
    find_cycle_decomposition,
    generate_random_derangement,
)
from .extension_counting import (
    count_cycle_structure_extensions as count_cycle_structure_extensions_from_lengths,
)
from .extension_counting import (
    count_extensions,
)

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
    """Format an extension count safely for CLI output."""
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


def count_random_extensions(n: int) -> tuple[int, list[int], int]:
    """
    Generate a random derangement and count its extensions.

    Args:
        n: Size of the derangement

    Returns:
        Tuple of (n, cycle_lengths, extensions_count)
    """
    if n <= 1:
        raise ValueError("n must be greater than 1 for derangements to exist")

    random_p = generate_random_derangement(n)
    random_cycles = find_cycle_decomposition(random_p)
    cycle_lengths = sorted([len(c) for c in random_cycles])
    extensions = count_extensions(random_p)

    return n, cycle_lengths, extensions


def count_cycle_structure_extensions(
    cycle_structure: str,
) -> tuple[int, list[int], int]:
    """
    Create a derangement with specific cycle structure and count its extensions.

    Args:
        cycle_structure: Comma-separated cycle lengths (e.g., "2,2,4")

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

    extensions = count_cycle_structure_extensions_from_lengths(cycle_lengths)

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


def enumerate_all_extensions(n: int) -> list[tuple[list[int], int]]:
    """
    Enumerate all possible cycle structures for n and count their extensions.

    Args:
        n: Size of the derangement

    Returns:
        List of tuples (cycle_structure, extensions_count) sorted by extensions_count
    """
    structures = generate_all_cycle_structures(n)
    results = []

    for cycle_lengths in structures:
        extensions = count_cycle_structure_extensions_from_lengths(cycle_lengths)
        results.append((cycle_lengths, extensions))

    # Sort by extensions count (descending), then by cycle structure
    results.sort(key=lambda x: (-x[1], x[0]))
    return results


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments and run. If argv is None, use sys.argv[1:]."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Latin Rectangles Extension Counter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --n 42             # Generate random derangement for n=42
  %(prog)s --c "2,2,4"        # Use specific cycle structure: two 2-cycles and one 4-cycle
  %(prog)s --c "8"            # Single 8-cycle
  %(prog)s --c "2,2,2,2"      # Four 2-cycles
  %(prog)s --n 8 --all        # Enumerate all possible cycle structures for n=8
        """,
    )
    # Add --n option for backward compatibility
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
        "--max-digits",
        type=_positive_int,
        default=_DEFAULT_MAX_OUTPUT_DIGITS,
        help=(
            "Maximum decimal digits to print exactly before summarizing a count "
            f"(default: {_DEFAULT_MAX_OUTPUT_DIGITS})"
        ),
    )
    parser.add_argument(
        "--full-output",
        action="store_true",
        help="Print the full decimal count even when it has thousands of digits",
    )

    args = parser.parse_args(argv)

    if args.n and args.c:
        print("❌ Error: Cannot specify both --n and --c arguments", file=sys.stderr)
        sys.exit(1)

    if args.c and args.all:
        print(
            "❌ Error: Cannot use --all with --c (use --all with --n)", file=sys.stderr
        )
        sys.exit(1)

    if not args.n and not args.c:
        parser.print_help()
        sys.exit(1)

    try:
        if args.n and args.all:
            # Enumerate all cycle structures mode
            results = enumerate_all_extensions(args.n)
            if not results:
                print(f"❌ No valid cycle structures found for n={args.n}")
                sys.exit(1)

            print(f"🔍 All Cycle Structures for n={args.n}")
            print(
                f"📊 Found {len(results)} possible structures with non-zero extensions:"
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

        elif args.n:
            # Generate random derangement mode
            n_val, cycle_lengths, extensions = count_random_extensions(args.n)
            print(f"🎲 Generated Random Derangement for n={n_val}")
            print(f"📊 Cycle structure: {cycle_lengths}")
            print(
                "🔢 Number of extensions: "
                f"{_format_extension_count(extensions, max_digits=args.max_digits, full_output=args.full_output)}"
            )
        elif args.c:
            # Specific cycle structure mode
            n_val, cycle_lengths, extensions = count_cycle_structure_extensions(args.c)
            print(f"⚙️  Specific Cycle Structure for n={n_val}")
            print(f"📊 Cycle structure: {cycle_lengths}")
            print(
                "🔢 Number of extensions: "
                f"{_format_extension_count(extensions, max_digits=args.max_digits, full_output=args.full_output)}"
            )
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
