from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSizePolicy, QFrame
)
from PyQt6.QtWebEngineWidgets import QWebEngineView 
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QDesktopServices

class AnalyticsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.dashboard_url = "http://localhost:3000"
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        top_bar_frame = QFrame()
        top_bar_frame.setStyleSheet("background-color: #252526; border-bottom: 1px solid #333;")
        top_bar_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        top_bar_layout = QHBoxLayout(top_bar_frame)
        top_bar_layout.setContentsMargins(15, 10, 20, 10)
        top_bar_layout.setSpacing(12)

        btn_style = """
            QPushButton { 
                background-color: #333333; 
                color: #ddd; 
                border: 1px solid #444; 
                border-radius: 6px; 
                font-weight: bold;
                font-size: 13px;
                padding: 6px 16px;
                min-height: 24px;
            }
            QPushButton:hover { background-color: #444; color: white; border-color: #555; }
            QPushButton:pressed { background-color: #222; }
        """

        self.back_btn = QPushButton("🡠")
        self.back_btn.setFixedWidth(50) 
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet(btn_style)
        self.back_btn.clicked.connect(self.go_back)

        self.forward_btn = QPushButton("🡢")
        self.forward_btn.setFixedWidth(50)
        self.forward_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forward_btn.setStyleSheet(btn_style)
        self.forward_btn.clicked.connect(self.go_forward)

        self.home_btn = QPushButton("🏠")
        self.home_btn.setFixedWidth(50)
        self.home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.home_btn.setStyleSheet(btn_style)
        self.home_btn.clicked.connect(self.go_home)

        self.refresh_btn = QPushButton("↻ Odśwież")
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet(btn_style)
        self.refresh_btn.clicked.connect(self.reload_page)

        self.open_ext_btn = QPushButton("↗ Otwórz w przeglądarce")
        self.open_ext_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_ext_btn.setStyleSheet(btn_style)
        self.open_ext_btn.clicked.connect(self.open_external)

        top_bar_layout.addWidget(self.back_btn)
        top_bar_layout.addWidget(self.forward_btn)
        top_bar_layout.addWidget(self.home_btn)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.refresh_btn)
        top_bar_layout.addWidget(self.open_ext_btn)
        
        self.layout.addWidget(top_bar_frame, 0)

        self.browser = QWebEngineView()
        self.browser.setStyleSheet("background-color: #1e1e1e;")
        self.browser.setUrl(QUrl(self.dashboard_url))
        
        self.layout.addWidget(self.browser, 1)

    def reload_page(self):
        self.browser.reload()

    def go_back(self):
        self.browser.back()

    def go_forward(self):
        self.browser.forward()

    def go_home(self):
        self.browser.setUrl(QUrl(self.dashboard_url))

    def open_external(self):
        QDesktopServices.openUrl(self.browser.url())