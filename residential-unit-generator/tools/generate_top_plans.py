from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "default_3br.json"
RUN_PROTOTYPE = REPO_ROOT / "run_prototype.py"
TOP_PLANS_SVG = REPO_ROOT / "tools" / "make_top_plans_svg.py"


def _summary(out_dir):
    unit_files = sorted(out_dir.glob("A*.json"))
    results = [json.loads(path.read_text(encoding="utf-8")) for path in unit_files]
    valid_count = sum(1 for r in results if r.get("status") == "valid")
    top = max(results, key=lambda r: float(r.get("score", 0.0))) if results else None
    return {
        "generated": len(results),
        "valid": valid_count,
        "top_score": float(top["score"]) if top else 0.0,
        "best_unit": top["unit_id"] if top else None,
    }


def _run(cmd):
    subprocess.check_call([sys.executable, *cmd], cwd=str(REPO_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run batch generation and emit a top-plans SVG collage.")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "results" / "top_plans")
    parser.add_argument("--top", type=int, default=6)
    args = parser.parse_args()

    if args.out_dir.exists():
        shutil.rmtree(args.out_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    _run([str(RUN_PROTOTYPE), str(CONFIG_PATH), str(args.count), str(args.out_dir)])
    collage_path = args.out_dir / "top_plans.svg"
    _run([str(TOP_PLANS_SVG), str(args.out_dir), str(collage_path), "--top", str(args.top)])

    report = {
        "count": args.count,
        "out_dir": str(args.out_dir),
        "summary": _summary(args.out_dir),
        "top_plans_svg": str(collage_path),
    }
    (args.out_dir / "top_plans_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
