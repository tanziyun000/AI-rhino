from .rectangle_utils import Rect, is_adjacent


def _rect_from_room(room):
    x0, y0 = room["polygon"][0]
    x1, y1 = room["polygon"][1]
    return Rect(x0, y0, x1 - x0, y1 - y0)


def build_walls(rooms, wall_thickness, entrance, door_rules=None):
    walls = []
    # Simple wall representation: shared room edges become line segments.
    for i, a in enumerate(rooms):
        for b in rooms[i + 1 :]:
            ra = _rect_from_room(a)
            rb = _rect_from_room(b)
            if is_adjacent(ra, rb, tol=0.05):
                walls.append({
                    "a": a["name"],
                    "b": b["name"],
                    "segment": _shared_edge(ra, rb, tol=0.05),
                })
    doors = []
    if entrance and rooms:
        # Create a simple entrance door at the first room closest to the entrance offset.
        target_room = min(
            rooms,
            key=lambda r: abs((_rect_from_room(r).center[0] - float(entrance.get("offset", 0))) + float(entrance.get("x", 0)))
        )
        doors.append({
            "from": "entrance",
            "to": target_room["name"],
            "point": [round(float(entrance.get("offset", 0)) + float(entrance.get("x", 0)), 2), round(float(entrance.get("y", 0)), 2)],
            "width": float(door_rules.get("entrance_width", 0.9)) if door_rules else 0.9,
        })
        # Add one door between adjacent rooms as a rough circulation proxy.
        for i, a in enumerate(rooms):
            for b in rooms[i + 1 :]:
                ra = _rect_from_room(a)
                rb = _rect_from_room(b)
                if is_adjacent(ra, rb, tol=0.05):
                    doors.append({
                        "from": a["name"],
                        "to": b["name"],
                        "point": _door_point(ra, rb),
                        "width": float(door_rules.get("internal_door_width", 0.8)) if door_rules else 0.8,
                    })
                    break
            else:
                continue
            break
    return walls, doors


def _shared_edge(ra: Rect, rb: Rect, tol=0.05):
    if abs(ra.x1 - rb.x0) <= tol:
        y0 = max(ra.y0, rb.y0)
        y1 = min(ra.y1, rb.y1)
        return [[ra.x1, y0], [ra.x1, y1]]
    if abs(rb.x1 - ra.x0) <= tol:
        y0 = max(ra.y0, rb.y0)
        y1 = min(ra.y1, rb.y1)
        return [[ra.x0, y0], [ra.x0, y1]]
    if abs(ra.y1 - rb.y0) <= tol:
        x0 = max(ra.x0, rb.x0)
        x1 = min(ra.x1, rb.x1)
        return [[x0, ra.y1], [x1, ra.y1]]
    if abs(rb.y1 - ra.y0) <= tol:
        x0 = max(ra.x0, rb.x0)
        x1 = min(ra.x1, rb.x1)
        return [[x0, rb.y1], [x1, rb.y1]]
    return [[0, 0], [0, 0]]


def _door_point(ra: Rect, rb: Rect):
    if abs(ra.x1 - rb.x0) <= 0.05:
        return [round(ra.x1, 2), round((ra.y0 + ra.y1) / 2, 2)]
    if abs(rb.x1 - ra.x0) <= 0.05:
        return [round(ra.x0, 2), round((ra.y0 + ra.y1) / 2, 2)]
    if abs(ra.y1 - rb.y0) <= 0.05:
        return [round((ra.x0 + ra.x1) / 2, 2), round(ra.y1, 2)]
    if abs(rb.y1 - ra.y0) <= 0.05:
        return [round((ra.x0 + ra.x1) / 2, 2), round(rb.y1, 2)]
    return [round(ra.center[0], 2), round(ra.center[1], 2)]
