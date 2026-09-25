from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def _read_svg(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _score_cell(value) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.4f}"
    except Exception:
        return str(value)


def build_policy_matrix_html(policy_matrix_report: dict | None) -> str:
    if not policy_matrix_report or not policy_matrix_report.get("items"):
        return ""

    rows = []
    preview_cards = []
    for item in policy_matrix_report.get("items", []):
        unit_type = item.get("unit_type") or item.get("config", "")
        if "error" in item:
            rows.append(
                "<tr>"
                f"<td>{html.escape(str(unit_type))}</td>"
                f"<td>failed</td>"
                f"<td>-</td><td>-</td><td>-</td><td>-</td>"
                "</tr>"
            )
            preview_cards.append(
                f'<div class="card"><div class="card-title">Policy {html.escape(str(unit_type))}</div>'
                '<p class="note">Comparison SVG unavailable.</p></div>'
            )
            continue

        default_summary = item.get("default", {})
        variant_summary = item.get("variant", {})
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(unit_type))}</td>"
            f"<td>ok</td>"
            f"<td>{html.escape(str(default_summary.get('valid', '-')))} </td>"
            f"<td>{html.escape(str(variant_summary.get('valid', '-')))} </td>"
            f"<td>{html.escape(_score_cell(default_summary.get('top_score')))} </td>"
            f"<td>{html.escape(_score_cell(variant_summary.get('top_score')))} </td>"
            "</tr>"
        )

        svg_path = Path(item.get("comparison_svg", "")) if item.get("comparison_svg") else None
        svg = _read_svg(svg_path) if svg_path and svg_path.exists() else ""
        fallback = '<p class="note">No comparison SVG found.</p>'
        default_top = _score_cell(default_summary.get('top_score'))
        variant_top = _score_cell(variant_summary.get('top_score'))
        preview_cards.append(
            f'<div class="card"><div class="card-title">Policy {html.escape(str(unit_type))}</div>'
            f'<div class="metric">default top {html.escape(str(default_top))}</div>'
            f'<div class="metric">variant top {html.escape(str(variant_top))}</div>'
            f"{svg or fallback}</div>"
        )

    preview_section = f"""
<div class="grid">{''.join(preview_cards)}</div>
""" if preview_cards else ""

    return f"""
<div class="section">
<h2>Policy matrix</h2>
<table>
<thead><tr><th>Unit type</th><th>Status</th><th>Default valid</th><th>Variant valid</th><th>Default top</th><th>Variant top</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</div>
<div class="section">
<h2>Policy comparison previews</h2>
{preview_section}
</div>
"""


