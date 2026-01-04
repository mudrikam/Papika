from pathlib import Path
import sys
from PySide6.QtWidgets import QSplashScreen, QApplication
from PySide6.QtCore import Qt, QTimer, QRect, Signal
from PySide6.QtGui import QPixmap, QFont, QPainter, QColor, QPen, QFontMetrics
from Configs.configs_file_manager import load_config
from UI.Assets.assets_manager import get_splash_pixmap


class SplashScreen(QSplashScreen):
    status_changed = Signal(str)
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.cfg = load_config(base_path)
        self.current_status = "Initializing..."
        pixmap = self._create_pixmap()
        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        self.status_changed.connect(self.update_status)

    def _create_pixmap(self) -> QPixmap:
        margin = 20

        pix = get_splash_pixmap(self.base_path)
        img_w = pix.width()
        img_h = pix.height()

        panel_width = 400
        overlap_at = img_w // 2
        
        total_width = margin + overlap_at + panel_width + margin
        total_height = img_h + (margin * 2)

        pixmap = QPixmap(total_width, total_height)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        text_color = self.cfg["splash"]["text_color"]
        painter.setPen(QColor(text_color))

        name = self.cfg["name"]
        version = self.cfg["version"]
        status = self.cfg.get("status", "")
        tagline = self.cfg.get("tagline", "")
        description = self.cfg.get("description", "")
        developer = self.cfg.get("developer", "")
        license_text = self.cfg.get("license", "")

        panel_x = margin + overlap_at
        panel_rect = QRect(panel_x, margin, panel_width, img_h)
        panel_color = self.cfg["splash"]["panel_color"]
        panel_radius = self.cfg["splash"]["panel_radius"]
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(panel_color))
        painter.drawRoundedRect(panel_rect, panel_radius, panel_radius)
        # stroke with text color
        pen = QPen(QColor(text_color))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(panel_rect, panel_radius, panel_radius)
        # restore text pen
        painter.setPen(QColor(text_color))

        img_x = margin
        img_y = margin
        painter.drawPixmap(img_x, img_y, pix)

        text_x = panel_x + 20
        y = margin + 20
        line_spacing = 28
        text_width = panel_width - 40

        # platform-specific font family for all labels
        if sys.platform == "win32":
            font_family = "Comic Sans MS"
        elif sys.platform == "darwin":
            font_family = "Marker Felt"
        else:
            font_family = "DejaVu Sans"

        title_font = QFont(font_family, 20)
        title_font.setBold(True)
        painter.setFont(title_font)
        title_metrics = QFontMetrics(title_font)
        title_h = title_metrics.height()
        painter.drawText(QRect(text_x, y, text_width, title_h), Qt.AlignLeft | Qt.AlignVCenter, f"{name} {version} ({status})" if status else f"{name} {version}")
        y += title_h + 8

        tag_font = QFont(font_family, 12)
        painter.setFont(tag_font)
        tag_metrics = QFontMetrics(tag_font)
        tag_h = tag_metrics.height()
        painter.drawText(QRect(text_x, y, text_width, tag_h), Qt.AlignLeft | Qt.AlignVCenter, tagline)
        y += tag_h + 8

        desc_font = QFont(font_family, 10)
        painter.setFont(desc_font)
        desc_metrics = QFontMetrics(desc_font)
        desc_line_h = desc_metrics.lineSpacing()
        desc_lines = 4
        desc_h = desc_line_h * desc_lines
        painter.drawText(QRect(text_x, y, text_width, desc_h), Qt.TextWordWrap | Qt.AlignJustify, description)
        y += desc_h + 16
        
        status_font = QFont(font_family, 11)
        status_font.setBold(True)
        painter.setFont(status_font)
        status_metrics = QFontMetrics(status_font)
        status_h = status_metrics.height()
        self.status_rect = QRect(text_x, y, text_width, status_h)
        painter.drawText(self.status_rect, Qt.AlignLeft | Qt.AlignVCenter, self.current_status)
        y += status_h + 16

        meta_font = QFont(font_family, 10)
        meta_font.setItalic(True)
        painter.setFont(meta_font)
        painter.drawText(QRect(text_x, y, text_width, line_spacing), Qt.AlignRight | Qt.AlignVCenter, f"Developer: {developer}")
        y += line_spacing
        painter.drawText(QRect(text_x, y, text_width, line_spacing), Qt.AlignRight | Qt.AlignVCenter, f"License: {license_text}")

        painter.end()
        return pixmap
    
    def update_status(self, status_text):
        self.current_status = status_text
        pixmap = self._create_pixmap()
        self.setPixmap(pixmap)
        QApplication.processEvents()


def show_splash(base_path: Path, delay_ms: int = 2000):
    splash = SplashScreen(base_path)
    splash.show()
    splash.update_status("Scanning drives on system...")
    QApplication.processEvents()
    screen = splash.screen() or QApplication.primaryScreen()
    available = screen.availableGeometry()
    frame = splash.frameGeometry()
    frame.moveCenter(available.center())
    splash.move(frame.topLeft())
    return splash
