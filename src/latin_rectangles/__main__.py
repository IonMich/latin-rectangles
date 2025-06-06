"""Entry point for running the latin_rectangles package as a script."""

import argparse
import sys

from .derangements import find_cycle_decomposition, generate_random_derangement
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


def main() -> None:
    """Main function with command-line interface for Latin rectangle extension counting."""
    parser = argparse.ArgumentParser(
        description="Latin Rectangles Extension Counter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run demo with predefined examples
  %(prog)s --n 12             # Generate random derangement for n=12
  %(prog)s generate 15        # Generate random derangement for n=15
  %(prog)s demo               # Run demo examples
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add generate subcommand
    generate_parser = subparsers.add_parser(
        "generate", help="Generate random derangement and count extensions"
    )
    generate_parser.add_argument(
        "n", type=int, help="Size of the derangement (must be > 1)"
    )

    # Add demo subcommand
    subparsers.add_parser("demo", help="Run demonstration with predefined examples")

    # Add --n option for backward compatibility
    parser.add_argument("--n", type=int, help="Size of the derangement (must be > 1)")

    args = parser.parse_args()

    if args.command == "generate" or args.n:
        # Generate random derangement mode
        n = args.n if args.command != "generate" else args.n

        try:
            n_val, cycle_lengths, extensions = count_random_extensions(n)
            print(f"🎲 Random Derangement for n={n_val}")
            print(f"📊 Cycle structure: {cycle_lengths}")
            print(f"🔢 Number of extensions: {extensions:,}")
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "demo":
        # Run demo mode
        run_demo()

    else:
        # Default: run demo if no arguments provided
        run_demo()


def run_demo() -> None:
    """Run the demonstration with predefined examples."""
    print("Latin Rectangles Extension Counter")
    print("=" * 40)

    # Example Usage for n=8
    print("--- Verifying results for n=8 ---")
    p_8 = [0, 2, 3, 4, 5, 6, 7, 8, 1]
    print(f"Permutation (8-cycle): Number of extensions: {count_extensions(p_8):,}")

    p_6_2 = [0, 2, 3, 4, 5, 6, 1, 8, 7]
    print(
        f"Permutation (6,2-cycles): Number of extensions: {count_extensions(p_6_2):,}"
    )

    p_4_4 = [0, 2, 3, 4, 1, 6, 7, 8, 5]
    print(
        f"Permutation (4,4-cycles): Number of extensions: {count_extensions(p_4_4):,}"
    )

    p_2_2_2_2 = [0, 2, 1, 4, 3, 6, 5, 8, 7]
    print(
        f"Permutation (four 2-cycles): Number of extensions: {count_extensions(p_2_2_2_2):,}"
    )

    # Example for a random derangement
    print("\n--- Example for a random derangement ---")
    n_random = 12
    n_val, cycle_lengths, extensions = count_random_extensions(n_random)

    print(f"Generated a random derangement for n={n_val}")
    print(f"Cycle structure (lengths): {cycle_lengths}")
    print(f"Number of extensions: {extensions:,}")

    print("\n💡 Try: 'latin-rectangles --n 15' for a custom size!")
    print("💡 Try: 'latin-rectangles generate 20' for larger examples!")


if __name__ == "__main__":
    main()
