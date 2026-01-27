from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from ui.tabs.budget_tab import BudgetTab
from ui.tabs.options_tab import OptionsTab
from ui.tabs.analytics_tab import AnalyticsTab
from ui.tabs.budget_goals_tab import BudgetGoalsTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("SupaMetaBudget | Private Finance")
        self.resize(1720, 850)

        self.tabs = QTabWidget()
        
        self.budget_tab = BudgetTab()

        self.analytics_tab = AnalyticsTab() 
        self.goals_tab = BudgetGoalsTab()
        self.options_tab = OptionsTab()

        self.tabs.addTab(self.budget_tab, "Budżet")

        self.tabs.addTab(self.analytics_tab, "Metabase") 
        self.tabs.addTab(self.goals_tab, "Cele Budżetowe")
        self.tabs.addTab(self.options_tab, "Opcje")

        self.setCentralWidget(self.tabs)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 
            "Wyjście", 
            "Czy na pewno chcesz zamknąć aplikację?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()