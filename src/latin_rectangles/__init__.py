"""Latin rectangles extension counting algorithms."""

from .derangements import (
    create_cycle_structure,
    find_cycle_decomposition,
    generate_random_derangement,
)
from .extension_counting import (
    CycleStructureMethod,
    count_extensions_from_cycle_type,
    count_extensions_from_derangement,
)
from .general_extensions import count_extensions, count_next_row_extensions


def count_random_extensions(n: int, *, rows_to_add: int = 1) -> int:
    """
    Generate a random derangement of size n and count ordered extensions.

    This is a convenience function that combines random derangement generation
    with extension counting in a single call.

    Args:
        n: Size of the derangement (must be > 1)
        rows_to_add: Number of further rows to add.

    Returns:
        Number of ordered extensions for the randomly generated derangement

    Raises:
        ValueError: If n <= 1 (no derangements exist)

    Example:
        >>> extensions = count_random_extensions(10, rows_to_add=1)
        >>> print(f"Random derangement for n=10 has {extensions} extensions")
    """
    if n <= 1:
        raise ValueError("n must be greater than 1 for derangements to exist")

    random_derangement = generate_random_derangement(n)
    return count_extensions_from_derangement(
        random_derangement,
        rows_to_add=rows_to_add,
    )


# Export the main functions
__all__ = [
    "CycleStructureMethod",
    "count_extensions",
    "count_extensions_from_cycle_type",
    "count_extensions_from_derangement",
    "count_next_row_extensions",
    "count_random_extensions",
    "create_cycle_structure",
    "find_cycle_decomposition",
    "generate_random_derangement",
]
