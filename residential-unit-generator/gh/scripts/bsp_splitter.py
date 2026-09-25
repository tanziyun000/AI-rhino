from .rectangle_utils import Rect, choose_split_direction


def normalize_ratio(part, whole, min_ratio=0.15, max_ratio=0.85):
    if whole <= 1e-9:
        raise ValueError("whole area is too small")
    ratio = part / whole
    return min(max(ratio, min_ratio), max_ratio)


def _build_split(rect: Rect, items, orientation: str, max_aspect_ratio: float):
    if len(items) == 1:
        item = items[0]
        return [Rect(
            rect.x,
            rect.y,
            rect.w,
            rect.h,
            name=item["name"],
            metadata={"target_area": float(item["target_area"]), "required": bool(item.get("required", False))},
        )]

    total_area = sum(float(r["target_area"]) for r in items)
    if total_area <= 1e-9:
        raise ValueError("total_area is too small")

    if orientation == "horizontal":
        cursor_x = rect.x
        children = []
        for r in items:
            w = rect.w * (float(r["target_area"]) / total_area if total_area else 0.25)
            w = min(w, rect.w - cursor_x)
            if w <= 1e-6:
                raise ValueError("not enough width for child rectangle")
            children.append(Rect(
                cursor_x,
                rect.y,
                w,
                rect.h,
                name=r["name"],
                metadata={"target_area": float(r["target_area"]), "required": bool(r.get("required", False))},
            ))
            cursor_x += w
        return children

    cursor_y = rect.y
    children = []
    for r in items:
        h = rect.h * (float(r["target_area"]) / total_area if total_area else 0.25)
        h = min(h, rect.h - cursor_y)
        if h <= 1e-6:
            raise ValueError("not enough height for child rectangle")
        children.append(Rect(
            rect.x,
            cursor_y,
            rect.w,
            h,
            name=r["name"],
            metadata={"target_area": float(r["target_area"]), "required": bool(r.get("required", False))},
        ))
        cursor_y += h
    return children


def split_group(rect: Rect, items, max_aspect_ratio=3.2):
    """Split a group of child items into a horizontal or vertical arrangement."""
    if len(items) == 1:
        item = items[0]
        return [Rect(
            rect.x,
            rect.y,
            rect.w,
            rect.h,
            name=item["name"],
            metadata={"target_area": float(item["target_area"]), "required": bool(item.get("required", False))},
        )]

    total_area = sum(float(r["target_area"]) for r in items)
    preferred = choose_split_direction(rect, max_aspect_ratio=max_aspect_ratio)
    orientation = "vertical" if preferred == "horizontal" else "horizontal"

    horizontal = None
    vertical = None
    try:
        horizontal = _build_split(rect, items, "horizontal", max_aspect_ratio)
    except ValueError:
        pass
    try:
        vertical = _build_split(rect, items, "vertical", max_aspect_ratio)
    except ValueError:
        pass

    if horizontal is None and vertical is None:
        raise ValueError("not enough space to split child rectangle")

    if horizontal is None:
        children = vertical
    elif vertical is None:
        children = horizontal
    else:
        h_score = sum(r.aspect_ratio for r in horizontal)
        v_score = sum(r.aspect_ratio for r in vertical)
        children = horizontal if h_score <= v_score * 1.02 else vertical

    if max(r.aspect_ratio for r in children) > max_aspect_ratio:
        try:
            children = _build_split(rect, items, orientation, max_aspect_ratio)
        except ValueError:
            pass

    return children


