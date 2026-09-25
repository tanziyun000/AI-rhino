from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.make_comparison_svg import comparison_svg


def _unit(name, score):
    return {
        "unit_id": name,
        "status": "valid",
        "score": score,
        "boundary": {"x": 0, "y": 0, "width": 3.0, "depth": 2.0},
        "rooms": [
            {
                "name": "kitchen",
                "area": 6.0,
                "center": [1.5, 1.0],
                "polygon": [[0.0, 0.0], [3.0, 0.0], [3.0, 2.0], [0.0, 2.0]],
            }
        ],
        "doors": [{"point": [0.6, 0.0]}],
    }


def test_comparison_svg_contains_both_plans():
    svg = comparison_svg(_unit("default", 0.9), _unit("variant", 0.8))
    assert "<svg" in svg
    assert "policy comparison" in svg
    assert "default" in svg
    assert "variant" in svg
    assert "score=0.9000" in svg
    assert "score=0.8000" in svg
