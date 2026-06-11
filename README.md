# Latin Rectangles Extension Counter

A high-performance Python library for counting the number of ways to extend a 2×n [Latin rectangle](https://en.wikipedia.org/wiki/Latin_rectangle) to a 3×n Latin rectangle using rook polynomial methods and cycle decomposition theory.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

A **Latin rectangle** is an r×n array filled with n different symbols such that each symbol occurs exactly once in each row and at most once in each column.

### Extension Problem

Given a 2×n Latin rectangle:

```text
1  2  3  4  5  6  7  8
p[1]  p[2]  p[3]  p[4]  p[5]  p[6]  p[7]  p[8]
```

where `p` is a [derangement](https://en.wikipedia.org/wiki/Derangement), the problem is to count how many valid third rows can be added such that the resulting 3×n rectangle remains a Latin rectangle. This library provides an efficient algorithm for computing Latin rectangle extensions.

### Key Features

- **High Performance**: Quadratic O(n^2) per-derangement time complexity (see Complexity), with exact NTT/CRT convolution available when CRT reconstruction is not too expensive and a cached Touchard formula for repeated cycle-structure queries
- **Memory Efficient**: Approximate O(n^1.36) memory complexity
- **Generalization to k→k+1**: Exact counting for extending k×n to (k+1)×n via component-wise rook/matching polynomials; exponential in the worst case (as expected from #P-completeness), but fast when orbits/components are small

## Installation

### Via pip

The library is available on PyPI and can be installed via pip:

```console
pip install latin-rectangles
```

### Via uv Package Manager (Recommended)

Using the [`uv` package manager](https://docs.astral.sh/uv/getting-started/installation/), you can try out the package without a separate installation step:

```console
# Get the number of extensions for a random derangement for a specific number of columns
uvx latin-rectangles --n 42
```

If you want to add it to your project, you can use:

```console
# Add to your project's environment using uv
uv add latin-rectangles
```

### Manual Installation

*Alternatively*, you can clone the repository and install it from source:

```console
git clone https://github.com/ionmich/latin-rectangles.git
cd latin-rectangles
```

## Quick Start

### Command Line (CLI) Usage

Generate random derangement:

```console
> uv run python -m latin_rectangles --n 42
🎲 Generated Random Derangement for n=42
📊 Cycle structure: [2, 2, 4, 8, 26]
🔢 Number of extensions: 185,566,788,772,996,286,199,647,931,971,186,844,003,087,641,029,824
```

Use specific cycle structure:

```console
> uv run python -m latin_rectangles --c "2,2,4"
⚙️  Specific Cycle Structure for n=8
📊 Cycle structure: [2, 2, 4]
🔢 Number of extensions: 4,744
```

Large counts are summarized by default to keep the CLI usable and to avoid
Python's decimal integer string-conversion guard:

```console
> uv run python -m latin_rectangles --n 1700
🎲 Generated Random Derangement for n=1700
📊 Cycle structure: [...]
🔢 Number of extensions: 4,685 decimal digits (bits=15,562; leading=...; trailing=...; mod 1,000,000,007=...; use --full-output to print all digits)
```

Use `--full-output` to print the entire decimal integer, or `--max-digits N` to
raise/lower the exact-printing threshold.

Enumerate all possible cycle structures:

```console
> uv run python -m latin_rectangles --n 8 --all
🔍 All Cycle Structures for n=8
📊 Found 7 possible structures with non-zero extensions:

 1. [2, 2, 2, 2] → 4,752 extensions
 2. [2, 2, 4] → 4,744 extensions
 3. [2, 3, 3] → 4,740 extensions
 4. [2, 6] → 4,740 extensions
 5. [4, 4] → 4,740 extensions
 6. [3, 5] → 4,738 extensions
 7. [8] → 4,738 extensions
```

## Get help

```console
uv run latin-rectangles --help
```

## Python Library Usage

```python
from latin_rectangles import (
  count_extensions,
  count_extensions_k,
  count_random_extensions,
  generate_random_derangement,
  count_cycle_structure_extensions,
)

# Method 1: One-liner for random derangement
extensions = count_random_extensions(n=12)
print(f"Extensions: {extensions:,}")

# Method 2: Step-by-step with custom derangement
derangement = generate_random_derangement(n=10)
extensions = count_extensions(derangement)
print(f"Derangement {derangement[1:]} has {extensions:,} extensions")

# Method 3: Using a specific cycle structure (e.g., "2,2,4") in one line
cycle_lengths = [2, 2, 4]
extensions = count_cycle_structure_extensions(cycle_lengths)
print(f"Cycle structure {cycle_lengths} has {extensions:,} extensions")  # 4,744 for n=8

# Method 4: With predefined derangement (1-indexed with dummy 0)
p = [0, 2, 3, 4, 5, 6, 7, 8, 1]  # 8-cycle for n=8
extensions = count_extensions(p)
print(f"8-cycle has {extensions:,} extensions")  # Output: 4,738

# Bonus: General k→k+1 extension counting (small example)
# Rows are 1-indexed permutations; the first row may be non-identity (will be standardized).
rows = [
  [0, 1, 2, 3, 4],      # identity
  [0, 2, 1, 4, 3],      # (1 2)(3 4)
  [0, 3, 4, 1, 2],      # (1 3)(2 4)
]
extensions_k = count_extensions_k(rows)
print(f"Extend 3×4 → 4×4: {extensions_k} ways")
```

## Algorithm Details

### Mathematical Foundation

The algorithms are derived in detail in [docs/methods.md](docs/methods.md),
including notation, the rook-polynomial formula, the Touchard identity, the
exact NTT/CRT convolution path, and the general `k x n -> (k + 1) x n` method.
The benchmark and plotting workflow is documented in
[docs/benchmarks.md](docs/benchmarks.md).

At a high level, the specialized `2 x n -> 3 x n` counter uses **rook
polynomial theory**:

1. **Input**: A derangement (permutation with no fixed points) representing the second row
2. **Cycle Decomposition**: Decompose the derangement into disjoint cycles
3. **Rook Polynomials**: Compute rook polynomial for each cycle structure
4. **Polynomial Multiplication**: Combine rook polynomials to get the final count

For direct cycle-structure inputs, the implementation also uses Touchard's
identity. If the cycle lengths are `l_1, ..., l_c`, then

```text
E(l_1, ..., l_c) = 1/2 * sum_epsilon M_|epsilon_1 l_1 + ... + epsilon_c l_c|
```

where `M_s` is the one-cycle inclusion-exclusion value. The values `M_0 = 2`
and `M_1 = -1` are formal correction terms from the Chebyshev polynomial
identity; they are not extension counts for actual 0- or 1-cycles.

This is Touchard's 1934 discordant-permutation formula specialized to the
no-fixed-point relative cycle structure of a normalized `2 x n` Latin rectangle.
The implementation derives the same expression from the
rook-polynomial/forbidden-graph view and evaluates it with cached one-cycle
values.

Internally, the rook polynomial for one `l`-cycle stores positive matching
numbers `r_j`, while the Touchard proof uses the reversed signed polynomial
`q_l(t) = sum_j (-1)^j r_j t^(l-j)` and the linear functional `F(t^d) = d!`.
For `l >= 2`, `M_l = F(q_l)` is exactly the same inclusion-exclusion count
computed from the rook polynomial.

## Complexity

- Per derangement (fixed 2×n Latin rectangle): the default method runs in O(n^2) time due to polynomial multiplications whose total degree sums to n. Memory usage is empirically ~O(n^1.36). The optional `use_fft=True` path uses exact NTT/CRT convolution for large dense polynomial products and falls back to schoolbook multiplication for small products, skinny products, or products whose coefficient sizes would require too many CRT primes.

- Repeated cycle-structure queries: the Touchard method reuses cached
  one-cycle values `M_s`, which is especially useful when enumerating all cycle
  structures for a fixed `n`.

- Enumerating all relevant cycle types at a fixed n: the number of distinct cycle-type inputs is
  T(n) = p(n) − p(n − 1),
  where p(n) is the partition function (partitions of n). Using the Hardy–Ramanujan asymptotic
  p(n) ≍ (1/(4√3 n)) · exp(C √n) with C = π√(2/3), one gets
  T(n) = p(n) − p(n − 1) = Θ(exp(C √n) / n^{3/2}).
  Therefore, the total time to compute extensions for all cycle types scales as
  O(n^2 · T(n)) = O(√n · exp(C √n))
  with the constant C = π√(2/3). Peak memory is still governed by the per-derangement footprint since enumeration can reuse buffers.

## API Reference

### Core Functions

#### `count_extensions(permutation: list[int]) -> int`

Counts the number of extensions for a given derangement.

**Parameters:**

- `permutation`: 1-indexed list representing a derangement (p[0] is dummy value)

**Returns:** Integer number of possible third rows

**Raises:** `ValueError` if input is not a derangement

The optional `use_fft=True` argument uses exact NTT/CRT convolution only when
the transform route is expected to be reasonable. It does not use rounded
floating-point convolution.

#### `count_cycle_structure_extensions(cycle_lengths: list[int], method: str = "auto") -> int`

The default `method="auto"` uses the Touchard formula when its needed
one-cycle values are cached or few, and falls back to the rook product for cold
dense high-`n` cycle types. Explicit methods are `"touchard"`, `"rook"`, and
`"rook_ntt"`.

#### `count_random_extensions(n: int) -> int`

Convenience function that generates a random derangement and counts its extensions.

**Parameters:**

- `n`: Size of the derangement (must be > 1)

**Returns:** Number of extensions for the randomly generated derangement

#### `generate_random_derangement(n: int) -> list[int]`

Generates a random derangement of size n.

**Parameters:**

- `n`: Size of the derangement

**Returns:** 1-indexed list representing the derangement

#### `find_cycle_decomposition(permutation: list[int]) -> list[list[int]]`

Finds the cycle decomposition of a permutation.

**Parameters:**

- `permutation`: 1-indexed permutation

**Returns:** List of cycles (each cycle is a list of indices)

## Examples

### Basic Usage Examples

```python
from latin_rectangles import count_extensions

# Example 1: Single 8-cycle
p_8_cycle = [0, 2, 3, 4, 5, 6, 7, 8, 1]
print(f"8-cycle: {count_extensions(p_8_cycle):,} extensions")
# Output: 8-cycle: 4,738 extensions

# Example 2: Two 4-cycles
p_4_4 = [0, 2, 3, 4, 1, 6, 7, 8, 5]
print(f"4,4-cycles: {count_extensions(p_4_4):,} extensions")
# Output: 4,4-cycles: 4,740 extensions

# Example 3: Four 2-cycles
p_2_2_2_2 = [0, 2, 1, 4, 3, 6, 5, 8, 7]
print(f"2,2,2,2-cycles: {count_extensions(p_2_2_2_2):,} extensions")
# Output: 2,2,2,2-cycles: 4,752 extensions
```

### Advanced Usage

```python
from latin_rectangles import generate_random_derangement, find_cycle_decomposition, count_extensions

# Generate and analyze a random derangement
n = 15
derangement = generate_random_derangement(n)
cycles = find_cycle_decomposition(derangement)
cycle_lengths = sorted([len(c) for c in cycles])
extensions = count_extensions(derangement)

print(f"n={n}")
print(f"Derangement: {derangement[1:]}")
print(f"Cycle structure: {cycle_lengths}")
print(f"Extensions: {extensions:,}")
```

### Batch Processing

```python
from latin_rectangles import count_random_extensions

# Process multiple sizes
results = []
for n in range(5, 21):
    extensions = count_random_extensions(n)
    results.append((n, extensions))
    print(f"n={n:2d}: {extensions:,} extensions")

# Find the size with the most extensions in this batch
max_n, max_extensions = max(results, key=lambda x: x[1])
print(f"Maximum: n={max_n} with {max_extensions:,} extensions")
```

## Development

### Running Tests

```bash
# Run the test suite
uv run pytest

# Run with coverage
uv run pytest --cov=latin_rectangles

# Run specific test
uv run pytest tests/test_main.py -v
```

### Code Quality

```bash
# Type checking
uv run mypy src/

# Linting
uv run ruff check src/

# Formatting
uv run ruff format src/
```

### Benchmarking

```bash
# Run performance benchmarks
uv run python benchmark.py

# Analyze complexity
uv run python complexity_analysis.py
```

## Contributing

Contributions are welcome! Please see [DEVELOPMENT.md](DEVELOPMENT.md) for development guidelines.

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this library in your research, please cite:

```bibtex
@software{latin_rectangles,
  title={Latin Rectangles Extensions},
  author={Ioannis Michaloliakos},
  year={2025},
  url={https://github.com/ionmich/latin-rectangles}
}
```
