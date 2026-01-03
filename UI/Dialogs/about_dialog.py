from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QWidget
from Configs.configs_file_manager import load_config


def show_about(parent: QWidget, base_path: Path):
    cfg = load_config(base_path)
    title = f"About {cfg['name']}"
    name_version = f"{cfg['name']} {cfg['version']}"
    status = cfg.get("status")
    if status:
        name_version = f"{name_version} ({status})"
    developer = cfg.get("developer", "")
    description = cfg.get('description', '')
    license_text = cfg.get('license', '')
    text = f"{name_version}\n\n{description}\n\nDeveloper: {developer}\n\nLicense: {license_text}"
    QMessageBox.about(parent, title, text)
