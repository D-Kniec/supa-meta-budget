import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ui.main_window import MainWindow
from ui.styles import DARK_QSS

def main():
    app = QApplication(sys.argv)
    
    app.setStyleSheet(DARK_QSS)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()