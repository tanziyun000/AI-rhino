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


def _fit_unit(unit, cell_w, cell_h, scale):
    b = unit["boundary"]
    x0 = float(b["x"])
    y0 = float(b["y"])
    width = float(b["width"])
    depth = float(b["depth"])
    return (width * scale, depth * scale)


def _render_unit(unit, title, x, y, scale=1.0, show_score=True):
    b = unit["boundary"]
    x0 = float(b["x"])
    y0 = float(b["y"])
    width = float(b["width"])
    depth = float(b["depth"])
    parts = [
        f'<text x="{x + 0.25:.2f}" y="{y - 0.35:.2f}" font-size="0.9" font-weight="bold" fill="#111111">{escape_xml(title)}</text>',
        '<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" fill="#ffffff" stroke="#111111" stroke-width="0.12"/>'.format(
            x, y, width * scale, depth * scale
        ),
    ]

    for room in unit.get("rooms", []):
        poly = " ".join(f'{x + (rx - x0) * scale:.2f},{y + (ry - y0) * scale:.2f}' for rx, ry in room["polygon"])
        parts.append(f'<polygon points="{poly}" fill="{room.get("fill", "#eef6ff")}" stroke="#444444" stroke-width="{0.05 * scale:.2f}"/>')
        cx, cy = room.get("center", [x0 + width / 2, y0 + depth / 2])
        label = f'{room.get("name", "")} | {room.get("area", 0):.1f}m2'
        parts.append(
            f'<text x="{x + (cx - x0) * scale:.2f}" y="{y + (cy - y0) * scale:.2f}" font-size="{0.45 * scale:.2f}" text-anchor="middle" dominant-baseline="middle" fill="#111111">{escape_xml(label)}</text>'
        )

    for door in unit.get("doors", []):
        pt = door.get("point", [x0, y0])
        parts.append(f'<circle cx="{x + (float(pt[0]) - x0) * scale:.2f}" cy="{y + (float(pt[1]) - y0) * scale:.2f}" r="{0.18 * scale:.2f}" fill="#b00020"/>')

    if show_score:
        score = unit.get("score", 0.0)
        status = unit.get("status", "unknown")
        parts.append(f'<text x="{x + 0.25:.2f}" y="{y + depth * scale + 0.55:.2f}" font-size="0.6" fill="#111111">score={float(score):.4f} status={escape_xml(status)}</text>')
    return "\n".join(parts)


def collage_svg(units, columns=3, scale=0.62, gap=0.8, margin=0.5):
    if not units:
        units = []
    rows = (len(units) + columns - 1) // columns
    unit_w = max(float(u["boundary"]["width"]) for u in units) * scale if units else 0.0
    unit_h = max(float(u["boundary"]["depth"]) for u in units) * scale if units else 0.0
    canvas_w = margin * 2 + columns * unit_w + (columns - 1) * gap
    canvas_h = margin * 2 + rows * (unit_h + 1.2) + (rows - 1) * gap

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w:.1f}mm" height="{canvas_h:.1f}mm" viewBox="0 0 {canvas_w:.2f} {canvas_h:.2f}">',
        f'<rect x="0" y="0" width="{canvas_w:.2f}" height="{canvas_h:.2f}" fill="#f6f7f9"/>',
        '<text x="0.6" y="0.6" font-size="1.1" font-weight="bold" fill="#111111">top plans</text>',
    ]

    for idx, unit in enumerate(units):
        row = idx // columns
        col = idx % columns
        x = margin + col * (unit_w + gap)
        y = margin + row * (unit_h + 1.2 + gap) + 0.5
        parts.append(_render_unit(unit, unit.get("unit_id", f"unit_{idx}"), x, y, scale=scale))

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("out_svg", type=Path)
    parser.add_argument("--top", type=int, default=6)
    parser.add_argument("--columns", type=int, default=3)
    parser.add_argument("--scale", type=float, default=0.62)
    args = parser.parse_args()

    units = []
    for path in sorted(args.input_dir.glob("A*.json")):
        units.append(json.loads(path.read_text(encoding="utf-8")))
    units.sort(key=lambda u: float(u.get("score", 0.0)), reverse=True)
    units = units[: args.top]
    args.out_svg.parent.mkdir(parents=True, exist_ok=True)
    args.out_svg.write_text(collage_svg(units, columns=args.columns, scale=args.scale), encoding="utf-8")
    print(f"wrote {args.out_svg}")


if __name__ == "__main__":
    main()
