from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.make_dashboard import build_policy_matrix_html


def test_build_policy_matrix_html_includes_table_and_preview_cards():
    with tempfile.TemporaryDirectory() as tmp:
        svg_path = Path(tmp) / "comparison.svg"
        svg_path.write_text("<svg><title>policy compare</title></svg>", encoding="utf-8")
        report = {
            "items": [
                {
                    "unit_type": "2BR",
                    "default": {"valid": 5, "top_score": 0.9277},
                    "variant": {"valid": 0, "top_score": 0.8017},
                    "comparison_svg": str(svg_path),
                },
                {
                    "unit_type": "studio",
                    "error": "missing variant policy",
                },
            ]
        }

        html = build_policy_matrix_html(report)

        assert "Policy matrix" in html
        assert "Policy comparison previews" in html
        assert "Policy 2BR" in html
        assert "Policy studio" in html
        assert "default top 0.9277" in html
        assert "variant top 0.8017" in html
        assert "Comparison SVG unavailable" in html
        assert "<svg><title>policy compare</title></svg>" in html


def test_build_policy_matrix_html_empty_report_returns_empty_string():
    assert build_policy_matrix_html({}) == ""
    assert build_policy_matrix_html({"items": []}) == ""
