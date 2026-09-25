from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPARE_POLICY_MATRIX = REPO_ROOT / "tools" / "compare_policy_matrix.py"
MATRIX_CONFIG = REPO_ROOT / "configs" / "unit_matrix.json"


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _run_policy_matrix(matrix_path: Path, out_dir: Path, cwd: Path | None = None):
    subprocess.check_call(
        [sys.executable, str(COMPARE_POLICY_MATRIX), str(matrix_path), "--count", "1", "--out-dir", str(out_dir)],
        cwd=str(cwd or REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


def test_compare_policy_matrix_relative_out_dir_resolves_under_cwd():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp).resolve()
        cwd_root = tmp_root / "cwd"
        cwd_root.mkdir(parents=True, exist_ok=True)
        relative_out = cwd_root / "relative-policy-matrix"

        matrix_path = MATRIX_CONFIG.resolve()
        _run_policy_matrix(matrix_path, Path("relative-policy-matrix"), cwd=cwd_root)

        report_path = relative_out / "policy_matrix_report.json"
        assert report_path.exists(), "relative out-dir should be resolved against the current working directory"
        report = _read_json(report_path)
        assert report["matrix"] == str(matrix_path)
        assert report["out_dir"] == str(relative_out)
        assert len(report["items"]) == len(json.loads(MATRIX_CONFIG.read_text(encoding="utf-8"))["configs"])

        summary_path = relative_out / "policy_matrix_summary.csv"
        assert summary_path.exists()
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == len(report["items"])


def test_compare_policy_matrix_absolute_out_dir_uses_absolute_report():
    with tempfile.TemporaryDirectory() as tmp:
        absolute_out = Path(tmp).resolve()
        matrix_path = MATRIX_CONFIG.resolve()

        _run_policy_matrix(matrix_path, absolute_out)

        report_path = absolute_out / "policy_matrix_report.json"
        assert report_path.exists()
        report = _read_json(report_path)
        assert report["matrix"] == str(matrix_path)
        assert report["out_dir"] == str(absolute_out)
        assert report["items"]