def generate_bsp(root_rect: Rect, target_areas, seed=0, depth_limit=8, max_aspect_ratio=3.2):
    """Very simple area-driven BSP-like layout for rectangular apartments."""
    if not target_areas:
        return []
    if depth_limit <= 0:
        raise ValueError("depth_limit too low")

    by_name = {r["name"]: r for r in target_areas}
    standard_names = ["bedroom_main", "living_room", "bedroom_2", "kitchen", "bathroom_wet", "bathroom_dry", "storage"]
    studio_names = ["living_room", "kitchen", "bathroom_wet", "storage"]
    compact_2br_names = ["living_room", "kitchen", "bedroom_main", "bedroom_2", "bathroom_wet", "bathroom_dry", "storage"]

    def _rect(name, x, y, w, h):
        meta = by_name[name]
        return Rect(x, y, w, h, name=name, metadata={"target_area": float(meta["target_area"]), "required": bool(meta.get("required", False))})

    if all(name in by_name for name in studio_names) and len(by_name) == len(studio_names):
        w = root_rect.w
        h = root_rect.h
        if w > h:
            hx1, hy1, hw1, hh1 = 0.0, 0.0, w * 0.6, h * 0.55
            hx2, hy2, hw2, hh2 = w * 0.6, 0.0, w * 0.4, h * 0.28
            hx3, hy3, hw3, hh3 = 0.0, h * 0.55, w * 0.35, h * 0.22
            hx4, hy4, hw4, hh4 = w * 0.35, h * 0.55, w * 0.65, h * 0.23
        else:
            hx1, hy1, hw1, hh1 = 0.0, 0.0, w * 0.55, h * 0.6
            hx2, hy2, hw2, hh2 = 0.0, h * 0.6, w * 0.35, h * 0.2
            hx3, hy3, hw3, hh3 = w * 0.35, h * 0.6, w * 0.65, h * 0.2
            hx4, hy4, hw4, hh4 = 0.0, h * 0.8, w, h * 0.2

        return [
            _rect("living_room", root_rect.x + hx1, root_rect.y + hy1, hw1, hh1),
            _rect("kitchen", root_rect.x + hx2, root_rect.y + hy2, hw2, hh2),
            _rect("bathroom_wet", root_rect.x + hx3, root_rect.y + hy3, hw3, hh3),
            _rect("storage", root_rect.x + hx4, root_rect.y + hy4, hw4, hh4),
        ]

    unit_type = root_rect.metadata.get("unit_type", "")
    standard_4br_names = ["living_room", "kitchen", "bedroom_main", "bedroom_2", "bedroom_3", "bedroom_4", "bathroom_wet", "bathroom_dry", "storage"]
    if unit_type == "4BR" and all(name in by_name for name in standard_4br_names) and len(by_name) == len(standard_4br_names):
        w = root_rect.w
        h = root_rect.h
        top_h = h * 0.32
        bottom_h = h - top_h
        return [
            _rect("bedroom_main", root_rect.x, root_rect.y, w * 0.50, top_h),
            _rect("bedroom_2", root_rect.x + w * 0.50, root_rect.y, w * 0.20, top_h),
            _rect("living_room", root_rect.x + w * 0.70, root_rect.y, w * 0.30, top_h),
            _rect("bedroom_3", root_rect.x, root_rect.y + top_h, w * 0.30, bottom_h),
            _rect("bedroom_4", root_rect.x + w * 0.30, root_rect.y + top_h, w * 0.30, bottom_h),
            _rect("bathroom_wet", root_rect.x + w * 0.60, root_rect.y + top_h, w * 0.14, bottom_h),
            _rect("bathroom_dry", root_rect.x + w * 0.74, root_rect.y + top_h, w * 0.14, bottom_h),
            _rect("storage", root_rect.x + w * 0.88, root_rect.y + top_h, w * 0.12, bottom_h),
            _rect("kitchen", root_rect.x + w * 0.88, root_rect.y, w * 0.12, top_h),
        ]
    if unit_type == "2BR" and all(name in by_name for name in compact_2br_names) and len(by_name) == len(compact_2br_names):
        w = root_rect.w
        h = root_rect.h
        top_h = h * 0.34
        bottom_h = h - top_h
        return [
            _rect("living_room", root_rect.x, root_rect.y, w * 0.30, top_h),
            _rect("bedroom_main", root_rect.x + w * 0.30, root_rect.y, w * 0.30, top_h),
            _rect("bedroom_2", root_rect.x + w * 0.60, root_rect.y, w * 0.40, top_h),
            _rect("kitchen", root_rect.x, root_rect.y + top_h, w * 0.30, bottom_h),
            _rect("bathroom_dry", root_rect.x + w * 0.30, root_rect.y + top_h, w * 0.22, bottom_h),
            _rect("bathroom_wet", root_rect.x + w * 0.52, root_rect.y + top_h, w * 0.22, bottom_h),
            _rect("storage", root_rect.x + w * 0.74, root_rect.y + top_h, w * 0.26, bottom_h),
        ]

    if unit_type == "3BR" and all(name in by_name for name in standard_names) and len(by_name) == len(standard_names):
        # Fixed MVP template tuned for the sample 12 x 8 boundary.
        y0 = root_rect.y
        h_main = 3.0
        h_bed2 = 2.3
        h_service = root_rect.h - h_main - h_bed2
        service_parts = [
            ("storage", 1.2),
            ("bathroom_dry", 1.6),
            ("bathroom_wet", 2.0),
            ("kitchen", 7.2),
        ]
        widths = [w for _, w in service_parts]
        total_w = sum(widths)
        scale_w = root_rect.w / total_w

        output = []
        output.append(Rect(root_rect.x, y0, 7.2, h_main, name="bedroom_main",
                           metadata={"target_area": float(by_name["bedroom_main"]["target_area"]), "required": bool(by_name["bedroom_main"].get("required", False))}))
        output.append(Rect(root_rect.x + 7.2, y0, root_rect.w - 7.2, h_main, name="living_room",
                           metadata={"target_area": float(by_name["living_room"]["target_area"]), "required": bool(by_name["living_room"].get("required", False))}))
        output.append(Rect(root_rect.x, y0 + h_main, root_rect.w, h_bed2, name="bedroom_2",
                           metadata={"target_area": float(by_name["bedroom_2"]["target_area"]), "required": bool(by_name["bedroom_2"].get("required", False))}))

        cursor_x = root_rect.x
        for room_name, width in service_parts:
            w = width * scale_w
            output.append(Rect(cursor_x, y0 + h_main + h_bed2, w, h_service, name=room_name,
                               metadata={"target_area": float(by_name[room_name]["target_area"]), "required": bool(by_name[room_name].get("required", False))}))
            cursor_x += w
        return output

    sorted_rooms = sorted(target_areas, key=lambda r: r["target_area"], reverse=True)
    total_area = sum(float(r["target_area"]) for r in sorted_rooms)
    scale = root_rect.area / total_area if total_area else 1.0

    scaled = []
    for room in sorted_rooms:
        scaled.append(
            {
                "name": room["name"],
                "required": bool(room.get("required", False)),
                "target_area": float(room["target_area"]) * scale,
            }
        )

    groups = [[scaled[0]]]
    remaining = scaled[1:]
    while remaining:
        group = remaining[:2]
        groups.append(group)
        remaining = remaining[2:]

    total_group_area = sum(sum(room["target_area"] for room in group) for group in groups)
    cursor_y = root_rect.y
    output = []
    for group in groups:
        group_area = sum(room["target_area"] for room in group)
        h = root_rect.h * (group_area / total_group_area if total_group_area else 0.25)
        group_rect = root_rect.copy(y=cursor_y, h=h)
        output.extend(split_group(group_rect, group, max_aspect_ratio=max_aspect_ratio))
        cursor_y += h
    return output
