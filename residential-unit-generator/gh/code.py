from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _component_base():
    try:
        from ghpythonlib.componentbase import executingcomponent as component  # type: ignore
        return component
    except Exception:
        return object


def _extract_unit_geometry(result: dict):
    rooms = []
    walls = []
    labels = []
    doors = []
    points = []

    for room in result.get("rooms", []):
        rooms.append(room.get("polygon", []))
        labels.append(room.get("name", ""))
        for x, y in room.get("polygon", []):
            points.append([float(x), float(y)])

    for wall in result.get("walls", []):
        seg = wall.get("segment", [])
        if isinstance(seg, list) and len(seg) >= 2:
            walls.append(seg[:2])

    for door in result.get("doors", []):
        pt = door.get("point", [])
        if len(pt) >= 2:
            doors.append(pt[:2])

    return rooms, walls, labels, doors, points


class ResidentialUnitGenerator(_component_base()):
    def __init__(self):
        super().__init__()

    def RunScript(self, config_path, count, seed_start, out_dir):
        if config_path is None:
            raise ValueError("config_path is required")
        if count is None:
            count = 20
        if seed_start is None:
            seed_start = 0
        if out_dir is None:
            out_dir = "results"

        config_path = str(config_path)
        count = int(count)
        seed_start = int(seed_start)
        out_dir = str(out_dir)

        gh_dir = Path(__file__).resolve().parent
        if str(gh_dir) not in sys.path:
            sys.path.insert(0, str(gh_dir))

        repo_root = gh_dir.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))

        try:
            from gh.GH_Interface import GH_Interface, MatrixGenerator  # type: ignore
        except ImportError:
            from GH_Interface import GH_Interface, MatrixGenerator  # type: ignore

        from gh.scripts.rhino_writer import convert_to_rhino_objects  # type: ignore
        from gh.scripts.rhino_output import assemble_rhino_outputs, write_to_rhino  # type: ignore

        iface = GH_Interface(
            config_path=config_path,
            count=count,
            seed_start=seed_start,
            out_dir=out_dir,
        )
        iface.run()
        summary, geometry = iface.payloads()
        top = iface.top_result or {}

        out_payload = json.dumps(summary, ensure_ascii=False, sort_keys=True)
        top_payload = json.dumps(top, ensure_ascii=False, sort_keys=True)
        csv_payload = iface.summary_path or ""

        rooms_payload, walls_payload, labels_payload, doors_payload, points_payload = _extract_unit_geometry(top)
        rhino_payload = convert_to_rhino_objects(top)
        extra_payload = assemble_rhino_outputs(top)
        write_status = write_to_rhino(top)

        return (
            out_payload,
            top_payload,
            csv_payload,
            json.dumps(geometry, ensure_ascii=False, sort_keys=True),
            rooms_payload,
            walls_payload,
            labels_payload,
            doors_payload,
            points_payload,
            rhino_payload,
            extra_payload,
            write_status,
        )


class ResidentialUnitMatrixGenerator(_component_base()):
    def __init__(self):
        super().__init__()

    def RunScript(self, matrix_path, out_dir):
        if matrix_path is None:
            raise ValueError("matrix_path is required")
        if out_dir is None:
            out_dir = "results/unit_matrix"

        matrix_path = str(matrix_path)
        out_dir = str(out_dir)

        gh_dir = Path(__file__).resolve().parent
        if str(gh_dir) not in sys.path:
            sys.path.insert(0, str(gh_dir))

        repo_root = gh_dir.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))

        try:
            from gh.GH_Interface import MatrixGenerator  # type: ignore
        except ImportError:
            from GH_Interface import MatrixGenerator  # type: ignore

        runner = MatrixGenerator(matrix_path=matrix_path, out_dir=out_dir)
        runner.run()
        summary = runner.summary()
        report_path = Path(out_dir) / "matrix_report.json"
        return (
            json.dumps(summary, ensure_ascii=False, sort_keys=True),
            runner.summary_path or "",
            str(report_path) if report_path.exists() else "",
            json.dumps(summary.get("best_unit_svg_paths", []), ensure_ascii=False, sort_keys=True),
        )


