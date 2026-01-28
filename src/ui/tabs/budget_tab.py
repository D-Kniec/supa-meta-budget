import os
import platform
import subprocess
import tempfile
import traceback
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QFrame, QLabel, 
    QGridLayout, QDoubleSpinBox, QLineEdit, QFileDialog, QMenu,
    QInputDialog, QDialog, QDateEdit, QComboBox, QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt, QDate, QThread
from PyQt6.QtGui import QColor, QFont

from services.budget_service import BudgetService
from models.transaction import TransactionType, TransactionStatus, TransactionSentiment
from core.config import BASE_DIR

from core.workers import DataLoaderWorker
from ui.delegates.highlight_delegate import HighlightDelegate
from models.budget_types import BudgetColumn, BudgetTableWidgetItem

from ui.delegates.budget_delegates import (
    StatusBadgeDelegate, BooleanIconDelegate, AmountDelegate, 
    ComboBoxDelegate, TagDelegate, FilteredCategoryDelegate, 
    SubcategoryDelegate, DateDelegate
)
from ui.dialogs.image_preview_dialog import ImagePreviewDialog
from ui.dialogs.recurring_transaction_dialog import RecurringTransactionDialog
from ui.styles import (
    SEARCH_INPUT_STYLE, SEARCH_INPUT_ACTIVE_STYLE, 
    BTN_STANDARD_STYLE, BTN_PENDING_STYLE, 
    BTN_RECURRING_STYLE, TABLE_STYLE, ENTRY_FRAME_STYLE, 
    COMBOBOX_STYLE, BTN_ATTACH_STYLE, BTN_ATTACH_ACTIVE_STYLE, 
    BTN_ADD_ROW_STYLE, INFO_LABEL_STYLE, SUMMARY_LABEL_TEMPLATE, 
    BTN_ADD_EXPENSE, BTN_ADD_INCOME, BTN_ADD_TRANSFER
)

