from typing import Dict, List

from .rectangle_utils import Rect


def assign_rooms(rectangles: List[Rect], program: List[dict], seed: int = 0):
    """Assign rectangles to room names by best area match."""
    unused = list(rectangles)
    assignments = {}
    for item in sorted(program, key=lambda r: float(r["target_area"])):
        target = float(item["target_area"])
        best_rect = min(unused, key=lambda r: abs(r.area - target))
        unused.remove(best_rect)
        assignments[item["name"]] = best_rect.copy(
            name=item["name"],
            metadata={
                "required": bool(item.get("required", False)),
                "target_area": target,
            },
        )
    return assignments


def build_room_objects(rectangles, assignment):
    rooms = []
    for name, rect in assignment.items():
        meta = rect.metadata
        rooms.append({
            "name": name,
            "area": round(rect.area, 2),
            "width": round(rect.w, 2),
            "depth": round(rect.h, 2),
            "aspect_ratio": round(rect.aspect_ratio, 2),
            "center": [round(rect.center[0], 2), round(rect.center[1], 2)],
            "polygon": [[round(x, 2), round(y, 2)] for x, y in rect.polygon],
            "required": bool(meta.get("required", False)),
            "target_area": round(float(meta.get("target_area", 0)), 2),
        })
    return rooms
