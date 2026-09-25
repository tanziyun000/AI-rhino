from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class LayerInfo:
    name: str
    color: str
    objects: List[str]


@dataclass
class TextBlock:
    text: str
    point: Tuple[float, float]


def build_room_text_blocks(unit_result: dict) -> List[TextBlock]:
    blocks = []
    for room in unit_result.get("rooms", []):
        center = room.get("center")
        if not center or len(center) < 2:
            continue
        blocks.append(TextBlock(text=room.get("name", ""), point=(float(center[0]), float(center[1]))))
    return blocks


def build_room_layers(unit_result: dict) -> List[LayerInfo]:
    layers = []
    seen = set()
    for room in unit_result.get("rooms", []):
        name = room.get("name", "room")
        if name in seen:
            continue
        seen.add(name)
        layers.append(LayerInfo(name=name, color="#888888", objects=[f"room:{name}"]))
    return layers


def build_unit_groups(unit_result: dict) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {
        "rooms": [room.get("name", "room") for room in unit_result.get("rooms", [])],
        "doors": [door.get("to", "door") for door in unit_result.get("doors", [])],
    }
    return groups


def assemble_rhino_outputs(unit_result: dict) -> Dict[str, object]:
    return {
        "layers": build_room_layers(unit_result),
        "texts": build_room_text_blocks(unit_result),
        "groups": build_unit_groups(unit_result),
    }


def write_to_rhino(unit_result: dict, doc=None) -> Dict[str, object]:
    """Write unit geometry into Rhino when available; otherwise return a status summary."""
    status = {
        "active": False,
        "written": 0,
        "skipped": 0,
        "errors": [],
    }

    try:
        import ScriptContext  # type: ignore
        from .rhino_writer import convert_to_rhino_objects  # type: ignore
    except Exception:
        return status

    status["active"] = True
    doc = doc or ScriptContext.Document
    if doc is None:
        status["errors"].append("no active Rhino document")
        return status

    obj_payload = convert_to_rhino_objects(unit_result)
    added = 0
    skipped = 0

    for polyline in obj_payload.get("rooms", []):
        try:
            doc.Objects.AddPolyline(polyline)
            added += 1
        except Exception:
            skipped += 1

    for line in obj_payload.get("walls", []):
        try:
            doc.Objects.AddLine(line)
            added += 1
        except Exception:
            skipped += 1

    for point in obj_payload.get("doors", []):
        try:
            doc.Objects.AddPoint(point)
            added += 1
        except Exception:
            skipped += 1

    status["written"] = added
    status["skipped"] = skipped
    return status