def _read_json(path: Path | None) -> dict | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def build_dashboard_html(top_plans_report: dict | None, policy_report: dict | None, matrix_report: dict | None = None, policy_matrix_report: dict | None = None, pack_summary: dict | None = None) -> str:
    top = top_plans_report or {}
    top_summary = top.get("summary", {})
    policy = policy_report or {}
    default = policy.get("default", {})
    variant = policy.get("variant", {})

    top_svg = _read_svg(Path(top.get("top_plans_svg", "")))
    comp_svg = _read_svg(Path(policy.get("comparison_svg", "")))

    cards = [
        ("Top plans", top_summary.get("generated", 0), top_summary.get("valid", 0), top_summary.get("top_score", None)),
        ("Policy default", default.get("generated", 0), default.get("valid", 0), default.get("top_score", None)),
        ("Policy variant", variant.get("generated", 0), variant.get("valid", 0), variant.get("top_score", None)),
    ]

    matrix = matrix_report or {}
    matrix_items = matrix.get("items", [])
    matrix_cards = []
    for item in matrix_items:
        s = item.get("summary", {})
        matrix_cards.append((
            item.get("unit_type", ""),
            s.get("count", 0),
            s.get("valid", 0),
            s.get("failed", 0),
            s.get("exception", 0),
            s.get("best_unit", "-"),
            s.get("top_score", None),
        ))

    card_html = []
    for name, generated, valid, score in cards:
        card_html.append(
            f'<div class="card"><div class="card-title">{html.escape(str(name))}</div>'
            f'<div class="metric">generated {html.escape(str(generated))}</div>'
            f'<div class="metric">valid {html.escape(str(valid))}</div>'
            f'<div class="metric">top score {html.escape(_score_cell(score))}</div></div>'
        )

    matrix_card_html = []
    for unit_type, count, valid, failed, exception, best_unit, score in matrix_cards:
        matrix_card_html.append(
            f'<div class="card"><div class="card-title">Matrix {html.escape(str(unit_type))}</div>'
            f'<div class="metric">generated {html.escape(str(count))}</div>'
            f'<div class="metric">valid {html.escape(str(valid))}</div>'
            f'<div class="metric">failed {html.escape(str(failed))}</div>'
            f'<div class="metric">exception {html.escape(str(exception))}</div>'
            f'<div class="metric">best unit {html.escape(str(best_unit))}</div>'
            f'<div class="metric">top score {html.escape(_score_cell(score))}</div></div>'
        )

    default_areas = default.get("top_room_areas", {})
    variant_areas = variant.get("top_room_areas", {})
    room_rows = []
    for room in sorted(set(default_areas) | set(variant_areas)):
        room_rows.append(
            "<tr>"
            f"<td>{html.escape(room)}</td>"
            f"<td>{html.escape(str(default_areas.get(room, '-')))}</td>"
            f"<td>{html.escape(str(variant_areas.get(room, '-')))}</td>"
            "</tr>"
        )

    matrix_section = ""
    if matrix_items:
        matrix_rows = []
        for unit_type, count, valid, failed, exception, best_unit, score in matrix_cards:
            matrix_rows.append(
                "<tr>"
                f"<td>{html.escape(str(unit_type))}</td>"
                f"<td>{html.escape(str(count))}</td>"
                f"<td>{html.escape(str(valid))}</td>"
                f"<td>{html.escape(str(failed))}</td>"
                f"<td>{html.escape(str(exception))}</td>"
                f"<td>{html.escape(str(best_unit))}</td>"
                f"<td>{html.escape(_score_cell(score))}</td>"
                "</tr>"
            )
        matrix_section = f"""
<div class="section">
<h2>Unit matrix</h2>
<table>
<thead><tr><th>Unit type</th><th>Generated</th><th>Valid</th><th>Failed</th><th>Exception</th><th>Best unit</th><th>Top score</th></tr></thead>
<tbody>
{''.join(matrix_rows)}
</tbody>
</table>
</div>
"""

    matrix_best_section = ""
    if matrix_items:
        best_plans = []
        for item in matrix_items:
            best_unit = item.get("summary", {}).get("best_unit", "-")
            best_svg_path = Path(item.get("best_unit_svg", "")) if item.get("best_unit_svg") else None
            best_svg = _read_svg(best_svg_path) if best_svg_path and best_svg_path.exists() else ""
            best_plans.append((item.get("unit_type", ""), best_unit, best_svg))
        plan_cards = []
        for unit_type, best_unit, best_svg in best_plans:
            fallback = '<p class="note">No SVG found.</p>'
            plan_cards.append(
                f'<div class="card"><div class="card-title">Matrix {html.escape(str(unit_type))} · {html.escape(str(best_unit))}</div>'
                f'{best_svg or fallback}</div>'
            )
        matrix_best_section = f"""
<div class="section">
<h2>Matrix best plans</h2>
<div class="grid">{''.join(plan_cards)}</div>
</div>
"""

    policy_matrix_section = build_policy_matrix_html(policy_matrix_report)

    pack_section = ""
    if pack_summary:
        pack_summary = pack_summary if isinstance(pack_summary, dict) else {}
        pack_rows = [
            ("Status", pack_summary.get("status", "-")),
            ("Matrix path", pack_summary.get("matrix_path", "-")),
            ("Unit report", pack_summary.get("unit_report_path", "-")),
            ("Policy report", pack_summary.get("policy_report_path", "-")),
            ("Dashboard path", pack_summary.get("dashboard_path", "-")),
            ("Summary path", pack_summary.get("summary_path", "-")),
            ("Dry run", str(bool(pack_summary.get("dry_run", False)))),
            ("Skip dashboard", str(bool(pack_summary.get("skip_dashboard", False)))),
            ("Verify", str(bool(pack_summary.get("verify", False)))),
            ("Started at", pack_summary.get("started_at", "-")),
            ("Finished at", pack_summary.get("finished_at", "-")),
        ]
        pack_rows_html = "".join(
            f"<tr><td>{html.escape(str(name))}</td><td>{html.escape(str(value))}</td></tr>"
            for name, value in pack_rows
        )
        pack_section = f"""
<div class="section">
<h2>Report pack summary</h2>
<table>
<thead><tr><th>Field</th><th>Value</th></tr></thead>
<tbody>{pack_rows_html}</tbody>
</table>
</div>
"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Residential Unit Generator Dashboard</title>
<style>
body {{ font-family: Inter, Segoe UI, Arial, sans-serif; margin: 24px; color: #111; background: #f6f7f9; }}
h1, h2 {{ margin: 0 0 12px 0; }}
.grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 20px; }}
.card {{ background: white; border: 1px solid #d8dee9; border-radius: 10px; padding: 14px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
.card-title {{ font-weight: 700; margin-bottom: 8px; }}
.metric {{ font-size: 0.95em; color: #333; margin: 2px 0; }}
.section {{ background: white; border: 1px solid #d8dee9; border-radius: 10px; padding: 14px; margin-bottom: 16px; }}
svg {{ width: 100%; height: auto; display: block; }}
table {{ width: 100%; table-collapse: collapse; margin-top: 10px; }}
th, td {{ border: 1px solid #d8dee9; padding: 8px; text-align: left; }}
th {{ background: #eef1f6; }}
.note {{ color: #555; font-size: 0.92em; }}
</style>
</head>
<body>
<h1>Residential Unit Generator Dashboard</h1>
<p class="note">Generated from current prototype outputs.</p>
<div class="grid">
{''.join(card_html)}
</div>
{('<div class="grid">' + ''.join(matrix_card_html) + '</div>') if matrix_card_html else ''}
{matrix_section}
{matrix_best_section}
{policy_matrix_section}
{pack_section}
<div class="section">
<h2>Top plans</h2>
{top_svg or '<p class="note">No top plans SVG found.</p>'}
</div>

<div class="section">
<h2>Policy comparison</h2>
{comp_svg or '<p class="note">No comparison SVG found.</p>'}
</div>

<div class="section">
<h2>Top room areas</h2>
<table>
<thead><tr><th>Room</th><th>Default</th><th>Variant</th></tr></thead>
<tbody>
{''.join(room_rows) if room_rows else '<tr><td colspan="3">No room area data.</td></tr>'}
</tbody>
</table>
</div>
</body>
</html>
"""


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a dashboard HTML from prototype reports.")
    parser.add_argument("--top-plans-report", type=Path, default=REPO_ROOT / "results" / "top_plans" / "top_plans_report.json")
    parser.add_argument("--policy-report", type=Path, default=REPO_ROOT / "results" / "policy_comparison" / "comparison_report.json")
    parser.add_argument("--matrix-report", type=Path, default=REPO_ROOT / "results" / "unit_matrix" / "matrix_report.json")
    parser.add_argument("--policy-matrix-report", type=Path, default=REPO_ROOT / "results" / "policy_matrix" / "policy_matrix_report.json")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "results" / "dashboard.html")
    parser.add_argument("--pack-summary", type=Path, default=None, help="Optional report pack summary JSON to include in the dashboard")
    args = parser.parse_args()

    top_plans_report = None
    if args.top_plans_report.exists():
        top_plans_report = json.loads(args.top_plans_report.read_text(encoding="utf-8"))

    policy_report = None
    if args.policy_report.exists():
        policy_report = json.loads(args.policy_report.read_text(encoding="utf-8"))

    matrix_report = None
    if args.matrix_report.exists():
        matrix_report = json.loads(args.matrix_report.read_text(encoding="utf-8"))

    policy_matrix_report = None
    if args.policy_matrix_report.exists():
        policy_matrix_report = json.loads(args.policy_matrix_report.read_text(encoding="utf-8"))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    pack_summary = _read_json(args.pack_summary)
    args.out.write_text(build_dashboard_html(top_plans_report, policy_report, matrix_report, policy_matrix_report, pack_summary), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
