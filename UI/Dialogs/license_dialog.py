from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QWidget
from Configs.configs_file_manager import load_config


def show_license(parent: QWidget, base_path: Path):
    cfg = load_config(base_path)
    license_name = cfg.get("license", "")
    license_file = base_path / "LICENSE"
    if license_file.exists():
        with open(license_file, "r", encoding="utf-8") as f:
            text = f.read()
        title = f"{license_name} License"
        QMessageBox.information(parent, title, text)
    else:
        QMessageBox.information(parent, "License", f"License: {license_name}")