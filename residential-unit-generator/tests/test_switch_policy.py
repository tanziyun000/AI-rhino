from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "default_3br.json"
SWITCH_SCRIPT = REPO_ROOT / "tools" / "switch_policy.py"


def _read_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _restore_default():
    subprocess.check_call(
        [sys.executable, str(SWITCH_SCRIPT), str(CONFIG_PATH), "default"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_switch_policy_variant_roundtrip():
    restored = _read_config()
    _restore_default()

    try:
        # switch to variant
        subprocess.check_call(
            [sys.executable, str(SWITCH_SCRIPT), str(CONFIG_PATH), "variant"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        variant_config = _read_config()
        assert variant_config["policy_file"] == "policies/3br_adjacency_policy_variant.json"

        # switch back to default
        subprocess.check_call(
            [sys.executable, str(SWITCH_SCRIPT), str(CONFIG_PATH), "default"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        default_config = _read_config()
        assert default_config["policy_file"] == "policies/3br_adjacency_policy.json"
        assert default_config == restored
    finally:
        # keep repository state stable
        _restore_default()
