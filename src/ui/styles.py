DARK_QSS = """
    QMainWindow, QDialog, QWidget {
        background-color: #1b1c1d;
        color: #e0e0e0;
        font-family: 'Segoe UI', Arial;
        font-size: 13px;
    }
    QTabWidget::pane { border: 1px solid #333; background-color: #1b1c1d; }
    QTabBar::tab {
        background-color: #252526;
        color: #888;
        padding: 10px 25px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
    }
    QTabBar::tab:selected { background-color: #825fa2; color: white; font-weight: bold; }
    
    QLineEdit, QDoubleSpinBox, QDateEdit, QTextEdit {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #444;
        border-radius: 4px;
        padding: 6px;
    }
    QLineEdit:focus { border: 1px solid #825fa2; }
    
    QPushButton {
        background-color: #3d3d3d;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #4d4d4d; }
    
    QScrollBar:vertical { border: none; background: #1b1c1d; width: 10px; }
    QScrollBar::handle:vertical { background: #333; min-height: 20px; border-radius: 5px; }
    QScrollBar::handle:vertical:hover { background: #825fa2; }
"""

SEARCH_INPUT_STYLE = """
    QLineEdit { 
        background-color: #252526; 
        color: white; 
        border: 1px solid #3e3e42; 
        border-radius: 8px; 
        padding-left: 12px; 
        font-size: 13px;
    }
    QLineEdit:focus { border: 1px solid #825fa2; }
"""

SEARCH_INPUT_ACTIVE_STYLE = """
    QLineEdit {
        background-color: #2d2d2d;
        color: #e0e0e0;
        border: 2px solid #81c784;
        border-radius: 4px;
        padding: 0 10px;
        font-size: 13px;
    }
"""

COMBOBOX_STYLE = """
    QComboBox { 
        background-color: #1e1e1e; 
        border: 1px solid #444; 
        border-radius: 6px; 
        padding: 4px 8px; 
        padding-right: 20px; /* Miejsce na strzałkę */
        color: white; 
    }
    QComboBox:focus { border: 1px solid #825fa2; }
    
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left-width: 1px;
        border-left-color: #333;
        border-left-style: solid; /* Dodaje separator */
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
        background-color: #252526; /* Nieco jaśniejsze tło dla przycisku */
    }
    
    QComboBox::down-arrow {
        image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
        width: 14px;
        height: 14px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #1e1e1e;
        color: white;
        selection-background-color: #825fa2;
        border: 1px solid #444;
        outline: none;
    }
"""

ENTRY_FRAME_STYLE = """
    QFrame#EntryFrame { 
        background-color: #252526; 
        border: 1px solid #3e3e42; 
        border-radius: 12px; 
    }
    QLabel { 
        color: #aaa; 
        font-weight: 600; 
        font-size: 10px; 
        border: none; 
        margin-bottom: 2px;
        margin-top: 4px;
    }
    QDoubleSpinBox, QDateEdit, QComboBox, QLineEdit {
        background-color: #1e1e1e;
        border: 1px solid #444;
        border-radius: 6px;
        padding: 4px 8px;
        color: white;
        selection-background-color: #825fa2;
        min-height: 28px;
    }
    QComboBox::drop-down { border: none; }
    QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus, QLineEdit:focus {
        border: 1px solid #825fa2;
    }
"""

BTN_STANDARD_STYLE = """
    QPushButton { 
        background-color: #333333; 
        color: #ddd; 
        border: 1px solid #444; 
        border-radius: 8px; 
        font-weight: 600;
    }
    QPushButton:hover { background-color: #444; color: white; }
"""

BTN_PENDING_STYLE = """
    QPushButton { 
        background-color: #333333; 
        color: #ffd54f; 
        border: 1px solid #444; 
        border-radius: 8px; 
        font-weight: bold;
        font-size: 14px;
    }
    QPushButton:hover { background-color: #444; }
    QPushButton:checked { 
        background-color: #4a2d2d; 
        color: #e57373; 
        border: 1px solid #e57373; 
    }
"""

