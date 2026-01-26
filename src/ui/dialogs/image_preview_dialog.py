from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QScrollArea, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap

class ImagePreviewDialog(QDialog):
    def __init__(self, image_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Podgląd Załącznika")
        self.resize(800, 600)
        self.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        image = QImage()
        image.loadFromData(image_data)
        pixmap = QPixmap.fromImage(image)
        
        if pixmap.width() > 1200 or pixmap.height() > 1200:
            pixmap = pixmap.scaled(1200, 1200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
        self.label.setPixmap(pixmap)
        scroll.setWidget(self.label)
        layout.addWidget(scroll)
        
        btn_close = QPushButton("Zamknij")
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("""
            QPushButton { background-color: #333; color: white; border: 1px solid #555; padding: 8px; border-radius: 6px; }
            QPushButton:hover { background-color: #444; }
        """)
        layout.addWidget(btn_close)