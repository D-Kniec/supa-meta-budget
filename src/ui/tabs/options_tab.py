import os
import json
import subprocess
from itertools import groupby
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, 
    QFrame, QHBoxLayout, QMessageBox, QListWidget, 
    QListWidgetItem, QAbstractItemView, QGroupBox,
    QFileDialog, QScrollArea, QSizePolicy, QLayout,
    QComboBox, QInputDialog, QColorDialog
)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QColor, QPixmap
from core.config import settings, BASE_DIR
from services.budget_service import BudgetService
from services.user_service import UserService
from ui.dialogs.add_wallet_dialog import AddWalletDialog
from ui.dialogs.add_category_dialog import AddCategoryDialog

from ui.styles import (
    COMBOBOX_STYLE, BTN_STANDARD_STYLE, BTN_ADD_ROW_STYLE,
    FRAME_CARD_STYLE, LBL_TITLE_STYLE, LBL_SUBTITLE_STYLE,
    SCROLL_TRANSPARENT_STYLE, WIDGET_TRANSPARENT_STYLE,
    GROUPBOX_STYLED, LIST_WIDGET_STYLE, CHIP_FRAME_STYLE,
    BTN_CHIP_EDIT_STYLE, BTN_CHIP_DELETE_STYLE,
    LBL_WALLET_ACTIVE, LBL_WALLET_INACTIVE,
    BTN_WALLET_SET_DEFAULT, BTN_WALLET_DELETE,
    GROUPBOX_BACKUP_STYLE, BTN_BACKUP_DUMP, BTN_BACKUP_RESTORE,
    LBL_SECTION_HEADER
)

USER_PREFS_FILE = os.path.join(BASE_DIR, "user_prefs.json")

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, h_spacing=10, v_spacing=10):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self._h_spacing

        for item in self._item_list:
            wid = item.widget()
            space_x = self.contentsMargins().left() + self.contentsMargins().right() + spacing
            space_y = self.contentsMargins().top() + self.contentsMargins().bottom() + self._v_spacing
            
            next_x = x + item.sizeHint().width() + space_x
            
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + self._v_spacing
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x - space_x + spacing
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()

class FlowContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        if self.layout():
            return self.layout().heightForWidth(width)
        return super().heightForWidth(width)
    
    def sizeHint(self):
        if self.layout():
            current_width = self.width() if self.width() > 0 else 400
            h = self.layout().heightForWidth(current_width)
            return QSize(current_width, h)
        return super().sizeHint()

    def resizeEvent(self, event):
        self.updateGeometry()
        super().resizeEvent(event)

class OptionsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.service = BudgetService()
        self.user_service = UserService()
        self.current_user_id = None
        self.init_ui()
        self.refresh_all()

    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        container_widget = QWidget()
        self.main_layout = QVBoxLayout(container_widget)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        top_bar.addStretch()
        
        lbl_user = QLabel("Użytkownik:")
        lbl_user.setStyleSheet("color: #aaa; font-weight: bold;")
        
        self.user_combo = QComboBox()
        self.user_combo.setFixedWidth(200)
        self.user_combo.setStyleSheet(COMBOBOX_STYLE)
        self.user_combo.currentIndexChanged.connect(self._on_user_changed)

        self.refresh_btn = QPushButton("↻ Odśwież dane")
        self.refresh_btn.setFixedSize(140, 30)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet(BTN_STANDARD_STYLE)
        self.refresh_btn.clicked.connect(self.refresh_all)
        
        top_bar.addWidget(lbl_user)
        top_bar.addWidget(self.user_combo)
        top_bar.addWidget(self.refresh_btn)
        
        self.main_layout.addLayout(top_bar)

        self.cats_container = QFrame()
        self.cats_container.setStyleSheet(FRAME_CARD_STYLE)
        self.cats_layout = QVBoxLayout(self.cats_container)
        self.cats_layout.setContentsMargins(20, 20, 20, 20)
        
        cat_header = QHBoxLayout()
        cat_title_layout = QVBoxLayout()
        t_lbl = QLabel("Hierarchia Kategorii")
        t_lbl.setStyleSheet(LBL_TITLE_STYLE)
        s_lbl = QLabel("Definiuj typy, grupy i podkategorie.")
        s_lbl.setStyleSheet(LBL_SUBTITLE_STYLE)
        cat_title_layout.addWidget(t_lbl)
        cat_title_layout.addWidget(s_lbl)
        
        add_cat_btn = QPushButton("+ NOWA KATEGORIA")
        add_cat_btn.setFixedSize(160, 38)
        add_cat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_cat_btn.setStyleSheet(BTN_ADD_ROW_STYLE)
        add_cat_btn.clicked.connect(self.open_category_dialog)
        
        cat_header.addLayout(cat_title_layout)
        cat_header.addStretch()
        cat_header.addWidget(add_cat_btn)
        self.cats_layout.addLayout(cat_header)

        cats_scroll = QScrollArea()
        cats_scroll.setWidgetResizable(True)
        cats_scroll.setStyleSheet(SCROLL_TRANSPARENT_STYLE)
        
        self.cats_scroll_content = QWidget()
        self.cats_scroll_content.setStyleSheet(WIDGET_TRANSPARENT_STYLE)
        self.cats_scroll_layout = QVBoxLayout(self.cats_scroll_content)
        self.cats_scroll_layout.setSpacing(20)

        self.income_group = self.create_category_group("PRZYCHODY (INCOME)")
        self.expense_group = self.create_category_group("WYDATKI (EXPENSE)")
        self.transfer_group = self.create_category_group("TRANSFERY (TRANSFER)")

        self.cats_scroll_layout.addWidget(self.income_group)
        self.cats_scroll_layout.addWidget(self.expense_group)
        self.cats_scroll_layout.addWidget(self.transfer_group)
        self.cats_scroll_layout.addStretch()

        cats_scroll.setWidget(self.cats_scroll_content)
        cats_scroll.setMinimumHeight(350) 
        self.cats_layout.addWidget(cats_scroll)

        self.main_layout.addWidget(self.cats_container)

        self.users_card = self.create_users_card()
        self.main_layout.addWidget(self.users_card)

        self.wallet_card = self.create_list_card(
            title="Zarządzanie Portfelami",
            subtitle="Domyślny portfel zależy od wybranego powyżej użytkownika.",
            btn_text="+ DODAJ PORTFEL",
            btn_callback=self.open_wallet_dialog
        )
        self.wallet_list = self.wallet_card.findChild(QListWidget)
        self.main_layout.addWidget(self.wallet_card)

        self.backup_group = self.create_backup_section()
        self.main_layout.addWidget(self.backup_group)

        scroll_area.setWidget(container_widget)
        outer_layout.addWidget(scroll_area)

    def create_users_card(self):
        card = QFrame()
        card.setStyleSheet(FRAME_CARD_STYLE)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        h_layout = QHBoxLayout()
        title = QLabel("Mapowanie Użytkowników")
        title.setStyleSheet(LBL_TITLE_STYLE)
        
        scan_btn = QPushButton("🔍 SKANUJ Z BAZY")
        scan_btn.setFixedSize(170, 30)
        scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scan_btn.setStyleSheet(BTN_STANDARD_STYLE)
        scan_btn.clicked.connect(self.handle_scan_users)

        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(scan_btn)
        layout.addLayout(h_layout)

        self.users_list_widget = QListWidget()
        self.users_list_widget.setStyleSheet(LIST_WIDGET_STYLE)
        self.users_list_widget.setFixedHeight(150)
        layout.addWidget(self.users_list_widget)

        return card

    def create_category_group(self, title):
        group = QGroupBox(title)
        group.setStyleSheet(GROUPBOX_STYLED)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(15)
        group.setLayout(layout)
        return group

    def create_list_card(self, title, subtitle, btn_text, btn_callback):
        card = QFrame()
        card.setStyleSheet(FRAME_CARD_STYLE)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        header_layout = QHBoxLayout()
        text_layout = QVBoxLayout()
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(LBL_TITLE_STYLE)
        
        s_lbl = QLabel(subtitle)
        s_lbl.setStyleSheet(LBL_SUBTITLE_STYLE)
        
        text_layout.addWidget(t_lbl)
        text_layout.addWidget(s_lbl)
        
        btn = QPushButton(btn_text)
        btn.setFixedSize(160, 38)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(BTN_ADD_ROW_STYLE)
        btn.clicked.connect(btn_callback)
        
        header_layout.addLayout(text_layout)
        header_layout.addStretch()
        header_layout.addWidget(btn)
        layout.addLayout(header_layout)

        list_widget = QListWidget()
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        list_widget.setFixedHeight(180)
        list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        list_widget.setStyleSheet(LIST_WIDGET_STYLE)
        layout.addWidget(list_widget)
        
        return card

    def refresh_user_combo(self):
        self.user_combo.blockSignals(True)
        self.user_combo.clear()
        
        users_map = self.user_service.get_users()
        
        saved_active_id = None
        if os.path.exists(USER_PREFS_FILE):
            try:
                with open(USER_PREFS_FILE, 'r') as f:
                    prefs = json.load(f)
                    saved_active_id = prefs.get('active_user_id')
            except Exception:
                pass
        
        if saved_active_id:
            self.user_service.set_active_user_id(str(saved_active_id))
            active_id = str(saved_active_id)
        else:
            active_id = self.user_service.get_active_user_id()
        
        idx_to_select = 0
        current_idx = 0
        
        for uid, alias in users_map.items():
            self.user_combo.addItem(alias, uid)
            if str(uid) == str(active_id):
                idx_to_select = current_idx
            current_idx += 1
            
        self.user_combo.setCurrentIndex(idx_to_select)
        self.current_user_id = self.user_combo.currentData()
        self.user_combo.blockSignals(False)

    def refresh_users_list(self):
        self.users_list_widget.clear()
        users_map = self.user_service.get_users()

        for uid, alias in users_map.items():
            item = QListWidgetItem(self.users_list_widget)
            
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(5, 5, 5, 5)
            
            user_color = self.user_service.get_user_color(uid)
            color_pix = QPixmap(10, 10)
            color_pix.fill(QColor(user_color))
            
            color_lbl = QLabel()
            color_lbl.setPixmap(color_pix)
            color_lbl.setFixedSize(10, 10)
            
            lbl_name = QLabel(f"{alias}")
            lbl_name.setStyleSheet(f"color: {user_color}; font-weight: bold; font-size: 14px;")
            
            lbl_uuid = QLabel(f"({uid})")
            lbl_uuid.setStyleSheet("color: #666; font-size: 11px;")
            
            btn_rename = QPushButton("ZMIEŃ NAZWĘ")
            btn_rename.setFixedSize(150, 24)
            btn_rename.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_rename.setStyleSheet(BTN_CHIP_EDIT_STYLE)
            btn_rename.clicked.connect(lambda checked, u=uid, a=alias: self.open_rename_dialog(u, a))

            btn_color = QPushButton("KOLOR")
            btn_color.setFixedSize(120, 24)
            btn_color.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_color.setStyleSheet(BTN_CHIP_EDIT_STYLE)
            btn_color.clicked.connect(lambda checked, u=uid: self.pick_user_color(u))

            l.addWidget(color_lbl)
            l.addWidget(lbl_name)
            l.addWidget(lbl_uuid)
            l.addStretch()
            l.addWidget(btn_color)
            l.addWidget(btn_rename)
            
            item.setSizeHint(w.sizeHint())
            self.users_list_widget.setItemWidget(item, w)

    def pick_user_color(self, uid):
        color = QColorDialog.getColor()
        if color.isValid():
            self.user_service.set_user_color(uid, color.name())
            self.refresh_users_list()

    def create_category_chip(self, category_obj):
        chip = QFrame()
        chip.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        chip.setMinimumHeight(34) 
        chip.setStyleSheet(CHIP_FRAME_STYLE)
        
        layout = QHBoxLayout(chip)
        layout.setContentsMargins(10, 4, 6, 4) 
        layout.setSpacing(6)

        pix = QPixmap(8, 8) 
        pix.fill(QColor(category_obj.color_hex or "#825fa2"))
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(pix)
        icon_lbl.setFixedSize(8, 8) 
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) 
        icon_lbl.setStyleSheet("border: none; background: transparent;")

        name_lbl = QLabel(category_obj.subcategory)
        name_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) 
        name_lbl.setStyleSheet("color: #e0e0e0; font-size: 13px; border: none; background: transparent; font-weight: 500;")
        
        layout.addWidget(icon_lbl)
        layout.addWidget(name_lbl)
        layout.addStretch() 

        edit_btn = QPushButton("✎")
        edit_btn.setFixedSize(16, 16) 
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setToolTip("Edytuj")
        edit_btn.setStyleSheet(BTN_CHIP_EDIT_STYLE)
        edit_btn.clicked.connect(lambda checked, c=category_obj: self.open_edit_category_dialog(c))

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(16, 16)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setToolTip("Usuń")
        del_btn.setStyleSheet(BTN_CHIP_DELETE_STYLE)
        del_btn.clicked.connect(lambda checked, cid=category_obj.subcategory_id: self.handle_delete_category(cid))

        layout.addWidget(edit_btn)
        layout.addWidget(del_btn)

        chip.show()
        return chip

    def create_wallet_item_widget(self, w):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 5, 10, 5)

        current_combo_user = self.user_combo.currentData()
        default_for_current = self.user_service.get_default_wallet_id(user_id=current_combo_user)
        
        is_default = (str(w.id) == str(default_for_current))
        
        icon_text = "⭐" if is_default else "💳"
        icon_lbl = QLabel(icon_text)
        icon_lbl.setStyleSheet("font-size: 14px; border: none; background: transparent;")
        
        users_map = self.user_service.get_users()
        owner_alias = users_map.get(str(w.owner_name), str(w.owner_name))
        
        name_text = f"{w.wallet_name}  ({owner_alias})"
        if is_default:
            name_text += " [DOMYŚLNY]"
            
        txt_lbl = QLabel(name_text)
        if is_default:
            txt_lbl.setStyleSheet(LBL_WALLET_ACTIVE)
        else:
            txt_lbl.setStyleSheet(LBL_WALLET_INACTIVE)
        
        layout.addWidget(icon_lbl)
        layout.addWidget(txt_lbl)
        layout.addStretch()

        if not is_default:
            def_btn = QPushButton("USTAW JAKO DOMYŚLNY")
            def_btn.setFixedSize(180, 26)
            def_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            def_btn.setStyleSheet(BTN_WALLET_SET_DEFAULT)
            def_btn.clicked.connect(lambda checked, wid=w.id: self._save_default_wallet_id(wid))
            layout.addWidget(def_btn)

        del_btn = QPushButton("USUŃ")
        del_btn.setFixedSize(65, 26)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(BTN_WALLET_DELETE)
        del_btn.clicked.connect(lambda checked, wid=w.id: self.handle_delete_wallet(wid))

        layout.addWidget(del_btn)
        
        return container

    def create_backup_section(self):
        group_box = QGroupBox("Metabase Config Backup & Restore")
        group_box.setStyleSheet(GROUPBOX_BACKUP_STYLE)
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        info_lbl = QLabel("Zarządzaj konfiguracją Metabase:")
        info_lbl.setStyleSheet("color: #aaa; border: none;")
        layout.addWidget(info_lbl)
        layout.addStretch()

        btn_dump = QPushButton("💾 Pobierz Backup")
        btn_dump.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_dump.clicked.connect(self.perform_metabase_dump)
        btn_dump.setFixedSize(150, 40)
        btn_dump.setStyleSheet(BTN_BACKUP_DUMP)
        layout.addWidget(btn_dump)

        btn_restore = QPushButton("♻️ Wgraj Backup")
        btn_restore.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_restore.clicked.connect(self.perform_metabase_restore)
        btn_restore.setFixedSize(150, 40)
        btn_restore.setStyleSheet(BTN_BACKUP_RESTORE)
        layout.addWidget(btn_restore)
        
        group_box.setLayout(layout)
        return group_box

    def refresh_all(self):
        self.service.reload_cache()
        self.refresh_users_list()
        self.refresh_user_combo()
        self.refresh_wallet_list()
        self.refresh_category_flow()

    def refresh_wallet_list(self):
        self.wallet_list.clear()
        wallets = self.service.get_wallets_for_combo()
        
        current_combo_user = self.user_combo.currentData()
        default_for_current = self.user_service.get_default_wallet_id(user_id=current_combo_user)
        
        wallets.sort(key=lambda x: 0 if str(x.id) == str(default_for_current) else 1)

        for w in wallets:
            item = QListWidgetItem(self.wallet_list)
            widget = self.create_wallet_item_widget(w)
            item.setSizeHint(widget.sizeHint())
            self.wallet_list.addItem(item)
            self.wallet_list.setItemWidget(item, widget)

    def _clear_layout(self, layout):
        if not layout: return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def refresh_category_flow(self):
        self._clear_layout(self.income_group.layout())
        self._clear_layout(self.expense_group.layout())
        self._clear_layout(self.transfer_group.layout())

        categories = self.service.get_categories_for_combo()
        sorted_cats = sorted(categories, key=lambda x: (x.type, x.category, x.subcategory))
        
        def fill_group_container(target_group_widget, type_key):
            main_layout = target_group_widget.layout()
            
            type_cats = [c for c in sorted_cats if c.type == type_key]
            if not type_cats:
                return

            for parent_cat, subcats_iter in groupby(type_cats, key=lambda x: x.category):
                subcats = list(subcats_iter)
                
                cat_block = QWidget()
                cat_block_layout = QVBoxLayout(cat_block)
                cat_block_layout.setContentsMargins(0, 0, 0, 10) 
                cat_block_layout.setSpacing(5)

                lbl_header = QLabel(parent_cat)
                lbl_header.setStyleSheet(LBL_SECTION_HEADER)
                cat_block_layout.addWidget(lbl_header)

                chips_container = FlowContainer()
                chips_layout = FlowLayout(chips_container, margin=0, h_spacing=8, v_spacing=8)
                
                for c in subcats:
                    chip = self.create_category_chip(c)
                    chip.setParent(chips_container)
                    chips_layout.addWidget(chip)
                
                cat_block_layout.addWidget(chips_container)
                main_layout.addWidget(cat_block)

            main_layout.addStretch()

        fill_group_container(self.income_group, "INCOME")
        fill_group_container(self.expense_group, "EXPENSE")
        fill_group_container(self.transfer_group, "TRANSFER")

    def handle_delete_wallet(self, wallet_id):
        msg = QMessageBox(self)
        msg.setWindowTitle("Usuwanie Portfela")
        msg.setText("Ten portfel może posiadać transakcje.")
        btn_cascade = msg.addButton("Usuń wszystko", QMessageBox.ButtonRole.DestructiveRole)
        btn_only = msg.addButton("Tylko portfel", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Anuluj", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        if msg.clickedButton() == btn_cascade:
            if self.service.delete_wallet(wallet_id, cascade=True): self.refresh_wallet_list()
        elif msg.clickedButton() == btn_only:
            if self.service.delete_wallet(wallet_id, cascade=False): self.refresh_wallet_list()
            else: QMessageBox.warning(self, "Błąd", "Nie można usunąć portfela z transakcjami.")

    def handle_delete_category(self, subcat_id):
        msg = QMessageBox(self)
        msg.setWindowTitle("Usuwanie Kategorii")
        msg.setText("Czy usunąć tę podkategorię?")
        btn_cascade = msg.addButton("Usuń z transakcjami", QMessageBox.ButtonRole.DestructiveRole)
        btn_only = msg.addButton("Tylko kategorię", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Anuluj", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        if msg.clickedButton() == btn_cascade:
            if self.service.delete_category(subcat_id, cascade=True): self.refresh_category_flow()
        elif msg.clickedButton() == btn_only:
            if self.service.delete_category(subcat_id, cascade=False): self.refresh_category_flow()
            else: QMessageBox.warning(self, "Błąd", "Kategoria używana.")

    def open_wallet_dialog(self):
        active_uid = self.user_combo.currentData()
        
        if not active_uid:
            QMessageBox.warning(self, "Błąd", "Musisz najpierw wybrać (lub zeskanować) użytkownika, aby dodać portfel.")
            return

        dialog = AddWalletDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if self.service.add_wallet(data["name"], str(active_uid)): 
                self.refresh_wallet_list()
            else:
                QMessageBox.warning(self, "Błąd", "Nie udało się dodać portfela (błąd bazy lub walidacji).")

    def open_category_dialog(self):
        # PRZEKAZUJEMY ISTNIEJĄCY SERWIS (self.service)
        dialog = AddCategoryDialog(self.service, self)
        if dialog.exec():
            data = dialog.get_data()
            if self.service.add_category(data["category"], data["subcategory"], data["type"], data["color"]): 
                self.refresh_all()

    def open_edit_category_dialog(self, category_obj):
        # PRZEKAZUJEMY ISTNIEJĄCY SERWIS (self.service)
        dialog = AddCategoryDialog(self.service, self, edit_mode=True)
        dialog.set_data(category_obj)
        if dialog.exec():
            data = dialog.get_data()
            if self.service.update_category(category_obj.subcategory_id, data["category"], data["subcategory"], data["type"], data["color"]):
                self.refresh_all()

    def _save_default_wallet_id(self, wallet_id):
        current_uid = self.user_combo.currentData()
        if not current_uid:
             QMessageBox.warning(self, "Błąd", "Brak wybranego użytkownika.")
             return

        self.user_service.set_default_wallet_id(str(wallet_id), user_id=str(current_uid))
        self.refresh_wallet_list()
        QMessageBox.information(self, "Sukces", "Domyślny portfel dla tego użytkownika został zapisany.")

    def _on_user_changed(self, index):
        user_id = self.user_combo.currentData()
        if user_id:
            self.user_service.set_active_user_id(str(user_id))
            
            try:
                prefs = {}
                if os.path.exists(USER_PREFS_FILE):
                    try:
                        with open(USER_PREFS_FILE, 'r') as f:
                            prefs = json.load(f)
                    except Exception:
                        prefs = {}
                
                prefs['active_user_id'] = str(user_id)
                
                with open(USER_PREFS_FILE, 'w') as f:
                    json.dump(prefs, f)
            except Exception as e:
                print(f"Błąd zapisu preferencji: {e}")
            
            self.refresh_wallet_list()

    def handle_scan_users(self):
        db_uuids = self.service.get_unique_authors()
        self.user_service.register_discovered_users(db_uuids)
        self.refresh_users_list()
        self.refresh_user_combo()
        QMessageBox.information(self, "Skanowanie", "Zaktualizowano listę użytkowników na podstawie historii transakcji.")

    def open_rename_dialog(self, uid, current_alias):
        new_name, ok = QInputDialog.getText(self, "Zmiana Nazwy", f"Podaj alias dla ID {uid}:", text=current_alias)
        if ok and new_name:
            self.user_service.rename_user(uid, new_name)
            self.refresh_users_list()
            self.refresh_user_combo()

    def perform_metabase_dump(self):
        dump_dir = os.path.join(BASE_DIR, "docker", "metabase")
        target_file = os.path.join(dump_dir, "metabase_config_dump.sql")
        internal_tmp_file = "/tmp/temp_metabase_backup.sql"
        container_name = "mb-app-db"

        try:
            os.makedirs(dump_dir, exist_ok=True)
        except PermissionError:
            QMessageBox.critical(self, "Błąd", f"Brak uprawnień do folderu:\n{dump_dir}")
            return

        if not settings.MB_DB_PASS:
            QMessageBox.critical(self, "Błąd", "Brak hasła MB_DB_PASS w .env")
            return

        cmd_dump = (
            f"docker exec -e PGPASSWORD={settings.MB_DB_PASS} {container_name} "
            f"pg_dump -U {settings.MB_DB_USER} -d {settings.MB_DB_NAME} "
            f"--clean --if-exists --no-owner --no-acl -f {internal_tmp_file}"
        )
        cmd_cp = f"docker cp {container_name}:{internal_tmp_file} \"{target_file}\""

        try:
            subprocess.run(cmd_dump, shell=True, check=True, capture_output=True, text=True)
            subprocess.run(cmd_cp, shell=True, check=True, capture_output=True, text=True)
            QMessageBox.information(self, "Sukces", f"Zapisano backup:\n{target_file}")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else e.stdout
            if not error_msg: error_msg = "Nieznany błąd."
            QMessageBox.critical(self, "Błąd Dockera", f"Operacja nie powiodła się:\n\n{error_msg}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił nieoczekiwany błąd:\n{str(e)}")

    def perform_metabase_restore(self):
        default_dir = os.path.join(BASE_DIR, "docker", "metabase")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik backupu", default_dir, "SQL Files (*.sql);;All Files (*)"
        )
        
        if not file_path:
            return

        reply = QMessageBox.warning(
            self, "Potwierdzenie", 
            "UWAGA: Ta operacja NADPISZE całą konfigurację Metabase (wykresy, pytania).\n"
            "Czy na pewno chcesz kontynuować?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        if not settings.MB_DB_PASS:
            QMessageBox.critical(self, "Błąd", "Brak hasła MB_DB_PASS w .env")
            return

        db_container = "mb-app-db"
        app_container = "supa-meta-budget-analytics" 
        internal_restore_file = "/tmp/restore_source.sql"

        cmd_stop_app = f"docker stop {app_container}"
        cmd_cp = f"docker cp \"{file_path}\" {db_container}:{internal_restore_file}"
        cmd_restore = (
            f"docker exec -e PGPASSWORD={settings.MB_DB_PASS} {db_container} "
            f"psql -U {settings.MB_DB_USER} -d {settings.MB_DB_NAME} "
            f"-f {internal_restore_file}"
        )
        cmd_start_app = f"docker start {app_container}"

        try:
            subprocess.run(cmd_stop_app, shell=True, check=True, capture_output=True)
            subprocess.run(cmd_cp, shell=True, check=True, capture_output=True)
            subprocess.run(cmd_restore, shell=True, check=True, capture_output=True, text=True)
            subprocess.run(cmd_start_app, shell=True, check=True, capture_output=True)
            QMessageBox.information(self, "Sukces", "Pomyślnie przywrócono konfigurację Metabase.\nAplikacja uruchamia się ponownie (może to zająć chwilę).")

        except subprocess.CalledProcessError as e:
            subprocess.run(cmd_start_app, shell=True, capture_output=True)
            error_msg = e.stderr if e.stderr else e.stdout
            if not error_msg: error_msg = "Nieznany błąd procesu."
            QMessageBox.critical(self, "Błąd Przywracania", f"Wystąpił błąd:\n\n{error_msg}\n\nMetabase został zrestartowany.")
        except Exception as e:
             QMessageBox.critical(self, "Błąd", f"Wystąpił nieoczekiwany błąd:\n{str(e)}")