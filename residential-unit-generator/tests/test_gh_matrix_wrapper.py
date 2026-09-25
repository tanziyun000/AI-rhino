from pathlib import Path
import json
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gh.GH_Interface import MatrixGenerator, PolicyMatrixGenerator


def test_matrix_generator_summary_without_report():
    with tempfile.TemporaryDirectory() as tmp:
        runner = MatrixGenerator(matrix_path="missing.json", out_dir=tmp)
        summary = runner.summary()
        assert summary["items"] == 0
        assert summary["summary_path"].endswith("matrix_summary.csv")
        assert summary["best_unit_svg_paths"] == []


def test_matrix_generator_summary_reads_report():
    with tempfile.TemporaryDirectory() as tmp:
        report_path = Path(tmp) / "matrix_report.json"
        report_path.write_text(
            json.dumps({
                "matrix": "cfg.json",
                "out_dir": tmp,
                "items": [
                    {"unit_type": "3BR", "best_unit_svg": str(Path(tmp) / "a.svg")},
                    {"unit_type": "studio", "best_unit_svg": ""},
                ],
            }),
            encoding="utf-8",
        )
        runner = MatrixGenerator(matrix_path="cfg.json", out_dir=tmp)
        summary = runner.summary()
        assert summary["items"] == 2
        assert summary["matrix"] == "cfg.json"
        assert summary["summary_path"].endswith("matrix_summary.csv")
        assert summary["best_unit_svg_paths"] == [str(Path(tmp) / "a.svg")]


def test_policy_matrix_generator_summary_without_report():
    with tempfile.TemporaryDirectory() as tmp:
        runner = PolicyMatrixGenerator(matrix_path="missing.json", out_dir=tmp)
        summary = runner.summary()
        assert summary["items"] == 0
        assert summary["ok_count"] == 0
        assert summary["failed_count"] == 0
        assert summary["count"] == 1
        assert summary["summary_path"].endswith("policy_matrix_summary.csv")
        assert summary["comparison_svg_paths"] == []
        assert summary["comparison_svg_count"] == 0
        assert summary["report_path"].endswith("policy_matrix_report.json")


def test_policy_matrix_generator_summary_reads_report():
    with tempfile.TemporaryDirectory() as tmp:
        report_path = Path(tmp) / "policy_matrix_report.json"
        report_path.write_text(
            json.dumps({
                "matrix": "cfg.json",
                "out_dir": tmp,
                "count": 2,
                "items": [
                    {"unit_type": "3BR", "comparison_svg": str(Path(tmp) / "comparison.svg")},
                    {"unit_type": "studio", "comparison_svg": ""},
                ],
            }),
            encoding="utf-8",
        )
        runner = PolicyMatrixGenerator(matrix_path="cfg.json", out_dir=tmp, count=2)
        summary = runner.summary()
        assert summary["items"] == 2
        assert summary["ok_count"] == 2
        assert summary["failed_count"] == 0
        assert summary["count"] == 2
        assert summary["matrix"] == "cfg.json"
        assert summary["summary_path"].endswith("policy_matrix_summary.csv")
        assert summary["comparison_svg_paths"] == [str(Path(tmp) / "comparison.svg")]
        assert summary["comparison_svg_count"] == 1
        assert summary["report_path"] == str(report_path)
