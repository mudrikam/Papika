from pathlib import Path
from PySide6.QtWidgets import QApplication
from UI.setup_ui import apply_app_metadata, center_on_screen, apply_window_metadata
from UI.main_window import MainWindow
import sys

BASE_PATH = Path(__file__).resolve().parent


def main():
    app = QApplication(sys.argv)
    apply_app_metadata(app, base_path=BASE_PATH)
    win = MainWindow(base_path=BASE_PATH)
    apply_window_metadata(win, BASE_PATH)
    win.show()
    center_on_screen(win)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
