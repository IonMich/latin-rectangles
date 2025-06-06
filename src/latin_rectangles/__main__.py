"""Entry point for running the latin_rectangles package as a script."""

from .derangements import find_cycle_decomposition, generate_random_derangement
from .extension_counting import count_extensions


def main() -> None:
    """Main function demonstrating the Latin rectangle extension counting."""
    print("Latin Rectangles Extension Counter")
    print("=" * 40)

    # Example Usage for n=8
    print("--- Verifying results for n=8 ---")
    p_8 = [0, 2, 3, 4, 5, 6, 7, 8, 1]
    print(f"Permutation (8-cycle): Number of extensions: {count_extensions(p_8)}")

    p_6_2 = [0, 2, 3, 4, 5, 6, 1, 8, 7]
    print(f"Permutation (6,2-cycles): Number of extensions: {count_extensions(p_6_2)}")

    p_4_4 = [0, 2, 3, 4, 1, 6, 7, 8, 5]
    print(f"Permutation (4,4-cycles): Number of extensions: {count_extensions(p_4_4)}")

    p_2_2_2_2 = [0, 2, 1, 4, 3, 6, 5, 8, 7]
    print(
        f"Permutation (four 2-cycles): Number of extensions: {count_extensions(p_2_2_2_2)}"
    )

    # Example for a random derangement
    print("\n--- Example for a random derangement ---")
    n_random = 12
    random_p = generate_random_derangement(n_random)
    random_cycles = find_cycle_decomposition(random_p)
    cycle_lengths = sorted([len(c) for c in random_cycles])

    print(f"Generated a random derangement for n={n_random}")
    print(f"Cycle structure (lengths): {cycle_lengths}")
    print(f"Number of extensions: {count_extensions(random_p)}")


if __name__ == "__main__":
    main()
