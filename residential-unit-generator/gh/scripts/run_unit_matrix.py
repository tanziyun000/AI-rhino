from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from gh.scripts.config_loader import load_config, validate_config
from gh.scripts.batch_runner import generate_batch, rank_results, write_summary, write_unit_json

RUN_PROTOTYPE = _REPO_ROOT / "run_prototype.py"


def _summarize(results):
    valid = sum(1 for r in results if r.get("status") == "valid")
    failures = sum(1 for r in results if r.get("status") == "failed")
    exceptions = sum(1 for r in results if r.get("status") == "exception")
    top = max(results, key=lambda r: float(r.get("score", 0.0))) if results else None
    return {
        "count": len(results),
        "valid": valid,
        "failed": failures,
        "exception": exceptions,
        "top_score": float(top.get("score", 0.0)) if top else 0.0,
        "best_unit": top.get("unit_id") if top else None,
    }


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _unit_summary(config_path: Path, out_dir: Path, count: int) -> dict:
    cmd = [sys.executable, str(RUN_PROTOTYPE), str(config_path), str(count), str(out_dir)]
    subprocess.check_call(cmd, cwd=str(_REPO_ROOT))

    unit_files = sorted(out_dir.glob("A*.json"))
    results = [_load_json(path) for path in unit_files]
    summary = _summarize(results)
    best_unit = summary.get("best_unit")
    best_json = out_dir / f"{best_unit}.json" if best_unit else None
    best_svg = out_dir / f"{best_unit}_plan.svg" if best_unit else None

    if best_json and best_json.exists():
        best_json = best_json.resolve()
        if best_svg:
            best_svg = best_svg.resolve()
            try:
                svg_path = _REPO_ROOT / "tools" / "make_plan_svg.py"
                import importlib.util
                spec = importlib.util.spec_from_file_location("make_plan_svg", svg_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                svg_for_unit = module.svg_for_unit
            except Exception:
                svg_for_unit = None
            if svg_for_unit is not None:
                best_svg.parent.mkdir(parents=True, exist_ok=True)
                unit_data = _load_json(best_json)
                if unit_data.get("boundary") is not None:
                    best_svg.write_text(svg_for_unit(unit_data), encoding="utf-8")

    return {
        "config": str(config_path),
        "unit_type": _load_json(config_path).get("unit_type", ""),
        "out_dir": str(out_dir),
        "summary": summary,
        "best_unit_json": str(best_json) if best_json else "",
        "best_unit_svg": str(best_svg) if best_svg and best_svg.exists() else "",
    }


def _resolve_out_dir(out_dir: Path, matrix_path: Path) -> Path:
    if out_dir.is_absolute():
        return out_dir
    cwd_candidate = Path.cwd() / out_dir
    if cwd_candidate.exists() or (cwd_candidate / "matrix_report.json").exists() or (cwd_candidate / "matrix_summary.csv").exists():
        return cwd_candidate
    repo_candidate = _REPO_ROOT / out_dir
    if repo_candidate.exists() or (repo_candidate / "matrix_report.json").exists() or (repo_candidate / "matrix_summary.csv").exists():
        return repo_candidate
    return _REPO_ROOT / matrix_path.parent / "results" / "unit_matrix"


def run_matrix(matrix_path: Path, out_dir: Path, count_override: int | None = None) -> int:
    matrix = _load_json(matrix_path)
    entries = matrix.get("configs", [])
    if not entries:
        raise ValueError("unit matrix must contain at least one config")

    out_dir = _resolve_out_dir(out_dir, matrix_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "matrix": str(matrix_path),
        "out_dir": str(out_dir),
        "items": [],
    }

    for entry in entries:
        cfg_candidates = []
        entry_path = Path(entry)
        if entry_path.is_absolute():
            cfg_candidates.append(entry_path)
        else:
            cfg_candidates.extend([
                entry_path,
                matrix_path.parent / entry_path,
                _REPO_ROOT / entry_path,
            ])
        cfg = next((candidate for candidate in cfg_candidates if candidate.exists()), None)
        if cfg is None:
            raise FileNotFoundError(f"config not found: {entry}")
        run_out = out_dir / f"{cfg.stem.replace('default_', '')}"
        if run_out.exists():
            import shutil
            shutil.rmtree(run_out)
        run_out.mkdir(parents=True, exist_ok=True)
        item = _unit_summary(cfg, run_out, count=count_override or int(matrix.get("count", 5)))
        report["items"].append(item)

    with (out_dir / "matrix_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["config", "unit_type", "out_dir", "count", "valid", "failed", "exception", "top_score", "best_unit"])
        writer.writeheader()
        for item in report["items"]:
            s = item["summary"]
            writer.writerow({
                "config": item["config"],
                "unit_type": item["unit_type"],
                "out_dir": item["out_dir"],
                "count": s["count"],
                "valid": s["valid"],
                "failed": s["failed"],
                "exception": s["exception"],
                "top_score": s["top_score"],
                "best_unit": s["best_unit"],
            })

    (out_dir / "matrix_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _resolve_arg_path(raw_path: Path) -> Path:
    if raw_path.is_absolute():
        return raw_path
    cwd_candidate = Path.cwd() / raw_path
    if cwd_candidate.exists():
        return cwd_candidate
    repo_candidate = _REPO_ROOT / raw_path
    if repo_candidate.exists():
        return repo_candidate
    return raw_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a matrix of residential unit configs.")
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--count", type=int, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    matrix_path = _resolve_arg_path(args.matrix)

    if args.out_dir is None:
        matrix_parent = matrix_path.parent
        out_dir_candidates = [
            matrix_parent / "results" / "unit_matrix",
            matrix_parent / "matrix_report",
            _REPO_ROOT / "results" / "unit_matrix",
        ]
        out_dir = next((candidate for candidate in out_dir_candidates if candidate.exists()), out_dir_candidates[0])
    else:
        out_dir = _resolve_arg_path(args.out_dir)

    return run_matrix(matrix_path, out_dir, count_override=args.count)


if __name__ == "__main__":
    raise SystemExit(main())
