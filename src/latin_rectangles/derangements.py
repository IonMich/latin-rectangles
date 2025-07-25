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


def create_cycle_structure(cycle_lengths: list[int]) -> list[int]:
    """
    Create a derangement with a specific cycle structure.

    Args:
        cycle_lengths: List of desired cycle lengths

    Returns:
        1-indexed permutation with the specified cycle structure

    Raises:
        ValueError: If cycle_lengths contains a 1-cycle (would create fixed point)
    """
    if 1 in cycle_lengths:
        raise ValueError("Cycle structure cannot contain 1-cycles (would create fixed points)")
    
    n = sum(cycle_lengths)
    if n == 0:
        return [0]
    
    perm = [0] * (n + 1)  # 1-indexed with 0 at start
    current_pos = 1

    for cycle_len in cycle_lengths:
        # Get positions for this cycle
        cycle_positions = list(range(current_pos, current_pos + cycle_len))
        
        # Create the cycle: each position points to the next, last points to first
        for i in range(cycle_len):
            perm[cycle_positions[i]] = cycle_positions[(i + 1) % cycle_len]
        
        current_pos += cycle_len

    return perm


__all__ = ["find_cycle_decomposition", "generate_random_derangement", "create_cycle_structure"]
