from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GH_SCRIPT = REPO_ROOT / "gh" / "scripts" / "run_unit_matrix.py"


def _resolve_cli_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path)
    cwd_candidate = Path.cwd() / path
    if cwd_candidate.exists():
        return str(cwd_candidate)
    repo_candidate = REPO_ROOT / path
    if repo_candidate.exists():
        return str(repo_candidate)
    return str(path)


def main() -> int:
    return subprocess.call([sys.executable, str(GH_SCRIPT), *[_resolve_cli_path(arg) for arg in sys.argv[1:]]], cwd=str(REPO_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
