import math

from .rectangle_utils import Rect, is_adjacent


def _room_rect(room):
    x0, y0 = room["polygon"][0]
    x1, y1 = room["polygon"][1]
    return Rect(x0, y0, x1 - x0, y1 - y0)


def _are_adjacent(room_a, room_b, tol=0.05):
    return is_adjacent(_room_rect(room_a), _room_rect(room_b), tol=tol)


def area_efficiency_score(unit_result):
    total = max(unit_result.get("total_area", 0.0), 1e-6)
    usable = max(unit_result.get("usable_area", 0.0), 0.0)
    return max(0.0, min(1.0, usable / total))


def room_quality_score(rooms, constraints):
    max_ratio = float(constraints.get("max_aspect_ratio", 3.2))
    scores = []
    for room in rooms:
        ratio = room.get("aspect_ratio", 1.0)
        penalty = min(1.0, ratio / max_ratio)
        scores.append(max(0.0, 1.0 - penalty * 0.35))
    return sum(scores) / len(scores) if scores else 0.0


def circulation_score(doors, rooms):
    if not doors or not rooms:
        return 0.0
    count_penalty = min(1.0, len(doors) / max(len(rooms), 1))
    return max(0.0, min(1.0, 1.0 - count_penalty * 0.6))


def layout_quality_score(rooms, warnings, failures):
    score = 1.0
    score -= 0.06 * len(failures)
    score -= 0.04 * len(warnings)
    return max(0.0, min(1.0, score))


def compliance_score(warnings, failures):
    if failures:
        return 0.0
    if warnings:
        return max(0.0, 1.0 - 0.08 * len(warnings))
    return 1.0


def score_unit(unit_result):
    rooms = unit_result["rooms"]
    constraints = unit_result.get("constraints", {})
    warnings = unit_result.get("warnings", [])
    failures = unit_result.get("failures", [])
    area_score = area_efficiency_score(unit_result)
    quality_score = room_quality_score(rooms, constraints)
    circulation_score_value = circulation_score(unit_result.get("doors", []), rooms)
    layout_score = layout_quality_score(rooms, warnings, failures)
    compliance_score_value = compliance_score(warnings, failures)
    total = (
        0.28 * area_score
        + 0.22 * quality_score
        + 0.22 * circulation_score_value
        + 0.14 * layout_score
        + 0.14 * compliance_score_value
    )
    return {
        "area_score": round(area_score, 4),
        "room_quality_score": round(quality_score, 4),
        "circulation_score": round(circulation_score_value, 4),
        "layout_score": round(layout_score, 4),
        "compliance_score": round(compliance_score_value, 4),
        "total_score": round(total, 4),
    }