BTN_RECURRING_STYLE = """
    QPushButton { 
        background-color: #333333; 
        color: #81c784; 
        border: 1px solid #444; 
        border-radius: 8px; 
        font-weight: bold;
        font-size: 14px;
    }
    QPushButton:hover { background-color: #444; }
"""

BTN_ATTACH_STYLE = """
    QPushButton { background-color: #333; color: #aaa; border: 1px dashed #555; border-radius: 6px; font-weight: bold; }
    QPushButton:hover { background-color: #3a3a3a; color: white; border-color: #777; }
"""

BTN_ATTACH_ACTIVE_STYLE = """
    background-color: #1e3a2a; color: #4ade80; border: 1px solid #2ecc71; border-radius: 6px; font-weight: bold;
"""

BTN_ADD_ROW_STYLE = """
    QPushButton { 
        background-color: #825fa2; color: white; border-radius: 6px; font-weight: bold; font-size: 11px;
    }
    QPushButton:hover { background-color: #9a72bd; }
"""

BTN_ADD_EXPENSE = """
    QPushButton { 
        background-color: #6e2f2f;
        color: #e0e0e0; 
        border: 1px solid #8a3b3b;
        border-radius: 6px; 
        font-weight: bold; 
        font-size: 11px;
    }
    QPushButton:hover { 
        background-color: #853a3a; 
        border-color: #a64d4d;
        color: white;
    }
    QPushButton:pressed { background-color: #572525; margin-top: 1px; }
"""

BTN_ADD_INCOME = """
    QPushButton { 
        background-color: #2f5c35;
        color: #e0e0e0; 
        border: 1px solid #427a4a;
        border-radius: 6px; 
        font-weight: bold; 
        font-size: 11px;
    }
    QPushButton:hover { 
        background-color: #3c7044; 
        border-color: #559160;
        color: white;
    }
    QPushButton:pressed { background-color: #244729; margin-top: 1px; }
"""

BTN_ADD_TRANSFER = """
    QPushButton { 
        background-color: #2f486e;
        color: #e0e0e0; 
        border: 1px solid #40608f;
        border-radius: 6px; 
        font-weight: bold; 
        font-size: 11px;
    }
    QPushButton:hover { 
        background-color: #3d5a85; 
        border-color: #547aa6;
        color: white;
    }
    QPushButton:pressed { background-color: #243854; margin-top: 1px; }
"""

TABLE_STYLE = """
    QTableWidget {
        background-color: #1e1e1e;
        gridline-color: #333;
        border: none;
        selection-background-color: #2a2d3e;
        font-size: 12px;
    }
    QHeaderView::section {
        background-color: #252526;
        color: #aaa;
        padding: 6px;
        border: none;
        border-bottom: 2px solid #333;
        font-weight: bold;
    }
    QScrollBar:vertical {
        border: none;
        background: #1e1e1e;
        width: 10px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #444;
        min-height: 20px;
        border-radius: 5px;
    }
"""

LIST_WIDGET_STYLE = """
    QListWidget { background-color: #1b1c1d; border: 1px solid #333; border-radius: 8px; color: #e0e0e0; padding: 5px; }
    QListWidget::item { background: transparent; border-bottom: 1px solid #2a2a2a; }
"""

FRAME_CARD_STYLE = """
    QFrame { 
        background-color: #252526; 
        border-radius: 12px; 
        border: 1px solid #333; 
    }
"""

CHIP_FRAME_STYLE = """
    QFrame { 
        background-color: #2b2b2b; 
        border: 1px solid #3e3e3e; 
        border-radius: 17px; 
    }
    QFrame:hover { border-color: #666; background-color: #333; }
"""

GROUPBOX_STYLED = """
    QGroupBox { 
        color: #aaa; 
        font-weight: bold; 
        border: 1px solid #444; 
        border-radius: 8px; 
        margin-top: 20px; 
        padding-top: 15px;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
"""