USER_PREFS_FILE = os.path.join(BASE_DIR, "user_prefs.json")

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
        self.all_transactions = []
        
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

        self.summary_label = QLabel("Bilans: 0.00")
        self.summary_label.setFixedHeight(36)
        self.summary_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 0 15px;
                color: #e0e0e0;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        
        self.toolbar.addWidget(self.summary_label)
        
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

    def setup_delegates(self, wallets=None, users=None):
        wallets_list = wallets if wallets else []
        users_map = users if users else {}
        user_names = list(users_map.values())
        
        badge_delegate = StatusBadgeDelegate(self)
        self.table.setItemDelegateForColumn(BudgetColumn.TYPE, badge_delegate)
        self.table.setItemDelegateForColumn(BudgetColumn.STATUS, badge_delegate)
        
        self.table.setItemDelegateForColumn(BudgetColumn.DATE, DateDelegate(self))
        self.table.setItemDelegateForColumn(BudgetColumn.AMOUNT, AmountDelegate(self))
        
        cat_delegate = FilteredCategoryDelegate(self.service, self)
        self.table.setItemDelegateForColumn(BudgetColumn.CATEGORY, HighlightDelegate(self.table, cat_delegate))
        
        sub_delegate = SubcategoryDelegate(self.service, self)
        self.table.setItemDelegateForColumn(BudgetColumn.SUBCATEGORY, HighlightDelegate(self.table, sub_delegate))
        
        wallet_from_del = ComboBoxDelegate(wallets_list, self)
        self.table.setItemDelegateForColumn(BudgetColumn.WALLET_FROM, HighlightDelegate(self.table, wallet_from_del))
        
        wallet_to_del = ComboBoxDelegate(["-"] + wallets_list, self)
        self.table.setItemDelegateForColumn(BudgetColumn.WALLET_TO, HighlightDelegate(self.table, wallet_to_del))
        
        sentiment_del = ComboBoxDelegate(["-"] + [s.value for s in TransactionSentiment], self)
        self.table.setItemDelegateForColumn(BudgetColumn.SENTIMENT, HighlightDelegate(self.table, sentiment_del))
        
        tag_del = TagDelegate(self.service, self)
        self.table.setItemDelegateForColumn(BudgetColumn.TAG, HighlightDelegate(self.table, tag_del))
        
        self.table.setItemDelegateForColumn(BudgetColumn.DESCRIPTION, HighlightDelegate(self.table))
        self.table.setItemDelegateForColumn(BudgetColumn.IN_STATS, BooleanIconDelegate(self))
        
        author_del = ComboBoxDelegate(user_names, self)
        self.table.setItemDelegateForColumn(BudgetColumn.AUTHOR, HighlightDelegate(self.table, author_del))
    def on_filter_changed(self, index):
        self.filter_table()

    def filter_table(self):
        query = self.search_input.text().lower()
        
        for col in range(self.table.columnCount()):
            delegate = self.table.itemDelegateForColumn(col)
            if isinstance(delegate, HighlightDelegate):
                delegate.setSearchQuery(query)
        
        self.table.viewport().update()
        
        hide_pending = self.hide_pending_btn.isChecked()
        selected_user_data = self.user_filter_combo.currentData()
        selected_user_id = str(selected_user_data) if selected_user_data is not None else None

        filtered_data = []
        total_income = 0.0
        total_expense = 0.0

        for row in self.all_transactions:
            if hide_pending and row.get('status') == "PENDING":
                continue

            if selected_user_id:
                row_author_id = str(row.get('author_id', 'None'))
                if row_author_id != selected_user_id:
                    continue

            if query:
                search_target = (
                    f"{row.get('description', '')} "
                    f"{row.get('category', '')} "
                    f"{row.get('subcategory', '')} "
                    f"{row.get('tag', '')} "
                    f"{str(row.get('amount', ''))} "
                    f"{row.get('from_wallet', '')} "
                    f"{row.get('to_wallet', '')} "
                    f"{row.get('author', '')} "
                    f"{row.get('sentiment', '')}"
                ).lower()
                
                if query not in search_target:
                    continue
            
            filtered_data.append(row)
            
            try:
                amt = float(row.get('amount', 0))
                t_type = row.get('type')
                if t_type == "INCOME":
                    total_income += amt
                elif t_type == "EXPENSE":
                    total_expense += amt
            except ValueError:
                pass

        balance = total_income - total_expense
        balance_str = f"{balance:,.2f}".replace(",", " ").replace(".", ",")
        
        if balance > 0:
            color = "#81c784"
            prefix = "+"
        elif balance < 0:
            color = "#e57373"
            prefix = ""
        else:
            color = "#e0e0e0"
            prefix = ""

        self.summary_label.setText(f"Bilans: {prefix}{balance_str} PLN")
        self.summary_label.setStyleSheet(SUMMARY_LABEL_TEMPLATE.format(color=color))

        self.populate_table(filtered_data)
        self._update_visuals()

    def recalculate_balance_from_ui(self):
        total_income = 0.0
        total_expense = 0.0

        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            
            type_item = self.table.item(row, BudgetColumn.TYPE)
            t_type = type_item.text() if type_item else ""

            amt_item = self.table.item(row, BudgetColumn.AMOUNT)
            amt = 0.0
            if amt_item:
                try:
                    val = amt_item.data(Qt.ItemDataRole.EditRole)
                    if isinstance(val, (float, int)):
                        amt = float(val)
                    else:
                        amt = float(amt_item.text().replace(' ', '').replace(',', '.'))
                except (ValueError, TypeError):
                    amt = 0.0
            
            if t_type == "INCOME":
                total_income += amt
            elif t_type == "EXPENSE":
                total_expense += amt

        balance = total_income - total_expense
        balance_str = f"{balance:,.2f}".replace(",", " ").replace(".", ",")
        
        if balance > 0:
            color = "#81c784"
            prefix = "+"
        elif balance < 0:
            color = "#e57373"
            prefix = ""
        else:
            color = "#e0e0e0"
            prefix = ""

        self.summary_label.setText(f"Bilans: {prefix}{balance_str} PLN")
        self.summary_label.setStyleSheet(SUMMARY_LABEL_TEMPLATE.format(color=color))

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
        
        cats = []
        try:
            if type_text:
                cats = self.service.get_categories_by_type(type_text)
            
            if not cats:
                cats = self.service.get_unique_categories()
        except Exception as e:
            print(f"UI Warning: Could not load categories: {e}")

        safe_cats = []
        seen = set()
        for c in cats:
            name = ""
            if isinstance(c, dict):
                name = str(c.get('name', ''))
            elif hasattr(c, 'name'):
                name = str(c.name)
            else:
                name = str(c)
            
            if name and name not in seen:
                safe_cats.append(name)
                seen.add(name)
        
        safe_cats.sort()
        self.f_category.addItems(safe_cats)
        
        self.f_category.blockSignals(False)

        if self.f_category.count() > 0:
            self.f_category.setCurrentIndex(0)
            self.update_form_subcategories(self.f_category.currentText())
        else:
            self.update_form_subcategories(None)

    def update_form_subcategories(self, name):
        self.f_subcategory.blockSignals(True)
        self.f_subcategory.clear()
        
        if name:
            try:
                subs = self.service.get_subcategories_by_category(name)
                for s in subs:
                    if isinstance(s, dict):
                        display = s.get("name", str(s))
                        val = s.get("id", display)
                        self.f_subcategory.addItem(display, val)
                    elif hasattr(s, 'id') and hasattr(s, 'name'):
                         self.f_subcategory.addItem(s.name, s.id)
                    else:
                        self.f_subcategory.addItem(str(s))
            except Exception as e:
                print(f"UI Warning: Could not load subcategories: {e}")
        
        if self.f_subcategory.count() > 0:
            self.f_subcategory.setCurrentIndex(0)
            
        self.f_subcategory.blockSignals(False)

    def toggle_to_wallet_field(self):
        is_t = self.f_type.currentText() == "TRANSFER"; self.f_to_wallet.setEnabled(is_t)
        if not is_t: self.f_to_wallet.setCurrentIndex(-1)

    def handle_full_refresh(self):
        self.table.setDisabled(True)
        self.refresh_btn.setText("⏳ ...")
        self.refresh_btn.setDisabled(True)

        self.thread = QThread()
        
        def refresh_task(local_service):
            local_service.reload_cache()
            return {
                "transactions": local_service.get_ui_transactions(),
                "snapshot": local_service.get_cache_snapshot()
            }

        self.worker = DataLoaderWorker(refresh_task)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_data_loaded)
        
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.error.connect(self.on_worker_error)
        self.worker.error.connect(self.thread.quit)

        self.thread.start()

    def on_worker_error(self, error_msg):
        self.table.setDisabled(False)
        self.refresh_btn.setText("↻ Odśwież")
        self.refresh_btn.setDisabled(False)
        QMessageBox.critical(self, "Error", f"Failed to load data: {error_msg}")

    def on_data_loaded(self, payload):
        transactions = payload.get("transactions", [])
        snapshot = payload.get("snapshot", {})

        self.service.hydrate_cache(snapshot)
        
        wallets_list = [w.wallet_name for w in self.service.get_wallets_for_combo()]
        users_data = snapshot.get("users", {})
        
        self.setup_delegates(wallets=wallets_list, users=users_data)

        self.all_transactions = transactions
        self.load_form_combos()
        self.active_column_filters = {}
        
        self.table.setDisabled(False)
        self.refresh_btn.setText("↻ Odśwież")
        self.refresh_btn.setDisabled(False)

        self.filter_table()

    def load_form_combos(self):
        self.f_date.setDate(QDate.currentDate())

        self.user_filter_combo.blockSignals(True)
        
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

            self.f_wallet.blockSignals(True)
            self.f_to_wallet.blockSignals(True)
            self.f_wallet.clear()
            self.f_to_wallet.clear()
            
            all_wallets = self.service.get_wallets_for_combo()
            
            user_default_wallet_id = None
            if active_user_id:
                raw_def_id = self.service.user_service.get_default_wallet_id(str(active_user_id))
                if raw_def_id is not None: user_default_wallet_id = str(raw_def_id)
            
            for w in all_wallets:
                if active_user_id and str(w.owner_name) == str(active_user_id):
                    self.f_wallet.addItem(w.wallet_name, str(w.id))
            
            if user_default_wallet_id:
                idx = self.f_wallet.findData(user_default_wallet_id)
                if idx >= 0: self.f_wallet.setCurrentIndex(idx)
                elif self.f_wallet.count() > 0: self.f_wallet.setCurrentIndex(0)
            elif self.f_wallet.count() > 0: self.f_wallet.setCurrentIndex(0)

            sorted_dest_wallets = list(all_wallets)
            if active_user_id:
                sorted_dest_wallets.sort(key=lambda w: 0 if str(w.owner_name) == str(active_user_id) else 1)
            self.f_to_wallet.addItem("-", None)
            for w in sorted_dest_wallets:
                self.f_to_wallet.addItem(w.wallet_name, str(w.id))
                
            self.f_wallet.blockSignals(False)
            self.f_to_wallet.blockSignals(False)

            self.f_tag.clear()
            if hasattr(self.service, 'get_unique_tags'):
                tags = self.service.get_unique_tags()
                self.f_tag.addItems(tags)
            self.f_tag.setCurrentIndex(-1)

            prefs = self.service.load_last_entry_prefs()
            
            self.f_type.blockSignals(True)
            last_type = prefs.get("last_type", "EXPENSE")
            idx_type = self.f_type.findText(last_type)
            if idx_type < 0:
                 idx_type = self.f_type.findText("EXPENSE")
                 if idx_type < 0 and self.f_type.count() > 0:
                     idx_type = 0
            
            if idx_type >= 0:
                self.f_type.setCurrentIndex(idx_type)
            
            current_type_text = self.f_type.currentText()
            self.f_type.blockSignals(False)

            self.update_form_categories(current_type_text)
            
            last_cat_text = prefs.get("last_category_text")
            if last_cat_text:
                self.f_category.blockSignals(True)
                idx_cat = self.f_category.findText(last_cat_text)
                if idx_cat >= 0:
                    self.f_category.setCurrentIndex(idx_cat)
                    self.f_category.blockSignals(False)
                    self.update_form_subcategories(last_cat_text)
                else:
                    self.f_category.blockSignals(False)
            
            last_sub_fk = prefs.get("last_subcategory_fk")
            if last_sub_fk:
                idx_sub = self.f_subcategory.findData(last_sub_fk)
                if idx_sub < 0:
                     try: idx_sub = self.f_subcategory.findData(int(last_sub_fk))
                     except: pass
                if idx_sub < 0:
                     try: idx_sub = self.f_subcategory.findData(str(last_sub_fk))
                     except: pass
                
                if idx_sub >= 0:
                    self.f_subcategory.setCurrentIndex(idx_sub)

        finally:
            self.user_filter_combo.blockSignals(False)
            self.toggle_to_wallet_field()
            self._update_add_btn_style(self.f_type.currentText())

    def _update_visuals(self):
        if self.search_input.text():
            self.search_input.setStyleSheet("""
                QLineEdit {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 2px solid #81c784;
                    border-radius: 4px;
                    padding: 0 10px;
                    font-size: 13px;
                }
            """)
        else:
            self.search_input.setStyleSheet(SEARCH_INPUT_STYLE)

        for col in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(col)
            if not item:
                item = QTableWidgetItem(self.headers[col])
                self.table.setHorizontalHeaderItem(col, item)
            
            base_name = self.headers[col]
            font = item.font()
            
            if col in self.active_column_filters:
                filter_val = str(self.active_column_filters[col])
                if len(filter_val) > 10:
                    filter_val = filter_val[:8] + ".."
                
                item.setText(f"{base_name} [{filter_val}]")
                font.setBold(True)
                item.setFont(font)
                item.setForeground(QColor("#81c784"))
            else:
                item.setText(base_name)
                font.setBold(False)
                item.setFont(font)
                item.setForeground(QColor("#e0e0e0"))

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
            QMessageBox.critical(self, "Błąd Zapisu", "Serwis odrzucił transakcję.\nSprawdź logi w terminalu.")

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
        self.table.setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)
        self.table.blockSignals(True)

        try:
            data.sort(key=lambda x: x['date'], reverse=True)
            data.sort(key=lambda x: 0 if x.get('status') == 'PENDING' else 1)
            
            self.table.setRowCount(len(data))
            
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            one_month_ago = QDate.currentDate().addMonths(-1)
            warn_old_date = False

            font_bold = QFont("Segoe UI", 9, QFont.Weight.Bold)
            color_high_amt = QColor("#e3c96d")
            color_bg_high = QColor(255, 215, 0, 25)
            color_success = QColor("#81c784")
            color_default = QColor("#e0e0e0")
            color_transparent = QColor(0, 0, 0, 0)

            for row_idx, entry in enumerate(data):
                is_modified_today = False
                tooltip_msg = ""
                ts_raw = entry.get("updated_at") or entry.get("created_at")
                
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

                def create_item(display_val, sort_val=None, align=Qt.AlignmentFlag.AlignCenter, color=color_default, editable=True):
                    item = BudgetTableWidgetItem(str(display_val))
                    item.setData(Qt.ItemDataRole.UserRole, entry["id"])
                    
                    if sort_val is not None:
                        item.setData(Qt.ItemDataRole.EditRole, sort_val)
                    else:
                        item.setData(Qt.ItemDataRole.EditRole, display_val)

                    item.setTextAlignment(align)
                    item.setForeground(color)
                    item.setBackground(color_transparent)
                    
                    if not editable:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        
                    return item

                self.table.setItem(row_idx, BudgetColumn.TYPE, create_item(entry["type"], editable=False))
                self.table.setItem(row_idx, BudgetColumn.STATUS, create_item(entry["status"]))
                
                d_q = QDate.fromString(entry["date"], "yyyy-MM-dd")
                d_item = create_item(entry["date"], sort_val=d_q)
                if is_modified_today:
                    d_item.setForeground(color_success)
                    d_item.setFont(font_bold)
                    if tooltip_msg: d_item.setToolTip(tooltip_msg)
                self.table.setItem(row_idx, BudgetColumn.DATE, d_item)

                try:
                    amt = float(entry["amount"])
                except ValueError:
                    amt = 0.0
                    
                amt_str = f"{amt:.2f}"
                amt_item = create_item(amt_str, sort_val=amt, align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                if amt > 1000:
                    amt_item.setForeground(color_high_amt)
                    amt_item.setFont(font_bold)
                    amt_item.setBackground(color_bg_high)
                self.table.setItem(row_idx, BudgetColumn.AMOUNT, amt_item)

                auth_color = QColor(entry.get("author_color", "#ffffff"))
                auth_item = create_item(entry["author"], color=auth_color)
                auth_item.setData(Qt.ItemDataRole.UserRole, entry.get("author_id"))
                self.table.setItem(row_idx, BudgetColumn.AUTHOR, auth_item)

                self.table.setItem(row_idx, BudgetColumn.CATEGORY, create_item(entry["category"]))
                self.table.setItem(row_idx, BudgetColumn.SUBCATEGORY, create_item(entry["subcategory"], color=QColor(row_color_hex)))

                self.table.setItem(row_idx, BudgetColumn.WALLET_FROM, create_item(entry["from_wallet"]))
                self.table.setItem(row_idx, BudgetColumn.WALLET_TO, create_item(entry["to_wallet"]))
                self.table.setItem(row_idx, BudgetColumn.SENTIMENT, create_item(entry["sentiment"]))
                self.table.setItem(row_idx, BudgetColumn.TAG, create_item(entry["tag"]))
                self.table.setItem(row_idx, BudgetColumn.DESCRIPTION, create_item(entry["description"], align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter))
                self.table.setItem(row_idx, BudgetColumn.IN_STATS, create_item(entry["in_stats"]))

                has_att = bool(entry.get("attachment_path"))
                att_item = create_item("📎" if has_att else "", editable=False)
                att_item.setData(Qt.ItemDataRole.UserRole, entry.get("attachment_path"))
                self.table.setItem(row_idx, BudgetColumn.ATTACHMENT, att_item)

                if entry["type"] != "TRANSFER":
                    to_wallet_item = self.table.item(row_idx, BudgetColumn.WALLET_TO)
                    to_wallet_item.setFlags(to_wallet_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if to_wallet_item.text() != "-": to_wallet_item.setText("-")

            if warn_old_date:
                self.info_label.setText("⚠️ Uwaga: Zmodyfikowano dzisiaj wpisy starsze niż 30 dni.")
            else:
                self.info_label.setText("")

        except Exception as e:
            print(f"CRITICAL UI ERROR in populate_table: {e}")
            traceback.print_exc()
        
        finally:
            self.table.setUpdatesEnabled(True)
            self.table.setSortingEnabled(True)
            self.table.blockSignals(False)

    def handle_reset_filters(self):
        self.search_input.clear()
        self.user_filter_combo.setCurrentIndex(0)
        self.active_column_filters.clear()
        
        for col in range(self.table.columnCount()):
            delegate = self.table.itemDelegateForColumn(col)
            if isinstance(delegate, HighlightDelegate):
                delegate.setSearchQuery("")

        self.table.viewport().update()
        
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)
            
        self.filter_table()

    def handle_default_sort(self):
        self.table.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        self.filter_table()


    def _prompt_date_range(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Wybierz zakres dat")
        layout = QFormLayout(dialog)
        d_from = QDateEdit(QDate.currentDate().addMonths(-1))
        d_from.setCalendarPopup(True)
        d_to = QDateEdit(QDate.currentDate())
        d_to.setCalendarPopup(True)
        layout.addRow("Od:", d_from); layout.addRow("Do:", d_to)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return d_from.date(), d_to.date()
        return None, None

    def _prompt_amount_filter(self):
        text, ok = QInputDialog.getText(self, "Filtruj Kwotę", "Wpisz kwotę lub warunek (np. >100):")
        if not ok or not text: return None, None
        
        text = text.replace(',', '.').strip()
        try:
            if text.startswith('>'): return '>', float(text[1:])
            if text.startswith('<'): return '<', float(text[1:])
            return '=', float(text)
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Niepoprawny format liczby.")
            return None, None

    def _prompt_text_filter(self, col_idx):
        unique_values = set()
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                item = self.table.item(row, col_idx)
                if item: unique_values.add(item.text())
        
        values_list = sorted(list(unique_values))
        item_text, ok = QInputDialog.getItem(self, "Filtruj kolumnę", "Wybierz:", ["(Pokaż wszystko)"] + values_list, 0, False)
        return item_text if ok else None

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
            self.handle_default_sort()
            return
        if action == reset_all_act:
            self.handle_reset_filters()
            return
        
        if action == clear_col_act:
            if logical_index in self.active_column_filters:
                del self.active_column_filters[logical_index]
            
            if not self.active_column_filters:
                for row in range(self.table.rowCount()):
                    self.table.setRowHidden(row, False)
            
            self.filter_table()
            self._update_visuals()
            return

        if action == sort_asc_act:
            self.table.sortItems(logical_index, Qt.SortOrder.AscendingOrder)
            return
        if action == sort_desc_act:
            self.table.sortItems(logical_index, Qt.SortOrder.DescendingOrder)
            return

        self.table.setUpdatesEnabled(False)
        filter_label = None 

        try:
            if logical_index == BudgetColumn.DATE:
                start, end = None, None
                today = QDate.currentDate()

                if action == date_presets.get("Ten miesiąc"):
                    start, end = QDate(today.year(), today.month(), 1), QDate(today.year(), today.month(), today.daysInMonth())
                    filter_label = "Ten mc"
                elif action == date_presets.get("Poprzedni miesiąc"):
                    prev = today.addMonths(-1)
                    start, end = QDate(prev.year(), prev.month(), 1), QDate(prev.year(), prev.month(), prev.daysInMonth())
                    filter_label = "Poprz. mc"
                elif action == date_presets.get("Ostatnie 30 dni"):
                    start, end = today.addDays(-30), today
                    filter_label = "30 dni"
                elif action == filter_act:
                    start, end = self._prompt_date_range()
                    if start and end:
                        filter_label = f"{start.toString('dd.MM')}-{end.toString('dd.MM')}"

                if start and end:
                    for row in range(self.table.rowCount()):
                        if self.table.isRowHidden(row): continue
                        item = self.table.item(row, logical_index)
                        if item:
                            val = item.data(Qt.ItemDataRole.EditRole)
                            r_date = val if isinstance(val, QDate) else QDate.fromString(item.text(), "yyyy-MM-dd")
                            if not (start <= r_date <= end): self.table.setRowHidden(row, True)

            elif logical_index == BudgetColumn.AMOUNT and action == filter_act:
                op, thr = self._prompt_amount_filter()
                if op:
                    filter_label = f"{op}{thr}"
                    for row in range(self.table.rowCount()):
                        if self.table.isRowHidden(row): continue
                        item = self.table.item(row, logical_index)
                        if item:
                            try:
                                val = float(item.data(Qt.ItemDataRole.EditRole))
                                match = (val > thr) if op == '>' else (val < thr) if op == '<' else (abs(val - thr) < 0.01)
                                if not match: self.table.setRowHidden(row, True)
                            except: self.table.setRowHidden(row, True)

            elif action == filter_act:
                txt = self._prompt_text_filter(logical_index)
                if txt and txt != "(Pokaż wszystko)":
                    filter_label = txt
                    for row in range(self.table.rowCount()):
                        if self.table.isRowHidden(row): continue
                        item = self.table.item(row, logical_index)
                        if item and item.text() != txt: self.table.setRowHidden(row, True)

            if filter_label:
                self.active_column_filters[logical_index] = filter_label

            self.recalculate_balance_from_ui()
            self._update_visuals()

        finally:
            self.table.setUpdatesEnabled(True)

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