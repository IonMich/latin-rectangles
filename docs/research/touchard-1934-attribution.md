# Touchard 1934 Attribution Recheck

This note records why the cycle-structure method should be named after
Touchard's 1934 formula.

Local source:

- `literature_sources/pdfs/touchard_1934_sur_un_probleme_de_permutations.pdf`
- `literature_sources/download_attempts/touchard_1934_f631.jpg`
- `literature_sources/download_attempts/touchard_1934_f632.jpg`
- `literature_sources/download_attempts/touchard_1934_f633.jpg`

The PDF is an image-only assembly of Gallica pages 631-633, so formulae should
be checked against the page images rather than the OCR text.

## Touchard's Problem

Touchard counts permutations `P` that are discordant with two given
permutations `A` and `B`. In current Latin-rectangle language, after viewing
permutations as row assignments, this means:

```text
P(i) != A(i)
P(i) != B(i)
```

for every position `i`.

That is exactly the one-row extension condition for a `2 x n` Latin rectangle.
After normalizing the first row to the identity, take:

```text
A = id
B = pi
P = sigma
```

Then Touchard's discordant-permutation count is the number of valid third rows.

## Touchard's Formula

Touchard writes the relative substitution between `A` and `B` as `T`. Only its
cycle type matters here. Let:

```text
h = number of 1-cycles of T
p_1, ..., p_s = lengths of the nontrivial cycles of T
```

Let `phi(h; n)` be Touchard's base count when `T` has `h` fixed points and one
nontrivial cycle of length `n`. Touchard states the general count as:

```text
D(h; p_1, ..., p_s)
  = sum phi(h; p_1 +/- p_2 +/- ... +/- p_s),
```

where the sum is over the `2^(s-1)` choices of signs after `p_1`. He also uses
the convention:

```text
phi(h; -n) = phi(h; n).
```

Therefore this is equivalently:

```text
D(h; p_1, ..., p_s)
  = (1/2) sum_{epsilon in {-1,+1}^s}
      phi(h; |epsilon_1 p_1 + ... + epsilon_s p_s|).
```

The factor `1/2` appears only because this version sums over both a sign vector
and its negation, while Touchard fixes the sign of `p_1`.

## Specialization To This Package

In a `2 x n` Latin rectangle, the two existing rows disagree in every column.
After normalization, `pi` is a derangement, so the relative substitution has:

```text
h = 0
p_r = l_r
```

where `(l_1, ..., l_c)` is the cycle type of `pi`.

Define this package's one-cycle value by:

```text
M_m = phi(0; m).
```

Then Touchard's formula becomes exactly:

```text
E(l_1, ..., l_c)
  = (1/2) sum_{epsilon in {-1,+1}^c}
      M_|epsilon_1 l_1 + ... + epsilon_c l_c|.
```

This is the Touchard formula implemented by
`count_cycle_structure_extensions(..., method="touchard")`.

The formal endpoint values are also aligned with Touchard's symbolic extension
of the one-cycle function, not an independent new correction. Touchard defines
`phi(h; 0)` through his symbolic formula rather than through an actual
nontrivial cycle; for `h = 0`, this gives the same role as this package's
`M_0 = 2`. Signed differences can also force the one-cycle function to be
evaluated at `1`, even though a 1-cycle is not a nontrivial cycle in a Latin
rectangle; this package records that formal value as `M_1 = -1`.

## Objective Conclusion

The package's Touchard identity is not materially distinct from Touchard's
1934 formula as an enumerative identity. It is Touchard's discordant-permutation
formula specialized to the case `h = 0`, written with modern cycle-type notation
and all sign vectors instead of Touchard's `2^(s-1)` sign convention.

What remains distinct in this package is computational and expository:

- the specialization is connected explicitly to `2 x n -> 3 x n` Latin rectangle
  extension counting;
- the same count is derived from the forbidden bipartite graph and rook
  polynomial inclusion-exclusion;
- the one-cycle values `M_m` are computed and cached through the package's
  rook-polynomial machinery;
- the all-sign formula is implemented through subset-sum multiplicities, which
  avoids enumerating sign vectors directly.

## Recommended Attribution Wording

Use wording like:

> The Touchard formula is Touchard's 1934 formula for permutations
> discordant with two given permutations, specialized to the case where the
> relative permutation has no fixed points. In the package notation this gives
> `E(l_1, ..., l_c) = (1/2) sum_epsilon M_|sum epsilon_i l_i|`. The package
> derives the same identity from the Latin-rectangle forbidden graph and uses it
> as an exact cached computation method.

Avoid wording like:

- "new formula";
- "first explicit fixed-cycle-type formula";
- "materially different from Touchard's formula".
