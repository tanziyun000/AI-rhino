import json
from pathlib import Path


class ConfigError(ValueError):
    pass


def load_config(path_or_text):
    """Load config from a JSON string or file path."""
    text = None
    base_dir = None
    if isinstance(path_or_text, (str, Path)):
        candidate = Path(path_or_text)
        if candidate.exists():
            text = candidate.read_text(encoding="utf-8")
            base_dir = candidate.parent
    if text is None:
        if isinstance(path_or_text, str):
            text = path_or_text
        else:
            raise ConfigError("load_config expects a JSON string, Path, or existing file path")
    config = json.loads(text)
    policy_file = config.get("policy_file")
    if policy_file:
        policy_path = Path(policy_file)
        if not policy_path.is_absolute():
            policy_path = (base_dir / policy_path) if base_dir else policy_path
        if not policy_path.exists():
            raise ConfigError(f"policy_file not found: {policy_file}")
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        if not isinstance(policy, dict):
            raise ConfigError(f"policy_file must be a JSON object: {policy_file}")
        if "preferred_adjacency" in policy:
            config.setdefault("constraints", {})["preferred_adjacency"] = policy["preferred_adjacency"]
        if "disallowed_adjacency" in policy:
            config.setdefault("constraints", {})["disallowed_adjacency"] = policy["disallowed_adjacency"]
    return config


def get_program(config):
    return list(config["program"])


def required_program(config):
    return [item for item in config["program"] if item.get("required", False)]


def _validate_adjacency_policy(config):
    room_names = {item["name"] for item in config["program"]}
    constraints = config.get("constraints", {})
    for key in ("preferred_adjacency", "disallowed_adjacency"):
        entries = constraints.get(key, [])
        if entries is None:
            continue
        if not isinstance(entries, list):
            raise ConfigError(f"constraints.{key} must be a list")
        for entry in entries:
            if isinstance(entry, dict):
                if "pair" not in entry and "rooms" not in entry:
                    raise ConfigError(f"constraints.{key} dict entries need 'pair' or 'rooms': {entry}")
                pair = entry.get("pair", entry.get("rooms"))
                if not isinstance(pair, list) or len(pair) != 2:
                    raise ConfigError(f"constraints.{key} dict entries need a two-room pair: {entry}")
            elif isinstance(entry, list):
                if len(entry) < 2 or len(entry) > 3:
                    raise ConfigError(f"constraints.{key} entries must be [room_a, room_b] or [room_a, room_b, severity]: {entry}")
                pair = entry[:2]
            else:
                raise ConfigError(f"constraints.{key} entries must be lists or objects: {entry}")

            for name in pair:
                if name not in room_names:
                    raise ConfigError(f"constraints.{key} references unknown room: {name}")

            if isinstance(entry, list) and len(entry) == 3:
                severity = str(entry[2]).lower()
                if severity not in ("soft", "hard"):
                    raise ConfigError(f"constraints.{key} severity must be 'soft' or 'hard': {entry}")
            if isinstance(entry, dict) and "severity" in entry:
                severity = str(entry["severity"]).lower()
                if severity not in ("soft", "hard"):
                    raise ConfigError(f"constraints.{key} severity must be 'soft' or 'hard': {entry}")
    return True


def validate_config(config):
    required_top = ["project_name", "unit_type", "boundary", "building", "program", "constraints"]
    missing = [key for key in required_top if key not in config]
    if missing:
        raise ConfigError(f"missing top-level keys: {missing}")
    if not config["program"]:
        raise ConfigError("program must contain at least one room")
    for item in config["program"]:
        for key in ["name", "target_area", "required"]:
            if key not in item:
                raise ConfigError(f"program item missing {key}: {item}")
        if float(item["target_area"]) <= 0:
            raise ConfigError(f"target_area must be positive: {item['name']}")
    boundary = config["boundary"]
    for key in ["x", "y", "width", "depth"]:
        if key not in boundary:
            raise ConfigError(f"boundary missing {key}")
        if float(boundary[key]) < 0 and key != "width" and key != "depth":
            raise ConfigError(f"boundary {key} must be >= 0")
    if float(boundary["width"]) <= 0 or float(boundary["depth"]) <= 0:
        raise ConfigError("boundary width and depth must be positive")
    constraints = config["constraints"]
    for key in ["max_aspect_ratio", "max_corridor_width", "min_corridor_width"]:
        if key not in constraints:
            raise ConfigError(f"constraints missing {key}")
    _validate_adjacency_policy(config)
    return True


def summarize_config(config):
    total = sum(float(item["target_area"]) for item in config["program"])
    b = config["boundary"]
    return {
        "project_name": config["project_name"],
        "unit_type": config["unit_type"],
        "boundary_area": round(float(b["width"]) * float(b["depth"]), 2),
        "program_total_area": round(total, 2),
        "room_count": len(config["program"]),
        "required_count": len(required_program(config)),
    }
