from enum import IntEnum
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt, QDate

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

class BudgetTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            val1 = self.data(Qt.ItemDataRole.EditRole)
            val2 = other.data(Qt.ItemDataRole.EditRole)

            if val1 is not None and val2 is not None:
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    return val1 < val2
                if isinstance(val1, QDate) and isinstance(val2, QDate):
                    return val1 < val2

            text1 = self.text().replace(' ', '').replace(',', '.')
            text2 = other.text().replace(' ', '').replace(',', '.')
            
            return float(text1) < float(text2)
        except (ValueError, TypeError):
            return super().__lt__(other)