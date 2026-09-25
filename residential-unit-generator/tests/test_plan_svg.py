from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.make_plan_svg import svg_for_unit


def _unit_with_single_room():
    return {
        "unit_id": "TEST001",
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


def test_svg_for_unit_contains_boundary_rooms_and_doors():
    svg = svg_for_unit(_unit_with_single_room())
    assert "<svg" in svg
    assert '<rect x="0.00" y="0.00" width="3.00" height="2.00"' in svg
    assert '<polygon points="0.00,0.00 3.00,0.00 3.00,2.00 0.00,2.00"' in svg
    assert "<text" in svg
    assert "<circle" in svg
