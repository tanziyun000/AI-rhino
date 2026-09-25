from .rectangle_utils import Rect, is_adjacent
from .rule_registry import resolve_ruleset


def _rect_from_result(room):
    return {
        "name": room["name"],
        "area": room["area"],
        "aspect_ratio": room["aspect_ratio"],
        "polygon": room["polygon"],
        "required": room.get("required", False),
        "target_area": room.get("target_area", 0),
    }


def check_min_area(rooms, constraints):
    failures = []
    min_area = constraints.get("min_area", {})
    for room in rooms:
        required_min = min_area.get(room["name"])
        if required_min is not None and room["area"] < float(required_min) - 1e-6:
            failures.append(f"{room['name']} area {room['area']} is below minimum {required_min}")
    return failures


def check_aspect_ratio(rooms, constraints):
    failures = []
    max_ratio = float(constraints.get("max_aspect_ratio", 3.2))
    for room in rooms:
        if room["aspect_ratio"] > max_ratio + 1e-6:
            failures.append(f"{room['name']} aspect ratio {room['aspect_ratio']} exceeds {max_ratio}")
    return failures


def check_required_rooms_present(rooms, program):
    failures = []
    names = {room["name"] for room in rooms}
    for item in program:
        if item.get("required", False) and item["name"] not in names:
            failures.append(f"required room missing: {item['name']}")
    return failures


def check_bathroom_not_dead_end(rooms):
    warnings = []
    baths = [r for r in rooms if r["name"].startswith("bathroom")]
    for bath in baths:
        neighbors = [r for r in rooms if r["name"] != bath["name"] and _are_adjacent(bath, r)]
        # A bathroom is not a dead end if it has at least one adjacent non-bathroom room.
        non_bathroom_neighbors = [r for r in neighbors if not r["name"].startswith("bathroom")]
        if len(non_bathroom_neighbors) < 1:
            warnings.append(f"{bath['name']} may be a dead-end bathroom")
    return warnings


def check_kitchen_has_window(room, boundary):
    if room["name"] != "kitchen":
        return []
    tol = 0.05
    b = boundary
    xs = [p[0] for p in room["polygon"]]
    ys = [p[1] for p in room["polygon"]]
    near_bottom = min(abs(y - float(b["y"])) for y in ys) <= tol
    near_top = min(abs(y - float(b["y"] + b["depth"])) for y in ys) <= tol
    near_left = min(abs(x - float(b["x"])) for x in xs) <= tol
    near_right = min(abs(x - float(b["x"] + b["width"])) for x in xs) <= tol
    if not (near_bottom or near_top or near_left or near_right):
        return ["kitchen does not touch an exterior boundary edge"]
    return []


def check_kitchen_not_adjacent_to_bedrooms(rooms):
    warnings = []
    kitchen = next((r for r in rooms if r["name"] == "kitchen"), None)
    if kitchen is None:
        return warnings
    adjacent_bedrooms = [r for r in rooms if r["name"].startswith("bedroom") and _are_adjacent(kitchen, r)]
    if len(adjacent_bedrooms) > 1:
        warnings.append("kitchen is directly adjacent to multiple bedrooms")
    return warnings


def check_bedroom_has_living_access(rooms):
    warnings = []
    living = next((r for r in rooms if r["name"] == "living_room"), None)
    if living is None:
        return warnings
    bedrooms = [r for r in rooms if r["name"].startswith("bedroom")]
    for room in bedrooms:
        if not _are_adjacent(room, living):
            warnings.append(f"{room['name']} is not directly adjacent to living_room")
    return warnings


def check_no_illegal_adjacency(rooms, adjacency_rules=None):
    warnings = []
    adjacency_rules = adjacency_rules or {}
    for i, a in enumerate(rooms):
        for b in rooms[i + 1 :]:
            pair = tuple(sorted([a["name"], b["name"]]))
            if pair in adjacency_rules and not adjacency_rules[pair]:
                if _are_adjacent(a, b):
                    warnings.append(f"illegal adjacency: {pair[0]} next to {pair[1]}")
    return warnings


def _policy_entry(parts, default_severity="soft"):
    """Normalize policy entries to (room_a, room_b, severity)."""
    if isinstance(parts, dict):
        if "severity" in parts:
            severity = str(parts["severity"]).lower()
            severity = "hard" if severity == "hard" else "soft"
        else:
            severity = default_severity
        if "pair" in parts:
            pair = parts["pair"]
        elif "rooms" in parts:
            pair = parts["rooms"]
        else:
            return None
        if isinstance(pair, (list, tuple)) and len(pair) >= 2:
            return str(pair[0]), str(pair[1]), severity
        return None

    if isinstance(parts, (list, tuple)):
        if len(parts) < 2:
            return None
        severity = default_severity
        if len(parts) >= 3:
            severity = str(parts[2]).lower()
            severity = "hard" if severity == "hard" else "soft"
        return str(parts[0]), str(parts[1]), severity
    return None


