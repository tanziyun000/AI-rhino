from __future__ import annotations


DEFAULT_RULESET = [
    "required_rooms",
    "min_area",
    "aspect_ratio",
    "access_patterns",
    "kitchen_not_adjacent_to_bedrooms",
    "illegal_adjacency",
    "adjacency_policy",
]

# Kept intentionally lightweight to avoid circular imports with rule_checker.
RULE_REGISTRY: dict[str, str] = {
    "required_rooms": "check_required_rooms_present",
    "min_area": "check_min_area",
    "aspect_ratio": "check_aspect_ratio",
    "access_patterns": "check_room_access_patterns",
    "kitchen_not_adjacent_to_bedrooms": "check_kitchen_not_adjacent_to_bedrooms",
    "illegal_adjacency": "check_no_illegal_adjacency",
    "adjacency_policy": "check_adjacency_policy",
}


def get_rule_names():
    return sorted(RULE_REGISTRY)


def resolve_ruleset(config):
    constraints = config.get("constraints", {})
    rule_set = constraints.get("rule_set")
    if rule_set is None:
        return DEFAULT_RULESET
    if isinstance(rule_set, list) and rule_set:
        return [str(rule) for rule in rule_set]
    raise ValueError("constraints.rule_set must be a non-empty list")
