import tempfile
import os
import json
import subprocess
import platform
from datetime import datetime, timedelta
from enum import IntEnum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QFrame, QLabel, 
    QGridLayout, QDoubleSpinBox, QLineEdit, QFileDialog, QMenu,
    QApplication, QInputDialog, QDialog, QDateEdit, QComboBox, QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QFont

from services.budget_service import BudgetService
from models.transaction import TransactionType, TransactionStatus, TransactionSentiment
from core.config import BASE_DIR

from ui.delegates.budget_delegates import (
    StatusBadgeDelegate, BooleanIconDelegate, AmountDelegate, 
    ComboBoxDelegate, TagDelegate, FilteredCategoryDelegate, 
    SubcategoryDelegate, DateDelegate
)
from ui.dialogs.image_preview_dialog import ImagePreviewDialog
from ui.dialogs.recurring_transaction_dialog import RecurringTransactionDialog
from ui.styles import (
    SEARCH_INPUT_STYLE, BTN_STANDARD_STYLE, BTN_PENDING_STYLE, 
    BTN_RECURRING_STYLE, TABLE_STYLE, ENTRY_FRAME_STYLE, 
    COMBOBOX_STYLE, BTN_ATTACH_STYLE, BTN_ATTACH_ACTIVE_STYLE, 
    BTN_ADD_ROW_STYLE, INFO_LABEL_STYLE,
    BTN_ADD_EXPENSE, BTN_ADD_INCOME, BTN_ADD_TRANSFER
)

USER_PREFS_FILE = os.path.join(BASE_DIR, "user_prefs.json")

class DataLoaderWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, service):
        super().__init__()
        self.service = service

    def run(self):
        try:
            self.service.reload_cache()
            data = self.service.get_ui_transactions()
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))

class BudgetColumn(IntEnum):
    TYPE = 0
    STATUS = 1
    DATE = 2
    AMOUNT = 3
    AUTHOR = 4
    CATEGORY = 5
    SUBCATEGORY = 6
    WALLET_FROM = 7
    WALLET_TO = 8
    SENTIMENT = 9
    TAG = 10
    DESCRIPTION = 11
    IN_STATS = 12
    ATTACHMENT = 13

