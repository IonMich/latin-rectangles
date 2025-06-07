# Latin Rectangles Extension Counter

A high-performance Python library for counting the number of ways to extend a 2×n Latin rectangle to a 3×n Latin rectangle using rook polynomial methods and cycle decomposition theory.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

This library provides an efficient algorithm for computing Latin rectangle extensions, a fundamental problem in combinatorics. Given the first two rows of a Latin rectangle (where the first row is the identity permutation and the second row is a derangement), the library calculates how many valid third rows exist.

### Key Features

- **High Performance**: Approximate O(n^2) time complexity, tested up to n=800
- **Memory Efficient**: Approximate O(n^1.36) memory complexity
- **Mathematically Rigorous**: Based on rook polynomial theory and cycle decomposition
- **Easy to Use**: Simple command-line interface and Python API
- **Well Tested**: Comprehensive test suite with complexity analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/latin-rectangles.git
cd latin-rectangles

# Install the package
pip install -e .
```

## Quick Start

### Command Line Usage

```bash
# Run demonstration with predefined examples
latin-rectangles

# Generate random derangement for specific size
latin-rectangles --n 15
latin-rectangles generate 20

# Run demo examples
latin-rectangles demo

# Get help
latin-rectangles --help
```

### Python Library Usage

```python
from latin_rectangles import count_extensions, count_random_extensions
from latin_rectangles import generate_random_derangement

# Method 1: One-liner for random derangement
extensions = count_random_extensions(n=12)
print(f"Extensions: {extensions:,}")

# Method 2: Step-by-step with custom derangement
derangement = generate_random_derangement(n=10)
extensions = count_extensions(derangement)
print(f"Derangement {derangement[1:]} has {extensions:,} extensions")

# Method 3: With predefined derangement (1-indexed with dummy 0)
p = [0, 2, 3, 4, 5, 6, 7, 8, 1]  # 8-cycle for n=8
extensions = count_extensions(p)
print(f"8-cycle has {extensions:,} extensions")  # Output: 4,738
```

## Algorithm Details

### Mathematical Foundation

The algorithm leverages **rook polynomial theory** to solve the Latin rectangle extension problem:

1. **Input**: A derangement (permutation with no fixed points) representing the second row
2. **Cycle Decomposition**: Decompose the derangement into disjoint cycles
3. **Rook Polynomials**: Compute rook polynomial for each cycle structure
4. **Polynomial Multiplication**: Combine rook polynomials to get the final count

## API Reference

### Core Functions

#### `count_extensions(permutation: list[int]) -> int`

Counts the number of extensions for a given derangement.

**Parameters:**
- `permutation`: 1-indexed list representing a derangement (p[0] is dummy value)

**Returns:** Integer number of possible third rows

**Raises:** `ValueError` if input is not a derangement

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
pytest

# Run with coverage
pytest --cov=latin_rectangles

# Run specific test
pytest tests/test_main.py -v
```

### Code Quality

```bash
# Type checking
mypy src/

# Linting
ruff check src/

# Formatting
ruff format src/
```

### Benchmarking

```bash
# Run performance benchmarks
python benchmark.py

# Analyze complexity
python complexity_analysis.py
```

## Mathematical Background

### Latin Rectangles

A **Latin rectangle** is an r×n array filled with n different symbols such that each symbol occurs exactly once in each row and at most once in each column.

### Extension Problem

Given a 2×n Latin rectangle:
```
1  2  3  4  5  6  7  8
p[1]  p[2]  p[3]  p[4]  p[5]  p[6]  p[7]  p[8]
```
where `p` is a derangement, the problem is to count how many valid third rows can be added such that the resulting 3×n rectangle remains a Latin rectangle.

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
  title={Latin Rectangles Extension Counter},
  author={Ioannis Michaloliakos},
  year={2025},
  url={https://github.com/ionmich/latin-rectangles}
}
```