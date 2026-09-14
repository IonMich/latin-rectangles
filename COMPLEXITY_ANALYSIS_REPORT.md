# Historical scaling measurements

The [stored benchmark data](benchmark_results.json) records 797 measurements,
one random derangement for each n from 4 through 800, dated 6 June 2025. It
captures the specialized one-row counter used at that time. The measurements
predate the current release and its method-selection changes.

Over that sample, recorded runtimes ranged from **25.6 μs to 276 ms**, and the
largest answer, at n=800, had **1,977 decimal digits**. The fitted runtime trend
was approximately proportional to n² over the measured range.

For dated comparisons of the current method families and commands for fresh
measurements, see [benchmarks and computational costs](docs/benchmarks.md).

## Recorded measurements and fitted trends

The fits below have been checked against the stored data using
`fit_power_model` in [complexity_analysis.py](complexity_analysis.py). This
recomputes a regression on existing measurements; it does not time the current
implementation.

| Quantity | Recorded range | Historical power fit | R² in log space |
|---|---|---|---:|
| Runtime | 25.6 μs–276 ms | T(n) ≈ 2.945 × 10⁻⁷ n<sup>2.009</sup> seconds | 0.9812 |
| Peak traced allocation | 0.516–315.4 KiB | M(n) ≈ 2.469 × 10⁻⁵ n<sup>1.360</sup> MiB | 0.9790 |

The JSON field is named `memory_peak_mb`, but the
[benchmark implementation](benchmark.py) divides bytes by 1024², so its unit
is **MiB**. Memory is measured with `tracemalloc` during a counted call. It
measures traced allocations, not total process memory or allocations already
present when tracing starts. Timing also includes the cost of tracing.

## How to interpret the fits

- The exponent 2.009 describes a near-quadratic empirical trend over this
  sample. It does not prove an O(n²) runtime bound or predict every cycle type.
- The exponent 1.360 is **superlinear and subquadratic**. The earlier report's
  description of it as “sub-linear” was incorrect.
- The fitter regresses log(y) against log(n), so these R² values describe the
  log-transformed response. They cannot be ranked directly against the
  original-scale R² values of the linear and logarithmic fits previously shown.
- Arithmetic-operation bounds and measured wall time describe different
  quantities. Large integer multiplication, coefficient construction and cache
  state affect the time and memory of exact counting.

## Measurement scope

The stored metadata contains a timestamp and record count; it does not record
hardware, OS/Python versions, a source commit, random seed or cache protocol.
There is one saved observation per n and no per-input timing sample series.
The data therefore does not support claims of controlled hardware conditions,
repeated-run averages, timing uncertainty or a universal crossover point.

The sampled cycle structure changes with n. That makes the fitted curve a
summary of this set of inputs, rather than a fixed-family or worst-case bound.
Use the separate fixed-family and exhaustive-cycle benchmarks to study those
questions. The historical memory fit does not establish a bound on the current
implementation's caches or on the general k-row algorithm.

## Result magnitude and comparisons

The recorded extension counts are exact integers. The earlier exponential
curve for their magnitude is omitted: the analysis routine substitutes a
proxy when an integer cannot be converted to a float, then mixes those proxies
with ordinary count values. That fitted curve does not reliably describe count
growth. The short-range factorial fit likewise does not establish an
asymptotic law.

No factorial-time or cubic-time implementation was timed in this dataset.
Consequently, claims such as “30× faster than cubic scaling” cannot be inferred
from these fits. The measured method comparisons in
[docs/benchmarks.md](docs/benchmarks.md#measured-method-comparisons) use explicit
baselines on the same inputs and cache conditions.
