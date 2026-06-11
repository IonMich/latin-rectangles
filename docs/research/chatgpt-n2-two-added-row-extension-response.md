# ChatGPT Response: Two Added Rows From a Two-Row Rectangle

Captured from a ChatGPT response to the implementation-side question:

> do you think it is materially useful from the implementation side to improve
> the 2-row extensions? do we even have routines for 2-row extensions of 2-row
> rectangles?

## Implementation Takeaway

Yes, this is materially useful as a research and validation target. Here
`N_2(lambda)` means two added rows from the given `2 x n` rectangle, i.e. the
number of ordered extensions from that fixed `2 x n` rectangle to a `4 x n`
Latin rectangle.

The current code has an inner primitive, but not the `N_2(lambda)` driver:

- `count_extensions(rows)` counts one added row from any explicit `k x n`
  rectangle. In particular, `count_extensions([id, pi, sigma])` counts fourth
  rows extending a concrete `3 x n` rectangle.
- What is missing is a dedicated `N_2(lambda)` routine for the full
  `2 x n -> 4 x n` count:

```text
N_2(lambda) = # ordered pairs (sigma, tau)
```

where `(sigma, tau)` are the two further rows extending the normalized two-row
rectangle `(id, pi)` to a four-row rectangle, and `pi` has cycle type `lambda`.

A direct implementation would enumerate all valid third rows `sigma` and sum
the number of valid fourth rows:

```text
N_2(pi) = sum_{sigma extending (id, pi)}
          count_extensions([id, pi, sigma])
```

That is enough for small `n`, regression tests, and empirical exploration. For
larger `n`, the natural next improvement is template grouping, because many
third rows lead to isomorphic forbidden graphs with the same number of future
extensions.

## Definition Of `N_t(lambda)`

Fix a normalized `2 x n` Latin rectangle:

```text
id: 0, 1, 2, ..., n - 1
pi: pi(0), pi(1), pi(2), ..., pi(n - 1)
```

where `pi` is a derangement with cycle type:

```text
lambda = (l_1, ..., l_c)
```

Then `N_t(lambda)` is the number of ordered ways to add `t` further rows.

The one-added-row count is the number of possible choices for the first new row
`sigma`. In the direct `N_2` sum, it is just the number of summands.

`N_2(lambda)` counts ordered pairs `(sigma, tau)` such that, for every column
`i`, the symbols:

```text
sigma(i), tau(i), i, pi(i)
```

are all distinct.

Rows are ordered here. If unordered added rows were desired, divide `N_2` by
`2`, because two valid added rows can never be identical.

## Direct Formula For `N_2`

For a fixed `pi`:

```text
N_2(pi) =
    sum_{sigma in S_n}
      1[sigma(i) != i and sigma(i) != pi(i) for every i]
      * per(A_{pi,sigma})
```

where `A_{pi,sigma}` is the `n x n` zero-one matrix:

```text
A_{pi,sigma}(i, j) = 1 if j not in {i, pi(i), sigma(i)}
                   = 0 otherwise
```

Equivalently:

```text
A_{pi,sigma} = J - I - P_pi - P_sigma
```

So:

```text
N_2(pi) =
    sum_{sigma extending (id, pi)}
      per(J - I - P_pi - P_sigma)
```

In repo terms, the permanent term is exactly the fourth-row count returned by:

```python
count_extensions([identity, pi, sigma])
```

for an explicit valid third row `sigma`.

## Direct Small-`n` Algorithm

For small `n`, the direct algorithm is:

1. Construct a canonical permutation `pi` with cycle type `lambda`.
2. Enumerate every permutation `sigma` in `S_n`.
3. Keep only those satisfying `sigma(i) != i` and `sigma(i) != pi(i)` for all
   columns `i`.
4. For each such `sigma`, compute
   `count_extensions([identity, pi, sigma])`.
5. Sum those fourth-row counts.

Pseudocode:

```text
N2(lambda):
    pi = canonical_permutation_with_cycle_type(lambda)
    total = 0

    for sigma in all_permutations(n):
        if sigma avoids identity and pi columnwise:
            total += count_extensions([identity, pi, sigma])

    return total
```

This is computationally expensive because it enumerates valid third rows. It is
still useful as a correctness oracle and for exploring the shape of the next
state space.

## Example: `lambda = (3, 4)`

Take:

```text
pi = (0,1,2)(3,4,5,6)
```

so `n = 7`. The number of valid third rows is:

```text
578
```

For each valid third row `sigma`, compute:

```text
per(J - I - P_pi - P_sigma)
```

In this case, the fourth-row counts take only two values:

```text
144 or 148
```

More precisely:

```text
554 third rows give fourth-row count 144
24  third rows give fourth-row count 148
```

Therefore:

```text
N_2(3,4) = 554 * 144 + 24 * 148 = 83328
```

