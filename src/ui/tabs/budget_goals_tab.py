from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QFrame, QLabel, 
    QGridLayout, QDoubleSpinBox, QLineEdit, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from services.budget_service import BudgetService

class BudgetGoalsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.service = BudgetService()
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        header_layout = QVBoxLayout()
        title_lbl = QLabel("Cele Budżetowe (Tagi)")
        title_lbl.setStyleSheet("color: #825fa2; font-size: 22px; font-weight: bold;")
        subtitle_lbl = QLabel("Zdefiniuj miesięczne cele wydatków dla konkretnych tagów.")
        subtitle_lbl.setStyleSheet("color: #888; font-size: 12px;")
        header_layout.addWidget(title_lbl)
        header_layout.addWidget(subtitle_lbl)
        self.main_layout.addLayout(header_layout)

        self.form_frame = QFrame()
        self.form_frame.setStyleSheet("""
            QFrame { background-color: #252526; border-radius: 12px; border: 1px solid #333; }
            QLabel { color: #aaa; font-weight: bold; font-size: 11px; border: none; }
            QLineEdit, QDoubleSpinBox { 
                background-color: #1e1e1e; border: 1px solid #444; 
                border-radius: 6px; padding: 5px; color: white; min-height: 30px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus { border: 1px solid #825fa2; }
        """)
        
        form_layout = QHBoxLayout(self.form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Wpisz tag (np. paliwo)")
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999.99)
        self.amount_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.amount_input.setPrefix("PLN ")

        self.add_btn = QPushButton("USTAW CEL")
        self.add_btn.setFixedSize(120, 32)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet("""
            QPushButton { background-color: #825fa2; color: white; font-weight: bold; border-radius: 6px; }
            QPushButton:hover { background-color: #9a72bd; }
        """)
        self.add_btn.clicked.connect(self.handle_upsert_goal)

        form_layout.addWidget(QLabel("TAG:"))
        form_layout.addWidget(self.tag_input, 2)
        form_layout.addWidget(QLabel("MIESIĘCZNY CEL:"))
        form_layout.addWidget(self.amount_input, 1)
        form_layout.addWidget(self.add_btn)

        self.main_layout.addWidget(self.form_frame)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Tag", "Miesięczny Cel", "Akcje"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 100)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e; gridline-color: #333; border: none; font-size: 13px;
            }
            QHeaderView::section {
                background-color: #252526; color: #aaa; padding: 8px; border: none; font-weight: bold;
            }
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.main_layout.addWidget(self.table)

    def refresh_data(self):
        self.table.setRowCount(0)
        goals = self.service.get_budget_goals()
        
        self.table.setRowCount(len(goals))
        for row, goal in enumerate(goals):
            tag_item = QTableWidgetItem(goal.tag)
            tag_item.setForeground(QColor("#e0e0e0"))
            tag_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            amount_item = QTableWidgetItem(f"{goal.monthly_target_amount:,.2f} PLN")
            amount_item.setForeground(QColor("#81c784"))
            amount_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            del_btn = QPushButton("USUŃ")
            del_btn.setFixedSize(60, 27)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton { background-color: #331d2c; color: #ff8a80; border: 1px solid #4d2a2a; border-radius: 4px; font-size: 10px; font-weight: bold; }
                QPushButton:hover { background-color: #e74c3c; color: white; }
            """)
            del_btn.clicked.connect(lambda _, g_id=goal.id: self.handle_delete_goal(g_id))
            
            btn_layout.addWidget(del_btn)

            self.table.setItem(row, 0, tag_item)
            self.table.setItem(row, 1, amount_item)
            self.table.setCellWidget(row, 2, btn_widget)

    def handle_upsert_goal(self):
        tag = self.tag_input.text().strip()
        amount = self.amount_input.value()
        
        if not tag:
            QMessageBox.warning(self, "Błąd", "Podaj nazwę taga.")
            return

        if self.service.set_budget_goal(tag, amount):
            self.tag_input.clear()
            self.amount_input.setValue(0)
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Błąd", "Nie udało się zapisać celu.")

    def handle_delete_goal(self, goal_id):
        if QMessageBox.question(self, "Usuń", "Usunąć cel?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if self.service.delete_budget_goal(goal_id):
                self.refresh_data()