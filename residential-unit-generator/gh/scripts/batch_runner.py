import json
import csv
import random
from pathlib import Path

from .config_loader import load_config, validate_config
from .rectangle_utils import Rect
from .bsp_splitter import generate_bsp
from .room_assigner import assign_rooms, build_room_objects
from .wall_builder import build_walls
from .rule_checker import check_unit
from .scorer import score_unit


def generate_unit(config, seed=0):
    b = config["boundary"]
    root_rect = Rect(
        float(b["x"]),
        float(b["y"]),
        float(b["width"]),
        float(b["depth"]),
        metadata={"seed": seed, "unit_type": config.get("unit_type", "")},
    )
    max_aspect_ratio = float(config["constraints"].get("max_aspect_ratio", 3.2))
    rectangles = generate_bsp(
        root_rect,
        config["program"],
        seed=seed,
        max_aspect_ratio=max_aspect_ratio,
    )

    # Assign names to rectangles by matching target-area ranking.
    assignment = assign_rooms(rectangles, config["program"], seed=seed)
    rooms = build_room_objects(rectangles, assignment)
    default_order = ["living_room", "kitchen", "bedroom_main", "bedroom_2", "bedroom_3", "bedroom_4", "bathroom_wet", "bathroom_dry", "storage"]
    program_order = {room["name"]: idx for idx, room in enumerate(config["program"])}
    def _sort_key(room):
        name = room["name"]
        return (
            program_order.get(name, len(program_order)),
            default_order.index(name) if name in default_order else len(default_order),
            name,
        )

    rooms.sort(key=_sort_key)
    walls, doors = build_walls(
        rooms,
        config["building"]["wall_thickness"],
        config["building"]["entrance"],
        {"entrance_width": 0.9, "internal_door_width": 0.8},
    )

    total_area = root_rect.area
    usable_area = sum(room["area"] for room in rooms)
    corridor_area = max(0.0, total_area - usable_area)

    unit_result = {
        "unit_id": f"A{seed:03d}",
        "seed": seed,
        "project_name": config["project_name"],
        "unit_type": config["unit_type"],
        "status": "valid",
        "total_area": round(total_area, 2),
        "usable_area": round(usable_area, 2),
        "corridor_area": round(corridor_area, 2),
        "rooms": rooms,
        "doors": doors,
        "walls": walls,
        "boundary": b,
        "constraints": config["constraints"],
        "warnings": [],
        "failures": [],
    }

    failures, warnings = check_unit(unit_result, config)
    unit_result["failures"] = failures
    unit_result["warnings"] = warnings
    if failures:
        unit_result["status"] = "failed"
    else:
        unit_result["status"] = "valid"

    scores = score_unit(unit_result)
    unit_result.update(scores)
    unit_result["score"] = scores["total_score"]
    return unit_result


def generate_batch(config, count=100, seed_start=0):
    results = []
    for seed in range(seed_start, seed_start + count):
        try:
            results.append(generate_unit(config, seed=seed))
        except Exception as exc:
            results.append({
                "unit_id": f"A{seed:03d}",
                "seed": seed,
                "project_name": config.get("project_name", ""),
                "unit_type": config.get("unit_type", ""),
                "status": "exception",
                "total_area": 0.0,
                "usable_area": 0.0,
                "corridor_area": 0.0,
                "rooms": [],
                "doors": [],
                "warnings": [],
                "failures": [f"exception: {exc}"],
                "score": 0.0,
                "area_score": 0.0,
                "room_quality_score": 0.0,
                "circulation_score": 0.0,
                "compliance_score": 0.0,
            })
    return results


def filter_valid(results):
    return [r for r in results if r.get("status") == "valid"]


def rank_results(results):
    return sorted(results, key=lambda r: r.get("score", 0.0), reverse=True)


def write_summary(results, csv_path):
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "unit_id", "seed", "status", "total_area", "usable_area", "corridor_area",
        "score", "area_score", "room_quality_score", "circulation_score", "layout_score",
        "compliance_score", "failures", "warnings",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {key: r.get(key, "") for key in fieldnames}
            if isinstance(row["failures"], list):
                row["failures"] = " | ".join(row["failures"])
            if isinstance(row["warnings"], list):
                row["warnings"] = " | ".join(row["warnings"])
            writer.writerow(row)


def write_unit_json(unit_result, out_dir):
    out_path = Path(out_dir) / f"{unit_result['unit_id']}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(unit_result, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
