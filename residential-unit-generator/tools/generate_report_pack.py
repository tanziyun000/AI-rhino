from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_UNIT_MATRIX = REPO_ROOT / "tools" / "run_unit_matrix.py"
COMPARE_POLICY_MATRIX = REPO_ROOT / "tools" / "compare_policy_matrix.py"
MAKE_DASHBOARD = REPO_ROOT / "tools" / "make_dashboard.py"


def _resolve(path: Path) -> Path:
    if path.is_absolute():
        return path
    repo_candidate = REPO_ROOT / path
    cwd_candidate = Path.cwd() / path
    if repo_candidate.exists():
        return repo_candidate
    if cwd_candidate.exists():
        return cwd_candidate
    return cwd_candidate


def _run(args: list[str]) -> None:
    subprocess.check_call(args, cwd=str(REPO_ROOT))


def _json_parse_report(path: Path) -> tuple[bool, str]:
    try:
        json.loads(path.read_text(encoding='utf-8'))
        return True, 'ok'
    except Exception as exc:
        return False, f"invalid json: {exc}"


def _dashboard_pack_summary_report(path: Path) -> tuple[bool, str]:
    try:
        text = path.read_text(encoding='utf-8')
    except Exception as exc:
        return False, f"cannot read dashboard: {exc}"
    if 'Report pack summary' not in text:
        return False, 'dashboard missing report pack summary section'
    return True, 'ok'


