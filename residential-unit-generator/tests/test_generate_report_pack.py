from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import tools.generate_report_pack as report_pack


def test_generate_report_pack_calls_unit_policy_and_dashboard_steps():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp).resolve()
        matrix_path = tmp_root / "matrix.json"
        matrix_path.write_text('{"configs": ["configs/studio.json"]}', encoding="utf-8")
        out_dir = tmp_root / "out"

        calls = []

        def fake_check_call(args):
            calls.append(("check_call", args))

        def fake_run(args, cwd, stdout, check):
            calls.append(("run", args, cwd, stdout, check))

        with patch.object(report_pack, "_run", side_effect=fake_check_call), patch.object(report_pack.subprocess, "run", side_effect=fake_run), patch.object(sys, "argv", [
            "generate_report_pack.py",
            str(matrix_path),
            "--unit-count",
            "7",
            "--policy-count",
            "3",
            "--out-dir",
            str(out_dir),
        ]):
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = report_pack.main()

        assert exit_code == 0
        assert len(calls) == 3
        assert calls[0][0] == "check_call"
        assert calls[1][0] == "check_call"
        assert calls[2][0] == "run"

        unit_args = calls[0][1]
        policy_args = calls[1][1]
        dashboard_args = calls[2][1]

        assert "run_unit_matrix.py" in unit_args[1]
        assert str(matrix_path) in unit_args
        assert "--count" in unit_args
        assert "7" in unit_args
        assert str(out_dir / "unit_matrix") in unit_args

        assert "compare_policy_matrix.py" in policy_args[1]
        assert str(matrix_path) in policy_args
        assert "--count" in policy_args
        assert "3" in policy_args
        assert str(out_dir / "policy_matrix") in policy_args

        assert "make_dashboard.py" in dashboard_args[1]
        assert str(out_dir / "unit_matrix" / "matrix_report.json") in dashboard_args
        assert str(out_dir / "policy_matrix" / "policy_matrix_report.json") in dashboard_args
        assert str(out_dir / "dashboard.html") in dashboard_args
        assert "--pack-summary" in dashboard_args
        assert str(out_dir / "report_pack_summary.json") in dashboard_args
        assert (out_dir / "report_pack_summary.json").exists()


def test_generate_report_pack_verify_reports_status_and_checks():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp).resolve()
        matrix_path = tmp_root / "matrix.json"
        matrix_path.write_text('{"configs": ["configs/studio.json"]}', encoding="utf-8")
        out_dir = tmp_root / "out"

        unit_report = out_dir / "unit_matrix" / "matrix_report.json"
        policy_report = out_dir / "policy_matrix" / "policy_matrix_report.json"
        dashboard_path = out_dir / "dashboard.html"
        summary_path = out_dir / "report_pack_summary.json"

        unit_report.parent.mkdir(parents=True, exist_ok=True)
        policy_report.parent.mkdir(parents=True, exist_ok=True)
        unit_report.write_text(json.dumps({"ok": True}), encoding="utf-8")
        policy_report.write_text(json.dumps({"ok": True}), encoding="utf-8")
        dashboard_path.write_text("<html><body>Report pack summary</body></html>", encoding="utf-8")

        with patch.object(sys, "argv", [
            "generate_report_pack.py",
            str(matrix_path),
            "--out-dir",
            str(out_dir),
            "--verify",
        ]):
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = report_pack.main()

        assert exit_code == 0
        assert "verified expected report artifacts" in captured.getvalue()
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        assert payload["status"] == "ok"
        assert payload["verify"] is True
        assert payload["checked_at"]
        assert payload["artifacts"]["dashboard_path"]["size_bytes"] > 0
        assert any(check["name"] == "dashboard_pack_summary" and check["status"] == "ok" for check in payload["checks"])
        assert not payload["missing_artifacts"]
