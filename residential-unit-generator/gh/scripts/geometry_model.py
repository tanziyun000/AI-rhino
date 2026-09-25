from pathlib import Path
from typing import Dict, List, Optional


class UnitGeometryBundle:
    """Container for unit geometry so the GH component can keep pure-Python and Rhino modes."""

    def __init__(self, results: List[dict]):
        self.results = list(results or [])
        self.top = self.results[0] if self.results else None

    def summary(self) -> dict:
        top = self.top or {}
        return {
            "count": len(self.results),
            "valid": sum(1 for r in self.results if r.get("status") == "valid"),
            "top_score": top.get("score", 0.0),
        }


def extract_unit_polygons(result: dict) -> Dict[str, List[tuple]]:
    return {room["name"]: [tuple(p) for p in room["polygon"]] for room in result.get("rooms", [])}


def build_geometry_payload(results: List[dict]) -> dict:
    return {
        "units": [
            {
                "unit_id": r.get("unit_id"),
                "status": r.get("status"),
                "score": r.get("score", 0.0),
                "rooms": extract_unit_polygons(r),
            }
            for r in results
        ]
    }
