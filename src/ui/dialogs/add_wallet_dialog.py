from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt

class AddWalletDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dodaj Portfel")
        self.setFixedSize(350, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        self.setStyleSheet("""
            QDialog { background-color: #252526; color: white; }
            QLabel { font-weight: bold; color: #ccc; }
            QLineEdit { 
                background-color: #1e1e1e; border: 1px solid #444; 
                padding: 8px; border-radius: 6px; color: white; 
            }
            QLineEdit:focus { border: 1px solid #825fa2; }
        """)

        layout.addWidget(QLabel("NAZWA PORTFELA"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("np. PKO, Gotówka, Revolut")
        layout.addWidget(self.name_input)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Anuluj")
        btn_cancel.setStyleSheet("background-color: transparent; color: #888; border: 1px solid #444; border-radius: 6px; padding: 6px;")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("ZAPISZ")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { background-color: #825fa2; color: white; font-weight: bold; border-radius: 6px; padding: 8px; border: none; }
            QPushButton:hover { background-color: #9a72bd; }
        """)
        btn_save.clicked.connect(self.validate_and_accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def validate_and_accept(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa portfela nie może być pusta.")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_input.text().strip()
        }