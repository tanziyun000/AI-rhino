from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gh.scripts.rule_registry import DEFAULT_RULESET, RULE_REGISTRY, get_rule_names, resolve_ruleset


def test_rule_registry_defaults_and_names():
    assert "required_rooms" in RULE_REGISTRY
    assert "adjacency_policy" in RULE_REGISTRY
    assert "required_rooms" in DEFAULT_RULESET
    assert get_rule_names() == sorted(RULE_REGISTRY)


def test_resolve_ruleset_default_and_custom():
    assert resolve_ruleset({"constraints": {}}) == DEFAULT_RULESET
    assert resolve_ruleset({"constraints": {"rule_set": ["min_area", "aspect_ratio"]}}) == ["min_area", "aspect_ratio"]
