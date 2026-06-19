#!/usr/bin/env python3
"""Render a Karpathy-style progress plot from an OpenEvolve checkpoint."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any

LOWER_IS_BETTER_METRICS = {
    "candidate_weighted_seconds",
    "candidate_total_seconds",
    "evaluation_seconds",
    "worst_regression",
    "max_memory_ratio",
    "candidate_lines",
}

ZERO_BASED_METRICS = {
    "combined_score",
    "correctness",
    "candidate_weighted_seconds",
    "candidate_total_seconds",
    "candidate_inputs_per_second",
}


@dataclass(frozen=True)
class Attempt:
    """One evaluated OpenEvolve program."""

    program_id: str
    iteration: int
    metric: float
    correctness: float
    lines: float
    change_summary: str
    label: str
    is_improvement: bool


def _checkpoint_number(path: Path) -> int:
    match = re.search(r"checkpoint_(\d+)$", path.name)
    return int(match.group(1)) if match else -1


def resolve_checkpoint(path: Path) -> Path:
    """Return a checkpoint directory from either a run directory or checkpoint."""
    if (path / "programs").is_dir():
        return path

    checkpoints = sorted(
        (
            candidate
            for candidate in (path / "checkpoints").glob("checkpoint_*")
            if candidate.is_dir()
        ),
        key=_checkpoint_number,
    )
    if not checkpoints:
        raise FileNotFoundError(f"No checkpoint directory found under {path}")
    return checkpoints[-1]


def _change_summary(raw: dict[str, Any]) -> str:
    """Extract a concise, human-useful change summary when OpenEvolve recorded one."""
    metadata = raw.get("metadata") or {}
    changes = str(metadata.get("changes") or raw.get("changes_description") or "")
    if not changes.strip():
        return ""

    targets: list[str] = []
    for pattern in (
        r"\bdef\s+([A-Za-z_]\w*)\s*\(",
        r"\bclass\s+([A-Za-z_]\w*)\b",
    ):
        for match in re.finditer(pattern, changes):
            target = match.group(1)
            if target not in targets:
                targets.append(target)

    if not targets and re.search(
        r"^\s*(from\s+\S+\s+)?import\s+", changes, re.MULTILINE
    ):
        return "changed imports"
    if not targets:
        return ""
    if len(targets) <= 2:
        return "changed " + " + ".join(targets)
    return "changed " + " + ".join(targets[:2]) + f" + {len(targets) - 2} more"


def _artifact_summary(raw: dict[str, Any]) -> dict[str, Any]:
    """Return the JSON summary artifact when present in an OpenEvolve record."""
    artifacts = raw.get("artifacts") or {}
    if not artifacts and raw.get("artifacts_json"):
        try:
            artifacts = json.loads(str(raw["artifacts_json"]))
        except json.JSONDecodeError:
            artifacts = {}

    summary = artifacts.get("summary")
    if not isinstance(summary, str):
        return {}
    try:
        parsed = json.loads(summary)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _derived_metric(raw: dict[str, Any], metric_name: str) -> float | None:
    """Derive newer absolute timing metrics from older comparison artifacts."""
    summary = _artifact_summary(raw)
    comparisons = summary.get("comparisons") or []
    if not isinstance(comparisons, list):
        return None

    candidate_seconds = [
        float(comparison["candidate_seconds"])
        for comparison in comparisons
        if isinstance(comparison, dict) and "candidate_seconds" in comparison
    ]
    if not candidate_seconds:
        return None

    if metric_name == "candidate_total_seconds":
        return sum(candidate_seconds)

    if metric_name == "candidate_weighted_seconds":
        weights = [
            float(comparison.get("weight", 1.0))
            for comparison in comparisons
            if isinstance(comparison, dict) and "candidate_seconds" in comparison
        ]
        total_weight = sum(weights)
        weighted_seconds = sum(
            weight * seconds
            for weight, seconds in zip(weights, candidate_seconds, strict=True)
        )
        return (
            weighted_seconds / total_weight if total_weight else sum(candidate_seconds)
        )

    return None


def _program_attempt(raw: dict[str, Any], metric_name: str) -> Attempt | None:
    metrics = raw.get("metrics") or {}
    metric = metrics.get(metric_name)
    if metric is None:
        metric = _derived_metric(raw, metric_name)
    if metric is None:
        return None

    return Attempt(
        program_id=str(raw.get("id", "")),
        iteration=int(raw.get("iteration_found") or raw.get("iteration") or 0),
        metric=float(metric),
        correctness=float(metrics.get("correctness", 1.0)),
        lines=float(metrics.get("candidate_lines", 0.0)),
        change_summary=_change_summary(raw),
        label=f"iter {int(raw.get('iteration_found') or raw.get('iteration') or 0)}",
        is_improvement=False,
    )


def _mark_improvements(
    attempts: list[Attempt],
    *,
    lower_is_better: bool,
) -> list[Attempt]:
    """Mark running-best improvements over attempts in display order."""
    best = math.inf if lower_is_better else -math.inf
    marked: list[Attempt] = []
    for attempt in attempts:
        is_valid = attempt.correctness >= 1.0 and math.isfinite(attempt.metric)
        is_improvement = is_valid and (
            attempt.metric < best if lower_is_better else attempt.metric > best
        )
        if is_improvement:
            best = attempt.metric
        marked.append(
            Attempt(
                program_id=attempt.program_id,
                iteration=attempt.iteration,
                metric=attempt.metric,
                correctness=attempt.correctness,
                lines=attempt.lines,
                change_summary=attempt.change_summary,
                label=attempt.label,
                is_improvement=is_improvement,
            )
        )
    return marked


def load_attempts(
    checkpoint: Path, metric_name: str, *, lower_is_better: bool
) -> list[Attempt]:
    """Load attempts and mark running-best improvements."""
    attempts = []
    for program_path in sorted((checkpoint / "programs").glob("*.json")):
        attempt = _program_attempt(json.loads(program_path.read_text()), metric_name)
        if attempt is not None:
            attempts.append(attempt)

    attempts.sort(key=lambda item: (item.iteration, item.program_id))
    return _mark_improvements(attempts, lower_is_better=lower_is_better)


def _metric_from_benchmark_report(report: dict[str, Any], metric_name: str) -> float:
    """Compute plot metrics from a benchmark_touchard_cold_start JSON report."""
    rows = report.get("workloads") or []
    if not isinstance(rows, list) or not rows:
        raise ValueError("Reference benchmark report has no workloads")

    total_seconds = sum(float(row["seconds"]) for row in rows)
    total_weight = sum(float(row.get("weight", 1.0)) for row in rows)
    total_inputs = sum(float(row.get("count_inputs", 0.0)) for row in rows)
    if metric_name == "candidate_total_seconds":
        return total_seconds
    if metric_name == "candidate_weighted_seconds":
        weighted_seconds = sum(
            float(row.get("weight", 1.0)) * float(row["seconds"]) for row in rows
        )
        return weighted_seconds / total_weight if total_weight else total_seconds
    if metric_name == "candidate_inputs_per_second":
        return total_inputs / total_seconds if total_seconds > 0 else 0.0
    raise ValueError(
        f"Cannot derive {metric_name!r} from a benchmark report. "
        "Use candidate_weighted_seconds, candidate_total_seconds, or "
        "candidate_inputs_per_second."
    )


def load_reference_attempt(
    report_path: Path,
    *,
    metric_name: str,
    label: str,
) -> Attempt:
    """Load a reference point from a benchmark report."""
    report = json.loads(report_path.read_text())
    correctness = (
        1.0
        if all(row.get("status") == "ok" for row in report.get("workloads", []))
        else 0.0
    )
    return Attempt(
        program_id=label,
        iteration=-1,
        metric=_metric_from_benchmark_report(report, metric_name),
        correctness=correctness,
        lines=0.0,
        change_summary=label,
        label=label,
        is_improvement=False,
    )


def _scale(
    value: float, low: float, high: float, pixel_low: float, pixel_high: float
) -> float:
    if high == low:
        return (pixel_low + pixel_high) / 2
    return pixel_low + (value - low) * (pixel_high - pixel_low) / (high - low)


def _nice_step(raw_step: float) -> float:
    """Return a human-friendly tick step at 1, 2, 2.5, 5, or 10 x magnitude."""
    if raw_step <= 0:
        return 1.0
    magnitude = 10 ** math.floor(math.log10(raw_step))
    normalized = raw_step / magnitude
    if normalized <= 1:
        nice = 1.0
    elif normalized <= 2:
        nice = 2.0
    elif normalized <= 2.5:
        nice = 2.5
    elif normalized <= 5:
        nice = 5.0
    else:
        nice = 10.0
    return nice * magnitude


def _nice_axis_bounds(
    values: list[float], *, include_zero: bool
) -> tuple[float, float, list[float]]:
    """Return clean axis bounds and tick values for plotted metrics."""
    value_min = min(values)
    value_max = max(values)
    if include_zero:
        value_min = min(0.0, value_min)
        value_max = max(0.0, value_max)
    if value_min == value_max:
        pad = max(abs(value_max) * 0.10, 1.0)
        value_min -= pad
        value_max += pad

    step = _nice_step((value_max - value_min) / 4)
    axis_min = math.floor(value_min / step) * step
    axis_max = math.ceil(value_max / step) * step
    ticks: list[float] = []
    current = axis_min
    while current <= axis_max + step / 2:
        ticks.append(0.0 if abs(current) < step / 1_000_000 else current)
        current += step
    return axis_min, axis_max, ticks


def _format_tick(value: float) -> str:
    """Format tick values without distracting floating-point noise."""
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _display_unit(values: list[float], metric_name: str) -> tuple[float, str]:
    """Return a display multiplier/unit for readability."""
    if not metric_name.endswith("_seconds") and metric_name != "evaluation_seconds":
        return 1.0, ""
    max_value = max(abs(value) for value in values)
    if max_value < 1.0:
        return 1000.0, "ms"
    return 1.0, "s"


def _metric_label(
    metric_name: str,
    *,
    lower_is_better: bool,
    display_unit: str,
) -> str:
    """Return a readable axis label for known evaluator metrics."""
    labels = {
        "combined_score": "Combined score: 0 wrong, 1 baseline, >1 faster",
        "candidate_weighted_seconds": "Candidate weighted time",
        "candidate_total_seconds": "Candidate total time",
        "candidate_inputs_per_second": "Candidate inputs per second",
        "geomean_speedup": "Geometric mean speedup",
        "weighted_log_speedup": "Weighted log speedup",
        "correctness": "Correctness",
        "worst_regression": "Worst regression",
        "candidate_lines": "Candidate lines",
    }
    label = labels.get(metric_name, metric_name.replace("_", " ").title())
    if display_unit:
        label = f"{label} ({display_unit})"
    direction = "lower is better" if lower_is_better else "higher is better"
    return f"{label} ({direction})"


def _metric_note(metric_name: str, *, display_unit: str) -> str:
    """Return a short, plot-level definition for common metrics."""
    unit_prefix = f"Plotted in {display_unit}. " if display_unit else ""
    notes = {
        "candidate_weighted_seconds": (
            unit_prefix
            + "Raw metric: candidate_weighted_seconds = sum(weight_i * candidate_seconds_i) / "
            "sum(weight_i) over the fixed workload suite."
        ),
        "candidate_total_seconds": (
            unit_prefix
            + "Raw metric: candidate_total_seconds = sum(candidate_seconds_i) "
            "over the fixed workload suite."
        ),
        "candidate_inputs_per_second": (
            "candidate_inputs_per_second = total cycle types evaluated / total candidate seconds."
        ),
        "combined_score": (
            "combined_score = 0 if wrong; else max(0, geomean_speedup - "
            "0.25*max(0, worst_regression-0.10))."
        ),
        "geomean_speedup": "Weighted geometric mean of baseline time divided by candidate time.",
        "weighted_log_speedup": "Weighted mean log speedup; zero means parity with baseline.",
        "correctness": "One means the candidate matched every exact result digest.",
        "worst_regression": "Largest single-workload slowdown relative to baseline.",
    }
    return notes.get(
        metric_name, unit_prefix + "Metric reported by the OpenEvolve evaluator."
    )


def render_svg(
    attempts: list[Attempt],
    *,
    metric_name: str,
    lower_is_better: bool,
    width: int = 1100,
    height: int = 620,
) -> str:
    """Render attempts as an SVG scatter plot."""
    if not attempts:
        raise ValueError("No attempts to plot")

    margin_left = 78
    margin_right = 34
    margin_top = 54
    margin_bottom = 74
    plot_left = margin_left
    plot_right = width - margin_right
    plot_top = margin_top
    plot_bottom = height - margin_bottom

    raw_finite_metrics = [
        attempt.metric for attempt in attempts if math.isfinite(attempt.metric)
    ]
    display_multiplier, display_unit = _display_unit(raw_finite_metrics, metric_name)
    finite_metrics = [value * display_multiplier for value in raw_finite_metrics]
    y_min, y_max, tick_values = _nice_axis_bounds(
        finite_metrics,
        include_zero=metric_name in ZERO_BASED_METRICS and min(finite_metrics) >= 0,
    )

    x_values = [
        attempt.iteration if attempt.iteration >= 0 else 0 for attempt in attempts
    ]
    x_min, x_max, x_tick_values = _nice_axis_bounds(
        [float(value) for value in x_values],
        include_zero=min(x_values) >= 0,
    )

    def x_pos(iteration: int) -> float:
        value = iteration if iteration >= 0 else 0
        return _scale(value, x_min, x_max, plot_left, plot_right)

    def y_pos(metric: float) -> float:
        return _scale(metric * display_multiplier, y_min, y_max, plot_bottom, plot_top)

    best_points: list[tuple[float, float]] = []
    best = math.inf if lower_is_better else -math.inf
    for attempt in attempts:
        is_valid = attempt.correctness >= 1.0 and math.isfinite(attempt.metric)
        if is_valid and (
            attempt.metric < best if lower_is_better else attempt.metric > best
        ):
            best = attempt.metric
        if math.isfinite(best):
            best_points.append((x_pos(attempt.iteration), y_pos(best)))

    best_path = ""
    if best_points:
        path_parts = [f"M {best_points[0][0]:.1f} {best_points[0][1]:.1f}"]
        for (_, prev_y), (x, y) in pairwise(best_points):
            path_parts.append(f"L {x:.1f} {prev_y:.1f} L {x:.1f} {y:.1f}")
        best_path = " ".join(path_parts)

    circles = []
    reference_labels = []
    for attempt in attempts:
        x = x_pos(attempt.iteration)
        y = y_pos(attempt.metric)
        if attempt.correctness < 1.0:
            color = "#d94848"
            opacity = "0.25"
            radius = "5"
        elif attempt.is_improvement:
            color = "#1f9d55"
            opacity = "0.95"
            radius = "7"
        else:
            color = "#9ca3af"
            opacity = "0.42"
            radius = "5"
        detail = (
            f", {attempt.change_summary}"
            if attempt.change_summary and attempt.change_summary != attempt.label
            else ""
        )
        title = html.escape(
            f"{attempt.label}, {metric_name}="
            f"{_format_tick(attempt.metric * display_multiplier)}"
            f"{display_unit}, "
            f"correctness={attempt.correctness:.0f}, lines={attempt.lines:.0f}" + detail
        )
        circles.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{color}" '
            f'fill-opacity="{opacity}"><title>{title}</title></circle>'
        )
        if attempt.iteration < 0:
            reference_labels.append(
                f'<text x="{min(x + 9, plot_right - 100):.1f}" '
                f'y="{max(y - 8, plot_top + 13):.1f}" font-size="11" '
                f'fill="#374151">{html.escape(attempt.label)}</text>'
            )

    y_ticks = []
    for value in tick_values:
        y = _scale(value, y_min, y_max, plot_bottom, plot_top)
        y_ticks.append(
            f'<line x1="{plot_left}" y1="{y:.1f}" x2="{plot_right}" y2="{y:.1f}" '
            f'stroke="#e5e7eb" />'
            f'<text x="{plot_left - 10}" y="{y + 4:.1f}" text-anchor="end" '
            f'font-size="12" fill="#4b5563">{_format_tick(value)}</text>'
        )

    x_ticks = []
    for value in x_tick_values:
        x = _scale(value, x_min, x_max, plot_left, plot_right)
        x_ticks.append(
            f'<line x1="{x:.1f}" y1="{plot_bottom}" x2="{x:.1f}" y2="{plot_bottom + 6}" '
            f'stroke="#6b7280" />'
            f'<text x="{x:.1f}" y="{plot_bottom + 23}" text-anchor="middle" '
            f'font-size="12" fill="#4b5563">{_format_tick(value)}</text>'
        )

    metric_label = _metric_label(
        metric_name,
        lower_is_better=lower_is_better,
        display_unit=display_unit,
    )
    metric_note = _metric_note(metric_name, display_unit=display_unit)
    best_attempt = max(
        (attempt for attempt in attempts if attempt.correctness >= 1.0),
        key=lambda attempt: -attempt.metric if lower_is_better else attempt.metric,
        default=None,
    )
    best_label = ""
    if best_attempt is not None:
        label = (
            f"best {_format_tick(best_attempt.metric * display_multiplier)}"
            f"{display_unit}"
        )
        if best_attempt.change_summary:
            label += f"; {best_attempt.change_summary}"
        best_label = (
            f'<text x="{min(x_pos(best_attempt.iteration) + 10, plot_right - 90):.1f}" '
            f'y="{max(y_pos(best_attempt.metric) - 10, plot_top + 14):.1f}" '
            f'font-size="12" font-weight="700" fill="#166534">'
            f"{html.escape(label)}</text>"
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="{margin_left}" y="30" font-size="20" font-weight="700" fill="#111827">OpenEvolve Attempts</text>
  <text x="{margin_left}" y="49" font-size="13" fill="#4b5563">{html.escape(metric_note)}</text>
  {"".join(y_ticks)}
  <line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" stroke="#111827"/>
  <line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" y2="{plot_bottom}" stroke="#111827"/>
  {"".join(x_ticks)}
  <path d="{best_path}" fill="none" stroke="#15803d" stroke-width="2.4" stroke-opacity="0.8"/>
  {"".join(circles)}
  {"".join(reference_labels)}
  {best_label}
  <text x="{(plot_left + plot_right) / 2:.1f}" y="{height - 24}" text-anchor="middle" font-size="13" fill="#374151">Iteration</text>
  <text x="20" y="{(plot_top + plot_bottom) / 2:.1f}" text-anchor="middle" font-size="13" fill="#374151" transform="rotate(-90 20 {(plot_top + plot_bottom) / 2:.1f})">{html.escape(metric_label)}</text>
  <circle cx="{width - 245}" cy="29" r="6" fill="#1f9d55"/><text x="{width - 233}" y="33" font-size="12" fill="#374151">new best</text>
  <circle cx="{width - 160}" cy="29" r="5" fill="#9ca3af" fill-opacity="0.42"/><text x="{width - 148}" y="33" font-size="12" fill="#374151">valid</text>
  <circle cx="{width - 88}" cy="29" r="5" fill="#d94848" fill-opacity="0.25"/><text x="{width - 76}" y="33" font-size="12" fill="#374151">failed</text>
</svg>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot OpenEvolve attempts from a run or checkpoint directory."
    )
    parser.add_argument(
        "path", type=Path, help="OpenEvolve output directory or checkpoint"
    )
    parser.add_argument(
        "--metric",
        default="candidate_weighted_seconds",
        help="Metric to plot.",
    )
    direction = parser.add_mutually_exclusive_group()
    direction.add_argument(
        "--lower-is-better",
        action="store_true",
        dest="lower_is_better",
        help="Treat lower metric values as improvements.",
    )
    direction.add_argument(
        "--higher-is-better",
        action="store_false",
        dest="lower_is_better",
        help="Treat higher metric values as improvements.",
    )
    parser.set_defaults(lower_is_better=None)
    parser.add_argument("--output", type=Path, help="Output SVG path")
    parser.add_argument(
        "--reference-report",
        type=Path,
        help="Optional benchmark JSON report to plot before OpenEvolve attempts.",
    )
    parser.add_argument(
        "--reference-label",
        default="reference",
        help="Label for --reference-report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checkpoint = resolve_checkpoint(args.path)
    lower_is_better = (
        args.lower_is_better
        if args.lower_is_better is not None
        else args.metric in LOWER_IS_BETTER_METRICS
    )
    attempts = load_attempts(
        checkpoint,
        args.metric,
        lower_is_better=lower_is_better,
    )
    if args.reference_report is not None:
        reference = load_reference_attempt(
            args.reference_report,
            metric_name=args.metric,
            label=args.reference_label,
        )
        attempts = _mark_improvements(
            [reference, *attempts],
            lower_is_better=lower_is_better,
        )
    output = args.output or checkpoint / f"{args.metric}_progress.svg"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_svg(
            attempts,
            metric_name=args.metric,
            lower_is_better=lower_is_better,
        )
    )
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
