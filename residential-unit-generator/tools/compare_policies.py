from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from make_comparison_svg import comparison_svg


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_PROTOTYPE = REPO_ROOT / "run_prototype.py"


def _run(cmd):
    subprocess.check_call([sys.executable, *cmd], cwd=str(REPO_ROOT))


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _summary(out_dir):
    unit_files = sorted(out_dir.glob("A*.json"))
    results = [_load(path) for path in unit_files]
    valid_count = sum(1 for r in results if r.get("status") == "valid")
    scores = [float(r.get("score", 0.0)) for r in results]
    warning_count = sum(len(r.get("warnings", [])) for r in results)
    failure_count = sum(len(r.get("failures", [])) for r in results)
    top = max(results, key=lambda r: float(r.get("score", 0.0))) if results else None
    room_areas = {r["name"]: round(float(r.get("area", 0.0)), 2) for r in (top.get("rooms", []) if top else [])}
    return {
        "generated": len(results),
        "valid": valid_count,
        "average_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "warning_count": warning_count,
        "failure_count": failure_count,
        "top_score": float(top["score"]) if top else 0.0,
        "best_unit": top["unit_id"] if top else None,
        "top_room_areas": room_areas,
    }


def _infer_unit_prefix(config_path: Path) -> str:
    unit_type = _load(config_path).get("unit_type", "")
    if isinstance(unit_type, str) and unit_type:
        return unit_type.lower().replace(" ", "_")
    stem = config_path.stem
    if stem.startswith("default_"):
        return stem.split("_", 1)[1]
    return stem.split("_", 1)[0]


def _policy_path(config_path: Path, variant: bool, unit_prefix: str) -> Path:
    filename = f"{unit_prefix}_adjacency_policy{'_variant' if variant else ''}.json"
    return config_path.parent / "policies" / filename


def _prepare_variant(config_path: Path, work_dir: Path, variant: bool, unit_prefix: str) -> Path:
    out_path = work_dir / (config_path.stem + ("_variant" if variant else "_default") + ".json")
    cfg = _load(config_path)
    policy_path = _policy_path(config_path, variant, unit_prefix).resolve()
    cfg["policy_file"] = str(policy_path)
    out_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def _resolve_config(raw: Path) -> Path:
    if raw.is_absolute():
        return raw
    candidates = [raw, REPO_ROOT / raw, REPO_ROOT / "configs" / raw.name]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run default vs variant policy comparison for a unit config.")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "configs" / "default_3br.json", help="Config JSON to compare")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "results" / "policy_comparison")
    parser.add_argument("--default-policy", type=Path, default=None, help="Override default policy path")
    parser.add_argument("--variant-policy", type=Path, default=None, help="Override variant policy path")
    args = parser.parse_args()

    config_path = _resolve_config(args.config)
    if not config_path.exists():
        print(f"config not found: {config_path}")
        return 2

    unit_prefix = _infer_unit_prefix(config_path)

    work_dir = args.out_dir / "work"
    work_dir.mkdir(parents=True, exist_ok=True)

    default_policy_path = args.default_policy if args.default_policy else _policy_path(config_path, False, unit_prefix)
    variant_policy_path = args.variant_policy if args.variant_policy else _policy_path(config_path, True, unit_prefix)
    if not default_policy_path.exists():
        print(f"policy not found: {default_policy_path}")
        return 2
    if not variant_policy_path.exists():
        print(f"policy not found: {variant_policy_path}")
        return 2

    default_cfg = _prepare_variant(config_path, work_dir, False, unit_prefix)
    variant_cfg = _prepare_variant(config_path, work_dir, True, unit_prefix)

    default_out = args.out_dir / "default"
    variant_out = args.out_dir / "variant"
    for out_dir in (default_out, variant_out):
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

    _run([str(RUN_PROTOTYPE), str(default_cfg.resolve()), str(args.count), str(default_out.resolve())])
    _run([str(RUN_PROTOTYPE), str(variant_cfg.resolve()), str(args.count), str(variant_out.resolve())])

    default_top_path = default_out / f"{_summary(default_out)['best_unit']}.json"
    variant_top_path = variant_out / f"{_summary(variant_out)['best_unit']}.json"
    comparison_svg_path = args.out_dir / "comparison_plan.svg"
    comparison_svg_path.write_text(comparison_svg(_load(default_top_path), _load(variant_top_path)), encoding="utf-8")

    report = {
        "count": args.count,
        "config": str(config_path),
        "unit_type": _load(config_path).get("unit_type", ""),
        "default": _summary(default_out),
        "variant": _summary(variant_out),
        "out_dir": str(args.out_dir),
        "comparison_svg": str(comparison_svg_path),
    }
    (args.out_dir / "comparison_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
