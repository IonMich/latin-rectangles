"""Entry point for running the latin_rectangles package as a script."""

import argparse
import sys

from .derangements import (
    create_cycle_structure,
    find_cycle_decomposition,
    generate_random_derangement,
)
from .extension_counting import count_extensions


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

    p = create_cycle_structure(cycle_lengths)
    extensions = count_extensions(p)

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
        p = create_cycle_structure(cycle_lengths)
        extensions = count_extensions(p)
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
                    print(f"{i:2d}. {cycle_structure} → {extensions:,} extensions")

        elif args.n:
            # Generate random derangement mode
            n_val, cycle_lengths, extensions = count_random_extensions(args.n)
            print(f"🎲 Generated Random Derangement for n={n_val}")
            print(f"📊 Cycle structure: {cycle_lengths}")
            print(f"🔢 Number of extensions: {extensions:,}")
        elif args.c:
            # Specific cycle structure mode
            n_val, cycle_lengths, extensions = count_cycle_structure_extensions(args.c)
            print(f"⚙️  Specific Cycle Structure for n={n_val}")
            print(f"📊 Cycle structure: {cycle_lengths}")
            print(f"🔢 Number of extensions: {extensions:,}")
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
