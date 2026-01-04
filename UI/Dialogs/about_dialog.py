from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QWidget
from Configs.configs_file_manager import load_config


def show_about(parent: QWidget, base_path: Path):
    cfg = load_config(base_path)
    title = f"About {cfg['name']}"
    name = cfg['name']
    version = cfg['version']
    status = cfg.get("status")
    name_version = f"<b>{name} {version}</b>"
    if status:
        name_version = f"{name_version} ({status})"
    developer = cfg.get("developer", "")
    description = cfg.get('description', '')
    license_text = cfg.get('license', '')
    text = (
        f"<p>{name_version}</p>"
        f"<p>{description}</p>"
        f"<p><b>Developer:</b> <b>{developer}</b></p>"
        f"<p><b>License:</b> <b>{license_text}</b></p>"
    )
    QMessageBox.about(parent, title, text)
