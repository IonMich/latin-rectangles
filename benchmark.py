#!/usr/bin/env python3
"""
Benchmark script for Latin rectangles extension counting.

This script stress-tests the algorithm to find the maximum number of columns
that can be computed in reasonable time, and analyzes how performance scales
with different factors.
"""

import argparse
import json
import math
import time
import tracemalloc
from dataclasses import dataclass

from latin_rectangles import (
    count_extensions,
    find_cycle_decomposition,
    generate_random_derangement,
)


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    n: int
    cycle_structure: list[int]
    cycle_type: str
    extensions_count: int
    time_seconds: float
    memory_peak_mb: float
    memory_current_mb: float


class LatinRectangleBenchmark:
    """Comprehensive benchmarking suite for Latin rectangle extension counting."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: list[BenchmarkResult] = []

    def log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def benchmark_single(
        self, permutation: list[int], cycle_type: str = "custom"
    ) -> BenchmarkResult:
        """
        Benchmark a single permutation.

        Args:
            permutation: The permutation to test (1-indexed with 0 at start)
            cycle_type: Description of the cycle type for reporting

        Returns:
            BenchmarkResult with timing and memory data
        """
        n = len(permutation) - 1
        cycles = find_cycle_decomposition(permutation)
        cycle_structure = sorted([len(c) for c in cycles])

        self.log(f"  Testing n={n}, cycle structure: {cycle_structure}")

        # Start memory and time tracking
        tracemalloc.start()
        start_time = time.perf_counter()

        # Run the computation
        result = count_extensions(permutation)

        # Stop timing and get memory stats
        end_time = time.perf_counter()
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        duration = end_time - start_time
        peak_mb = peak_mem / 1024 / 1024
        current_mb = current_mem / 1024 / 1024

        benchmark_result = BenchmarkResult(
            n=n,
            cycle_structure=cycle_structure,
            cycle_type=cycle_type,
            extensions_count=result,
            time_seconds=duration,
            memory_peak_mb=peak_mb,
            memory_current_mb=current_mb,
        )

        self.results.append(benchmark_result)

        # Safe logging of large numbers
        try:
            result_str = str(result)
            if len(result_str) > 100:
                result_display = (
                    f"{result_str[:50]}...{result_str[-50:]} ({len(result_str)} digits)"
                )
            else:
                result_display = result_str
        except ValueError:
            # Handle case where number is too large to convert to string
            result_display = f"<{result.bit_length()} bits>"

        self.log(f"    Result: {result_display} extensions")
        self.log(f"    Time: {duration:.4f}s")
        self.log(f"    Memory: {peak_mb:.2f}MB peak, {current_mb:.2f}MB current")

        return benchmark_result

    def create_specific_cycle_structure(
        self, n: int, cycle_lengths: list[int]
    ) -> list[int] | None:
        """
        Create a permutation with a specific cycle structure.

        Args:
            n: Total size
            cycle_lengths: List of desired cycle lengths

        Returns:
            Permutation with the specified cycle structure, or None if impossible
        """
        if sum(cycle_lengths) != n:
            return None

        perm = [0] * (n + 1)  # 1-indexed with 0 at start
        used = set()
        current_pos = 1

        for cycle_len in cycle_lengths:
            # Find available positions for this cycle
            cycle_positions: list[int] = []
            while len(cycle_positions) < cycle_len and current_pos <= n:
                if current_pos not in used:
                    cycle_positions.append(current_pos)
                current_pos += 1

            if len(cycle_positions) < cycle_len:
                # Find remaining positions
                for i in range(1, n + 1):
                    if i not in used and len(cycle_positions) < cycle_len:
                        cycle_positions.append(i)

            # Create the cycle
            for i in range(cycle_len):
                perm[cycle_positions[i]] = cycle_positions[(i + 1) % cycle_len]
                used.add(cycle_positions[i])

        return perm

    def benchmark_scaling(self, max_n: int = 20, timeout_seconds: float = 30.0) -> None:
        """
        Test how performance scales with n using random derangements.

        Args:
            max_n: Maximum n to test
            timeout_seconds: Stop if a single computation takes longer than this
        """
        self.log("=== Scaling Analysis with Random Derangements ===")

        for n in range(4, max_n + 1):
            try:
                self.log(f"\nTesting n={n}...")
                perm = generate_random_derangement(n)
                result = self.benchmark_single(perm, f"random_n{n}")

                if result.time_seconds > timeout_seconds:
                    self.log(f"Timeout reached at n={n}, stopping scaling test")
                    break

            except Exception as e:
                self.log(f"Error at n={n}: {e}")
                break

    def benchmark_cycle_structures(self, n: int = 16) -> None:
        """
        Test different cycle structures for a fixed n.

        Args:
            n: The value of n to test with different cycle structures
        """
        self.log(f"\n=== Cycle Structure Analysis (n={n}) ===")

        # Test various cycle structures
        test_structures_raw = [
            ([n], "single_cycle"),
            ([n // 2, n // 2], "two_equal_cycles") if n % 2 == 0 else None,
            ([2] * (n // 2), "all_2_cycles") if n % 2 == 0 else None,
            ([3] * (n // 3), "all_3_cycles") if n % 3 == 0 else None,
            ([4] * (n // 4), "all_4_cycles") if n % 4 == 0 else None,
        ]

        # Remove None entries and ensure proper typing
        test_structures: list[tuple[list[int], str]] = [
            s for s in test_structures_raw if s is not None
        ]

        # Add some mixed structures
        if n >= 8:
            mixed_structures_raw = [
                ([n // 2, n // 4, n // 4], "mixed_large_small") if n % 4 == 0 else None,
                ([n - 3, 3], "large_plus_small"),
                ([n - 4, 2, 2], "large_plus_two_small") if n >= 6 else None,
            ]
            test_structures.extend([s for s in mixed_structures_raw if s is not None])

        for cycle_lengths, description in test_structures:
            if sum(cycle_lengths) == n:
                perm = self.create_specific_cycle_structure(n, cycle_lengths)
                if perm:
                    self.log(f"\nTesting {description}: {cycle_lengths}")
                    self.benchmark_single(perm, description)

    def find_maximum_n(
        self, timeout_seconds: float = 60.0, memory_limit_mb: float = 1024.0
    ) -> int:
        """
        Find the maximum n that can be computed within time and memory limits using binary search.

        Args:
            timeout_seconds: Maximum time allowed per computation
            memory_limit_mb: Maximum memory allowed

        Returns:
            The maximum n that was successfully computed
        """
        self.log(
            f"\n=== Finding Maximum n (timeout: {timeout_seconds}s, memory limit: {memory_limit_mb}MB) ==="
        )

        # First, find an upper bound by exponential search
        self.log("Phase 1: Finding upper bound with exponential search...")

        lower_bound = 4  # Start with a reasonable minimum
        upper_bound = lower_bound

        # Exponential search to find upper bound
        while True:
            try:
                self.log(f"Testing upper bound candidate: n={upper_bound}")
                perm = generate_random_derangement(upper_bound)
                result = self.benchmark_single(perm, f"upper_bound_test_n{upper_bound}")

                if (
                    result.time_seconds > timeout_seconds
                    or result.memory_peak_mb > memory_limit_mb
                ):
                    self.log(f"Found upper bound at n={upper_bound}")
                    break

                # Double the upper bound and continue
                lower_bound = upper_bound
                upper_bound *= 2

                # Safety check to prevent infinite growth
                if upper_bound > 100000:
                    self.log("Safety limit reached, stopping exponential search")
                    break

            except Exception as e:
                self.log(f"Error at n={upper_bound}: {e}")
                break

        # Now binary search between lower_bound and upper_bound
        self.log(f"Phase 2: Binary search between n={lower_bound} and n={upper_bound}")

        max_successful_n = lower_bound

        while lower_bound <= upper_bound:
            mid = (lower_bound + upper_bound) // 2
            self.log(f"Testing n={mid} (range: {lower_bound}-{upper_bound})")

            try:
                perm = generate_random_derangement(mid)
                result = self.benchmark_single(perm, f"binary_search_n{mid}")

                if (
                    result.time_seconds <= timeout_seconds
                    and result.memory_peak_mb <= memory_limit_mb
                ):
                    # Success - try larger values
                    max_successful_n = mid
                    lower_bound = mid + 1
                    self.log(f"✅ n={mid} succeeded, trying larger values")
                else:
                    # Failed - try smaller values
                    upper_bound = mid - 1
                    if result.time_seconds > timeout_seconds:
                        self.log(
                            f"❌ n={mid} failed: time {result.time_seconds:.2f}s > {timeout_seconds}s"
                        )
                    if result.memory_peak_mb > memory_limit_mb:
                        self.log(
                            f"❌ n={mid} failed: memory {result.memory_peak_mb:.2f}MB > {memory_limit_mb}MB"
                        )

            except Exception as e:
                self.log(f"❌ n={mid} failed with error: {e}")
                upper_bound = mid - 1

        self.log(f"\n🎯 Maximum successfully computed n: {max_successful_n}")

        # Do a final test with a few values around the maximum for verification
        self.log("Phase 3: Verification tests around maximum...")
        for test_n in [max_successful_n - 1, max_successful_n, max_successful_n + 1]:
            if test_n >= 4:
                try:
                    perm = generate_random_derangement(test_n)
                    result = self.benchmark_single(perm, f"verification_n{test_n}")
                    status = (
                        "✅"
                        if (
                            result.time_seconds <= timeout_seconds
                            and result.memory_peak_mb <= memory_limit_mb
                        )
                        else "❌"
                    )
                    self.log(
                        f"{status} n={test_n}: {result.time_seconds:.3f}s, {result.memory_peak_mb:.1f}MB"
                    )
                except Exception as e:
                    self.log(f"❌ n={test_n}: Error - {e}")

        return max_successful_n

    def estimate_complexity_scaling(self, start_n: int = 10, samples: int = 5) -> None:
        """
        Estimate how time complexity scales with n by sampling a few points.

        Args:
            start_n: Starting value of n for sampling
            samples: Number of sample points to collect
        """
        self.log(f"\n=== Complexity Scaling Estimation (starting n={start_n}) ===")

        sample_points = []
        current_n = start_n

        for i in range(samples):
            try:
                self.log(f"Sampling point {i + 1}/{samples}: n={current_n}")
                perm = generate_random_derangement(current_n)
                result = self.benchmark_single(perm, f"scaling_sample_n{current_n}")

                sample_points.append((current_n, result.time_seconds))

                # Increase n for next sample (exponential spacing)
                current_n = int(current_n * 1.5)

            except Exception as e:
                self.log(f"Error at n={current_n}: {e}")
                break

        if len(sample_points) >= 3:
            self.log("\nComplexity analysis:")
            for i in range(1, len(sample_points)):
                n1, t1 = sample_points[i - 1]
                n2, t2 = sample_points[i]

                ratio = t2 / t1
                n_ratio = n2 / n1

                # Estimate complexity exponent
                if ratio > 1.1:  # Only if there's meaningful growth
                    exponent = math.log(ratio) / math.log(n_ratio)
                    self.log(
                        f"  n={n1}→{n2}: time ratio {ratio:.2f}, estimated O(n^{exponent:.2f})"
                    )
                else:
                    self.log(f"  n={n1}→{n2}: time ratio {ratio:.2f} (minimal growth)")

    def save_results(self, filename: str) -> None:
        """Save benchmark results to a JSON file."""

        def safe_extensions_count(count: int) -> str | int:
            """Safely convert extensions_count to a JSON-serializable format."""
            try:
                # Try to convert to string to check if it's too large
                str(count)
                return count  # Return as int if conversion succeeds
            except ValueError:
                # If too large, return a descriptive string
                return f"<large_number_with_{count.bit_length()}_bits>"

        data = {
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_tests": len(self.results),
            },
            "results": [
                {
                    "n": r.n,
                    "cycle_structure": r.cycle_structure,
                    "cycle_type": r.cycle_type,
                    "extensions_count": safe_extensions_count(r.extensions_count),
                    "time_seconds": r.time_seconds,
                    "memory_peak_mb": r.memory_peak_mb,
                    "memory_current_mb": r.memory_current_mb,
                }
                for r in self.results
            ],
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        self.log(f"\nResults saved to {filename}")

    def print_summary(self) -> None:
        """Print a summary of benchmark results."""
        if not self.results:
            self.log("No benchmark results to summarize.")
            return

        self.log("\n" + "=" * 60)
        self.log("BENCHMARK SUMMARY")
        self.log("=" * 60)

        # Group by n
        by_n: dict[int, list[BenchmarkResult]] = {}
        for result in self.results:
            if result.n not in by_n:
                by_n[result.n] = []
            by_n[result.n].append(result)

        print(
            f"{'n':<4} {'Cycle Type':<20} {'Extensions':<12} {'Time(s)':<10} {'Memory(MB)':<12}"
        )
        print("-" * 70)

        for n in sorted(by_n.keys()):
            for result in by_n[n]:
                cycle_str = f"{result.cycle_type}"
                # Format large numbers to avoid string conversion limit
                try:
                    ext_str = str(result.extensions_count)
                    if len(ext_str) > 50:
                        ext_str = (
                            f"{ext_str[:20]}...{ext_str[-20:]} ({len(ext_str)} digits)"
                        )
                except ValueError:
                    # Handle case where number is too large to convert to string
                    ext_str = f"<{result.extensions_count.bit_length()} bits>"
                print(
                    f"{result.n:<4} {cycle_str:<20} {ext_str:<12} "
                    f"{result.time_seconds:<10.4f} {result.memory_peak_mb:<12.2f}"
                )

        # Find patterns
        self.log(
            f"\nFastest computation: {min(self.results, key=lambda r: r.time_seconds).time_seconds:.4f}s"
        )
        self.log(
            f"Slowest computation: {max(self.results, key=lambda r: r.time_seconds).time_seconds:.4f}s"
        )
        self.log(f"Largest n tested: {max(result.n for result in self.results)}")
        self.log(
            f"Highest memory usage: {max(result.memory_peak_mb for result in self.results):.2f}MB"
        )


def main() -> None:
    """Main function for running benchmarks."""
    parser = argparse.ArgumentParser(
        description="Benchmark Latin rectangles extension counting"
    )
    parser.add_argument(
        "--max-n", type=int, default=20, help="Maximum n for scaling test (default: 20)"
    )
    parser.add_argument(
        "--cycle-test-n",
        type=int,
        default=16,
        help="Value of n for cycle structure testing (default: 16)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds for individual computations (default: 30)",
    )
    parser.add_argument(
        "--memory-limit",
        type=float,
        default=1024.0,
        help="Memory limit in MB (default: 1024)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_results.json",
        help="Output file for results (default: benchmark_results.json)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    parser.add_argument(
        "--scaling-only", action="store_true", help="Only run scaling test"
    )
    parser.add_argument(
        "--cycles-only", action="store_true", help="Only run cycle structure test"
    )
    parser.add_argument("--max-only", action="store_true", help="Only find maximum n")

    args = parser.parse_args()

    benchmark = LatinRectangleBenchmark(verbose=not args.quiet)

    if args.max_only:
        benchmark.find_maximum_n(args.timeout, args.memory_limit)
    elif args.scaling_only:
        benchmark.benchmark_scaling(args.max_n, args.timeout)
    elif args.cycles_only:
        benchmark.benchmark_cycle_structures(args.cycle_test_n)
    else:
        # Run all tests
        benchmark.benchmark_scaling(args.max_n, args.timeout)
        benchmark.benchmark_cycle_structures(args.cycle_test_n)
        benchmark.find_maximum_n(args.timeout, args.memory_limit)

    benchmark.print_summary()
    benchmark.save_results(args.output)


if __name__ == "__main__":
    main()