class BudgetTab(QWidget):
    def __init__(self):
        super().__init__()
        self.service = BudgetService()
        self.current_attachment = None
        self.current_attachment_folder = "transactions"
        
        self.available_folders = ["Paragony", "Faktury", "Gwarancje", "Inne"]
        
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.handle_full_refresh()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(25, 25, 25, 25)

        self._setup_toolbar()
        self._setup_table()
        self._setup_entry_form()

    def _setup_toolbar(self):
        self.toolbar = QHBoxLayout()
        self.toolbar.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Szukaj...")
        self.search_input.setFixedWidth(280)
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet(SEARCH_INPUT_STYLE)
        
        self.hide_pending_btn = QPushButton("⏳")
        self.hide_pending_btn.setCheckable(True)
        self.hide_pending_btn.setChecked(True)
        self.hide_pending_btn.setFixedSize(46, 36)
        self.hide_pending_btn.setToolTip("Ukryj oczekujące (PENDING)")
        self.hide_pending_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hide_pending_btn.setStyleSheet(BTN_PENDING_STYLE)

        self.gen_recurring_btn = QPushButton("♻️")
        self.gen_recurring_btn.setFixedSize(46, 36)
        self.gen_recurring_btn.setToolTip("Generuj cykliczne wpisy")
        self.gen_recurring_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_recurring_btn.setStyleSheet(BTN_RECURRING_STYLE)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet(INFO_LABEL_STYLE)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.user_filter_combo = QComboBox()
        self.user_filter_combo.setFixedWidth(150)
        self.user_filter_combo.setFixedHeight(36)
        self.user_filter_combo.setStyleSheet(COMBOBOX_STYLE)
        self.user_filter_combo.addItem("Wszyscy", None)

        self.session_label = QLabel("Zalogowany: -")
        self.session_label.setStyleSheet("color: #666; font-size: 10px; font-weight: bold; margin-right: 5px;")
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.refresh_btn = QPushButton("↻ Odśwież")
        self.refresh_btn.setFixedSize(100, 36)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet(BTN_STANDARD_STYLE)
        
        self.toolbar.addWidget(self.search_input)
        self.toolbar.addWidget(self.hide_pending_btn)
        self.toolbar.addWidget(self.gen_recurring_btn)
        self.toolbar.addWidget(self.info_label)
        self.toolbar.addStretch()
        self.toolbar.addWidget(self.session_label)
        self.toolbar.addWidget(self.user_filter_combo)
        self.toolbar.addWidget(self.refresh_btn)
        
        self.main_layout.addLayout(self.toolbar)

        self.search_input.textChanged.connect(self.filter_table)
        self.hide_pending_btn.clicked.connect(self.filter_table)
        
        self.user_filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        
        self.gen_recurring_btn.clicked.connect(self.handle_generate_recurring)
        self.refresh_btn.clicked.connect(self.handle_full_refresh)

    def _setup_table(self):
        self.table = QTableWidget()
        self.headers = [
            "  Typ", "  Status", "  Data", "  Wartość", "  Autor", "  Kategoria", "  Podkategoria", 
            "  Z Portfela", "  Do Portfela", "  Sentyment", "  Tag", "  Opis", "  Wliczony", "  Plik"
        ]
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setStyleSheet(TABLE_STYLE)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h.setSectionResizeMode(BudgetColumn.DESCRIPTION, QHeaderView.ResizeMode.Stretch)
        h.setMinimumSectionSize(30)
        h.setDefaultSectionSize(100)
        h.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        h.customContextMenuRequested.connect(self.show_header_menu)
        
        self.table.setColumnWidth(BudgetColumn.TYPE, 100)
        self.table.setColumnWidth(BudgetColumn.STATUS, 110)
        self.table.setColumnWidth(BudgetColumn.DATE, 90)
        self.table.setColumnWidth(BudgetColumn.AMOUNT, 100)
        self.table.setColumnWidth(BudgetColumn.SUBCATEGORY, 170)
        self.table.setColumnWidth(BudgetColumn.ATTACHMENT, 40)

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        self.table.setSortingEnabled(True)
        self.setup_delegates()
        
        self.main_layout.addWidget(self.table)

        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.itemChanged.connect(self.on_item_changed)

    def _setup_entry_form(self):
        self.entry_frame = QFrame()
        self.entry_frame.setObjectName("EntryFrame")
        self.entry_frame.setStyleSheet(ENTRY_FRAME_STYLE)
        
        self.form_layout = QGridLayout(self.entry_frame)
        self.form_layout.setContentsMargins(15, 15, 15, 15)
        self.form_layout.setSpacing(10)

        self.f_date = QDateEdit(calendarPopup=True)
        self.f_date.setDate(QDate.currentDate())
        self.f_date.setFixedWidth(110)
        
        self.f_amount = QDoubleSpinBox()
        self.f_amount.setRange(0, 999999.99)
        self.f_amount.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.f_amount.setFixedWidth(110)
        
        self.f_type = QComboBox()
        self.f_type.addItems([t.value for t in TransactionType])
        
        self.f_category = QComboBox()
        self.f_subcategory = QComboBox()
        self.f_wallet = QComboBox()
        self.f_to_wallet = QComboBox()
        
        self.f_sentiment = QComboBox()
        self.f_sentiment.addItems(["Brak"] + [s.value for s in TransactionSentiment])
        self.f_sentiment.setFixedWidth(110)

        self.f_status = QComboBox()
        self.f_status.addItems([s.value for s in TransactionStatus])
        
        self.f_tag = QComboBox()
        self.f_tag.setEditable(True)
        self.f_tag.setPlaceholderText("Tag")
        self.f_tag.setFixedWidth(110)
        self.f_tag.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.f_tag.setStyleSheet(COMBOBOX_STYLE)

        self.f_desc = QLineEdit()
        self.f_desc.setPlaceholderText("Szczegóły transakcji...")

        self.f_attach_btn = QPushButton("📎")
        self.f_attach_btn.setFixedSize(30, 30)
        self.f_attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.f_attach_btn.setStyleSheet(BTN_ATTACH_STYLE)

        self.form_layout.addWidget(QLabel("DATA"), 0, 0); self.form_layout.addWidget(self.f_date, 1, 0)
        self.form_layout.addWidget(QLabel("KWOTA"), 0, 1); self.form_layout.addWidget(self.f_amount, 1, 1)
        self.form_layout.addWidget(QLabel("TYP"), 0, 2); self.form_layout.addWidget(self.f_type, 1, 2)
        self.form_layout.addWidget(QLabel("KATEGORIA"), 0, 3); self.form_layout.addWidget(self.f_category, 1, 3)
        self.form_layout.addWidget(QLabel("Z PORTFELA"), 0, 4); self.form_layout.addWidget(self.f_wallet, 1, 4)

        self.form_layout.addWidget(QLabel("TAG"), 2, 0); self.form_layout.addWidget(self.f_tag, 3, 0)
        self.form_layout.addWidget(QLabel("SENTYMENT"), 2, 1); self.form_layout.addWidget(self.f_sentiment, 3, 1)
        self.form_layout.addWidget(QLabel("STATUS"), 2, 2); self.form_layout.addWidget(self.f_status, 3, 2)
        
        self.form_layout.addWidget(QLabel("PODKATEGORIA"), 2, 3); self.form_layout.addWidget(self.f_subcategory, 3, 3)
        self.form_layout.addWidget(QLabel("DO PORTFELA"), 2, 4); self.form_layout.addWidget(self.f_to_wallet, 3, 4)

        self.form_layout.addWidget(QLabel("OPIS"), 4, 0)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0,0,0,0)
        bottom_layout.setSpacing(10)
        
        self.add_row_btn = QPushButton("DODAJ")
        self.add_row_btn.setFixedSize(130, 30)
        self.add_row_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_row_btn.setStyleSheet(BTN_ADD_ROW_STYLE)
        
        bottom_layout.addWidget(self.f_attach_btn)
        bottom_layout.addWidget(self.f_desc)
        bottom_layout.addWidget(self.add_row_btn)
        
        self.form_layout.addLayout(bottom_layout, 5, 0, 1, 5)

        self.main_layout.addWidget(self.entry_frame)

        self.add_row_btn.clicked.connect(self.handle_add_row)
        self.f_attach_btn.clicked.connect(self.handle_select_attachment)
        self.f_type.currentTextChanged.connect(self.on_type_changed)
        self.f_category.currentTextChanged.connect(self.update_form_subcategories)

    def setup_delegates(self):
        w = [wal.wallet_name for wal in self.service.get_wallets_for_combo()]
        
        badge_delegate = StatusBadgeDelegate(self)
        self.table.setItemDelegateForColumn(BudgetColumn.TYPE, badge_delegate)
        self.table.setItemDelegateForColumn(BudgetColumn.STATUS, badge_delegate)
        
        self.table.setItemDelegateForColumn(BudgetColumn.DATE, DateDelegate(self))
        self.table.setItemDelegateForColumn(BudgetColumn.AMOUNT, AmountDelegate(self))
        
        self.table.setItemDelegateForColumn(BudgetColumn.CATEGORY, FilteredCategoryDelegate(self.service, self))
        
        self.table.setItemDelegateForColumn(BudgetColumn.SUBCATEGORY, SubcategoryDelegate(self.service, self))
        
        self.table.setItemDelegateForColumn(BudgetColumn.WALLET_FROM, ComboBoxDelegate(w, self))
        self.table.setItemDelegateForColumn(BudgetColumn.WALLET_TO, ComboBoxDelegate(["-"] + w, self))
        self.table.setItemDelegateForColumn(BudgetColumn.SENTIMENT, ComboBoxDelegate(["-"] + [s.value for s in TransactionSentiment], self))
        
        self.table.setItemDelegateForColumn(BudgetColumn.TAG, TagDelegate(self.service, self))
        
        self.table.setItemDelegateForColumn(BudgetColumn.IN_STATS, BooleanIconDelegate(self))
        
        users_map = self.service.user_service.get_users()
        user_names = list(users_map.values())
        self.table.setItemDelegateForColumn(BudgetColumn.AUTHOR, ComboBoxDelegate(user_names, self))

    def on_filter_changed(self, index):
        self.filter_table()

    def filter_table(self):
        self.table.setUpdatesEnabled(False) 
        
        query = self.search_input.text().lower()
        hide_pending = self.hide_pending_btn.isChecked()
        
        selected_user_data = self.user_filter_combo.currentData()
        selected_user_id = str(selected_user_data) if selected_user_data is not None else None

        searchable_columns = [
            BudgetColumn.DESCRIPTION, 
            BudgetColumn.CATEGORY, 
            BudgetColumn.SUBCATEGORY, 
            BudgetColumn.TAG, 
            BudgetColumn.AMOUNT  
        ]

        row_count = self.table.rowCount()

        for row in range(row_count):
            should_hide = False

            if not should_hide and hide_pending:
                status_item = self.table.item(row, BudgetColumn.STATUS)
                if status_item and status_item.text() == "PENDING":
                    should_hide = True
            if not should_hide and selected_user_id:
                author_item = self.table.item(row, BudgetColumn.AUTHOR)
                row_author_id = str(author_item.data(Qt.ItemDataRole.UserRole)) if author_item else "None"
                
                if row_author_id != selected_user_id:
                    should_hide = True

            if not should_hide and query:
                text_match = False
                for col in searchable_columns:
                    item = self.table.item(row, col)
                    if item and query in item.text().lower():
                        text_match = True
                        break 
                
                if not text_match:
                    should_hide = True
            self.table.setRowHidden(row, should_hide)

        self.table.setUpdatesEnabled(True)

    def show_header_menu(self, pos):
        header = self.table.horizontalHeader()
        logical_index = header.logicalIndexAt(pos)
        
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #252526; color: white; border: 1px solid #333; } QMenu::item:selected { background-color: #007acc; }")
        
        default_sort_act = menu.addAction("⚡ Domyślne sortowanie")
        menu.addSeparator()
        
        sort_asc_act = menu.addAction("⬆️ Sortuj rosnąco")
        sort_desc_act = menu.addAction("⬇️ Sortuj malejąco")
        menu.addSeparator()
        
        filter_act = menu.addAction("📅 Filtruj datą..." if logical_index == BudgetColumn.DATE else "🔍 Filtruj wartości...")
        clear_col_act = menu.addAction("❌ Wyczyść filtr tej kolumny")
        
        date_presets = {}
        if logical_index == BudgetColumn.DATE:
            menu.addSeparator()
            date_presets["Ten miesiąc"] = menu.addAction("📅 Ten miesiąc")
            date_presets["Poprzedni miesiąc"] = menu.addAction("📅 Poprzedni miesiąc")
            date_presets["Ostatnie 30 dni"] = menu.addAction("📅 Ostatnie 30 dni")

        menu.addSeparator()
        reset_all_act = menu.addAction("🔄 Zresetuj wszystkie filtry")

        action = menu.exec(header.mapToGlobal(pos))
        
        if not action: return

        if action == default_sort_act:
            self.table.setUpdatesEnabled(False)
            self.table.sortItems(BudgetColumn.DATE, Qt.SortOrder.DescendingOrder)
            self.table.sortItems(BudgetColumn.STATUS, Qt.SortOrder.DescendingOrder)
            self.table.setUpdatesEnabled(True)
            return

        if action == sort_asc_act:
            self.table.sortItems(logical_index, Qt.SortOrder.AscendingOrder)
            return
        elif action == sort_desc_act:
            self.table.sortItems(logical_index, Qt.SortOrder.DescendingOrder)
            return
        elif action == reset_all_act:
            self.filter_table()
            return
        elif action == clear_col_act:
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
            self.filter_table()
            return

        self.table.setUpdatesEnabled(False)
        try:
            if logical_index == BudgetColumn.DATE:
                start_date = None
                end_date = None
                today = QDate.currentDate()

                if action == date_presets.get("Ten miesiąc"):
                    start_date = QDate(today.year(), today.month(), 1)
                    end_date = QDate(today.year(), today.month(), today.daysInMonth())
                
                elif action == date_presets.get("Poprzedni miesiąc"):
                    prev_month = today.addMonths(-1)
                    start_date = QDate(prev_month.year(), prev_month.month(), 1)
                    end_date = QDate(prev_month.year(), prev_month.month(), prev_month.daysInMonth())
                
                elif action == date_presets.get("Ostatnie 30 dni"):
                    start_date = today.addDays(-30)
                    end_date = today

                elif action == filter_act:
                    dialog = QDialog(self)
                    dialog.setWindowTitle("Wybierz zakres dat")
                    layout = QFormLayout(dialog)
                    d_from = QDateEdit(QDate.currentDate().addMonths(-1))
                    d_from.setCalendarPopup(True)
                    d_to = QDateEdit(QDate.currentDate())
                    d_to.setCalendarPopup(True)
                    
                    layout.addRow("Od:", d_from)
                    layout.addRow("Do:", d_to)
                    
                    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
                    buttons.accepted.connect(dialog.accept)
                    buttons.rejected.connect(dialog.reject)
                    layout.addWidget(buttons)
                    
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        start_date = d_from.date()
                        end_date = d_to.date()
                    else:
                        return

                if start_date and end_date:
                    for row in range(self.table.rowCount()):
                        if self.table.isRowHidden(row): continue
                        
                        item = self.table.item(row, logical_index)
                        if item:
                            try:
                                row_date = QDate.fromString(item.text(), "yyyy-MM-dd")
                                if not (start_date <= row_date <= end_date):
                                    self.table.setRowHidden(row, True)
                            except Exception:
                                pass

            elif logical_index == BudgetColumn.AMOUNT and action == filter_act:
                text, ok = QInputDialog.getText(self, "Filtruj Kwotę", "Wpisz kwotę lub warunek (np. >100):")
                
                if ok and text:
                    text = text.replace(',', '.').strip()
                    operator = None
                    threshold = 0.0
                    
                    try:
                        if text.startswith('>'):
                            operator = '>'
                            threshold = float(text[1:])
                        elif text.startswith('<'):
                            operator = '<'
                            threshold = float(text[1:])
                        else:
                            operator = '='
                            threshold = float(text)
                    except ValueError:
                        QMessageBox.warning(self, "Błąd", "Niepoprawny format liczby.")
                        return

                    for row in range(self.table.rowCount()):
                        if self.table.isRowHidden(row): continue
                        
                        item = self.table.item(row, logical_index)
                        if item:
                            try:
                                val = float(item.data(Qt.ItemDataRole.EditRole))
                                match = False
                                if operator == '>': match = val > threshold
                                elif operator == '<': match = val < threshold
                                else: match = abs(val - threshold) < 0.01
                                
                                if not match: self.table.setRowHidden(row, True)
                            except (ValueError, TypeError):
                                self.table.setRowHidden(row, True)

            elif action == filter_act:
                unique_values = set()
                for row in range(self.table.rowCount()):
                    if not self.table.isRowHidden(row):
                        item = self.table.item(row, logical_index)
                        if item: unique_values.add(item.text())
                
                values_list = sorted(list(unique_values))
                item_text, ok = QInputDialog.getItem(self, "Filtruj kolumnę", "Wybierz:", ["(Pokaż wszystko)"] + values_list, 0, False)
                
                if ok and item_text:
                    if item_text == "(Pokaż wszystko)":
                        self.filter_table()
                    else:
                        for row in range(self.table.rowCount()):
                            cell = self.table.item(row, logical_index)
                            if cell and cell.text() != item_text:
                                self.table.setRowHidden(row, True)

        finally:
            self.table.setUpdatesEnabled(True)

    def handle_select_attachment(self):
        path, _ = QFileDialog.getOpenFileName(self, "Wybierz plik", "", "Pliki (*.pdf *.jpg *.jpeg *.png)")
        if path:
            folder, ok = QInputDialog.getItem(self, "Wybierz folder", "Gdzie zapisać plik?", self.available_folders, 0, True)
            
            if ok and folder:
                folder = folder.strip()
                if folder not in self.available_folders:
                    self.available_folders.append(folder)
                
                self.current_attachment = path
                self.current_attachment_folder = folder
                self.f_attach_btn.setText("✅")
                self.f_attach_btn.setStyleSheet(BTN_ATTACH_ACTIVE_STYLE)

    def on_type_changed(self, type_text):
        self.toggle_to_wallet_field()
        self.update_form_categories(type_text)
        self._update_add_btn_style(type_text)

    def _update_add_btn_style(self, type_text):
        if type_text == "INCOME":
            self.add_row_btn.setStyleSheet(BTN_ADD_INCOME)
            self.add_row_btn.setText("DODAJ WPŁYW")
        elif type_text == "TRANSFER":
            self.add_row_btn.setStyleSheet(BTN_ADD_TRANSFER)
            self.add_row_btn.setText("DODAJ TRANSFER")
        else:
            self.add_row_btn.setStyleSheet(BTN_ADD_EXPENSE)
            self.add_row_btn.setText("DODAJ WYDATEK")

    def update_form_categories(self, type_text):
        self.f_category.blockSignals(True)
        self.f_category.clear()
        
        try:
            cats = self.service.get_categories_by_type(type_text)
        except AttributeError:
            cats = self.service.get_unique_categories()
            
        self.f_category.addItems(cats)
        self.f_category.blockSignals(False)
        self.update_form_subcategories(self.f_category.currentText())

    def update_form_subcategories(self, name):
        self.f_subcategory.clear()
        if name:
            for s in self.service.get_subcategories_by_category(name): 
                self.f_subcategory.addItem(s["name"], s["id"])

    def toggle_to_wallet_field(self):
        is_t = self.f_type.currentText() == "TRANSFER"; self.f_to_wallet.setEnabled(is_t)
        if not is_t: self.f_to_wallet.setCurrentIndex(-1)

    def handle_full_refresh(self):
        self.table.setDisabled(True)
        self.refresh_btn.setText("⏳ ...")
        self.refresh_btn.setDisabled(True)

        self.thread = QThread()
        self.worker = DataLoaderWorker(self.service)
        
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_data_loaded)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.error.connect(self.on_worker_error)

        self.thread.start()

    def on_worker_error(self, error_msg):
        self.table.setDisabled(False)
        self.refresh_btn.setText("↻ Odśwież")
        self.refresh_btn.setDisabled(False)
        QMessageBox.critical(self, "Error", f"Failed to load data: {error_msg}")

    def on_data_loaded(self, data):
        self.load_form_combos()
        
        self.table.setSortingEnabled(False)
        self.table.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.DescendingOrder)
        
        self.populate_table(data)
        
        self.table.setSortingEnabled(True)
        self.table.setUpdatesEnabled(True)
        self.table.blockSignals(False)
        self.filter_table()
        
        self.table.setDisabled(False)
        self.refresh_btn.setText("↻ Odśwież")
        self.refresh_btn.setDisabled(False)

    def load_form_combos(self):
        self.f_date.setDate(QDate.currentDate())

        self.user_filter_combo.blockSignals(True)
        self.f_wallet.blockSignals(True)
        self.f_to_wallet.blockSignals(True)
        self.f_type.blockSignals(True)
        self.f_category.blockSignals(True)
        self.f_subcategory.blockSignals(True)

        try:
            current_filter_index = self.user_filter_combo.currentIndex()
            self.user_filter_combo.clear()
            self.user_filter_combo.addItem("Wszyscy", None)
            
            if hasattr(self.service.user_service, 'load_users'):
                self.service.user_service.load_users()

            users_map = self.service.user_service.get_users()
            active_user_id = self.service.get_active_user_id()
            
            if not active_user_id and users_map:
                first_uid = next(iter(users_map))
                self.service.user_service.set_active_user_id(str(first_uid))
                active_user_id = str(first_uid)

            for uid, alias in users_map.items():
                self.user_filter_combo.addItem(alias, str(uid))
                
            if current_filter_index > 0:
                self.user_filter_combo.setCurrentIndex(current_filter_index)

            active_alias = users_map.get(str(active_user_id), "Nieznany") if active_user_id else "-"
            self.session_label.setText(f"Zalogowany: {active_alias}")

            self.f_wallet.clear()
            self.f_to_wallet.clear()
            
            all_wallets = self.service.get_wallets_for_combo()
            
            user_default_wallet_id = None
            if active_user_id:
                raw_def_id = self.service.user_service.get_default_wallet_id(str(active_user_id))
                if raw_def_id is not None:
                    user_default_wallet_id = str(raw_def_id)

            for w in all_wallets:
                if active_user_id and str(w.owner_name) == str(active_user_id):
                    self.f_wallet.addItem(w.wallet_name, str(w.id))

            if user_default_wallet_id:
                idx = self.f_wallet.findData(user_default_wallet_id)
                if idx >= 0:
                    self.f_wallet.setCurrentIndex(idx)
                elif self.f_wallet.count() > 0:
                    self.f_wallet.setCurrentIndex(0)
            elif self.f_wallet.count() > 0:
                self.f_wallet.setCurrentIndex(0)

            sorted_dest_wallets = list(all_wallets)
            if active_user_id:
                sorted_dest_wallets.sort(key=lambda w: 0 if str(w.owner_name) == str(active_user_id) else 1)

            self.f_to_wallet.addItem("-", None)
            for w in sorted_dest_wallets:
                self.f_to_wallet.addItem(w.wallet_name, str(w.id))

            self.f_tag.clear()
            if hasattr(self.service, 'get_unique_tags'):
                tags = self.service.get_unique_tags()
                self.f_tag.addItems(tags)
            self.f_tag.setCurrentIndex(-1)

            prefs = self.service.load_last_entry_prefs()
            
            last_type = prefs.get("last_type", "EXPENSE")
            self.f_type.setCurrentText(last_type)
            
            self.update_form_categories(last_type)
            
            last_cat_text = prefs.get("last_category_text")
            if last_cat_text:
                self.f_category.setCurrentText(last_cat_text)
                self.update_form_subcategories(last_cat_text)
            
            last_sub_fk = prefs.get("last_subcategory_fk")
            if last_sub_fk:
                idx = self.f_subcategory.findData(str(last_sub_fk) if last_sub_fk else None)
                if idx >= 0:
                    self.f_subcategory.setCurrentIndex(idx)

        finally:
            self.user_filter_combo.blockSignals(False)
            self.f_wallet.blockSignals(False)
            self.f_to_wallet.blockSignals(False)
            self.f_type.blockSignals(False)
            self.f_category.blockSignals(False)
            self.f_subcategory.blockSignals(False)
            
            self.toggle_to_wallet_field()
            self._update_add_btn_style(self.f_type.currentText())

    def handle_add_row(self):
        active_user_id = self.service.get_active_user_id()

        if not active_user_id:
             QMessageBox.warning(self, "Błąd", "Brak aktywnej sesji użytkownika. Wybierz użytkownika w Opcjach.")
             return

        if self.f_amount.value() <= 0:
            QMessageBox.warning(self, "Błąd", "Kwota musi być większa od zera.")
            return
        
        if not self.f_wallet.currentData():
            QMessageBox.warning(self, "Błąd", "Wybierz portfel źródłowy.")
            return

        if self.f_type.currentText() == "TRANSFER" and not self.f_to_wallet.currentData():
            QMessageBox.warning(self, "Błąd", "Wybierz portfel docelowy dla transferu.")
            return

        att_path = None
        att_type = None
        if self.current_attachment:
            att_path = self.service.upload_attachment(self.current_attachment, self.current_attachment_folder)
            att_type = self.current_attachment.split('.')[-1]

        current_status = self.f_status.currentText()
        is_excluded = (current_status == "PENDING")

        d = {
            "transaction_date": self.f_date.date().toPyDate().isoformat(),
            "amount": self.f_amount.value(),
            "transaction_type": self.f_type.currentText(),
            "status": current_status,
            "wallet_fk": self.f_wallet.currentData(),
            "to_wallet_fk": self.f_to_wallet.currentData() if self.f_type.currentText() == "TRANSFER" else None,
            "subcategory_fk": self.f_subcategory.currentData(),
            "created_by_fk": str(active_user_id), 
            "sentiment": None if self.f_sentiment.currentText() == "Brak" else self.f_sentiment.currentText(),
            "tag": self.f_tag.currentText().strip(),
            "description": self.f_desc.text().strip(),
            "is_excluded_from_stats": is_excluded,
            "attachment_path": att_path,
            "attachment_type": att_type
        }
        
        if self.service.add_transaction(d):
            prefs = {
                "last_type": self.f_type.currentText(),
                "last_category_text": self.f_category.currentText(),
                "last_subcategory_fk": self.f_subcategory.currentData(),
                "last_wallet_fk": self.f_wallet.currentData(), 
                "last_to_wallet_fk": self.f_to_wallet.currentData()
            }
            self.service.save_last_entry_prefs(prefs)

            self.handle_full_refresh()
            self.f_amount.setValue(0)
            self.f_tag.setCurrentIndex(-1)
            self.f_desc.clear()
            self.current_attachment = None
            self.current_attachment_folder = "transactions"
            self.f_attach_btn.setText("📎")
            self.f_attach_btn.setStyleSheet(BTN_ATTACH_STYLE)
            self.f_amount.setFocus()
        else:
            QMessageBox.critical(self, "Błąd Zapisu", "Serwis odrzucił transakcję.\nSprawdź logi w terminalu (konsoli), aby zobaczyć szczegóły błędu.")

    def handle_generate_recurring(self):
        dialog = RecurringTransactionDialog(self.service, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            start_date = data['start_date']
            count = data['count']
            base_desc = data['description']
            
            active_user_id = self.service.get_active_user_id()
            if not active_user_id:
                 QMessageBox.warning(self, "Błąd", "Nie wybrano użytkownika (sesja wygasła?).")
                 return

            for i in range(count):
                next_date = start_date.addMonths(i)
                desc = f"{base_desc} (miesiąc {i+1})" if base_desc else f"(miesiąc {i+1})"
                
                d = {
                    "transaction_date": next_date.toPyDate().isoformat(),
                    "amount": data['amount'],
                    "transaction_type": data['type'],
                    "status": data['status'], 
                    "wallet_fk": data['wallet_fk'],
                    "to_wallet_fk": data['to_wallet_fk'] if data['type'] == "TRANSFER" else None,
                    "subcategory_fk": data['subcategory_fk'],
                    "created_by_fk": str(active_user_id),
                    "sentiment": data['sentiment'],
                    "tag": data['tag'],
                    "description": desc,
                    "attachment_path": None,
                    "attachment_type": None
                }
                self.service.add_transaction(d)
            
            self.handle_full_refresh()
            QMessageBox.information(self, "Sukces", f"Wygenerowano {count} wpisów.")

    def populate_table(self, data):
        self.table.blockSignals(True)
        self.table.setUpdatesEnabled(False)

        try:
            data.sort(key=lambda x: x['date'], reverse=True)
            data.sort(key=lambda x: 0 if x.get('status') == 'PENDING' else 1)
            
            self.table.setRowCount(len(data))
            
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            one_month_ago = QDate.currentDate().addMonths(-1)
            warn_old_date = False

            for row, entry in enumerate(data):
                row_map = [
                    entry["type"], entry["status"], entry["date"], entry["amount"], 
                    entry["author"], entry["category"], entry["subcategory"], 
                    entry["from_wallet"], entry["to_wallet"], entry["sentiment"], 
                    entry["tag"], entry["description"], entry["in_stats"], 
                    "📎" if entry.get("attachment_path") else ""
                ]
                
                is_modified_today = False
                ts_raw = entry.get("updated_at") or entry.get("created_at")
                tooltip_msg = ""
                
                if ts_raw:
                    try:
                        ts_str = str(ts_raw).replace('T', ' ')[:19]
                        dt_obj = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                        dt_pl = dt_obj + timedelta(hours=1)
                        
                        if dt_pl.strftime("%Y-%m-%d") == today_str:
                            is_modified_today = True
                            tooltip_msg = f"Edytowano: {dt_pl.strftime('%H:%M')}"
                    except Exception:
                        pass

                if entry["date"] == today_str and not is_modified_today:
                    is_modified_today = True
                    tooltip_msg = "Nowa transakcja"

                try:
                    entry_date_q = QDate.fromString(entry["date"], "yyyy-MM-dd")
                    if is_modified_today and entry_date_q < one_month_ago:
                        warn_old_date = True
                except Exception:
                    pass

                row_color_hex = entry.get("row_color", "#888888")

                for col, val in enumerate(row_map):
                    item = QTableWidgetItem(str(val))
                    item.setData(Qt.ItemDataRole.UserRole, entry["id"])
                    
                    if col == BudgetColumn.ATTACHMENT: 
                        item.setData(Qt.ItemDataRole.UserRole, entry.get("attachment_path"))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    if col == BudgetColumn.AUTHOR:
                        item.setData(Qt.ItemDataRole.UserRole, entry.get("author_id"))
                        item.setForeground(QColor(entry.get("author_color", "#ffffff")))
                    
                    item.setBackground(QColor(0, 0, 0, 0))

                    if col == BudgetColumn.AMOUNT:
                        amount_val = float(entry["amount"])
                        item.setData(Qt.ItemDataRole.EditRole, amount_val)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        
                        if amount_val > 1000:
                            item.setForeground(QColor("#e3c96d"))
                            item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                            item.setBackground(QColor(255, 215, 0, 25))
                        else:
                            item.setForeground(QColor("#e0e0e0"))
                    
                    elif col == BudgetColumn.SUBCATEGORY:
                        item.setForeground(QColor(row_color_hex))
                    
                    elif col == BudgetColumn.DATE:
                        if is_modified_today:
                            item.setForeground(QColor("#81c784"))
                            item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            if tooltip_msg:
                                item.setToolTip(tooltip_msg)
                        else:
                            item.setForeground(QColor("#e0e0e0"))
                            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        if col not in [BudgetColumn.AMOUNT, BudgetColumn.SUBCATEGORY, BudgetColumn.AUTHOR]:
                             item.setForeground(QColor("#e0e0e0"))

                    if col == BudgetColumn.ATTACHMENT: 
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                    self.table.setItem(row, col, item)
                
                self._update_row_locks(row)

            if warn_old_date:
                self.info_label.setText("⚠️ Uwaga: Zmodyfikowano dzisiaj wpisy starsze niż 30 dni.")
            else:
                self.info_label.setText("")

        finally:
            self.table.setUpdatesEnabled(True)
            self.table.blockSignals(False)

    def _update_row_locks(self, row):
        t_item = self.table.item(row, BudgetColumn.TYPE)
        to_item = self.table.item(row, BudgetColumn.WALLET_TO)
        if not t_item or not to_item: return
        if t_item.text() == "TRANSFER": 
            to_item.setFlags(to_item.flags() | Qt.ItemFlag.ItemIsEditable)
        else: 
            to_item.setFlags(to_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if to_item.text() != "-": to_item.setText("-")

    def on_item_changed(self, item):
        if not item: return
        self.table.blockSignals(True)
        try:
            tx_id = item.data(Qt.ItemDataRole.UserRole)
            row, col, val = item.row(), item.column(), item.text()
            
            mapping = {
                BudgetColumn.TYPE: "transaction_type", 
                BudgetColumn.STATUS: "status", 
                BudgetColumn.DATE: "transaction_date", 
                BudgetColumn.AMOUNT: "amount", 
                BudgetColumn.CATEGORY: "category", 
                BudgetColumn.SUBCATEGORY: "subcategory", 
                BudgetColumn.WALLET_FROM: "wallet_fk", 
                BudgetColumn.WALLET_TO: "to_wallet_fk", 
                BudgetColumn.SENTIMENT: "sentiment", 
                BudgetColumn.TAG: "tag", 
                BudgetColumn.DESCRIPTION: "description", 
                BudgetColumn.IN_STATS: "is_excluded_from_stats"
            }
            
            success = False

            if col == BudgetColumn.AMOUNT:
                val = val.replace(',', '.')
                try:
                    float(val)
                    success = self.service.update_transaction_field(tx_id, "amount", val)
                except ValueError:
                    item.setText("0.00")
            
            elif col == BudgetColumn.TYPE:
                if self.service.update_transaction_field(tx_id, "transaction_type", val):
                    success = True
                    self.table.blockSignals(False)
                    self.refresh_data() 
                    return 

            elif col == BudgetColumn.CATEGORY:
                sub = self.table.item(row, BudgetColumn.SUBCATEGORY)
                if sub: sub.setText("Wybierz...")
                success = True
                
            elif col == BudgetColumn.SUBCATEGORY:
                cat_item = self.table.item(row, BudgetColumn.CATEGORY)
                if cat_item:
                    cat = cat_item.text()
                    match = next((c for c in self.service.get_categories_for_combo() if c.category == cat and c.subcategory == val), None)
                    if match: 
                        success = self.service.update_transaction_field(tx_id, "subcategory_fk", match.subcategory_id)

            elif col == BudgetColumn.AUTHOR:
                users_map = self.service.user_service.get_users()
                new_uid = next((uid for uid, name in users_map.items() if name == val), None)
                if new_uid:
                    success = self.service.update_transaction_field(tx_id, "created_by_fk", new_uid)

            elif col in mapping:
                f = mapping[col]
                if f == "is_excluded_from_stats": 
                    success = self.service.update_transaction_field(tx_id, f, (val == "Nie"))
                elif f in ["wallet_fk", "to_wallet_fk"]:
                    w_id = next((w.id for w in self.service.get_wallets_for_combo() if w.wallet_name == val), None)
                    success = self.service.update_transaction_field(tx_id, f, str(w_id) if w_id else None)
                else: 
                    success = self.service.update_transaction_field(tx_id, f, val)
            
            if success:
                date_item = self.table.item(row, BudgetColumn.DATE)
                if date_item:
                    date_item.setForeground(QColor("#81c784"))
                    date_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                    
                    current_date_val = QDate.fromString(date_item.text(), "yyyy-MM-dd")
                    one_month_ago = QDate.currentDate().addMonths(-1)
                    if current_date_val < one_month_ago:
                        self.info_label.setText("⚠️ Uwaga: Zmodyfikowano dzisiaj wpisy starsze niż 30 dni.")

            self._update_row_locks(row)
        except Exception as e: 
            print(f"UI UPDATE ERROR: {e}")
        finally: 
            self.table.blockSignals(False)

    def refresh_data(self):
        self.handle_full_refresh()

    def show_context_menu(self, pos):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #252526; color: white; border: 1px solid #333; } QMenu::item:selected { background-color: #825fa2; }")
        
        row_idx = rows[0].row()
        file_path_data = self.table.item(row_idx, BudgetColumn.ATTACHMENT).data(Qt.ItemDataRole.UserRole)
        
        view_act = None
        remove_attachment_act = None
        
        if file_path_data:
            view_act = menu.addAction("👁️ Pokaż załącznik")
            remove_attachment_act = menu.addAction("❌ Usuń załącznik")
        
        add_act = menu.addAction("➕ Dodaj/Zmień załącznik")
        
        menu.addSeparator()
        include_stats_act = menu.addAction("📊 Włącz do statystyk (Tak)")
        exclude_stats_act = menu.addAction("🚫 Wyklucz ze statystyk (Nie)")
        
        menu.addSeparator()
        dup = menu.addAction("👯 Zduplikuj zaznaczone")
        dele = menu.addAction("🗑️ Usuń zaznaczone")
        
        act = menu.exec(self.table.mapToGlobal(pos))
        
        if act == view_act and view_act:
            file_content = self.service.download_attachment_content(file_path_data)
            if not file_content:
                QMessageBox.warning(self, "Błąd", "Nie udało się pobrać pliku.")
                return

            ext = file_path_data.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'bmp', 'gif']:
                preview = ImagePreviewDialog(file_content, self)
                preview.exec()
            else:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                        tmp.write(file_content)
                        tmp_path = tmp.name
                    if platform.system() == 'Darwin':
                        subprocess.call(('open', tmp_path))
                    elif platform.system() == 'Windows':
                        os.startfile(tmp_path)
                    else:
                        subprocess.call(('xdg-open', tmp_path))
                except Exception as e:
                    QMessageBox.critical(self, "Błąd", f"Nie można otworzyć pliku:\n{e}")

        elif act == remove_attachment_act and remove_attachment_act:
            tx_id = self.table.item(row_idx, BudgetColumn.TYPE).data(Qt.ItemDataRole.UserRole)
            if QMessageBox.question(self, "Usuń załącznik", "Czy na pewno chcesz usunąć załącznik z tej transakcji?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.service.update_transaction_multiple_fields(tx_id, {"attachment_path": None, "attachment_type": None})
                self.handle_full_refresh()

        elif act == add_act:
            self.handle_manual_attachment(row_idx)
            
        elif act == include_stats_act:
            for index in rows:
                tx_id = self.table.item(index.row(), BudgetColumn.TYPE).data(Qt.ItemDataRole.UserRole)
                self.service.update_transaction_field(tx_id, "is_excluded_from_stats", False)
            self.handle_full_refresh()

        elif act == exclude_stats_act:
            for index in rows:
                tx_id = self.table.item(index.row(), BudgetColumn.TYPE).data(Qt.ItemDataRole.UserRole)
                self.service.update_transaction_field(tx_id, "is_excluded_from_stats", True)
            self.handle_full_refresh()

        elif act == dup:
            for index in rows:
                tx_id = self.table.item(index.row(), BudgetColumn.TYPE).data(Qt.ItemDataRole.UserRole)
                original = self.service.get_transaction_by_id(tx_id)
                if original: self.service.add_transaction(original)
            self.handle_full_refresh()
        elif act == dele:
            if QMessageBox.question(self, "Usuń", f"Usunąć {len(rows)} transakcji?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                ids = [self.table.item(r.row(), BudgetColumn.TYPE).data(Qt.ItemDataRole.UserRole) for r in rows]
                if self.service.delete_transactions(ids): 
                    self.handle_full_refresh()

    def handle_manual_attachment(self, row):
        tx_id = self.table.item(row, BudgetColumn.TYPE).data(Qt.ItemDataRole.UserRole)
        path, _ = QFileDialog.getOpenFileName(self, "Dodaj załącznik", "", "Pliki (*.pdf *.jpg *.jpeg *.png)")
        if path:
            folder, ok = QInputDialog.getItem(self, "Wybierz folder", "Gdzie zapisać plik?", self.available_folders, 0, True)
            if ok and folder:
                folder = folder.strip()
                if folder and folder not in self.available_folders:
                    self.available_folders.append(folder)
                
                new_path = self.service.upload_attachment(path, folder)
                if new_path:
                    ext = path.split('.')[-1]
                    self.service.update_transaction_multiple_fields(tx_id, {"attachment_path": new_path, "attachment_type": ext})
                    self.handle_full_refresh()

    def handle_delete_wallet(self, wallet_id):
        msg = QMessageBox(self)
        msg.setWindowTitle("Usuwanie Portfela")
        msg.setText("Portfel może posiadać przypisane transakcje.")
        btn_cascade = msg.addButton("Usuń wszystko (Kaskadowo)", QMessageBox.ButtonRole.DestructiveRole)
        btn_only = msg.addButton("Usuń tylko portfel", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Anuluj", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        if msg.clickedButton() == btn_cascade:
            if self.service.delete_wallet(wallet_id, cascade=True): self.handle_full_refresh()
        elif msg.clickedButton() == btn_only:
            if self.service.delete_wallet(wallet_id, cascade=False): self.handle_full_refresh()
            else: QMessageBox.warning(self, "Błąd", "Nie można usunąć portfela z historią.")

    def handle_delete_category(self, subcat_id):
        msg = QMessageBox(self)
        msg.setWindowTitle("Usuwanie Kategorii")
        msg.setText("Czy usunąć tę podkategorię?")
        btn_cascade = msg.addButton("Usuń wraz z transakcjami", QMessageBox.ButtonRole.DestructiveRole)
        btn_only = msg.addButton("Usuń tylko kategorię", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Anuluj", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        if msg.clickedButton() == btn_cascade:
            if self.service.delete_category(subcat_id, cascade=True): self.handle_full_refresh()
        elif msg.clickedButton() == btn_only:
            if self.service.delete_category(subcat_id, cascade=False): self.handle_full_refresh()
            else: QMessageBox.warning(self, "Błąd", "Kategoria w użyciu.")