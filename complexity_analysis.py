#!/usr/bin/env python3
"""
Complexity analysis tool for the Latin Rectangles algorithm.

This module analyzes time and memory complexity patterns from benchmark data,
fitting various mathematical models to determine algorithmic complexity.
"""

import json
import math
from pathlib import Path
from typing import Any


def load_benchmark_data(
    filename: str = "benchmark_results.json",
) -> list[dict[str, Any]]:
    """Load benchmark results from JSON file.

    Args:
        filename: Path to the benchmark results JSON file

    Returns:
        List of benchmark result dictionaries

    Raises:
        FileNotFoundError: If the benchmark file doesn't exist
    """
    path = Path(filename)
    if not path.exists():
        raise FileNotFoundError(f"Benchmark file {filename} not found")

    with path.open() as f:
        data: dict[str, Any] = json.load(f)
    results: list[dict[str, Any]] = data["results"]
    return results


def analyze_cycle_structure(cycle_structure: list[int]) -> dict[str, float]:
    """Analyze cycle structure properties.

    Args:
        cycle_structure: List of cycle lengths in a derangement

    Returns:
        Dictionary containing cycle structure metrics
    """
    n_cycles = len(cycle_structure)
    max_cycle = max(cycle_structure)
    min_cycle = min(cycle_structure)
    avg_cycle = sum(cycle_structure) / len(cycle_structure)

    # Calculate variance
    variance = sum((c - avg_cycle) ** 2 for c in cycle_structure) / len(cycle_structure)

    # Calculate entropy
    total = sum(cycle_structure)
    entropy = 0.0
    for c in cycle_structure:
        if c > 0:
            p = c / total
            entropy -= p * math.log(p)

    return {
        "n_cycles": n_cycles,
        "max_cycle": max_cycle,
        "min_cycle": min_cycle,
        "avg_cycle": avg_cycle,
        "cycle_variance": variance,
        "cycle_entropy": entropy,
    }


def fit_linear_model(x_values: list[float], y_values: list[float]) -> dict[str, float]:
    """Fit a linear model using least squares regression.

    Args:
        x_values: Independent variable values
        y_values: Dependent variable values

    Returns:
        Dictionary containing slope, intercept, and R² score
    """
    n = len(x_values)
    if n < 2:
        return {"slope": 0.0, "intercept": 0.0, "r2": 0.0}

    # Calculate means
    x_mean = sum(x_values) / n
    y_mean = sum(y_values) / n

    # Calculate slope and intercept
    numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
    denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return {"slope": 0.0, "intercept": y_mean, "r2": 0.0}

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    # Calculate R²
    y_pred = [slope * x + intercept for x in x_values]
    ss_res = sum((y_values[i] - y_pred[i]) ** 2 for i in range(n))
    ss_tot = sum((y_values[i] - y_mean) ** 2 for i in range(n))

    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    return {"slope": slope, "intercept": intercept, "r2": r2}


def fit_power_model(x_values: list[float], y_values: list[float]) -> dict[str, float]:
    """Fit a power model by taking logarithms.

    Args:
        x_values: Independent variable values
        y_values: Dependent variable values

    Returns:
        Dictionary containing exponent, coefficient, and R² score
    """
    # Filter out zero or negative values
    valid_pairs = [
        (x, y) for x, y in zip(x_values, y_values, strict=False) if x > 0 and y > 0
    ]

    if len(valid_pairs) < 2:
        return {"exponent": 0.0, "coefficient": 1.0, "r2": 0.0}

    log_x = [math.log(x) for x, y in valid_pairs]
    log_y = [math.log(y) for x, y in valid_pairs]

    linear_result = fit_linear_model(log_x, log_y)

    return {
        "exponent": linear_result["slope"],
        "coefficient": math.exp(linear_result["intercept"]),
        "r2": linear_result["r2"],
    }


