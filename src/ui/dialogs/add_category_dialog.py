from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QColorDialog, QComboBox, QLabel, 
    QFrame, QHBoxLayout, QListWidget, QListWidgetItem,
    QAbstractItemView, QWidget, QMessageBox
)
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtCore import Qt
from models.transaction import TransactionType

class AddCategoryDialog(QDialog):
    def __init__(self, service_instance, parent=None, edit_mode=False):
        super().__init__(parent)
        self.service = service_instance  
        self.edit_mode = edit_mode
        self.setWindowTitle("Edytuj Kategorię" if edit_mode else "Zarządzanie Kategoriami")
        self.setMinimumWidth(500)
        self.setMinimumHeight(650)
        
        self.color_hex = "#825fa2"
        self.cached_categories = []
        
        self.init_ui()
        
        self.refresh_data_cache()
        
        if not edit_mode:
            self.load_initial_data()

    def refresh_data_cache(self):
        try:
            self.cached_categories = self.service.get_categories_for_combo()
            print(f"DEBUG DIALOG: Loaded {len(self.cached_categories)} categories from Shared Service.")
        except Exception as e:
            print(f"ERROR DIALOG: {e}")
            self.cached_categories = []

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        header_layout = QVBoxLayout()
        title_text = "Edycja Kategorii" if self.edit_mode else "Konfiguracja Kategorii"
        self.title = QLabel(title_text)
        self.title.setStyleSheet("color: #825fa2; font-size: 20px; font-weight: bold; border: none;")
        self.subtitle = QLabel("Zdefiniuj typ, grupę oraz podkategorię.")
        self.subtitle.setStyleSheet("color: #888; font-size: 12px; border: none;")
        header_layout.addWidget(self.title)
        header_layout.addWidget(self.subtitle)
        layout.addLayout(header_layout)

        form_container = QFrame()
        form_container.setStyleSheet("background-color: #252526; border-radius: 10px; border: 1px solid #333;")
        form_layout = QFormLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in TransactionType])
        self.type_combo.setStyleSheet("""
            QComboBox { background-color: #1e1e1e; border: 1px solid #444; padding: 5px; color: white; }
            QComboBox QAbstractItemView { background-color: #1e1e1e; color: white; selection-background-color: #3d3d3d; }
        """)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)

        self.cat_combo = QComboBox()
        self.cat_combo.setEditable(True)
        self.cat_combo.setPlaceholderText("Wybierz lub wpisz kategorię główną")
        self.cat_combo.setStyleSheet("""
            QComboBox { 
                background-color: #1e1e1e; 
                border: 1px solid #444; 
                padding: 5px; 
                color: white; 
            }
            QComboBox:focus { 
                border: 1px solid #825fa2; 
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e1e;
                color: white;
                selection-background-color: #825fa2;
            }
        """)
        self.cat_combo.currentTextChanged.connect(self.update_subcategory_list)

        self.subcat_input = QLineEdit()
        self.subcat_input.setPlaceholderText("Nazwa podkategorii (np. Paliwo)")
        self.subcat_input.setStyleSheet("""
            QLineEdit { background-color: #1e1e1e; border: 1px solid #444; padding: 5px; color: white; }
            QLineEdit:focus { border: 1px solid #825fa2; }
        """)

        color_row = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet(f"background-color: {self.color_hex}; border-radius: 12px; border: 2px solid #444;")
        
        self.color_btn = QPushButton("Zmień kolor")
        self.color_btn.setFixedWidth(120)
        self.color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.color_btn.setStyleSheet("background-color: #333; color: #ddd; font-size: 11px; padding: 4px; border-radius: 4px;")
        self.color_btn.clicked.connect(self.pick_color)
        
        color_row.addWidget(self.color_preview)
        color_row.addWidget(self.color_btn)
        color_row.addStretch()

        form_layout.addRow("TYP TRANSAKCJI", self.type_combo)
        form_layout.addRow("GRUPA GŁÓWNA", self.cat_combo)
        form_layout.addRow("PODKATEGORIA", self.subcat_input)
        form_layout.addRow("KOLOR WIZUALNY", color_row)
        layout.addWidget(form_container)

        if not self.edit_mode:
            list_container = QVBoxLayout()
            list_label = QLabel("ISTNIEJĄCE PODKATEGORIE W TEJ GRUPIE")
            list_label.setStyleSheet("color: #825fa2; font-weight: bold; font-size: 11px; letter-spacing: 1px;")
            list_container.addWidget(list_label)

            self.subcat_list = QListWidget()
            self.subcat_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
            self.subcat_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.subcat_list.setStyleSheet("""
                QListWidget {
                    background-color: #1b1c1d;
                    border: 1px solid #333;
                    border-radius: 8px;
                    padding: 5px;
                    color: #e0e0e0;
                }
                QListWidget::item { background: transparent; border-bottom: 1px solid #252526; }
                QListWidget::item:last { border-bottom: none; }
            """)
            list_container.addWidget(self.subcat_list)
            layout.addLayout(list_container)

        button_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("background-color: transparent; color: #888; border: 1px solid #444; border-radius: 6px; padding: 8px;")

        self.save_btn = QPushButton("ZAPISZ" if self.edit_mode else "DODAJ")
        self.save_btn.setFixedHeight(45)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #825fa2;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 0 40px;
                border: none;
            }
            QPushButton:hover { background-color: #9374b3; }
        """)
        self.save_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

    def load_initial_data(self):
        current_type = self.type_combo.currentText()
        self.on_type_changed(current_type)

    def on_type_changed(self, type_text):
        self.cat_combo.blockSignals(True)
        self.cat_combo.clear()
        
        target_type = str(type_text).upper()
        
        try:
            matching_groups = sorted(list(set(
                c.category for c in self.cached_categories 
                if c.category and str(c.type).upper() == target_type
            )))
        except Exception:
            matching_groups = []
        
        self.cat_combo.addItems(matching_groups)
        self.cat_combo.setCurrentIndex(-1)
        self.cat_combo.blockSignals(False)
        
        if not self.edit_mode:
            self.subcat_list.clear()

    def update_subcategory_list(self, category_text):
        if self.edit_mode:
            return
            
        self.subcat_list.clear()
        if not category_text:
            return

        target_type = str(self.type_combo.currentText()).upper()
        target_cat = str(category_text).strip().upper()

        matching_subcats = [
            c for c in self.cached_categories 
            if c.category and str(c.type).upper() == target_type and str(c.category).strip().upper() == target_cat
        ]
        
        matching_subcats.sort(key=lambda x: x.subcategory)

        if matching_subcats:
            for sub in matching_subcats:
                item = QListWidgetItem(self.subcat_list)
                widget = self.create_subcat_widget(sub.subcategory, sub.color_hex, sub.subcategory_id)
                item.setSizeHint(widget.sizeHint())
                self.subcat_list.addItem(item)
                self.subcat_list.setItemWidget(item, widget)
        else:
            item = QListWidgetItem("Brak podkategorii. Dodaj nową.")
            item.setForeground(QColor("#666"))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.subcat_list.addItem(item)

    def create_subcat_widget(self, name, color_hex, subcat_id):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 5, 10, 5)

        c_val = color_hex if color_hex else "#825fa2"
        pix = QPixmap(10, 10)
        pix.fill(QColor(c_val))
        icon_lbl = QLabel()
        icon_lbl.setPixmap(pix)
        
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("color: #ccc; font-size: 12px; border: none;")
        
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(22, 22)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton { color: #666; background: transparent; border-radius: 11px; font-weight: bold; border: none; }
            QPushButton:hover { color: #ff8a80; background: #331d2c; }
        """)
        del_btn.clicked.connect(lambda checked, sid=subcat_id: self.handle_inline_delete(sid))

        layout.addWidget(icon_lbl)
        layout.addWidget(name_lbl)
        layout.addStretch()
        layout.addWidget(del_btn)
        return container

    def handle_inline_delete(self, subcat_id):
        reply = QMessageBox.question(self, "Usuń", "Usunąć tę podkategorię?", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.service.delete_category(subcat_id, cascade=False):
                self.refresh_data_cache()
                self.update_subcategory_list(self.cat_combo.currentText())
            else:
                QMessageBox.warning(self, "Błąd", "Nie można usunąć podkategorii (prawdopodobnie posiada przypisane transakcje).")

    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.color_hex), self, "Wybierz Kolor")
        if color.isValid():
            self.color_hex = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.color_hex}; border-radius: 12px; border: 2px solid #444;")

    def set_data(self, category_obj):
        self.type_combo.setCurrentText(category_obj.type)
        self.cat_combo.setCurrentText(category_obj.category)
        self.subcat_input.setText(category_obj.subcategory)
        self.color_hex = category_obj.color_hex or "#825fa2"
        self.color_preview.setStyleSheet(f"background-color: {self.color_hex}; border-radius: 12px; border: 2px solid #444;")

    def get_data(self):
        return {
            "type": self.type_combo.currentText(),
            "category": self.cat_combo.currentText().strip(),
            "subcategory": self.subcat_input.text().strip(),
            "color": self.color_hex
        }