class ResidentialPolicyMatrixGenerator(_component_base()):
    def __init__(self):
        super().__init__()

    def RunScript(self, matrix_path, out_dir, count):
        if matrix_path is None:
            raise ValueError("matrix_path is required")
        if out_dir is None:
            out_dir = "results/policy_matrix"
        if count is None:
            count = 1

        matrix_path = str(matrix_path)
        out_dir = str(out_dir)
        count = int(count)

        gh_dir = Path(__file__).resolve().parent
        if str(gh_dir) not in sys.path:
            sys.path.insert(0, str(gh_dir))

        repo_root = gh_dir.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))

        try:
            from gh.GH_Interface import PolicyMatrixGenerator  # type: ignore
        except ImportError:
            from GH_Interface import PolicyMatrixGenerator  # type: ignore

        runner = PolicyMatrixGenerator(matrix_path=matrix_path, out_dir=out_dir, count=count)
        runner.run()
        summary = runner.summary()
        report_path = Path(out_dir) / "policy_matrix_report.json"
        return (
            json.dumps(summary, ensure_ascii=False, sort_keys=True),
            runner.summary_path or "",
            str(report_path) if report_path.exists() else "",
            json.dumps(summary.get("comparison_svg_paths", []), ensure_ascii=False, sort_keys=True),
        )


class ResidentialReportPackGenerator(_component_base()):
    def __init__(self):
        super().__init__()

    def RunScript(self, matrix_path, out_dir, unit_count, policy_count, dry_run, skip_dashboard, verify):
        if matrix_path is None:
            raise ValueError("matrix_path is required")
        if out_dir is None:
            out_dir = "results"
        if unit_count is None:
            unit_count = 5
        if policy_count is None:
            policy_count = 1
        if dry_run is None:
            dry_run = False
        if skip_dashboard is None:
            skip_dashboard = False
        if verify is None:
            verify = False

        gh_dir = Path(__file__).resolve().parent
        repo_root = gh_dir.parent
        script_path = repo_root / "tools" / "generate_report_pack.py"
        matrix_path_obj = Path(matrix_path)
        if not matrix_path_obj.exists():
            raise FileNotFoundError(f"matrix config not found: {matrix_path}")

        args = [
            sys.executable,
            str(script_path),
            str(matrix_path),
            "--unit-count",
            str(int(unit_count)),
            "--policy-count",
            str(int(policy_count)),
            "--out-dir",
            str(out_dir),
        ]
        if bool(dry_run):
            args.append("--dry-run")
        if bool(skip_dashboard):
            args.append("--skip-dashboard")
        if bool(verify):
            args.append("--verify")

        result = subprocess.run(args, cwd=str(repo_root), capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, args, output=result.stdout, stderr=result.stderr)

        out_dir_path = Path(out_dir)
        dashboard_path = Path(out_dir) / "dashboard.html"
        summary_path = out_dir_path / "report_pack_summary.json"
        summary_content = ""
        parsed_summary = {}
        if summary_path.exists():
            summary_content = summary_path.read_text(encoding="utf-8")
            try:
                parsed_summary = json.loads(summary_content)
            except json.JSONDecodeError:
                parsed_summary = {}

        summary_payload = {
            "status": parsed_summary.get("status", "dry-run" if bool(dry_run) else "ok"),
            "script_path": script_path.as_posix(),
            "matrix_path": matrix_path_obj.as_posix(),
            "out_dir": out_dir_path.as_posix(),
            "unit_report_path": (out_dir_path / "unit_matrix" / "matrix_report.json").as_posix(),
            "policy_report_path": (out_dir_path / "policy_matrix" / "policy_matrix_report.json").as_posix(),
            "dashboard_path": dashboard_path.as_posix(),
            "summary_path": summary_path.as_posix(),
            "dry_run": bool(dry_run),
            "skip_dashboard": bool(skip_dashboard),
            "verify": bool(verify),
            "started_at": parsed_summary.get("started_at"),
            "finished_at": parsed_summary.get("finished_at"),
            "args": args,
            "summary_json": summary_content,
        }

        return (
            result.stdout.strip(),
            result.stderr.strip(),
            str(script_path),
            args,
            summary_path.as_posix(),
            json.dumps(summary_payload, ensure_ascii=False, sort_keys=True),
        )
