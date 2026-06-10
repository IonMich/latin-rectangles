#!/usr/bin/env python3
"""Create SVG plots from cycle-type benchmark CSV files.

The plots are intentionally separate files rather than subplots. They show
absolute runtime and memory behavior without choosing a reference method.
"""

from __future__ import annotations

import argparse
import csv
import html
import math
import re
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

CSVRow = dict[str, str]
Point = tuple[float, float]

PALETTE = [
    "#2f6fbb",
    "#c45a17",
    "#2f8f4e",
    "#8b4aa8",
    "#6f6a00",
    "#2c8f8f",
]


@dataclass(frozen=True)
class Series:
    """One named plotted series."""

    name: str
    points: list[Point]


def load_csv(path: Path) -> list[CSVRow]:
    """Load a benchmark CSV, returning an empty list if it is absent."""
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(row: Mapping[str, str], key: str) -> float:
    """Read a float column."""
    value = row.get(key, "")
    return float(value) if value else 0.0


def as_int(row: Mapping[str, str], key: str) -> int:
    """Read an integer column."""
    value = row.get(key, "")
    return int(value) if value else 0


def safe_filename(value: str) -> str:
    """Return a conservative filename fragment."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def format_axis_value(value: float) -> str:
    """Format a compact axis tick label."""
    if value == 0:
        return "0"
    abs_value = abs(value)
    if 0.001 <= abs_value < 10_000:
        return f"{value:.4g}"
    return f"{value:.2e}"


def _domain(values: Sequence[float], *, scale: str) -> tuple[float, float]:
    if scale == "log":
        positive = [value for value in values if value > 0]
        if not positive:
            return 1.0, 10.0
        low = min(positive)
        high = max(positive)
        if low == high:
            return low / 2, high * 2
        return low, high

    low = min(values)
    high = max(values)
    if low == high:
        pad = max(1.0, abs(low) * 0.1)
        return low - pad, high + pad
    pad = (high - low) * 0.05
    return low - pad, high + pad


def _transformer(
    domain: tuple[float, float],
    *,
    scale: str,
    pixel_min: float,
    pixel_max: float,
) -> Callable[[float], float]:
    low, high = domain
    if scale == "log":
        log_low = math.log10(low)
        log_high = math.log10(high)

        def transform_log(value: float) -> float:
            value = max(value, low)
            fraction = (math.log10(value) - log_low) / (log_high - log_low)
            return pixel_min + fraction * (pixel_max - pixel_min)

        return transform_log

    def transform_linear(value: float) -> float:
        fraction = (value - low) / (high - low)
        return pixel_min + fraction * (pixel_max - pixel_min)

    return transform_linear


def _tick_values(domain: tuple[float, float], *, scale: str) -> list[float]:
    low, high = domain
    if scale == "log":
        log_low = math.log10(low)
        log_high = math.log10(high)
        return [10 ** (log_low + (log_high - log_low) * i / 4) for i in range(5)]
    return [low + (high - low) * i / 4 for i in range(5)]


def write_svg_plot(
    path: Path,
    *,
    title: str,
    x_label: str,
    y_label: str,
    series: Sequence[Series],
    x_scale: str = "linear",
    y_scale: str = "log",
    scatter: bool = False,
) -> None:
    """Write a standalone SVG plot."""
    nonempty = [entry for entry in series if entry.points]
    if not nonempty:
        return

    all_x = [x for entry in nonempty for x, _ in entry.points]
    all_y = [y for entry in nonempty for _, y in entry.points if y > 0]
    if not all_x or not all_y:
        return

    width = 960
    height = 560
    left = 90
    right = 30
    top = 70
    bottom = 78
    plot_width = width - left - right
    plot_height = height - top - bottom
    x_domain = _domain(all_x, scale=x_scale)
    y_domain = _domain(all_y, scale=y_scale)

    x_to_px = _transformer(
        x_domain,
        scale=x_scale,
        pixel_min=left,
        pixel_max=left + plot_width,
    )
    y_to_px_unflipped = _transformer(
        y_domain,
        scale=y_scale,
        pixel_min=0,
        pixel_max=plot_height,
    )

    def y_to_px(value: float) -> float:
        return top + plot_height - y_to_px_unflipped(value)

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        "<style>"
        "text{font-family:Arial,Helvetica,sans-serif;fill:#202124}"
        ".axis{stroke:#303134;stroke-width:1.2}"
        ".grid{stroke:#d7dbe0;stroke-width:1}"
        ".label{font-size:14px}"
        ".tick{font-size:12px;fill:#4b5563}"
        ".title{font-size:20px;font-weight:700}"
        ".legend{font-size:13px}"
        "</style>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="34" class="title">{html.escape(title)}</text>',
    ]

    for tick in _tick_values(x_domain, scale=x_scale):
        x = x_to_px(tick)
        lines.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" '
            f'y2="{top + plot_height}" class="grid"/>'
        )
        lines.append(
            f'<text x="{x:.2f}" y="{top + plot_height + 24}" '
            f'text-anchor="middle" class="tick">{format_axis_value(tick)}</text>'
        )

    for tick in _tick_values(y_domain, scale=y_scale):
        y = y_to_px(tick)
        lines.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" '
            f'y2="{y:.2f}" class="grid"/>'
        )
        lines.append(
            f'<text x="{left - 10}" y="{y + 4:.2f}" '
            f'text-anchor="end" class="tick">{format_axis_value(tick)}</text>'
        )

    lines.extend(
        [
            f'<line x1="{left}" y1="{top + plot_height}" '
            f'x2="{left + plot_width}" y2="{top + plot_height}" class="axis"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" '
            f'y2="{top + plot_height}" class="axis"/>',
            f'<text x="{left + plot_width / 2:.2f}" y="{height - 24}" '
            f'text-anchor="middle" class="label">{html.escape(x_label)}</text>',
            f'<text transform="translate(22 {top + plot_height / 2:.2f}) rotate(-90)" '
            f'text-anchor="middle" class="label">{html.escape(y_label)}</text>',
        ]
    )

    legend_x = left + plot_width - 210
    legend_y = top + 4
    for index, entry in enumerate(nonempty):
        color = PALETTE[index % len(PALETTE)]
        sorted_points = sorted(entry.points)
        pixel_points = [
            (x_to_px(x), y_to_px(y))
            for x, y in sorted_points
            if x > 0 or x_scale != "log"
        ]
        pixel_points = [
            (x, y)
            for (x, y), (_, original_y) in zip(
                pixel_points, sorted_points, strict=False
            )
            if original_y > 0
        ]
        if not pixel_points:
            continue

        if not scatter and len(pixel_points) > 1:
            path_data = " ".join(
                f"{'M' if point_index == 0 else 'L'} {x:.2f} {y:.2f}"
                for point_index, (x, y) in enumerate(pixel_points)
            )
            lines.append(
                f'<path d="{path_data}" fill="none" stroke="{color}" '
                'stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>'
            )

        radius = 2.4 if len(pixel_points) <= 2_000 else 1.4
        opacity = 0.78 if scatter else 0.95
        for x, y in pixel_points:
            lines.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius}" '
                f'fill="{color}" opacity="{opacity}"/>'
            )

        y = legend_y + index * 20
        lines.append(
            f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 24}" '
            f'y2="{y}" stroke="{color}" stroke-width="2.8"/>'
        )
        lines.append(
            f'<text x="{legend_x + 32}" y="{y + 4}" class="legend">'
            f"{html.escape(entry.name)}</text>"
        )

    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def series_by_method(
    rows: Sequence[CSVRow],
    *,
    x_key: str,
    y_key: str,
) -> list[Series]:
    """Group rows by method into plotted series."""
    grouped: dict[str, list[Point]] = defaultdict(list)
    for row in rows:
        y = as_float(row, y_key)
        if y <= 0:
            continue
        grouped[row["method"]].append((float(as_int(row, x_key)), y))
    return [
        Series(name=method, points=points)
        for method, points in sorted(grouped.items(), key=lambda item: item[0])
    ]


def aggregate_series_by_method(
    rows: Sequence[CSVRow],
    *,
    y_key: str,
    reducer: str,
) -> list[Series]:
    """Aggregate all-cycle-type rows by n and method."""
    grouped: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in rows:
        value = as_float(row, y_key)
        if value > 0:
            grouped[(row["method"], as_int(row, "n"))].append(value)

    series_map: dict[str, list[Point]] = defaultdict(list)
    for (method, n), values in grouped.items():
        if reducer == "sum":
            reduced = sum(values)
        elif reducer == "max":
            reduced = max(values)
        else:
            raise ValueError(f"Unknown reducer {reducer!r}")
        series_map[method].append((float(n), reduced))

    return [
        Series(method, sorted(points))
        for method, points in sorted(series_map.items(), key=lambda item: item[0])
    ]


def create_family_plots(rows: Sequence[CSVRow], output_dir: Path) -> list[Path]:
    """Create one runtime and one memory plot per cycle family."""
    by_family: dict[str, list[CSVRow]] = defaultdict(list)
    for row in rows:
        by_family[row["family"]].append(row)

    written: list[Path] = []
    for family, family_rows in sorted(by_family.items()):
        filename_family = safe_filename(family)
        runtime_path = output_dir / f"runtime_family_{filename_family}.svg"
        write_svg_plot(
            runtime_path,
            title=f"Runtime for {family}",
            x_label="n",
            y_label="median runtime (seconds)",
            series=series_by_method(
                family_rows,
                x_key="n",
                y_key="time_seconds_median",
            ),
            x_scale="log",
            y_scale="log",
        )
        if runtime_path.exists():
            written.append(runtime_path)

        memory_path = output_dir / f"memory_family_{filename_family}.svg"
        write_svg_plot(
            memory_path,
            title=f"Peak memory for {family}",
            x_label="n",
            y_label="peak tracemalloc memory (MB)",
            series=series_by_method(
                family_rows,
                x_key="n",
                y_key="peak_memory_mb",
            ),
            x_scale="log",
            y_scale="log",
        )
        if memory_path.exists():
            written.append(memory_path)

    return written


def create_all_cycle_type_plots(rows: Sequence[CSVRow], output_dir: Path) -> list[Path]:
    """Create exhaustive fixed-n plots and aggregate plots."""
    by_n: dict[int, list[CSVRow]] = defaultdict(list)
    for row in rows:
        by_n[as_int(row, "n")].append(row)

    written: list[Path] = []
    for n, n_rows in sorted(by_n.items()):
        runtime_index_path = output_dir / f"runtime_all_cycle_types_n_{n}.svg"
        write_svg_plot(
            runtime_index_path,
            title=f"Runtime across all cycle types, n={n}",
            x_label="cycle type index sorted by (cycle count, largest cycle, type)",
            y_label="median runtime (seconds)",
            series=series_by_method(
                n_rows,
                x_key="cycle_type_index",
                y_key="time_seconds_median",
            ),
            x_scale="linear",
            y_scale="log",
        )
        if runtime_index_path.exists():
            written.append(runtime_index_path)

        cycle_count_path = output_dir / f"runtime_vs_cycle_count_n_{n}.svg"
        write_svg_plot(
            cycle_count_path,
            title=f"Runtime vs cycle count, n={n}",
            x_label="number of cycles",
            y_label="median runtime (seconds)",
            series=series_by_method(
                n_rows,
                x_key="cycle_count",
                y_key="time_seconds_median",
            ),
            x_scale="linear",
            y_scale="log",
            scatter=True,
        )
        if cycle_count_path.exists():
            written.append(cycle_count_path)

        largest_cycle_path = output_dir / f"runtime_vs_largest_cycle_n_{n}.svg"
        write_svg_plot(
            largest_cycle_path,
            title=f"Runtime vs largest cycle, n={n}",
            x_label="largest cycle length",
            y_label="median runtime (seconds)",
            series=series_by_method(
                n_rows,
                x_key="largest_cycle",
                y_key="time_seconds_median",
            ),
            x_scale="linear",
            y_scale="log",
            scatter=True,
        )
        if largest_cycle_path.exists():
            written.append(largest_cycle_path)

    aggregate_specs = [
        (
            "runtime_total_all_cycle_types.svg",
            "Total runtime across all cycle types",
            "sum of median runtimes (seconds)",
            "time_seconds_median",
            "sum",
        ),
        (
            "runtime_worst_all_cycle_types.svg",
            "Worst single cycle-type runtime",
            "max median runtime (seconds)",
            "time_seconds_median",
            "max",
        ),
        (
            "memory_worst_all_cycle_types.svg",
            "Worst peak memory across all cycle types",
            "max peak tracemalloc memory (MB)",
            "peak_memory_mb",
            "max",
        ),
    ]
    for filename, title, y_label, y_key, reducer in aggregate_specs:
        path = output_dir / filename
        write_svg_plot(
            path,
            title=title,
            x_label="n",
            y_label=y_label,
            series=aggregate_series_by_method(rows, y_key=y_key, reducer=reducer),
            x_scale="linear",
            y_scale="log",
        )
        if path.exists():
            written.append(path)

    return written


def create_plots(input_dir: Path, output_dir: Path) -> list[Path]:
    """Create every plot available from the benchmark CSVs."""
    family_rows = load_csv(input_dir / "cycle_families.csv")
    all_cycle_rows = load_csv(input_dir / "all_cycle_types.csv")

    written: list[Path] = []
    if family_rows:
        written.extend(create_family_plots(family_rows, output_dir))
    if all_cycle_rows:
        written.extend(create_all_cycle_type_plots(all_cycle_rows, output_dir))
    return written


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Create separate SVG plots from benchmark CSV files."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("benchmark_results/scaling"),
        help="Directory containing benchmark CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_plots/scaling"),
        help="Directory where SVG plots will be written.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Create plots and report output paths."""
    args = parse_args(argv)
    written = create_plots(args.input_dir, args.output_dir)
    if not written:
        print(f"No benchmark CSV data found in {args.input_dir}")
        return
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
