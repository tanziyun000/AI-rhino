from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPARISON_TOOL = REPO_ROOT / "tools" / "compare_policies.py"


def _resolve_config(raw: Path, matrix_path: Path) -> Path:
    if raw.is_absolute():
        return raw
    candidates = [raw, matrix_path.parent / raw, REPO_ROOT / raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _run_compare(config_path: Path, out_dir: Path, count: int) -> dict:
    result = subprocess.run(
        [sys.executable, str(COMPARISON_TOOL), "--config", str(config_path), "--count", str(count), "--out-dir", str(out_dir)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "compare_policies failed").strip()
        raise subprocess.CalledProcessError(result.returncode, [str(COMPARISON_TOOL)], output=result.stdout, stderr=result.stderr)
    report_path = out_dir / "comparison_report.json"
    if report_path.exists():
        return json.loads(report_path.read_text(encoding="utf-8"))
    return {
        "config": str(config_path),
        "unit_type": "",
        "error": "compare_policies did not produce comparison_report.json",
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run default vs variant policy comparisons for a matrix of unit configs.")
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "results" / "policy_matrix")
    args = parser.parse_args()

    matrix_path = args.matrix
    if not matrix_path.is_absolute():
        cwd_candidate = Path.cwd() / matrix_path
        if cwd_candidate.exists():
            matrix_path = cwd_candidate
        else:
            repo_candidate = REPO_ROOT / matrix_path
            matrix_path = repo_candidate if repo_candidate.exists() else cwd_candidate

    matrix_path = matrix_path.resolve()
    args.out_dir = (args.out_dir if args.out_dir.is_absolute() else Path.cwd() / args.out_dir).resolve()

    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    entries = matrix.get("configs", [])
    if not entries:
        raise ValueError("matrix must contain at least one config")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    matrix_report = {
        "matrix": str(matrix_path),
        "out_dir": str(args.out_dir),
        "count": args.count,
        "items": [],
    }

    for idx, entry in enumerate(entries):
        config_path = _resolve_config(Path(entry), matrix_path)
        if not config_path.exists():
            raise FileNotFoundError(f"config not found: {entry}")

        unit_type = json.loads(config_path.read_text(encoding="utf-8")).get("unit_type", config_path.stem)
        unit_dir = args.out_dir / unit_type
        unit_dir.mkdir(parents=True, exist_ok=True)

        try:
            report = _run_compare(config_path, unit_dir, args.count)
        except subprocess.CalledProcessError as exc:
            report = {
                "config": str(config_path),
                "unit_type": unit_type,
                "error": f"compare_policies failed: {exc}",
            }
        matrix_report["items"].append(report)

    report_path = args.out_dir / "policy_matrix_report.json"
    report_path.write_text(json.dumps(matrix_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (args.out_dir / "policy_matrix_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["unit_type", "default_valid", "variant_valid", "default_score", "variant_score", "status"])
        writer.writeheader()
        for item in matrix_report["items"]:
            status = "ok" if "error" not in item else "failed"
            default_summary = item.get("default", {})
            variant_summary = item.get("variant", {})
            writer.writerow({
                "unit_type": item.get("unit_type", ""),
                "default_valid": default_summary.get("valid", ""),
                "variant_valid": variant_summary.get("valid", ""),
                "default_score": default_summary.get("top_score", ""),
                "variant_score": variant_summary.get("top_score", ""),
                "status": status,
            })

    print(json.dumps(matrix_report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
