from pathlib import Path
from PySide6.QtGui import QIcon, QPixmap

ICON_DIRS = ["Icons", "Mascot", "Illustrations"]


def get_icon(name: str, base_path: Path) -> QIcon:
    for d in ICON_DIRS:
        p = base_path / "UI" / "Assets" / d / name
        if p.exists():
            icon = QIcon(str(p))
            if icon.isNull():
                raise ValueError(f"Failed to load icon: {p}")
            return icon
    raise FileNotFoundError(f"Icon not found in assets: {name}")


def get_pixmap(name: str, base_path: Path) -> QPixmap:
    for d in ICON_DIRS:
        p = base_path / "UI" / "Assets" / d / name
        if p.exists():
            pix = QPixmap(str(p))
            if pix.isNull():
                raise ValueError(f"Failed to load image: {p}")
            return pix
    raise FileNotFoundError(f"Image not found in assets: {name}")
