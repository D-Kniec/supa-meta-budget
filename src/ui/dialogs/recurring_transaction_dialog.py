from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QDateEdit, QSpinBox,
    QDoubleSpinBox, QAbstractSpinBox, QComboBox, QLineEdit, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import QDate
from models.transaction import TransactionType, TransactionStatus, TransactionSentiment

class RecurringTransactionDialog(QDialog):
    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("Dodaj Transakcje Cykliczne")
        self.resize(700, 350)
        self.setStyleSheet("""
            QDialog { background-color: #252526; color: white; }
            QLabel { color: #aaa; font-weight: 600; font-size: 11px; }
            QDoubleSpinBox, QDateEdit, QComboBox, QLineEdit, QSpinBox {
                background-color: #1e1e1e; border: 1px solid #444; border-radius: 6px;
                padding: 5px; color: white; min-height: 25px;
            }
            QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus, QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #825fa2;
            }
            QPushButton {
                background-color: #825fa2; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #9a72bd; }
            QPushButton#CancelBtn {
                background-color: #333; border: 1px solid #444; color: #ddd;
            }
            QPushButton#CancelBtn:hover { background-color: #444; }
        """)
        
        layout = QVBoxLayout(self)
        form_layout = QGridLayout()
        form_layout.setSpacing(15)

        self.f_date = QDateEdit(calendarPopup=True)
        self.f_date.setDate(QDate.currentDate())
        self.f_date.setDisplayFormat("yyyy-MM-dd")
        
        self.f_count = QSpinBox()
        self.f_count.setRange(2, 60)
        self.f_count.setValue(12)
        self.f_count.setSuffix(" miesięcy")

        self.f_amount = QDoubleSpinBox()
        self.f_amount.setRange(0, 999999.99)
        self.f_amount.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        
        self.f_type = QComboBox()
        self.f_type.addItems([t.value for t in TransactionType])
        
        self.f_category = QComboBox()
        self.f_subcategory = QComboBox()
        
        self.f_wallet = QComboBox()
        self.f_to_wallet = QComboBox()
        
        self.f_sentiment = QComboBox()
        self.f_sentiment.addItems(["Brak"] + [s.value for s in TransactionSentiment])

        self.f_status = QComboBox()
        self.f_status.addItems([s.value for s in TransactionStatus])
        self.f_status.setCurrentText("PENDING")

        self.f_tag = QComboBox()
        self.f_tag.setEditable(True)
        
        self.f_desc = QLineEdit()
        self.f_desc.setPlaceholderText("Opis transakcji cyklicznej...")

        form_layout.addWidget(QLabel("DATA POCZĄTKOWA"), 0, 0)
        form_layout.addWidget(self.f_date, 1, 0)
        
        form_layout.addWidget(QLabel("LICZBA POWTÓRZEŃ"), 0, 1)
        form_layout.addWidget(self.f_count, 1, 1)
        
        form_layout.addWidget(QLabel("KWOTA"), 0, 2)
        form_layout.addWidget(self.f_amount, 1, 2)

        form_layout.addWidget(QLabel("TYP"), 2, 0)
        form_layout.addWidget(self.f_type, 3, 0)
        
        form_layout.addWidget(QLabel("KATEGORIA"), 2, 1)
        form_layout.addWidget(self.f_category, 3, 1)
        
        form_layout.addWidget(QLabel("PODKATEGORIA"), 2, 2)
        form_layout.addWidget(self.f_subcategory, 3, 2)

        form_layout.addWidget(QLabel("Z PORTFELA"), 4, 0)
        form_layout.addWidget(self.f_wallet, 5, 0)
        
        form_layout.addWidget(QLabel("DO PORTFELA"), 4, 1)
        form_layout.addWidget(self.f_to_wallet, 5, 1)
        
        form_layout.addWidget(QLabel("STATUS"), 4, 2)
        form_layout.addWidget(self.f_status, 5, 2)

        form_layout.addWidget(QLabel("TAG"), 6, 0)
        form_layout.addWidget(self.f_tag, 7, 0)
        
        form_layout.addWidget(QLabel("SENTYMENT"), 6, 1)
        form_layout.addWidget(self.f_sentiment, 7, 1)

        form_layout.addWidget(QLabel("OPIS"), 8, 0, 1, 3)
        form_layout.addWidget(self.f_desc, 9, 0, 1, 3)

        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Anuluj")
        btn_cancel.setObjectName("CancelBtn")
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("Generuj Transakcje")
        btn_ok.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

        self.service.reload_cache()
        self.load_combos()
        self.f_type.currentTextChanged.connect(self.on_type_changed)
        self.f_category.currentTextChanged.connect(self.update_subcategories)
        self.on_type_changed(self.f_type.currentText())

    def load_combos(self):
        self.f_wallet.clear()
        self.f_to_wallet.clear()
        self.f_category.clear()
        self.f_tag.clear()

        for wal in self.service.get_wallets_for_combo():
            self.f_wallet.addItem(wal.wallet_name, wal.id)
            self.f_to_wallet.addItem(wal.wallet_name, wal.id)
        
        if hasattr(self.service, 'get_unique_tags'):
            self.f_tag.addItems(self.service.get_unique_tags())
        self.f_tag.setCurrentIndex(-1)

    def on_type_changed(self, type_text):
        is_transfer = (type_text == "TRANSFER")
        self.f_to_wallet.setEnabled(is_transfer)
        if not is_transfer:
            self.f_to_wallet.setCurrentIndex(-1)
        
        self.f_category.blockSignals(True)
        self.f_category.clear()
        try:
            cats = self.service.get_categories_by_type(type_text)
        except:
            cats = self.service.get_unique_categories()
        self.f_category.addItems(cats)
        self.f_category.blockSignals(False)
        self.update_subcategories(self.f_category.currentText())

    def update_subcategories(self, name):
        self.f_subcategory.clear()
        if name:
            for s in self.service.get_subcategories_by_category(name): 
                self.f_subcategory.addItem(s["name"], s["id"])

    def get_data(self):
        return {
            "start_date": self.f_date.date(),
            "count": self.f_count.value(),
            "amount": self.f_amount.value(),
            "type": self.f_type.currentText(),
            "category": self.f_category.currentText(),
            "subcategory_fk": self.f_subcategory.currentData(),
            "wallet_fk": self.f_wallet.currentData(),
            "to_wallet_fk": self.f_to_wallet.currentData(),
            "status": self.f_status.currentText(),
            "sentiment": None if self.f_sentiment.currentText() == "Brak" else self.f_sentiment.currentText(),
            "tag": self.f_tag.currentText().strip(),
            "description": self.f_desc.text().strip()
        }