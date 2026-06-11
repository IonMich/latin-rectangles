"""General extension counting for Latin rectangles.

This module implements exact counting algorithms for extending a k x n Latin
rectangle by one or more rows, given the existing k rows as permutations
sigma1..sigmak.

We assume the first row can be standardized to the identity by simultaneous
conjugation (this preserves the count). The number of valid next rows equals
the permanent of the n x n 0-1 matrix A with A[i,j] = 1 iff i is not in {sigma_r(j)}.

We compute it via rook/matching polynomials of the forbidden bipartite graph F
with edges (j, sigma_r(j)) for r=1..k:
    per(A) = sum_{t=0}^n (-1)^t r_t (n-t)!
where r_t is the number of size-t matchings in F. The rook polynomial R_F(x)
factors over the connected components of F; with sigma1=id, components are the orbits
of G = <sigma2,...,sigmak> acting on [n]. We exploit this factorization and compute each
component's matching polynomial with a branching DP.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import cache
from itertools import permutations

from .rook_polynomials import multiply_polynomials, multiply_polynomials_fft


def _is_identity_row(row: list[int]) -> bool:
    """Check if a 1-indexed permutation row is identity."""
    n = len(row) - 1
    if n < 0:
        return False
    return all(row[i] == i for i in range(1, n + 1))


def _validate_rows_to_add(rows_to_add: int) -> None:
    if rows_to_add < 0:
        raise ValueError("rows_to_add must be non-negative")


def _validate_permutation_row(row: list[int]) -> int:
    """Validate a 1-indexed permutation row and return n."""
    n = len(row) - 1
    if n < 0 or not row or row[0] != 0:
        raise ValueError("Rows must be 1-indexed permutations with row[0] == 0")
    if set(row[1:]) != set(range(1, n + 1)):
        raise ValueError("Rows must be valid permutations of 1..n")
    return n


def _validate_latin_rows(rows: list[list[int]]) -> int:
    """Validate rows as a 1-indexed Latin rectangle and return n."""
    if not rows:
        raise ValueError("Provide at least one row")

    n = _validate_permutation_row(rows[0])
    for row in rows[1:]:
        if len(row) != n + 1:
            raise ValueError("All rows must have the same length")
        _validate_permutation_row(row)

    for column in range(1, n + 1):
        symbols = [row[column] for row in rows]
        if len(set(symbols)) != len(symbols):
            raise ValueError("Rows must form a Latin rectangle")

    return n


def _invert_perm(p: list[int]) -> list[int]:
    """Return the inverse of a 1-indexed permutation p (p[0] is ignored)."""
    n = len(p) - 1
    inv = [0] * (n + 1)
    for i in range(1, n + 1):
        inv[p[i]] = i
    return inv


def _compose_perm(a: list[int], b: list[int]) -> list[int]:
    """Return composition a∘b (apply b then a), 1-indexed."""
    n = len(a) - 1
    out = [0] * (n + 1)
    for i in range(1, n + 1):
        out[i] = a[b[i]]
    return out


def _standardize_rows(rows: list[list[int]]) -> list[list[int]]:
    """Simultaneously conjugate rows so that the first becomes identity.

    Args:
        rows: list of k permutations (1-indexed lists of length n+1)

    Returns:
        New list of permutations with first row equal to identity.
    """
    if not rows:
        raise ValueError("At least one row (the first) is required")

    n = len(rows[0]) - 1
    if any(len(r) != n + 1 for r in rows):
        raise ValueError("All rows must have the same length (1-indexed permutations)")

    if _is_identity_row(rows[0]):
        return [r[:] for r in rows]

    pi = _invert_perm(rows[0])  # relabel symbols by pi = (sigma1)^{-1}
    # Apply π to outputs of every row
    return [[0] + [pi[r[j]] for j in range(1, n + 1)] for r in rows]


def _compute_orbits(generators: list[list[int]]) -> list[list[int]]:
    """Compute orbits of subgroup <generators> acting on [n].

    Each generator is a 1-indexed permutation of length n+1. Inverses are
    included implicitly.
    """
    if not generators:
        return []
    n = len(generators[0]) - 1
    invs = [_invert_perm(g) for g in generators]

    seen = [False] * (n + 1)
    orbits: list[list[int]] = []
    for start in range(1, n + 1):
        if seen[start]:
            continue
        orbit = []
        stack = [start]
        seen[start] = True
        while stack:
            u = stack.pop()
            orbit.append(u)
            for g, gi in zip(generators, invs, strict=True):
                for perm in (g, gi):
                    v = perm[u]
                    if not seen[v]:
                        seen[v] = True
                        stack.append(v)
        orbits.append(sorted(orbit))
    return orbits


def _least_significant_bit_index(mask: int) -> int:
    """Return index (0-based) of least significant set bit in mask."""
    return (mask & -mask).bit_length() - 1


def _add_poly(a: list[int], b: list[int]) -> list[int]:
    if len(b) > len(a):
        a, b = b, a
    out = a[:]
    for i, v in enumerate(b):
        out[i] += v
    return out


def _shift_x(poly: list[int]) -> list[int]:
    """Multiply polynomial by x (shift right)."""
    return [0, *poly]


def _component_matching_polynomial(neigh_masks: list[int], m: int) -> list[int]:
    """Compute R_component(x) for a bipartite component of size m.

    left vertices are 0..m-1, right vertices are 0..m-1.
    neigh_masks[i] is a bitmask of right neighbors of left i.
    """

    @cache
    def dp(lmask: int, rmask: int) -> tuple[int, ...]:
        # If no left vertices remain, only empty matching
        if lmask == 0:
            return (1,)
        # Choose a left vertex u
        u = _least_significant_bit_index(lmask)
        # Exclude u
        poly_excl = list(dp(lmask & ~(1 << u), rmask))
        # Include one edge u-v for v in N(u)
        nmask = neigh_masks[u] & rmask
        if nmask == 0:
            return tuple(poly_excl)
        # Sum over neighbors
        poly_incl: list[int] = [0]
        while nmask:
            v = _least_significant_bit_index(nmask)
            nmask &= ~(1 << v)
            poly_sub = list(dp(lmask & ~(1 << u), rmask & ~(1 << v)))
            poly_incl = _add_poly(poly_incl, poly_sub)
        poly_incl = _shift_x(poly_incl)
        # Combine
        res = _add_poly(poly_excl, poly_incl)
        return tuple(res)

    full_l = (1 << m) - 1
    full_r = (1 << m) - 1
    return list(dp(full_l, full_r))


def _derangement_number(n: int) -> int:
    """Return the number of derangements of n symbols."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return 1
    prev2 = 1  # !0
    prev1 = 0  # !1
    for k in range(2, n + 1):
        prev2, prev1 = prev1, (k - 1) * (prev1 + prev2)
    return prev1