SCROLL_TRANSPARENT_STYLE = "border: none; background-color: transparent;"
WIDGET_TRANSPARENT_STYLE = "background-color: transparent;"

# --- Labels & Text ---
LBL_TITLE_STYLE = "color: white; font-size: 18px; font-weight: bold; border: none; background: transparent;"
LBL_SUBTITLE_STYLE = "color: #888; font-size: 12px; border: none; background: transparent;"
LBL_SECTION_HEADER = "color: #999; font-weight: bold; font-size: 12px; text-transform: uppercase;"
INFO_LABEL_STYLE = "color: #ef5350; font-weight: bold; font-size: 11px; margin-left: 10px;"

SUMMARY_LABEL_TEMPLATE = """
    QLabel {{
        background-color: #2d2d2d;
        border: 1px solid {color};
        color: {color};
        border-radius: 4px;
        padding: 0 15px;
        font-weight: bold;
        font-size: 13px;
    }}
"""

BTN_CHIP_EDIT_STYLE = """
    QPushButton { 
        border: 1px solid #555;
        background-color: #383838;
        border-radius: 4px;
        color: #ddd; 
        font-weight: bold; 
        font-size: 12px;
        padding-bottom: 2px;
    } 
    QPushButton:hover { 
        background-color: #555;
        color: white; 
        border-color: #777;
    }
"""

BTN_CHIP_DELETE_STYLE = """
    QPushButton { 
        border: 1px solid #5a3030;
        background-color: #382020;
        border-radius: 4px;
        color: #ff6666; 
        font-weight: bold; 
        font-size: 11px;
        padding-bottom: 1px;
    } 
    QPushButton:hover { 
        background-color: #552525;
        color: #ff8888;
        border-color: #ff4444;
    }
"""

LBL_WALLET_ACTIVE = "color: #81c784; font-size: 13px; font-weight: bold; border: none; background: transparent;"
LBL_WALLET_INACTIVE = "color: #e0e0e0; font-size: 13px; border: none; background: transparent;"

BTN_WALLET_SET_DEFAULT = """
    QPushButton { background-color: #2d3a4a; color: #64b5f6; border: 1px solid #3a4a5a; border-radius: 4px; font-size: 10px; font-weight: bold; }
    QPushButton:hover { background-color: #3a4a5a; color: white; }
"""

BTN_WALLET_DELETE = """
    QPushButton { background-color: #331d2c; color: #ff8a80; border: 1px solid #4d2a2a; border-radius: 4px; font-size: 9px; font-weight: bold; }
    QPushButton:hover { background-color: #e74c3c; color: white; }
"""

GROUPBOX_BACKUP_STYLE = "QGroupBox { color: white; font-weight: bold; border: 1px solid #333; border-radius: 8px; margin-top: 10px; }"

BTN_BACKUP_DUMP = """
    QPushButton { background-color: #2c3e50; color: white; border-radius: 6px; font-weight: bold; }
    QPushButton:hover { background-color: #16a085; }
"""

BTN_BACKUP_RESTORE = """
    QPushButton { background-color: #c0392b; color: white; border-radius: 6px; font-weight: bold; }
    QPushButton:hover { background-color: #e74c3c; }
"""
BTN_INLINE_DELETE = """
    QPushButton { 
        color: #666; 
        background: transparent; 
        border-radius: 11px; 
        font-weight: bold; 
        border: none; 
    }
    QPushButton:hover { 
        color: #ff8a80; 
        background: #331d2c; 
    }
"""
BTN_PRIMARY_STYLE = """
    QPushButton {
        background-color: #825fa2;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        padding: 0 40px;
        border: none;
    }
    QPushButton:hover { background-color: #9374b3; }
"""

BTN_DISABLED_STYLE = """
    QPushButton {
        background-color: #4a4a4a;
        color: #888;
        border-radius: 6px;
        border: none;
    }
"""