def check_adjacency_policy(rooms, constraints):
    warnings = []
    failures = []
    preferred = constraints.get("preferred_adjacency", []) or []
    disallowed = constraints.get("disallowed_adjacency", []) or []

    for entry in preferred:
        parsed = _policy_entry(entry, default_severity="soft")
        if not parsed:
            continue
        a_name, b_name, severity = parsed
        a = next((r for r in rooms if r["name"] == a_name), None)
        b = next((r for r in rooms if r["name"] == b_name), None)
        if a is None or b is None:
            continue
        if not _are_adjacent(a, b):
            msg = f"preferred adjacency missing: {a_name} next to {b_name}"
            if severity == "hard":
                failures.append(msg)
            else:
                warnings.append(msg)

    for entry in disallowed:
        parsed = _policy_entry(entry, default_severity="hard")
        if not parsed:
            continue
        a_name, b_name, severity = parsed
        a = next((r for r in rooms if r["name"] == a_name), None)
        b = next((r for r in rooms if r["name"] == b_name), None)
        if a is None or b is None:
            continue
        if _are_adjacent(a, b):
            msg = f"disallowed adjacency: {a_name} next to {b_name}"
            if severity == "hard":
                failures.append(msg)
            else:
                warnings.append(msg)

    return failures, warnings


def _bbox_from_polygon(polygon):
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return min(xs), min(ys), max(xs), max(ys)


def _are_adjacent(room_a, room_b, tol=0.05):
    ax0, ay0, ax1, ay1 = _bbox_from_polygon(room_a["polygon"])
    bx0, by0, bx1, by1 = _bbox_from_polygon(room_b["polygon"])
    return is_adjacent(
        Rect(ax0, ay0, ax1 - ax0, ay1 - ay0),
        Rect(bx0, by0, bx1 - bx0, by1 - by0),
        tol=tol,
    )


def _touch_exterior_edge(room, boundary):
    tol = 0.05
    b = boundary
    xs = [p[0] for p in room["polygon"]]
    ys = [p[1] for p in room["polygon"]]
    return (
        min(abs(y - float(b["y"])) for y in ys) <= tol
        or min(abs(y - float(b["y"] + b["depth"])) for y in ys) <= tol
        or min(abs(x - float(b["x"])) for x in xs) <= tol
        or min(abs(x - float(b["x"] + b["width"])) for x in xs) <= tol
    )


def check_room_access_patterns(rooms, boundary):
    warnings = []
    kitchen = next((r for r in rooms if r["name"] == "kitchen"), None)
    living = next((r for r in rooms if r["name"] == "living_room"), None)

    if kitchen is not None and not _touch_exterior_edge(kitchen, boundary):
        warnings.append("kitchen does not touch an exterior boundary edge")

    if living is not None:
        for room in rooms:
            if room["name"].startswith("bedroom") and not _are_adjacent(room, living):
                warnings.append(f"{room['name']} is not directly adjacent to living_room")

    for room in rooms:
        if room["name"].startswith("bathroom"):
            non_bath_neighbors = [r for r in rooms if r["name"] != room["name"] and not r["name"].startswith("bathroom") and _are_adjacent(room, r)]
            if not non_bath_neighbors:
                warnings.append(f"{room['name']} may be a dead-end bathroom")

    return warnings


def check_unit(unit_result, config):
    rooms = unit_result["rooms"]
    boundary = config["boundary"]
    constraints = config["constraints"]
    program = config["program"]
    rule_set = resolve_ruleset(config)
    failures = []
    warnings = []

    if "required_rooms" in rule_set:
        failures.extend(check_required_rooms_present(rooms, program))
    if "min_area" in rule_set:
        failures.extend(check_min_area(rooms, constraints))
    if "aspect_ratio" in rule_set:
        failures.extend(check_aspect_ratio(rooms, constraints))
    if "access_patterns" in rule_set:
        warnings.extend(check_room_access_patterns(rooms, boundary))
    if "kitchen_not_adjacent_to_bedrooms" in rule_set:
        warnings.extend(check_kitchen_not_adjacent_to_bedrooms(rooms))
    if "illegal_adjacency" in rule_set:
        warnings.extend(check_no_illegal_adjacency(rooms))
    if "adjacency_policy" in rule_set:
        policy_failures, policy_warnings = check_adjacency_policy(rooms, constraints)
        failures.extend(policy_failures)
        warnings.extend(policy_warnings)
    return failures, warnings
