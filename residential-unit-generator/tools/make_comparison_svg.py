from __future__ import annotations

import argparse
import json
from pathlib import Path


def escape_xml(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _unit_svg(unit, title, x_offset, y_offset, scale=1.0):
    boundary = unit["boundary"]
    x0 = float(boundary["x"])
    y0 = float(boundary["y"])
    width = float(boundary["width"])
    depth = float(boundary["depth"])
    padding = 0.4

    def tx(x):
        return (x - x0) * scale + x_offset

    def ty(y):
        return (y - y0) * scale + y_offset

    parts = [f'<text x="{tx(x0) + 0.2:.2f}" y="{ty(y0) - 0.3:.2f}" font-size="0.9" font-weight="bold" fill="#111111">{escape_xml(title)}</text>']
    parts.append(
        '<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" fill="#ffffff" stroke="#111111" stroke-width="0.12"/>'.format(
            tx(x0), ty(y0), width * scale, depth * scale
        )
    )

    for room in unit.get("rooms", []):
        poly = " ".join(f"{tx(x):.2f},{ty(y):.2f}" for x, y in room["polygon"])
        parts.append(
            f'<polygon points="{poly}" fill="{room.get("fill", "#eef6ff")}" stroke="#444444" stroke-width="{0.05 * scale:.2f}"/>'
        )
        cx, cy = room.get("center", [(x0 + width / 2), (y0 + depth / 2)])
        label = f'{room.get("name", "")} | {room.get("area", 0):.1f}m2'
        parts.append(
            f'<text x="{tx(cx):.2f}" y="{ty(cy):.2f}" font-size="{0.45 * scale:.2f}" text-anchor="middle" dominant-baseline="middle" fill="#111111">{escape_xml(label)}</text>'
        )

    for door in unit.get("doors", []):
        pt = door.get("point", [x0, y0])
        parts.append(
            f'<circle cx="{tx(float(pt[0])):.2f}" cy="{ty(float(pt[1])):.2f}" r="{0.18 * scale:.2f}" fill="#b00020"/>'
        )

    score = unit.get("score", 0.0)
    status = unit.get("status", "unknown")
    parts.append(
        f'<text x="{tx(x0) + 0.2:.2f}" y="{ty(y0 + depth) + 0.55:.2f}" font-size="0.6" fill="#111111">score={float(score):.4f} status={escape_xml(status)}</text>'
    )

    return "\n".join(parts)


def comparison_svg(default_unit, variant_unit, width=24.0, height=10.0):
    default_svg = _unit_svg(default_unit, "default", x_offset=0.4, y_offset=1.0)
    variant_svg = _unit_svg(variant_unit, "variant", x_offset=13.0, y_offset=1.0)
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}mm" height="{height:.1f}mm" viewBox="0 0 {width:.2f} {height:.2f}">',
            '<rect x="0" y="0" width="24.00" height="10.00" fill="#f6f7f9"/>',
            '<text x="1.0" y="0.7" font-size="1.1" font-weight="bold" fill="#111111">policy comparison</text>',
            default_svg,
            variant_svg,
            '</svg>',
        ]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("default_json", type=Path)
    parser.add_argument("variant_json", type=Path)
    parser.add_argument("out_svg", type=Path)
    args = parser.parse_args()

    default_unit = json.loads(args.default_json.read_text(encoding="utf-8"))
    variant_unit = json.loads(args.variant_json.read_text(encoding="utf-8"))
    args.out_svg.parent.mkdir(parents=True, exist_ok=True)
    args.out_svg.write_text(comparison_svg(default_unit, variant_unit), encoding="utf-8")
    print(f"wrote {args.out_svg}")


if __name__ == "__main__":
    main()
