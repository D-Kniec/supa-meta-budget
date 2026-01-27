from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QComboBox, 
    QDoubleSpinBox, QDateEdit, QPushButton, 
    QLabel, QFrame, QHBoxLayout, QGridLayout
)
from PyQt6.QtCore import QDate, Qt
from models.transaction import TransactionType, TransactionSentiment, TransactionStatus
from services.budget_service import BudgetService

class AddTransactionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = BudgetService()
        self.setWindowTitle("Nowa Transakcja")
        self.setMinimumWidth(550)
        self.init_ui()
        self.load_initial_data()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        
        self.setStyleSheet("""
            QDialog { background-color: #252526; color: white; }
            QLabel { color: #825fa2; font-weight: bold; font-size: 10px; border: none; }
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 5px;
                color: white;
                min-height: 25px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {
                border: 1px solid #825fa2;
            }
            QComboBox::drop-down { border: none; }
        """)

        header_layout = QVBoxLayout()
        self.title_lbl = QLabel("Rejestracja Transakcji")
        self.title_lbl.setStyleSheet("color: #825fa2; font-size: 22px; font-weight: bold; border: none;")
        self.subtitle_lbl = QLabel("Wprowadź dane finansowe do księgi głównej.")
        self.subtitle_lbl.setStyleSheet("color: #888; font-size: 12px; border: none; font-weight: normal;")
        header_layout.addWidget(self.title_lbl)
        header_layout.addWidget(self.subtitle_lbl)
        self.main_layout.addLayout(header_layout)

        self.form_frame = QFrame()
        self.form_frame.setStyleSheet("background-color: #252526; border-radius: 12px; border: 1px solid #333;")
        
        self.grid = QGridLayout(self.form_frame)
        self.grid.setContentsMargins(20, 20, 20, 20)
        self.grid.setSpacing(15)

        self.date_input = QDateEdit(calendarPopup=True)
        self.date_input.setDate(QDate.currentDate())
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 9999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        
        self.type_input = QComboBox()
        self.type_input.addItems([t.value for t in TransactionType])
        self.type_input.currentTextChanged.connect(self.on_type_changed)

        self.status_input = QComboBox()
        self.status_input.addItems([s.value for s in TransactionStatus])

        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.update_subcategories)

        self.subcategory_combo = QComboBox()

        self.wallet_combo = QComboBox()
        self.to_wallet_combo = QComboBox()

        self.sentiment_input = QComboBox()
        self.sentiment_input.addItems(["Brak"] + [s.value for s in TransactionSentiment])

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Tag")

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Opis szczegółowy...")

        self.grid.addWidget(QLabel("DATA"), 0, 0)
        self.grid.addWidget(self.date_input, 1, 0)
        self.grid.addWidget(QLabel("KWOTA"), 0, 1)
        self.grid.addWidget(self.amount_input, 1, 1)

        self.grid.addWidget(QLabel("TYP"), 2, 0)
        self.grid.addWidget(self.type_input, 3, 0)
        self.grid.addWidget(QLabel("STATUS"), 2, 1)
        self.grid.addWidget(self.status_input, 3, 1)

        self.grid.addWidget(QLabel("KATEGORIA"), 4, 0)
        self.grid.addWidget(self.category_combo, 5, 0)
        self.grid.addWidget(QLabel("PODKATEGORIA"), 4, 1)
        self.grid.addWidget(self.subcategory_combo, 5, 1)

        self.grid.addWidget(QLabel("Z PORTFELA"), 6, 0)
        self.grid.addWidget(self.wallet_combo, 7, 0)
        self.grid.addWidget(QLabel("DO PORTFELA"), 6, 1)
        self.grid.addWidget(self.to_wallet_combo, 7, 1)

        self.grid.addWidget(QLabel("SENTYMENT"), 8, 0)
        self.grid.addWidget(self.sentiment_input, 9, 0)
        self.grid.addWidget(QLabel("TAG"), 8, 1)
        self.grid.addWidget(self.tag_input, 9, 1)

        self.grid.addWidget(QLabel("OPIS"), 10, 0, 1, 2)
        self.grid.addWidget(self.desc_input, 11, 0, 1, 2)

        self.main_layout.addWidget(self.form_frame)

        self.button_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("ANULUJ")
        self.cancel_btn.setFixedSize(120, 40)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("background-color: transparent; color: #888; border: 1px solid #444; font-weight: bold;")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("ZATWIERDŹ")
        self.save_btn.setFixedHeight(45)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #825fa2; color: white; font-weight: bold;
                border-radius: 6px; font-size: 13px; padding: 0 40px;
            }
            QPushButton:hover { background-color: #9374b3; }
        """)
        self.save_btn.clicked.connect(self.accept)

        self.button_layout.addWidget(self.cancel_btn)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.save_btn)
        self.main_layout.addLayout(self.button_layout)

    def load_initial_data(self):
        wallets = self.service.get_wallets_for_combo()
        for w in wallets:
            self.wallet_combo.addItem(w.wallet_name, w.id)
            self.to_wallet_combo.addItem(w.wallet_name, w.id)
        
        self.on_type_changed(self.type_input.currentText())

    def on_type_changed(self, type_text):
        is_transfer = (type_text == "TRANSFER")
        self.to_wallet_combo.setEnabled(is_transfer)
        
        if not is_transfer:
            self.to_wallet_combo.setCurrentIndex(-1)
            self.to_wallet_combo.setStyleSheet("background-color: #2a2a2a; color: #555; border: 1px solid #333;")
        else:
            self.to_wallet_combo.setStyleSheet("")

        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        
        try:
            cats = self.service.get_categories_by_type(type_text)
        except AttributeError:
            cats = self.service.get_unique_categories()
            
        self.category_combo.addItems(cats)
        self.category_combo.blockSignals(False)
        
        self.update_subcategories(self.category_combo.currentText())

    def update_subcategories(self, category_name):
        self.subcategory_combo.clear()
        if category_name:
            subs = self.service.get_subcategories_by_category(category_name)
            for s in subs:
                self.subcategory_combo.addItem(s["name"], s["id"])

    def get_data(self) -> dict:
        sentiment_val = self.sentiment_input.currentText()
        is_transfer = self.type_input.currentText() == "TRANSFER"
        
        return {
            "transaction_date": self.date_input.date().toPyDate().isoformat(),
            "amount": self.amount_input.value(),
            "transaction_type": self.type_input.currentText(),
            "status": self.status_input.currentText(),
            "wallet_fk": self.wallet_combo.currentData(),
            "to_wallet_fk": self.to_wallet_combo.currentData() if is_transfer else None,
            "subcategory_fk": self.subcategory_combo.currentData(),
            "sentiment": None if sentiment_val == "Brak" else sentiment_val,
            "tag": self.tag_input.text().strip(),
            "description": self.desc_input.text().strip()
        }