import tempfile
import os
import subprocess
import platform
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QLabel, QPushButton, QSplitter, QMessageBox, QListWidgetItem)
from PyQt6.QtCore import Qt
from ui.dialogs.image_preview_dialog import ImagePreviewDialog

class AttachmentBrowserDialog(QDialog):
    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("Przeglądarka Załączników")
        self.resize(900, 600)
        
        self.layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Odśwież")
        self.refresh_btn.clicked.connect(self.load_folders)
        
        top_layout.addWidget(QLabel("STREFA PLIKÓW"))
        top_layout.addStretch()
        top_layout.addWidget(self.refresh_btn)
        self.layout.addLayout(top_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.folder_list = QListWidget()
        self.folder_list.itemClicked.connect(self.on_folder_clicked)
        
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        
        splitter.addWidget(self.folder_list)
        splitter.addWidget(self.file_list)
        splitter.setSizes([250, 650])
        
        self.layout.addWidget(splitter)
        
        self.info_lbl = QLabel("")
        self.layout.addWidget(self.info_lbl)

        self.load_folders()

    def load_folders(self):
        self.folder_list.clear()
        self.file_list.clear()
        folders = self.service.get_storage_folders()
        for f in folders:
            item = QListWidgetItem(f"📁 {f}")
            item.setData(Qt.ItemDataRole.UserRole, f)
            self.folder_list.addItem(item)

    def on_folder_clicked(self, item):
        folder_name = item.data(Qt.ItemDataRole.UserRole)
        self.file_list.clear()
        self.info_lbl.setText(f"Ładowanie: {folder_name}...")
        
        files = self.service.get_files_in_folder(folder_name)
        
        if not files:
            self.info_lbl.setText(f"Folder '{folder_name}' jest pusty.")
            return

        self.info_lbl.setText(f"Pliki: {len(files)}")
        
        for f in files:
            name = f.get('name', '???')
            size_kb = f.get('metadata', {}).get('size', 0) / 1024
            full_path = f.get('full_path')
            
            display_text = f"📄 {name} ({size_kb:.1f} KB)"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, full_path)
            self.file_list.addItem(item)

    def on_file_double_clicked(self, item):
        full_path = item.data(Qt.ItemDataRole.UserRole)
        content = self.service.download_attachment_content(full_path)
        if not content:
            return
            
        ext = full_path.split('.')[-1].lower()
        if ext in ['jpg', 'jpeg', 'png', 'bmp', 'gif']:
            preview = ImagePreviewDialog(content, self)
            preview.exec()
        else:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                
                if platform.system() == 'Darwin':
                    subprocess.call(('open', tmp_path))
                elif platform.system() == 'Windows':
                    os.startfile(tmp_path)
                else:
                    subprocess.call(('xdg-open', tmp_path))
            except Exception:
                pass