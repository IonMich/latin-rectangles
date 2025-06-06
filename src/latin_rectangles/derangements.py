"""Functions for generating and working with derangements."""

import random


def generate_random_derangement(n: int) -> list[int]:
    """
    Quickly generates a random derangement of length n.
    A derangement is a permutation p of {1, ..., n} such that p[i] != i.

    Args:
        n: The size of the derangement.

    Returns:
        A list of length n+1 representing the derangement (1-indexed).

    Raises:
        ValueError: If n=1 (no derangements exist) or n < 0.
    """
    if n == 1:
        raise ValueError("No derangements exist for n=1.")
    if n < 0:
        raise ValueError("n must be non-negative.")
    if n == 0:
        return [0]

    while True:
        # Create a list of numbers from 1 to n
        p = list(range(1, n + 1))
        # Shuffle the list to get a random permutation
        random.shuffle(p)

        # Check if it's a derangement (p[i] != i+1 for 0-indexed list)
        is_derangement = True
        for i in range(n):
            if p[i] == i + 1:
                is_derangement = False
                break

        if is_derangement:
            # Prepend a 0 for 1-based indexing and return
            return [0, *p]


def find_cycle_decomposition(p: list[int]) -> list[list[int]]:
    """
    Finds the cycle decomposition of a permutation.
    Permutation p is 1-indexed, so p[0] is ignored.

    Args:
        p: 1-indexed permutation where p[0] is ignored.

    Returns:
        List of cycles, where each cycle is represented as a list of indices.
    """
    n = len(p) - 1
    visited = [False] * (n + 1)
    cycles = []
    for i in range(1, n + 1):
        if not visited[i]:
            current_cycle = []
            j = i
            while not visited[j]:
                visited[j] = True
                current_cycle.append(j)
                j = p[j]
            cycles.append(current_cycle)
    return cycles


__all__ = ["find_cycle_decomposition", "generate_random_derangement"]
