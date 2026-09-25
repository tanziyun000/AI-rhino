from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .scripts.config_loader import load_config, validate_config
from .scripts.batch_runner import generate_batch, rank_results, write_summary
from .scripts.geometry_model import UnitGeometryBundle, build_geometry_payload


class GH_Interface:
    """Grasshopper-facing wrapper for the residential-unit-generator prototype."""

    def __init__(
        self,
        config_path: str = "configs/default_3br.json",
        count: int = 20,
        seed_start: int = 0,
        out_dir: str = "results",
    ) -> None:
        self.config_path = str(config_path)
        self.count = int(count)
        self.seed_start = int(seed_start)
        self.out_dir = str(out_dir)
        self._results: Optional[List[dict]] = None
        self._ranked_results: Optional[List[dict]] = None
        self._geometry: Optional[UnitGeometryBundle] = None
        self._summary_path: Optional[Path] = None

    def run(
        self,
        config_path: Optional[str] = None,
        count: Optional[int] = None,
        seed_start: Optional[int] = None,
        out_dir: Optional[str] = None,
    ) -> List[dict]:
        if config_path is not None:
            self.config_path = str(config_path)
        if count is not None:
            self.count = int(count)
        if seed_start is not None:
            self.seed_start = int(seed_start)
        if out_dir is not None:
            self.out_dir = str(out_dir)

        config = load_config(self.config_path)
        validate_config(config)

        self._results = generate_batch(config, count=self.count, seed_start=self.seed_start)
        self._ranked_results = rank_results(self._results)
        self._geometry = UnitGeometryBundle(self._ranked_results)

        out_dir = Path(self.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        self._summary_path = out_dir / "batch_summary.csv"
        write_summary(self._ranked_results, self._summary_path)

        return self._ranked_results

    @property
    def results(self) -> List[dict]:
        return list(self._results or [])

    @property
    def ranked_results(self) -> List[dict]:
        return list(self._ranked_results or [])

    @property
    def top_result(self) -> Optional[dict]:
        if not self._ranked_results:
            return None
        return self._ranked_results[0]

    @property
    def geometry(self) -> UnitGeometryBundle:
        if self._geometry is None:
            self._geometry = UnitGeometryBundle(self.ranked_results)
        return self._geometry

    @property
    def summary_path(self) -> Optional[str]:
        return str(self._summary_path) if self._summary_path is not None else None

    def summary(self) -> Dict[str, Any]:
        top = self.top_result or {}
        return {
            "generated": len(self._ranked_results or []),
            "valid": sum(1 for r in self._ranked_results or [] if r.get("status") == "valid"),
            "failed": sum(1 for r in self._ranked_results or [] if r.get("status") == "failed"),
            "exception": sum(1 for r in self._ranked_results or [] if r.get("status") == "exception"),
            "top_score": float(top.get("score", 0.0)),
            "top_unit_id": top.get("unit_id"),
            "summary_path": self.summary_path,
        }

    def payloads(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        summary = self.summary()
        geometry = build_geometry_payload(self.ranked_results)
        return summary, geometry

    def json_text(self) -> str:
        summary, geometry = self.payloads()
        return json.dumps({"summary": summary, "geometry": geometry}, ensure_ascii=False, indent=2)


class PolicyMatrixGenerator:
    """Grasshopper-facing wrapper for policy-matrix comparisons."""

    def __init__(
        self,
        matrix_path: str = "configs/unit_matrix.json",
        out_dir: str = "results/policy_matrix",
        count: Optional[int] = 1,
    ) -> None:
        self.matrix_path = str(matrix_path)
        self.out_dir = str(out_dir)
        self.count = int(count) if count is not None else 1
        self._summary_path: Optional[Path] = Path(out_dir) / "policy_matrix_summary.csv"

    def run(self) -> None:
        import subprocess

        repo_root = Path(__file__).resolve().parents[1]
        comparison_tool = repo_root / "tools" / "compare_policy_matrix.py"

        matrix_path = Path(self.matrix_path)
        if not matrix_path.is_absolute():
            repo_candidate = repo_root / matrix_path
            cwd_candidate = Path.cwd() / matrix_path
            if repo_candidate.exists():
                matrix_path = repo_candidate
            elif cwd_candidate.exists():
                matrix_path = cwd_candidate

        out_dir = Path(self.out_dir)
        if not out_dir.is_absolute():
            out_dir = Path.cwd() / out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        self._summary_path = out_dir / "policy_matrix_summary.csv"

        result = subprocess.run(
            [
                sys.executable,
                str(comparison_tool),
                str(matrix_path),
                "--count",
                str(self.count),
                "--out-dir",
                str(out_dir),
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "policy matrix failed").strip()
            raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout, stderr=result.stderr)
        self._last_stdout = result.stdout
        self._last_stderr = result.stderr

    @property
    def summary_path(self) -> Optional[str]:
        return str(self._summary_path) if self._summary_path is not None else None

    def summary(self) -> Dict[str, Any]:
        report_path = Path(self.out_dir) / "policy_matrix_report.json"
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            items = report.get("items", [])
            comparison_svg_paths = [item.get("comparison_svg", "") for item in items if item.get("comparison_svg")]
            ok_count = sum(1 for item in items if "error" not in item)
            failed_count = sum(1 for item in items if "error" in item)
            return {
                "matrix": report.get("matrix", self.matrix_path),
                "out_dir": report.get("out_dir", self.out_dir),
                "count": report.get("count", self.count),
                "items": len(items),
                "ok_count": ok_count,
                "failed_count": failed_count,
                "summary_path": self.summary_path,
                "comparison_svg_paths": comparison_svg_paths,
                "comparison_svg_count": len(comparison_svg_paths),
                "report_path": str(report_path),
            }
        return {
            "matrix": self.matrix_path,
            "out_dir": self.out_dir,
            "count": self.count,
            "items": 0,
            "ok_count": 0,
            "failed_count": 0,
            "summary_path": self.summary_path,
            "comparison_svg_paths": [],
            "comparison_svg_count": 0,
            "report_path": str(report_path),
        }


class MatrixGenerator:
    """Grasshopper-facing wrapper for unit-matrix runs."""

    def __init__(
        self,
        matrix_path: str = "configs/unit_matrix.json",
        out_dir: str = "results/unit_matrix",
        config_path: Optional[str] = None,
        count: Optional[int] = None,
        seed_start: Optional[int] = None,
    ) -> None:
        self.matrix_path = str(matrix_path)
        self.out_dir = str(out_dir)
        self.config_path = config_path
        self.count = int(count) if count is not None else None
        self.seed_start = int(seed_start) if seed_start is not None else None
        self._summary_path: Optional[Path] = Path(out_dir) / "matrix_summary.csv"

    def run(self) -> None:
        out_dir = Path(self.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        self._summary_path = out_dir / "matrix_summary.csv"
        from gh.scripts.run_unit_matrix import run_matrix

        matrix_path = Path(self.matrix_path)
        if not matrix_path.is_absolute():
            repo_root = Path(__file__).resolve().parents[1]
            candidate = repo_root / matrix_path
            if candidate.exists():
                matrix_path = candidate

        run_matrix(matrix_path, Path(self.out_dir))

    @property
    def summary_path(self) -> Optional[str]:
        return str(self._summary_path) if self._summary_path is not None else None

    def summary(self) -> Dict[str, Any]:
        report_path = Path(self.out_dir) / "matrix_report.json"
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            items = report.get("items", [])
            return {
                "matrix": report.get("matrix", self.matrix_path),
                "out_dir": report.get("out_dir", self.out_dir),
                "items": len(items),
                "summary_path": self.summary_path,
                "best_unit_svg_paths": [item.get("best_unit_svg", "") for item in items if item.get("best_unit_svg")],
            }
        return {
            "matrix": self.matrix_path,
            "out_dir": self.out_dir,
            "items": 0,
            "summary_path": self.summary_path,
            "best_unit_svg_paths": [],
        }