## Small Table With Internal Distributions

The more informative object is the distribution of fourth-row counts over valid
third rows.

```text
n  lambda     valid third rows  distribution of fourth-row counts
4  (2,2)      4            4 * 1
4  (4)        2            2 * 1
5  (2,3)      12           12 * 2
5  (5)        13           8 * 2 + 5 * 4
6  (2,2,2)    80           16 * 17 + 64 * 20
6  (2,4)      80           64 * 18 + 16 * 20
6  (3,3)      82           12 * 17 + 36 * 18 + 33 * 20 + 1 * 36
6  (6)        80           6 * 17 + 60 * 18 + 14 * 20
7  (2,2,3)    580          436 * 144 + 144 * 148
7  (2,5)      580          460 * 144 + 120 * 148
7  (3,4)      578          554 * 144 + 24 * 148
7  (7)        579          523 * 144 + 56 * 148
```

For example:

```text
N_2(2,4) = 64 * 18 + 16 * 20 = 1472
N_2(6)   = 6 * 17 + 60 * 18 + 14 * 20 = 1462
```

## Why The Distribution Matters

This already shows that `N_2` is not determined only by the number of valid
third rows.

For `n = 6`:

```text
valid third rows for (2,2,2) = 80
valid third rows for (2,4)   = 80
valid third rows for (6)     = 80
```

but:

```text
N_2(2,2,2) = 1552
N_2(2,4)   = 1472
N_2(6)     = 1462
```

The first extension count loses information. The second extension count is
sensitive to how the valid third rows are distributed into different three-row
template types.

This is the main reason the promising algorithmic direction is not "derive a
scalar formula from the number of third rows." It is to build a transition
theory among templates.

## Recursive Graph/Template Algorithm

Given a current `k x n` Latin rectangle `R`, define its forbidden bipartite
graph `G(R)`.

- Left vertices are columns.
- Right vertices are symbols.
- Edge `(i, j)` means symbol `j` has already appeared in column `i`.

A new row is a perfect matching in the complement graph:

```text
K_{n,n} \ G(R)
```

Define:

```text
N_t(G) = # ordered t-row extensions from forbidden graph G
```

Then:

```text
N_0(G) = 1

N_t(G) =
    sum_{M in PM(K_{n,n} \ G)}
      N_{t-1}(G union M)
```

For the initial two-row rectangle with cycle type `lambda`, the starting graph
is:

```text
G_lambda = C_{2 l_1} disjoint-union ... disjoint-union C_{2 l_c}
```

So:

```text
N_t(lambda) = N_t(G_lambda)
```

For `t = 1`, this is the one-added-row count:

```text
one_row_extensions(G_lambda) = per(K_{n,n} \ G_lambda)
```

For `t = 2`:

```text
N_2(G_lambda) =
    sum_{M in PM(K_{n,n} \ G_lambda)}
      per(K_{n,n} \ (G_lambda union M))
```

This is the graph version of the direct formula above.

## Why Templates Help

Many different choices of third row `sigma` lead to isomorphic forbidden graphs:

```text
G_lambda union P_sigma
```

If two such graphs are isomorphic as bipartite graphs, they have the same
number of future extensions.

So instead of summing over every `sigma` individually, group them:

```text
N_2(G_lambda) =
    sum_T m_lambda(T) * per(K_{n,n} \ T)
```

where:

- `T` ranges over isomorphism classes of three-regular bipartite graphs
  obtainable from `G_lambda` by adding one perfect matching.
- `m_lambda(T)` is the number of third rows `sigma` that produce template `T`.
- `per(K_{n,n} \ T)` is the number of possible fourth rows from that template.

For larger `t`, this becomes a transition system:

```text
N_t(T) =
    sum_{T'} a_{T,T'} * N_{t-1}(T')
```

where `a_{T,T'}` is the number of perfect matchings in the complement of `T`
whose addition leads to template `T'`.

## Research Direction

For one added row, the state space collapses to cycle type because the
forbidden graph is two-regular:

```text
G_lambda = C_{2 l_1} disjoint-union ... disjoint-union C_{2 l_c}
```

For `N_2`, the intermediate graphs are three-regular bipartite graphs. There is
no reason for a one-variable cycle-type formula to survive, but the process
still has a finite structured state space for fixed `n`.

A practical research program would be:

1. For each `n`, enumerate all initial cycle types `lambda`.
2. Generate all possible three-row templates from each `G_lambda`.
3. Canonicalize templates up to bipartite graph isomorphism.
4. Count transition multiplicities.
5. Use the transition matrix to compute `N_t(lambda)` for many `t`.
6. Look for closed forms, recurrences, extremal behavior, or asymptotic
   regularities.

In short:

```text
One added row is controlled by cycle lengths.
Two added rows are controlled by the distribution of resulting three-row templates.
```
