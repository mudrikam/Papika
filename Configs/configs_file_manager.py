from pathlib import Path
import json


def load_config(base_path: Path):
    config_path = base_path / "Configs" / "papika_configs.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_env(base_path: Path):
    env_path = base_path / ".env"
    with open(env_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
    result = {}
    for line in lines:
        if "=" not in line:
            raise ValueError(f"Invalid .env line: {line}")
        key, val = line.split("=", 1)
        result[key.strip()] = val.strip()
    return result


def load_menu_config(base_path: Path):
    menu_path = base_path / "Configs" / "papika_menu_configs.json"
    with open(menu_path, "r", encoding="utf-8") as f:
        return json.load(f)

