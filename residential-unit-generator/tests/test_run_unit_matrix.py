from pathlib import Path
import contextlib
import io
import tempfile
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gh.scripts import run_unit_matrix as runner


def _make_file(path: Path, content: str = "{}") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_resolve_arg_path_prefers_repo_root_then_cwd():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        repo_root = root / "repo"
        cwd_root = root / "cwd"
        repo_file = repo_root / "configs" / "matrix.json"
        cwd_file = cwd_root / "results" / "unit_matrix.json"
        _make_file(repo_file)
        _make_file(cwd_file)

        with patch.object(runner, "_REPO_ROOT", repo_root), patch.object(runner.Path, "cwd", return_value=cwd_root):
            assert runner._resolve_arg_path(Path("configs/matrix.json")) == repo_file
            assert runner._resolve_arg_path(Path("results/unit_matrix.json")) == cwd_file


def test_resolve_out_dir_existing_relative_dir():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        repo_root = root / "repo"
        out_dir = repo_root / "relative-out" / "unit_matrix"
        out_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(runner, "_REPO_ROOT", repo_root):
            assert runner._resolve_out_dir(Path("relative-out/unit_matrix"), Path("configs/unit_matrix.json")) == out_dir


def test_resolve_out_dir_fallback():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        repo_root = root / "repo"
        repo_root.mkdir(parents=True, exist_ok=True)

        with patch.object(runner, "_REPO_ROOT", repo_root):
            assert runner._resolve_out_dir(Path("missing/out"), Path("configs/unit_matrix.json")) == (repo_root / "configs" / "results" / "unit_matrix")


def test_run_matrix_count_override_uses_cli_value():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        repo_root = root / "repo"
        repo_root.mkdir(parents=True, exist_ok=True)
        matrix_path = repo_root / "configs" / "matrix.json"
        matrix_path.parent.mkdir(parents=True, exist_ok=True)
        unit_path = repo_root / "configs" / "unit.json"
        unit_path.write_text('{}', encoding="utf-8")
        matrix_path.write_text('{"configs": ["configs/unit.json"], "count": 5}', encoding="utf-8")

        calls = []

        def fake_unit_summary(cfg_path: Path, out_dir: Path, count: int):
            calls.append(int(count))
            return {
                "config": str(cfg_path),
                "unit_type": "studio",
                "out_dir": str(out_dir),
                "summary": {"count": count, "valid": 0, "failed": 0, "exception": 0, "top_score": 0.0, "best_unit": None},
                "best_unit_json": "",
                "best_unit_svg": "",
            }

        with contextlib.redirect_stdout(io.StringIO()), patch.object(runner, "_unit_summary", side_effect=fake_unit_summary), patch.object(runner, "_REPO_ROOT", repo_root):
            runner.run_matrix(matrix_path, root / "out", count_override=3)

        assert calls == [3]
