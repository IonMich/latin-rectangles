"""Regression checks for provenance in frozen scorecard summaries."""

import hashlib
import json

import pytest

from benchmarks.scorecard_v1 import report


@pytest.fixture
def metadata():
    return {
        "fixtures_sha256": hashlib.sha256(report.FIXTURES.read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(report.RUNNER.read_bytes()).hexdigest(),
        "platform": "macOS-arm64",
        "cpu": "Apple M2",
        "python": "3.12.9",
        "hash_seed": 23,
    }


@pytest.mark.parametrize("protocol", ["capacity", "compare"])
def test_stale_measurement_runner_is_rejected(tmp_path, metadata, protocol):
    metadata["runner_sha256"] = "old-runner"
    path = tmp_path / "result.json"
    path.write_text(
        json.dumps({"version": 1, "protocol": protocol, "metadata": metadata})
    )
    with pytest.raises(ValueError, match="frozen scorecard.py"):
        report.read_report(path, protocol)


def test_capacity_requires_its_measured_revision_and_environment(tmp_path, metadata):
    base = {"commit": "1111111", "status": ""}
    candidate = {"commit": "2222222", "status": ""}
    comparison = {"base": base, "candidate": candidate, "metadata": metadata}
    capacity = {
        "version": 1,
        "protocol": "capacity",
        "metadata": metadata,
        "revision": candidate,
        "rungs": [{"width": 8, "status": "worker timeout"}],
    }
    path = tmp_path / "candidate-capacity.json"
    path.write_text(json.dumps(capacity))
    assert "worker timeout" in report.capacity_row("candidate", path, comparison)[-1]
    with pytest.raises(ValueError, match="base revision"):
        report.capacity_row("base", path, comparison)
    capacity["metadata"] = {**metadata, "python": "3.13"}
    path.write_text(json.dumps(capacity))
    with pytest.raises(ValueError, match="different python"):
        report.capacity_row("candidate", path, comparison)
