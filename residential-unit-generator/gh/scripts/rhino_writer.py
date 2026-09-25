"""Rhino/Grasshopper geometry helpers for the unit generator prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


def _try_import_rhino():
    try:
        import Rhino.Geometry as rg  # type: ignore
        return rg
    except Exception:
        return None


def _safe_polyline(rg, polygon):
    if rg is None:
        return [[float(x), float(y)] for x, y in polygon]
    return rg.Polyline([rg.Point3d(float(x), float(y), 0.0) for x, y in polygon])


def _safe_point(rg, point):
    if rg is None:
        return [float(point[0]), float(point[1])]
    return rg.Point3d(float(point[0]), float(point[1]), 0.0)


@dataclass
class RhinoUnitGeometry:
    room_polylines: List
    wall_lines: List
    door_points: List
    room_labels: List[str]


def unit_polygons(unit_result: dict) -> Dict[str, List[Tuple[float, float]]]:
    return {room["name"]: [tuple(pt) for pt in room.get("polygon", [])] for room in unit_result.get("rooms", [])}


def points_from_polygons(unit_result: dict) -> List[Tuple[float, float]]:
    points = []
    for room in unit_result.get("rooms", []):
        for pt in room.get("polygon", []):
            points.append((float(pt[0]), float(pt[1])))
    return points


def summarize_units(results: Iterable[dict]) -> dict:
    items = list(results)
    return {
        "count": len(items),
        "valid": sum(1 for r in items if r.get("status") == "valid"),
        "failed": sum(1 for r in items if r.get("status") == "failed"),
        "exception": sum(1 for r in items if r.get("status") == "exception"),
    }


def convert_to_rhino_objects(unit_result: dict) -> Dict[str, object]:
    """Convert a unit result into Rhino geometry when available; otherwise pure Python."""
    rg = _try_import_rhino()

    room_polylines = []
    room_labels = []
    door_points = []
    wall_lines = []

    for room in unit_result.get("rooms", []):
        polygon = room.get("polygon", [])
        if len(polygon) < 3:
            continue
        room_polylines.append(_safe_polyline(rg, polygon))
        room_labels.append(room.get("name", ""))

    for door in unit_result.get("doors", []):
        pt = door.get("point", [])
        if len(pt) >= 2:
            door_points.append(_safe_point(rg, pt))

    for wall in unit_result.get("walls", []):
        seg = wall.get("segment", [])
        if isinstance(seg, list) and len(seg) >= 2:
            if rg is None:
                wall_lines.append([seg[0], seg[1]])
            else:
                p0 = rg.Point3d(float(seg[0][0]), float(seg[0][1]), 0.0)
                p1 = rg.Point3d(float(seg[1][0]), float(seg[1][1]), 0.0)
                wall_lines.append(rg.Line(p0, p1))

    return {
        "rooms": room_polylines,
        "walls": wall_lines,
        "doors": door_points,
        "labels": room_labels,
    }
