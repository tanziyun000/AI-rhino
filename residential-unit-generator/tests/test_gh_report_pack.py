from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gh import code as gh_code


def test_residential_report_pack_generator_builds_expected_command():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp).resolve()
        matrix_path = tmp_root / "matrix.json"
        matrix_path.write_text('{"configs": ["configs/studio.json"]}', encoding="utf-8")

        def fake_run(args, cwd, capture_output, text):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="wrote dashboard\n", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            component = gh_code.ResidentialReportPackGenerator()
            out = component.RunScript(
                matrix_path=str(matrix_path),
                out_dir=str(tmp_root / "out"),
                unit_count=7,
                policy_count=3,
                dry_run=True,
                skip_dashboard=True,
                verify=False,
            )

        stdout, stderr, script_path, args, summary_path_out, summary_json = out
        assert stdout == "wrote dashboard"
        assert stderr == ""
        assert "generate_report_pack.py" in script_path
        assert "--unit-count" in args
        assert "7" in args
        assert "--policy-count" in args
        assert "3" in args
        assert "--dry-run" in args
        assert "--skip-dashboard" in args

        import json

        summary = json.loads(summary_json)
        assert summary["status"] == "dry-run"
        assert summary["dry_run"] is True
        assert summary["skip_dashboard"] is True
        assert summary["dashboard_path"].endswith("dashboard.html")
        assert summary_path_out.endswith("report_pack_summary.json")
        assert summary["summary_path"].endswith("report_pack_summary.json")
        assert summary["started_at"] is None
        assert summary["finished_at"] is None
        assert summary["unit_report_path"].endswith("unit_matrix/matrix_report.json")
        assert summary["policy_report_path"].endswith("policy_matrix/policy_matrix_report.json")


def test_residential_report_pack_generator_omits_optional_flags_by_default():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp).resolve()
        matrix_path = tmp_root / "matrix.json"
        matrix_path.write_text('{"configs": ["configs/studio.json"]}', encoding="utf-8")

        def fake_run(args, cwd, capture_output, text):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="wrote dashboard\n", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            component = gh_code.ResidentialReportPackGenerator()
            out = component.RunScript(
                matrix_path=str(matrix_path),
                out_dir=str(tmp_root / "out"),
                unit_count=2,
                policy_count=1,
                dry_run=False,
                skip_dashboard=False,
                verify=False,
            )

        stdout, stderr, script_path, args, summary_path_out, summary_json = out
        assert stdout == "wrote dashboard"
        assert stderr == ""
        assert "generate_report_pack.py" in script_path
        assert "--unit-count" in args
        assert "2" in args
        assert "--policy-count" in args
        assert "1" in args
        assert "--dry-run" not in args
        assert "--skip-dashboard" not in args

        import json

        summary = json.loads(summary_json)
        assert summary["status"] == "ok"
        assert summary["dry_run"] is False
        assert summary["skip_dashboard"] is False
        assert summary["dashboard_path"].endswith("dashboard.html")
        assert summary_path_out.endswith("report_pack_summary.json")
        assert summary["summary_path"].endswith("report_pack_summary.json")
        assert summary["started_at"] is None
        assert summary["finished_at"] is None
        assert summary["matrix_path"].endswith("matrix.json")
        assert summary["out_dir"].endswith("out")
