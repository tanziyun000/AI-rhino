from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.make_top_plans_svg import collage_svg


def _unit(uid, score, area=20.0):
    return {
        "unit_id": uid,
        "score": score,
        "status": "valid",
        "boundary": {"x": 0, "y": 0, "width": 3.0, "depth": 2.0},
        "rooms": [
            {
                "name": "kitchen",
                "area": area,
                "center": [1.5, 1.0],
                "polygon": [[0.0, 0.0], [3.0, 0.0], [3.0, 2.0], [0.0, 2.0]],
            }
        ],
        "doors": [{"point": [0.6, 0.0]}],
    }


def test_collage_svg_contains_top_units():
    svg = collage_svg([_unit("A001", 0.9), _unit("A000", 0.8)], columns=2, scale=1.0)
    assert "<svg" in svg
    assert "top plans" in svg
    assert "A001" in svg
    assert "A000" in svg
    assert "score=0.9000" in svg
    assert "score=0.8000" in svg
