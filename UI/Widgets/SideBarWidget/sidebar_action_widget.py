from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
import qtawesome as qta

class SidebarActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        label = QLabel('Step 1 Generate Embedding')
        label.setAlignment(Qt.AlignLeft)
        layout.addWidget(label)
        generate_embedding_button = QPushButton('Generate Embedding', self)
        generate_embedding_button.setObjectName('generate_embedding_button')
        generate_embedding_button.setIcon(qta.icon('fa6s.wand-magic-sparkles'))
        generate_embedding_button.setCursor(Qt.PointingHandCursor)
        generate_embedding_button.setFixedHeight(36)
        layout.addWidget(generate_embedding_button)

        label2 = QLabel('Step 2 Generate Image Caption')
        label2.setAlignment(Qt.AlignLeft)
        layout.addWidget(label2)
        generate_caption_button = QPushButton('Generate Caption', self)
        generate_caption_button.setObjectName('generate_caption_button')
        generate_caption_button.setIcon(qta.icon('fa6s.image'))
        generate_caption_button.setCursor(Qt.PointingHandCursor)
        generate_caption_button.setFixedHeight(36)
        layout.addWidget(generate_caption_button)

        label3 = QLabel('Step 3 Generate Image Hash')
        label3.setAlignment(Qt.AlignLeft)
        layout.addWidget(label3)
        generate_hash_button = QPushButton('Generate Image Hash', self)
        generate_hash_button.setObjectName('generate_hash_button')
        generate_hash_button.setIcon(qta.icon('fa6s.hashtag'))
        generate_hash_button.setCursor(Qt.PointingHandCursor)
        generate_hash_button.setFixedHeight(36)
        layout.addWidget(generate_hash_button)
        layout.addStretch()
