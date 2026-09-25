from __future__ import annotations

import importlib
import sys
import traceback
from pathlib import Path


def run_tests() -> int:
    tests_dir = Path(__file__).resolve().parent
    repo_root = tests_dir.parent
    sys.path.insert(0, str(repo_root))

    modules = [
        importlib.import_module("tests.test_rule_checker"),
        importlib.import_module("tests.test_rule_registry"),
        importlib.import_module("tests.test_plan_svg"),
        importlib.import_module("tests.test_switch_policy"),
        importlib.import_module("tests.test_comparison_svg"),
        importlib.import_module("tests.test_top_plans_svg"),
        importlib.import_module("tests.test_run_unit_matrix"),
        importlib.import_module("tests.test_gh_matrix_wrapper"),
        importlib.import_module("tests.test_compare_policy_matrix"),
        importlib.import_module("tests.test_generate_report_pack"),
        importlib.import_module("tests.test_gh_report_pack"),
        importlib.import_module("tests.test_make_dashboard"),
    ]

    failures = 0
    for module in modules:
        for name in sorted(dir(module)):
            if not name.startswith("test_"):
                continue
            obj = getattr(module, name)
            if not callable(obj):
                continue
            try:
                obj()
            except Exception:
                failures += 1
                print(f"FAIL: {module.__name__}.{name}")
                traceback.print_exc()

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