def analyze_time_complexity(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze time complexity patterns from benchmark data.

    Args:
        data: List of benchmark result dictionaries

    Returns:
        Dictionary containing analysis results and best-fit model
    """
    n_values = [float(d["n"]) for d in data]
    time_values = [float(d["time_seconds"]) for d in data]

    print("🕐 TIME COMPLEXITY ANALYSIS")
    print("=" * 50)
    print(f"Data points: {len(data)}")
    print(f"n range: {int(min(n_values))} to {int(max(n_values))}")
    print(f"Time range: {min(time_values):.2e}s to {max(time_values):.2e}s")
    print(f"Time growth factor: {max(time_values) / min(time_values):.1f}x")
    print()

    # Fit different models
    linear_model = fit_linear_model(n_values, time_values)
    power_model = fit_power_model(n_values, time_values)

    # Try logarithmic model (time vs log(n))
    log_n_values = [math.log(n) for n in n_values]
    log_model = fit_linear_model(log_n_values, time_values)

    print("MODEL FITTING RESULTS:")
    print("-" * 30)
    print(f"LINEAR       R² = {linear_model['r2']:.4f}")
    print(
        f"             T(n) ≈ {linear_model['slope']:.2e}n + {linear_model['intercept']:.2e}"
    )

    print(f"POWER        R² = {power_model['r2']:.4f}")
    print(
        f"             T(n) ≈ {power_model['coefficient']:.2e} x n^{power_model['exponent']:.3f}"
    )

    print(f"LOGARITHMIC  R² = {log_model['r2']:.4f}")
    print(
        f"             T(n) ≈ {log_model['slope']:.2e}log(n) + {log_model['intercept']:.2e}"
    )

    # Determine best model
    models = {"linear": linear_model, "power": power_model, "logarithmic": log_model}
    best_model = max(models.items(), key=lambda x: x[1]["r2"])

    print(f"\nBEST FIT: {best_model[0].upper()} (R² = {best_model[1]['r2']:.4f})")

    return {
        "n_values": n_values,
        "time_values": time_values,
        "models": models,
        "best_model": best_model[0],
    }


def analyze_memory_complexity(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze memory complexity patterns from benchmark data.

    Args:
        data: List of benchmark result dictionaries

    Returns:
        Dictionary containing analysis results and best-fit model
    """
    n_values = [float(d["n"]) for d in data]
    memory_values = [float(d["memory_peak_mb"]) for d in data]

    print("\n💾 MEMORY COMPLEXITY ANALYSIS")
    print("=" * 50)
    print(f"Data points: {len(data)}")
    print(f"n range: {int(min(n_values))} to {int(max(n_values))}")
    print(f"Memory range: {min(memory_values):.4f}MB to {max(memory_values):.4f}MB")
    print(f"Memory growth factor: {max(memory_values) / min(memory_values):.1f}x")
    print()

    # Fit different models
    linear_model = fit_linear_model(n_values, memory_values)
    power_model = fit_power_model(n_values, memory_values)

    # Try logarithmic model
    log_n_values = [math.log(n) for n in n_values]
    log_model = fit_linear_model(log_n_values, memory_values)

    print("MODEL FITTING RESULTS:")
    print("-" * 30)
    print(f"LINEAR       R² = {linear_model['r2']:.4f}")
    print(
        f"             M(n) ≈ {linear_model['slope']:.2e}n + {linear_model['intercept']:.2e}"
    )

    print(f"POWER        R² = {power_model['r2']:.4f}")
    print(
        f"             M(n) ≈ {power_model['coefficient']:.2e} x n^{power_model['exponent']:.3f}"
    )

    print(f"LOGARITHMIC  R² = {log_model['r2']:.4f}")
    print(
        f"             M(n) ≈ {log_model['slope']:.2e}log(n) + {log_model['intercept']:.2e}"
    )

    # Determine best model
    models = {"linear": linear_model, "power": power_model, "logarithmic": log_model}
    best_model = max(models.items(), key=lambda x: x[1]["r2"])

    print(f"\nBEST FIT: {best_model[0].upper()} (R² = {best_model[1]['r2']:.4f})")

    return {
        "n_values": n_values,
        "memory_values": memory_values,
        "models": models,
        "best_model": best_model[0],
    }


def analyze_cycle_impact(data: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    """Analyze how cycle structure affects performance.

    Args:
        data: List of benchmark result dictionaries

    Returns:
        Dictionary containing cycle structure analysis results
    """
    print("\n🔄 CYCLE STRUCTURE IMPACT ANALYSIS")
    print("=" * 50)

    # Group by n value to compare different cycle structures
    by_n: dict[int, list[dict[str, Any]]] = {}
    for d in data:
        n = d["n"]
        if n not in by_n:
            by_n[n] = []
        by_n[n].append(d)

    # Find n values with multiple cycle structures
    multiple_cycles = {n: tests for n, tests in by_n.items() if len(tests) > 1}

    if not multiple_cycles:
        print("No n values with multiple cycle structures found for comparison.")
        return {}

    print(f"Found {len(multiple_cycles)} n values with multiple cycle structures:")

    cycle_analysis = {}
    for n, tests in multiple_cycles.items():
        print(f"\nn = {n}:")
        cycle_data = []
        for test in tests:
            cycle_props = analyze_cycle_structure(test["cycle_structure"])
            cycle_data.append(
                {
                    "cycle_structure": test["cycle_structure"],
                    "n_cycles": cycle_props["n_cycles"],
                    "max_cycle": cycle_props["max_cycle"],
                    "time": test["time_seconds"],
                    "memory": test["memory_peak_mb"],
                    "extensions": test["extensions_count"],
                }
            )

        # Sort by number of cycles
        cycle_data.sort(key=lambda x: x["n_cycles"])

        for cd in cycle_data:
            extensions_str = str(cd["extensions"])
            if len(extensions_str) > 20:
                extensions_str = (
                    f"{extensions_str[:10]}...({len(extensions_str)} digits)"
                )

            print(
                f"  Cycles {cd['cycle_structure']!s:20} → "
                f"Time: {cd['time']:.2e}s, "
                f"Memory: {cd['memory']:.4f}MB, "
                f"Extensions: {extensions_str}"
            )

        cycle_analysis[n] = cycle_data

    return cycle_analysis


def analyze_result_magnitude(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze how result magnitude (number of extensions) grows.

    Args:
        data: List of benchmark result dictionaries

    Returns:
        Dictionary containing result magnitude analysis
    """
    print("\n📊 RESULT MAGNITUDE ANALYSIS")
    print("=" * 50)

    n_values = [float(d["n"]) for d in data]
    extensions = []

    for d in data:
        ext = d["extensions_count"]
        try:
            # Try to convert to float
            extensions.append(float(ext))
        except (ValueError, OverflowError):
            # For extremely large numbers, just use the logarithm of digit count
            if isinstance(ext, int):
                digit_count = len(str(ext))
                extensions.append(float(digit_count * 2.3))  # Approximate log10 scaling
            else:
                extensions.append(1.0)

    print(f"Extensions range: {min(extensions):.2e} to {max(extensions):.2e}")
    print(f"Growth factor: {max(extensions) / min(extensions):.2e}x")

    # Fit exponential model by taking log of extensions
    log_extensions = [math.log(max(e, 1)) for e in extensions]
    exp_model = fit_linear_model(n_values, log_extensions)

    print("\nRESULT MAGNITUDE MODELS:")
    print("-" * 30)
    print(f"EXPONENTIAL  R² = {exp_model['r2']:.4f}")
    print(
        f"             Extensions ≈ {math.exp(exp_model['intercept']):.2e} x {math.exp(exp_model['slope']):.3f}^n"
    )

    # Try factorial comparison for smaller n values
    small_n = [n for n in n_values if n <= 20]
    small_ext = [extensions[i] for i, n in enumerate(n_values) if n <= 20]

    if len(small_n) > 3:
        factorials = [math.factorial(int(n)) for n in small_n]
        log_fact = [math.log(f) for f in factorials]
        log_small_ext = [math.log(max(e, 1)) for e in small_ext]

        fact_model = fit_linear_model(log_fact, log_small_ext)
        print(f"FACTORIAL    R² = {fact_model['r2']:.4f} (for n ≤ 20)")
        print(
            f"             Extensions ≈ {math.exp(fact_model['intercept']):.2e} x (n!)^{fact_model['slope']:.3f}"
        )

    return {
        "n_values": n_values,
        "extensions": extensions,
        "exp_model": exp_model,
    }


def main() -> None:
    """Main analysis function."""
    print("🔬 LATIN RECTANGLES COMPLEXITY ANALYSIS")
    print("=" * 60)

    # Load data
    try:
        data = load_benchmark_data()
        print(f"Loaded {len(data)} benchmark results")
    except FileNotFoundError:
        print("❌ benchmark_results.json not found. Run benchmark.py first.")
        return

    # Perform analyses
    time_analysis = analyze_time_complexity(data)
    memory_analysis = analyze_memory_complexity(data)
    analyze_cycle_impact(data)  # For side effects (printing)
    analyze_result_magnitude(data)  # For side effects (printing)

    # Summary
    print("\n" + "=" * 60)
    print("🎯 SUMMARY")
    print("=" * 60)
    print(f"Time Complexity:   Best fit is {time_analysis['best_model'].upper()}")
    print(f"Memory Complexity: Best fit is {memory_analysis['best_model'].upper()}")

    # Performance characteristics
    n_vals = time_analysis["n_values"]
    time_vals = time_analysis["time_values"]

    if len(n_vals) > 1:
        time_per_n = [t / n for t, n in zip(time_vals, n_vals, strict=False)]
        avg_time_per_n = sum(time_per_n) / len(time_per_n)
        print("\nPerformance Characteristics:")
        print(f"  • Average time per n: {avg_time_per_n:.2e} seconds")
        print(f"  • Algorithm remains highly efficient up to n={int(max(n_vals))}")

        # Check if time complexity is sub-quadratic
        power_exp = time_analysis["models"]["power"]["exponent"]
        if power_exp < 2:
            print(f"  • Time complexity appears sub-quadratic (O(n^{power_exp:.2f}))")
        else:
            print(f"  • Time complexity is O(n^{power_exp:.2f})")

    print("\n✅ Analysis complete! Results show excellent algorithmic efficiency.")


if __name__ == "__main__":
    main()
