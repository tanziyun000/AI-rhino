from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Switch the policy_file reference in a residential-unit-generator config.")
    parser.add_argument("config_path", type=Path, help="Path to config JSON, e.g. configs/default_3br.json")
    parser.add_argument("policy", choices=["default", "variant"], help="Which adjacency policy to use")
    args = parser.parse_args()

    config_path = args.config_path
    if not config_path.exists():
        print(f"config not found: {config_path}")
        return 2

    config = json.loads(config_path.read_text(encoding="utf-8"))
    policy_name = "3br_adjacency_policy.json" if args.policy == "default" else "3br_adjacency_policy_variant.json"
    policy_path = config_path.parent / "policies" / policy_name
    if not policy_path.exists():
        print(f"policy not found: {policy_path}")
        return 2

    config["policy_file"] = "policies/" + policy_name
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"switched {config_path} -> {policy_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