def _iter_valid_next_rows(rows: list[list[int]]) -> Iterator[list[int]]:
    """Yield all valid next rows extending the explicit Latin rectangle."""
    n = _validate_latin_rows(rows)
    used_by_column: list[set[int]] = [set() for _ in range(n + 1)]
    for row in rows:
        for column in range(1, n + 1):
            used_by_column[column].add(row[column])

    for candidate in permutations(range(1, n + 1)):
        if all(
            candidate[column - 1] not in used_by_column[column]
            for column in range(1, n + 1)
        ):
            yield [0, *candidate]


def count_next_row_extensions(rows: list[list[int]], *, use_fft: bool = False) -> int:
    """Count extensions from k x n to (k+1) x n given k rows.

    Args:
        rows: List of k permutations, each a 1-indexed list of length n+1.
              The first row may be non-identity; it will be standardized.
        use_fft: Use exact NTT/CRT convolution for large polynomial products.

    Returns:
        The number of valid extensions (permanent of the allowed matrix).

    Notes:
        - With one existing row, this returns the derangement number in O(n).
        - With multiple rows, exact worst-case time is exponential in the size
          of the largest orbit of <sigma2,...,sigmak> (as expected from
          #P-completeness).
        - It is fast on inputs whose orbits are small; otherwise it will be slow.
        - use_fft=True uses exact transform-based multiplication, not the old
          floating-point convolution path.
    """
    n = _validate_latin_rows(rows)
    k = len(rows)
    if n <= 0:
        return 1  # empty permutation → exactly one empty extension
    if k == 1:
        return _derangement_number(n)

    std_rows = _standardize_rows(rows)
    # Generators for orbit computation exclude the first identity row
    generators = std_rows[1:]
    orbits = _compute_orbits(generators)

    # Build component matching polynomials
    polys: list[list[int]] = []
    for orbit in orbits:
        m = len(orbit)
        # Map orbit elements to 0..m-1 indices
        idx = {v: i for i, v in enumerate(orbit)}
        # Build neighbor masks: include edges from all k rows (including identity)
        neigh_masks = [0] * m
        for j_val in orbit:  # left index in original labeling
            u = idx[j_val]
            for r in std_rows:
                v_sym = r[j_val]
                # Because orbit is invariant under generators, v_sym ∈ orbit
                v = idx[v_sym]
                neigh_masks[u] |= 1 << v
        polys.append(_component_matching_polynomial(neigh_masks, m))

    # Multiply component polynomials
    total = [1]
    for p in polys:
        total = (
            multiply_polynomials_fft(total, p)
            if use_fft
            else multiply_polynomials(total, p)
        )

    # Inclusion-exclusion to recover the permanent of the allowed matrix A
    # per(A) = sum (-1)^t r_t (n - t)!
    import math

    ans = 0
    for t, rt in enumerate(total):
        if rt == 0:
            continue
        ans += ((-1) ** t) * rt * math.factorial(n - t)
    return ans


def count_extensions(
    rows: list[list[int]], *, rows_to_add: int = 1, use_fft: bool = False
) -> int:
    """Count ordered extensions by adding ``rows_to_add`` rows to ``rows``.

    Args:
        rows: Existing Latin rectangle rows as 1-indexed permutations.
        rows_to_add: Number of further rows to add. ``0`` returns ``1``.
        use_fft: Use exact NTT/CRT convolution for one-row subproblems.

    Returns:
        The number of ordered ways to add the requested rows.

    Notes:
        The ``rows_to_add=1`` path uses the component rook/matching-polynomial
        counter. Larger values use direct recursion over valid next rows, which
        is intended for small-n exact work and regression oracles.
    """
    _validate_rows_to_add(rows_to_add)
    n = _validate_latin_rows(rows)
    if rows_to_add == 0:
        return 1
    if n > 0 and len(rows) + rows_to_add > n:
        return 0
    if rows_to_add == 1:
        return count_next_row_extensions(rows, use_fft=use_fft)

    total = 0
    for next_row in _iter_valid_next_rows(rows):
        total += count_extensions(
            [*rows, next_row],
            rows_to_add=rows_to_add - 1,
            use_fft=use_fft,
        )
    return total


__all__ = ["count_extensions", "count_next_row_extensions"]
