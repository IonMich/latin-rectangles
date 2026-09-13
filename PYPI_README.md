# Latin Rectangles

Exact counts for extending a Latin rectangle: append rows that use every symbol
once and never repeat a symbol in a column. The library combines specialized
**two-row methods based on permutation cycles and Touchard's identity** with
**general k-row counting on forbidden bipartite graphs**.

![Inclusion-exclusion gives 4,744 legal third rows for the illustrated eight-column rectangle.](https://raw.githubusercontent.com/IonMich/latin-rectangles/v0.3.3/docs/assets/math-motion/counting-still-desktop.png)

[Read the full mathematical explanation, animation and diagrams](https://github.com/IonMich/latin-rectangles/blob/v0.3.3/README.md).

## Try it

Requires Python 3.12+. Install with `uv add latin-rectangles` or
`pip install latin-rectangles`. Try the illustrated example with
`uvx latin-rectangles --c "2,2,4"`.

```python
from latin_rectangles import count_extensions, count_extensions_from_cycle_type

# Two fixed rows; the relative permutation has cycle lengths 2, 2 and 4.
count_extensions_from_cycle_type([2, 2, 4])  # 4744 legal third rows

# Three explicit rows; a leading zero marks the 1-indexed representation.
rows = [[0, 1, 2, 3, 4], [0, 2, 1, 4, 3], [0, 3, 4, 1, 2]]
count_extensions(rows)  # 1 legal fourth row
```

## Methods and scope

The cycle-type API offers `auto`, `touchard`, `rook` and `rook_ntt` methods for
one added row. Counts use integers throughout. The optional transform path
uses exact NTT/CRT reconstruction with schoolbook fallback, not floating-point
FFT. The favorable method depends on structure, coefficient size and cache
state.

The two-row reduction implements **Touchard's 1934 counting identity**.
For general starting rectangles, component matching polynomials and
inclusion-exclusion count the next rows. Multiple added rows are ordered and
use direct recursion, intended for small-n exact work; the general matching
computation is exponential in the largest forbidden component.

- [Methods, derivation and attribution](https://github.com/IonMich/latin-rectangles/blob/v0.3.3/docs/methods.md)
- [Benchmark workloads and reproduction](https://github.com/IonMich/latin-rectangles/blob/v0.3.3/docs/benchmarks.md)
- [Independent correctness checks](https://github.com/IonMich/latin-rectangles/blob/v0.3.3/tests/test_independent_verification.py)
- [Changelog](https://github.com/IonMich/latin-rectangles/blob/v0.3.3/CHANGELOG.md)

## License

[MIT](https://github.com/IonMich/latin-rectangles/blob/v0.3.3/LICENSE).
