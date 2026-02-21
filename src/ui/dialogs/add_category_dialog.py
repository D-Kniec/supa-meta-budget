from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QColorDialog, QComboBox, QLabel, 
    QFrame, QHBoxLayout, QListWidget, QListWidgetItem,
    QAbstractItemView, QWidget, QMessageBox
)
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtCore import Qt, pyqtSlot
from models.transaction import TransactionType
from ui.styles import (
    COMBOBOX_STYLE, FRAME_CARD_STYLE, LIST_WIDGET_STYLE,
    BTN_STANDARD_STYLE, SEARCH_INPUT_STYLE, LBL_TITLE_STYLE,
    LBL_SUBTITLE_STYLE, BTN_PRIMARY_STYLE, BTN_INLINE_DELETE,
    BTN_DISABLED_STYLE
)

class AddCategoryDialog(QDialog):
    def __init__(self, service_instance, parent: Optional[QWidget] = None, edit_mode: bool = False):
        super().__init__(parent)
        self.service = service_instance  
        self.edit_mode = edit_mode
        self.setWindowTitle("Edytuj Kategorię" if edit_mode else "Zarządzanie Kategoriami")
        self.setMinimumWidth(500)
        self.setMinimumHeight(650)
        
        self.color_hex: str = "#825fa2"
        self.cached_categories: List[Any] = []
        
        self.init_ui()
        self.refresh_data_cache()
        
        if not edit_mode:
            self.load_initial_data()
            
        self.validate_form()

    def refresh_data_cache(self):
        try:
            self.cached_categories = self.service.get_categories_for_combo()
        except Exception as e:
            print(f"Error loading categories: {e}")
            self.cached_categories = []

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        layout.addLayout(self._setup_header())

        self.form_container = self._setup_form_container()
        layout.addWidget(self.form_container)

        if not self.edit_mode:
            self.list_container = self._setup_existing_list()
            layout.addLayout(self.list_container)

        layout.addLayout(self._setup_buttons())

    def _setup_header(self) -> QVBoxLayout:
        header_layout = QVBoxLayout()
        
        title_text = "Edycja Kategorii" if self.edit_mode else "Konfiguracja Kategorii"
        self.title = QLabel(title_text)
        self.title.setStyleSheet(LBL_TITLE_STYLE + "color: #825fa2;")
        
        self.subtitle = QLabel("Zdefiniuj typ, grupę oraz podkategorię.")
        self.subtitle.setStyleSheet(LBL_SUBTITLE_STYLE)
        
        header_layout.addWidget(self.title)
        header_layout.addWidget(self.subtitle)
        return header_layout

    def _setup_form_container(self) -> QFrame:
        container = QFrame()
        container.setStyleSheet(FRAME_CARD_STYLE)
        
        form_layout = QFormLayout(container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in TransactionType])
        self.type_combo.setStyleSheet(COMBOBOX_STYLE)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)

        self.cat_combo = QComboBox()
        self.cat_combo.setEditable(True)
        self.cat_combo.setPlaceholderText("Wybierz lub wpisz kategorię główną")
        self.cat_combo.setStyleSheet(COMBOBOX_STYLE)
        self.cat_combo.editTextChanged.connect(self.validate_form)
        self.cat_combo.currentTextChanged.connect(self.update_subcategory_list)

        self.subcat_input = QLineEdit()
        self.subcat_input.setPlaceholderText("Nazwa podkategorii (np. Paliwo)")
        self.subcat_input.setStyleSheet(SEARCH_INPUT_STYLE)
        self.subcat_input.textChanged.connect(self.validate_form)
        self.subcat_input.returnPressed.connect(self.attempt_submit)

        color_row_layout = self._create_color_picker_row()

        form_layout.addRow(self._create_label("TYP TRANSAKCJI"), self.type_combo)
        form_layout.addRow(self._create_label("GRUPA GŁÓWNA"), self.cat_combo)
        form_layout.addRow(self._create_label("PODKATEGORIA"), self.subcat_input)
        form_layout.addRow(self._create_label("KOLOR WIZUALNY"), color_row_layout)

        return container

    def _create_color_picker_row(self) -> QHBoxLayout:
        row_layout = QHBoxLayout()
        
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet(
            f"background-color: {self.color_hex}; border-radius: 12px; border: 2px solid #444;"
        )
        
        self.color_btn = QPushButton("Zmień kolor")
        self.color_btn.setFixedWidth(120)
        self.color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.color_btn.setStyleSheet(BTN_STANDARD_STYLE)
        self.color_btn.clicked.connect(self.pick_color)
        
        row_layout.addWidget(self.color_preview)
        row_layout.addWidget(self.color_btn)
        row_layout.addStretch()
        
        return row_layout

    def _setup_existing_list(self) -> QVBoxLayout:
        list_container = QVBoxLayout()
        list_label = QLabel("ISTNIEJĄCE PODKATEGORIE W TEJ GRUPIE")
        list_label.setStyleSheet("color: #825fa2; font-weight: bold; font-size: 11px; letter-spacing: 1px;")
        list_container.addWidget(list_label)

        self.subcat_list = QListWidget()
        self.subcat_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.subcat_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.subcat_list.setStyleSheet(LIST_WIDGET_STYLE)
        
        list_container.addWidget(self.subcat_list)
        return list_container

    def _setup_buttons(self) -> QHBoxLayout:
        button_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet(BTN_STANDARD_STYLE)

        self.save_btn = QPushButton("ZAPISZ" if self.edit_mode else "DODAJ")
        self.save_btn.setFixedHeight(45)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet(BTN_PRIMARY_STYLE)
        self.save_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        return button_layout

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("color: #888; font-weight: bold; font-size: 11px; margin-top: 4px;")
        return label

    @pyqtSlot()
    def validate_form(self):
        cat_text = self.cat_combo.currentText().strip()
        sub_text = self.subcat_input.text().strip()
        
        is_valid = bool(cat_text) and bool(sub_text)
        
        self.save_btn.setEnabled(is_valid)
        if is_valid:
            self.save_btn.setStyleSheet(BTN_PRIMARY_STYLE)
            self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.save_btn.setStyleSheet(BTN_DISABLED_STYLE)
            self.save_btn.setCursor(Qt.CursorShape.ArrowCursor)

    @pyqtSlot()
    def attempt_submit(self):
        if self.save_btn.isEnabled():
            self.accept()

    def load_initial_data(self):
        current_type = self.type_combo.currentText()
        self.on_type_changed(current_type)

    @pyqtSlot(str)
    def on_type_changed(self, type_text: str):
        self.cat_combo.blockSignals(True)
        self.cat_combo.clear()
        
        if not type_text:
            self.cat_combo.blockSignals(False)
            self.validate_form()
            return

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
        self.validate_form()
        
        if not self.edit_mode:
            self.subcat_list.clear()

    @pyqtSlot(str)
    def update_subcategory_list(self, category_text: str):
        self.validate_form()
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

    def create_subcat_widget(self, name: str, color_hex: str, subcat_id: int) -> QWidget:
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
        del_btn.setStyleSheet(BTN_INLINE_DELETE)
        del_btn.clicked.connect(lambda checked, sid=subcat_id: self.handle_inline_delete(sid))

        layout.addWidget(icon_lbl)
        layout.addWidget(name_lbl)
        layout.addStretch()
        layout.addWidget(del_btn)
        return container

    def handle_inline_delete(self, subcat_id: int):
        reply = QMessageBox.question(self, "Usuń", "Usunąć tę podkategorię?", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.service.delete_category(subcat_id, cascade=False):
                self.refresh_data_cache()
                self.update_subcategory_list(self.cat_combo.currentText())
            else:
                QMessageBox.warning(self, "Błąd", "Nie można usunąć podkategorii.")

    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.color_hex), self, "Wybierz Kolor")
        if color.isValid():
            self.color_hex = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.color_hex}; border-radius: 12px; border: 2px solid #444;")

    @property
    def category_data(self) -> Dict[str, str]:
        """Zwraca dane formularza jako słownik."""
        return {
            "type": self.type_combo.currentText(),
            "category": self.cat_combo.currentText().strip(),
            "subcategory": self.subcat_input.text().strip(),
            "color": self.color_hex
        }

    def set_data(self, category_obj: Any):
        self.type_combo.blockSignals(True)
        self.cat_combo.blockSignals(True)

        self.type_combo.setCurrentText(category_obj.type)
        self.on_type_changed(category_obj.type)
        
        self.cat_combo.setCurrentText(category_obj.category)
        self.subcat_input.setText(category_obj.subcategory)
        self.color_hex = category_obj.color_hex or "#825fa2"
        self.color_preview.setStyleSheet(f"background-color: {self.color_hex}; border-radius: 12px; border: 2px solid #444;")
        
        self.validate_form()

        self.type_combo.blockSignals(False)
        self.cat_combo.blockSignals(False)