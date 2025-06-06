"""Latin rectangles extension counting algorithms."""

from .derangements import find_cycle_decomposition, generate_random_derangement
from .extension_counting import count_extensions

# Export the main functions
__all__ = [
    "count_extensions",
    "find_cycle_decomposition",
    "generate_random_derangement",
]
