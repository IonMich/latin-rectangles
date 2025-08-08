"""Latin rectangles extension counting algorithms."""

from .derangements import (
    create_cycle_structure,
    find_cycle_decomposition,
    generate_random_derangement,
)
from .extension_counting import count_extensions


def count_random_extensions(n: int) -> int:
    """
    Generate a random derangement of size n and count its extensions.

    This is a convenience function that combines random derangement generation
    with extension counting in a single call.

    Args:
        n: Size of the derangement (must be > 1)

    Returns:
        Number of extensions for the randomly generated derangement

    Raises:
        ValueError: If n <= 1 (no derangements exist)

    Example:
        >>> extensions = count_random_extensions(10)
        >>> print(f"Random derangement for n=10 has {extensions} extensions")
    """
    if n <= 1:
        raise ValueError("n must be greater than 1 for derangements to exist")

    random_derangement = generate_random_derangement(n)
    return count_extensions(random_derangement)


def count_cycle_structure_extensions(cycle_lengths: list[int]) -> int:
    """
    Count extensions for a derangement defined by a given cycle structure.

    This convenience function mirrors the CLI option `--c "a,b,c"` by
    constructing a 1-indexed derangement with the specified cycle lengths and
    returning the number of valid third rows.

    Args:
        cycle_lengths: List of cycle lengths (each >= 2). The sum is n.

    Returns:
        Number of extensions for the constructed derangement.

    Raises:
        ValueError: If the cycle_lengths include 1 (fixed points) or are invalid.
    """
    p = create_cycle_structure(cycle_lengths)
    return count_extensions(p)


# Export the main functions
__all__ = [
    "count_cycle_structure_extensions",
    "count_extensions",
    "count_random_extensions",
    "create_cycle_structure",
    "find_cycle_decomposition",
    "generate_random_derangement",
]