def main() -> int:
    parser = argparse.ArgumentParser(description="Run matrix, policy matrix, and dashboard generation together.")
    parser.add_argument("matrix", type=Path, help="Unit matrix config, e.g. configs/unit_matrix.json")
    parser.add_argument("--unit-count", type=int, default=5)
    parser.add_argument("--policy-count", type=int, default=1)
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "results")
    parser.add_argument("--top-plans-report", type=Path, default=None)
    parser.add_argument("--policy-report", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them")
    parser.add_argument("--skip-dashboard", action="store_true", help="Skip dashboard generation")
    parser.add_argument("--verify", action="store_true", help="Check that the expected report artifacts exist without regenerating them")
    parser.add_argument("--json-summary", type=Path, default=None, help="Optional path to write a machine-readable summary JSON")
    args = parser.parse_args()

    started_at = datetime.now(timezone.utc).isoformat()

    matrix_path = _resolve(args.matrix)
    if not matrix_path.exists():
        raise FileNotFoundError(f"matrix config not found: {matrix_path}")

    out_dir = args.out_dir if args.out_dir.is_absolute() else Path.cwd() / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    unit_matrix_dir = out_dir / "unit_matrix"
    policy_matrix_dir = out_dir / "policy_matrix"
    dashboard_path = args.out if args.out else out_dir / "dashboard.html"
    summary_path = args.json_summary if args.json_summary else out_dir / "report_pack_summary.json"

    preliminary_summary = {
        "status": "dry-run" if args.dry_run else "ok",
        "script_path": str(Path(__file__).resolve()),
        "matrix_path": str(matrix_path),
        "out_dir": str(out_dir),
        "unit_report_path": str(unit_matrix_dir / "matrix_report.json"),
        "policy_report_path": str(policy_matrix_dir / "policy_matrix_report.json"),
        "dashboard_path": str(dashboard_path) if not args.skip_dashboard else "",
        "summary_path": str(summary_path),
        "dry_run": bool(args.dry_run),
        "skip_dashboard": bool(args.skip_dashboard),
        "verify": bool(args.verify),
        "started_at": started_at,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(preliminary_summary, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    if args.verify:
        expected_paths = {
            "unit_report_path": unit_matrix_dir / "matrix_report.json",
            "policy_report_path": policy_matrix_dir / "policy_matrix_report.json",
            "dashboard_path": dashboard_path,
        }
        artifacts = {}
        missing = []
        checks = []

        for label, path in expected_paths.items():
            exists = path.exists()
            size = path.stat().st_size if exists else 0
            artifacts[label] = {
                "path": str(path),
                "exists": exists,
                "size_bytes": size,
                "type": "json" if path.suffix == ".json" else "html" if path.suffix == ".html" else path.suffix or "other",
            }
            if not exists:
                missing.append(str(path))
                checks.append({"name": label, "status": "error", "message": "missing artifact"})
            else:
                checks.append({"name": label, "status": "ok", "message": "artifact exists"})

        if not missing:
            for label in ("unit_report_path", "policy_report_path"):
                ok, message = _json_parse_report(expected_paths[label])
                checks.append({"name": f"json_parse:{label}", "status": "ok" if ok else "error", "message": message})
                artifacts[label]["json_parse"] = ok
            if dashboard_path.exists():
                ok, message = _dashboard_pack_summary_report(dashboard_path)
                checks.append({"name": "dashboard_pack_summary", "status": "ok" if ok else "error", "message": message})

        failed_checks = [item for item in checks if item["status"] != "ok"]
        summary_payload = {
            "status": "error" if failed_checks else "ok",
            "script_path": str(Path(__file__).resolve()),
            "matrix_path": str(matrix_path),
            "out_dir": str(out_dir),
            "unit_report_path": str(unit_matrix_dir / "matrix_report.json"),
            "policy_report_path": str(policy_matrix_dir / "policy_matrix_report.json"),
            "dashboard_path": str(dashboard_path),
            "summary_path": str(summary_path),
            "dry_run": bool(args.dry_run),
            "skip_dashboard": bool(args.skip_dashboard),
            "verify": bool(args.verify),
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": artifacts,
            "checks": checks,
            "missing_artifacts": missing,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
        summary_path.write_text(json.dumps(summary_payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        if missing:
            print("missing expected artifacts:")
            for item in missing:
                print(f"- {item}")
            return 1
        if failed_checks:
            print("verification failed:")
            for item in failed_checks:
                print(f"- {item['name']}: {item['message']}")
            return 1
        print("verified expected report artifacts")
        return 0

    unit_matrix_args = [
        sys.executable,
        str(RUN_UNIT_MATRIX),
        str(matrix_path),
        "--count",
        str(args.unit_count),
        "--out-dir",
        str(unit_matrix_dir),
    ]
    if args.dry_run:
        print(" ".join(unit_matrix_args))
    else:
        _run(unit_matrix_args)

    policy_matrix_args = [
        sys.executable,
        str(COMPARE_POLICY_MATRIX),
        str(matrix_path),
        "--count",
        str(args.policy_count),
        "--out-dir",
        str(policy_matrix_dir),
    ]
    if args.dry_run:
        print(" ".join(policy_matrix_args))
    else:
        _run(policy_matrix_args)

    dashboard_args = [
        sys.executable,
        str(MAKE_DASHBOARD),
        "--matrix-report",
        str(unit_matrix_dir / "matrix_report.json"),
        "--policy-matrix-report",
        str(policy_matrix_dir / "policy_matrix_report.json"),
        "--out",
        str(dashboard_path),
        "--pack-summary",
        str(summary_path),
    ]
    if args.top_plans_report:
        dashboard_args.extend(["--top-plans-report", str(_resolve(args.top_plans_report))])
    if args.policy_report:
        dashboard_args.extend(["--policy-report", str(_resolve(args.policy_report))])

    finished_at = datetime.now(timezone.utc).isoformat()
    summary_payload = {
        "status": "dry-run" if args.dry_run else "ok",
        "script_path": str(Path(__file__).resolve()),
        "matrix_path": str(matrix_path),
        "out_dir": str(out_dir),
        "unit_report_path": str(unit_matrix_dir / "matrix_report.json"),
        "policy_report_path": str(policy_matrix_dir / "policy_matrix_report.json"),
        "dashboard_path": str(dashboard_path) if not args.skip_dashboard else "",
        "summary_path": str(summary_path),
        "dry_run": bool(args.dry_run),
        "skip_dashboard": bool(args.skip_dashboard),
        "verify": bool(args.verify),
        "started_at": started_at,
        "finished_at": finished_at,
    }

    if args.skip_dashboard:
        print("skipped dashboard")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary_payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        print(f"wrote {summary_path}")
        return 0

    if args.dry_run:
        print(" ".join(dashboard_args))
    else:
        subprocess.run(
            dashboard_args,
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            check=True,
        )
        print(f"wrote {dashboard_path}")

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary_payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
