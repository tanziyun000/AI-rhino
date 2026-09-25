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


def svg_for_unit(unit):
    boundary = unit["boundary"]
    x0 = float(boundary["x"])
    y0 = float(boundary["y"])
    width = float(boundary["width"])
    depth = float(boundary["depth"])
    padding = 0.4
    left = x0 - padding
    top = y0 - padding
    canvas_w = width + padding * 2
    canvas_h = depth + padding * 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w * 10:.1f}mm" height="{canvas_h * 10:.1f}mm" viewBox="{left:.2f} {top:.2f} {canvas_w:.2f} {canvas_h:.2f}">',
        '<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" fill="white" stroke="#111111" stroke-width="0.12"/>'.format(x0, y0, width, depth),
    ]

    for room in unit.get("rooms", []):
        poly = " ".join(f'{x:.2f},{y:.2f}' for x, y in room["polygon"])
        parts.append(
            f'<polygon points="{poly}" fill="{room.get("fill", "#eef6ff")}" stroke="#444444" stroke-width="0.05"/>'
        )
        cx, cy = room.get("center", [(x0 + width / 2), (y0 + depth / 2)])
        label = f'{room.get("name", "")} | {room.get("area", 0):.1f}m2'
        parts.append(
            f'<text x="{float(cx):.2f}" y="{float(cy):.2f}" font-size="0.45" text-anchor="middle" dominant-baseline="middle" fill="#111111">{escape_xml(label)}</text>'
        )

    for door in unit.get("doors", []):
        pt = door.get("point", [x0, y0])
        parts.append(
            f'<circle cx="{float(pt[0]):.2f}" cy="{float(pt[1]):.2f}" r="0.18" fill="#b00020"/>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("unit_json", type=Path)
    parser.add_argument("out_svg", type=Path)
    args = parser.parse_args()

    unit = json.loads(args.unit_json.read_text(encoding="utf-8"))
    args.out_svg.parent.mkdir(parents=True, exist_ok=True)
    args.out_svg.write_text(svg_for_unit(unit), encoding="utf-8")
    print(f"wrote {args.out_svg}")


if __name__ == "__main__":
    main()
