from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gh.scripts.config_loader import load_config, validate_config
from gh.scripts.rule_checker import _policy_entry, check_adjacency_policy


def _room(name, polygon):
    return {
        "name": name,
        "area": 1.0,
        "width": 1.0,
        "depth": 1.0,
        "aspect_ratio": 1.0,
        "center": [0.5, 0.5],
        "polygon": polygon,
        "required": False,
        "target_area": 1.0,
    }


def test_policy_entry_normalization():
    assert _policy_entry(["a", "b"]) == ("a", "b", "soft")
    assert _policy_entry(["a", "b", "hard"]) == ("a", "b", "hard")
    assert _policy_entry({"pair": ["a", "b"], "severity": "soft"}) == ("a", "b", "soft")
    assert _policy_entry({"rooms": ["a", "b"]}) == ("a", "b", "soft")


def test_config_loads_policy_and_severity():
    cfg_path = Path(__file__).resolve().parents[1] / "configs" / "default_3br.json"
    cfg = load_config(str(cfg_path))
    validate_config(cfg)
    assert cfg["constraints"]["preferred_adjacency"][0] == ["kitchen", "living_room", "soft"]
    assert cfg["constraints"]["preferred_adjacency"][1] == ["bathroom_wet", "bedroom_2", "hard"]


def test_check_adjacency_policy_severity_split():
    rooms = [
        _room("a", [[0, 0], [1, 0], [1, 1], [0, 1]]),
        _room("b", [[1, 0], [2, 0], [2, 1], [1, 1]]),
    ]
    constraints = {
        "preferred_adjacency": [["a", "b", "soft"]],
        "disallowed_adjacency": [["a", "b", "hard"]],
    }
    failures, warnings = check_adjacency_policy(rooms, constraints)
    assert warnings == []
    assert failures == ["disallowed adjacency: a next to b"]
