from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPushButton, QInputDialog, QMessageBox, QLabel, 
                             QAbstractItemView, QFrame, QWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QCursor

class FolderManagerDialog(QDialog):
    def __init__(self, current_folders, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Menedżer Folderów")
        self.resize(480, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: #ffffff;
            }
            QLabel#Header {
                font-size: 18px;
                font-weight: bold;
                color: #e0e0e0;
                padding: 10px 0;
            }
            QLabel#SubHeader {
                font-size: 13px;
                color: #a0a0a0;
                margin-bottom: 10px;
            }
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 8px;
                outline: none;
                padding: 5px;
            }
            QListWidget::item {
                background-color: transparent;
                padding: 12px;
                margin: 2px 5px;
                border-radius: 6px;
                color: #e0e0e0;
                font-size: 14px;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
            }
            QListWidget::item:selected {
                background-color: #3d3d45;
                border: 1px solid #555555;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                color: #e0e0e0;
                padding: 12px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #505050;
            }
            QPushButton:pressed {
                background-color: #252525;
            }
            QPushButton#BtnPrimary {
                background-color: #2563eb;
                border: none;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#BtnPrimary:hover {
                background-color: #3b82f6;
            }
            QPushButton#BtnDanger {
                background-color: #2d2d2d;
                border: 1px solid #7f1d1d;
                color: #fca5a5;
            }
            QPushButton#BtnDanger:hover {
                background-color: #450a0a;
                border-color: #991b1b;
                color: #fecaca;
            }
            QPushButton#BtnAdd {
                background-color: #2d2d2d;
                border: 1px dashed #555;
                color: #aaa;
            }
            QPushButton#BtnAdd:hover {
                background-color: #333;
                color: #fff;
                border-style: solid;
            }
        """)
        
        self.selected_folder = None
        self.system_folders = ["Paragony", "Faktury", "Gwarancje", "Inne"]
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        
        header = QLabel("Wybierz Folder")
        header.setObjectName("Header")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(header)
        
        subheader = QLabel("Zaznacz folder docelowy lub utwórz nowy.")
        subheader.setObjectName("SubHeader")
        subheader.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(subheader)
        
        self.folder_list = QListWidget()
        self.folder_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.folder_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        
        for f in current_folders:
            self.folder_list.addItem(f"📁  {f}")
            
        self.folder_list.itemDoubleClicked.connect(self.confirm_selection)
        self.main_layout.addWidget(self.folder_list)
        
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(10)
        
        self.btn_add = QPushButton("＋  Nowy Folder")
        self.btn_add.setObjectName("BtnAdd")
        self.btn_add.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add.clicked.connect(self.add_folder)
        
        self.btn_del = QPushButton("Usuń")
        self.btn_del.setObjectName("BtnDanger")
        self.btn_del.setFixedWidth(80)
        self.btn_del.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_del.clicked.connect(self.delete_folder)
        
        mid_layout.addWidget(self.btn_add)
        mid_layout.addWidget(self.btn_del)
        self.main_layout.addLayout(mid_layout)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #333; border: none; max-height: 1px;")
        self.main_layout.addWidget(line)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)
        
        self.btn_cancel = QPushButton("Anuluj")
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_select = QPushButton("Wybierz Folder")
        self.btn_select.setObjectName("BtnPrimary")
        self.btn_select.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_select.setSizePolicy(self.btn_cancel.sizePolicy())
        self.btn_select.clicked.connect(self.confirm_selection)
        
        bottom_layout.addWidget(self.btn_cancel)
        bottom_layout.addWidget(self.btn_select)
        self.main_layout.addLayout(bottom_layout)

    def add_folder(self):
        text, ok = QInputDialog.getText(self, "Nowy Folder", "Nazwa folderu:")
        if ok and text:
            name = text.strip().replace("/", "").replace("\\", "")
            if not name:
                return
            
            clean_name = f"📁  {name}"
            
            existing_items = self.folder_list.findItems(clean_name, Qt.MatchFlag.MatchExactly)
            if existing_items:
                QMessageBox.warning(self, "Duplikat", f"Folder '{name}' już istnieje.")
                return
                
            self.folder_list.addItem(clean_name)
            self.folder_list.scrollToBottom()
            items = self.folder_list.findItems(clean_name, Qt.MatchFlag.MatchExactly)
            if items:
                self.folder_list.setCurrentItem(items[0])

    def delete_folder(self):
        row = self.folder_list.currentRow()
        if row < 0:
            return
            
        item = self.folder_list.currentItem()
        raw_text = item.text().replace("📁  ", "")
        
        if raw_text in self.system_folders:
            QMessageBox.warning(self, "Zablokowane", f"'{raw_text}' to folder systemowy.")
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Potwierdzenie")
        msg.setText(f"Usunąć '{raw_text}' z listy?")
        msg.setStyleSheet("background-color: #222; color: #fff;")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.folder_list.takeItem(row)

    def confirm_selection(self):
        current = self.folder_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Błąd", "Nie wybrano folderu.")
            return
            
        self.selected_folder = current.text().replace("📁  ", "")
        self.accept()

    def get_folder(self):
        return self.selected_folder