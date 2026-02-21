from PyQt6.QtWidgets import (
    QStyledItemDelegate, QComboBox, QDoubleSpinBox, QAbstractSpinBox,
    QStyleOptionViewItem, QStyle, QDateEdit
)
from PyQt6.QtCore import Qt, QDate, QRectF, QEvent
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QPainterPath
from models.transaction import TransactionType, TransactionStatus, TransactionSentiment

class StatusBadgeDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        text = index.data(Qt.ItemDataRole.DisplayRole)
        
        bg_color = QColor("#333333")
        text_color = QColor("#ffffff")
        
        if text == "INCOME":
            bg_color = QColor("#2d4a3e")
            text_color = QColor("#81c784")
        elif text == "EXPENSE":
            bg_color = QColor("#4a2d2d")
            text_color = QColor("#e57373")
        elif text == "TRANSFER":
            bg_color = QColor("#2d3a4a")
            text_color = QColor("#64b5f6")
        elif text == "COMPLETED":
            bg_color = QColor("#2d4a3e")
            text_color = QColor("#81c784")
        elif text == "PENDING":
            bg_color = QColor("#4a402d")
            text_color = QColor("#ffd54f")
        
        rect = QRectF(option.rect)
        rect.adjust(5, 5, -5, -5)
        
        path = QPainterPath()
        path.addRoundedRect(rect, 6, 6)
        
        if option.state & QStyle.StateFlag.State_Selected:
             painter.fillRect(option.rect, QColor("#2a2d3e"))

        bg_brush = QColor(bg_color)
        bg_brush.setAlphaF(0.4) 
        painter.fillPath(path, QBrush(bg_brush))
        
        pen_color = QColor(text_color)
        pen_color.setAlphaF(0.5)
        pen = QPen(pen_color)
        pen.setWidthF(0.5)
        painter.setPen(pen)
        painter.drawPath(path)

        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        
        painter.restore()

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        if index.column() == 0:
             editor.addItems([t.value for t in TransactionType])
        elif index.column() == 1:
             editor.addItems([s.value for s in TransactionStatus])
        return editor

    def setEditorData(self, editor, index):
        editor.setCurrentText(str(index.data(Qt.ItemDataRole.EditRole)))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

class BooleanIconDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#2a2d3e"))
            
        value = index.data(Qt.ItemDataRole.DisplayRole)
        is_yes = (value == "Tak")
        
        rect = QRectF(option.rect)
        center = rect.center()
        
        size = 16
        icon_rect = QRectF(center.x() - size/2, center.y() - size/2, size, size)
        
        path = QPainterPath()
        pen = QPen()
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        if is_yes:
            pen.setColor(QColor("#66bb6a"))
            path.moveTo(icon_rect.left(), icon_rect.center().y())
            path.lineTo(icon_rect.left() + size * 0.4, icon_rect.bottom() - size * 0.2)
            path.lineTo(icon_rect.right(), icon_rect.top())
        else:
            pen.setColor(QColor("#ef5350"))
            path.moveTo(icon_rect.left(), icon_rect.top())
            path.lineTo(icon_rect.right(), icon_rect.bottom())
            path.moveTo(icon_rect.right(), icon_rect.top())
            path.lineTo(icon_rect.left(), icon_rect.bottom())
            
        painter.setPen(pen)
        painter.drawPath(path)
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease:
            current_val = index.data(Qt.ItemDataRole.EditRole)
            new_val = "Nie" if current_val == "Tak" else "Tak"
            model.setData(index, new_val, Qt.ItemDataRole.EditRole)
            return True
        return False

class AmountDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QDoubleSpinBox(parent)
        editor.setFrame(False)
        editor.setRange(0, 999999.99)
        editor.setDecimals(2)
        editor.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        return editor

    def setEditorData(self, editor, index):
        val_str = index.model().data(index, Qt.ItemDataRole.EditRole)
        try:
            val = float(str(val_str).replace(',', '.'))
            editor.setValue(val)
        except ValueError:
            editor.setValue(0.00)

    def setModelData(self, editor, model, index):
        value = editor.value()
        model.setData(index, f"{value:.2f}", Qt.ItemDataRole.EditRole)
    
    def paint(self, painter, option, index):
        option.displayAlignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        super().paint(painter, option, index)

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.items)
        return editor

    def setEditorData(self, editor, index):
        editor.setCurrentText(str(index.data(Qt.ItemDataRole.EditRole)))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

class TagDelegate(QStyledItemDelegate):
    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.setEditable(True)
        if hasattr(self.service, 'get_unique_tags'):
            editor.addItems(self.service.get_unique_tags())
        return editor

    def setEditorData(self, editor, index):
        text = index.data(Qt.ItemDataRole.EditRole) or index.data(Qt.ItemDataRole.DisplayRole)
        editor.setCurrentText(str(text) if text else "")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

class FilteredCategoryDelegate(QStyledItemDelegate):
    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service

    def createEditor(self, parent, option, index):
        type_idx = index.siblingAtColumn(0)
        current_type = type_idx.data(Qt.ItemDataRole.DisplayRole)
        
        try:
            categories = self.service.get_categories_by_type(current_type)
        except AttributeError:
            categories = self.service.get_unique_categories()

        editor = QComboBox(parent)
        editor.addItems(categories)
        return editor

    def setEditorData(self, editor, index):
        editor.setCurrentText(str(index.data(Qt.ItemDataRole.EditRole)))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

class SubcategoryDelegate(QStyledItemDelegate):
    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service

    def createEditor(self, parent, option, index):
        row = index.row()
        category_item = index.model().index(row, 5)
        category_name = category_item.data(Qt.ItemDataRole.DisplayRole)
        editor = QComboBox(parent)
        if category_name and category_name != "-":
            subs = self.service.get_subcategories_by_category(category_name)
            editor.addItems([s["name"] for s in subs])
        return editor

    def setEditorData(self, editor, index):
        editor.setCurrentText(str(index.data(Qt.ItemDataRole.EditRole)))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

class DateDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("yyyy-MM-dd")
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        
        if not value:
             value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        
        if isinstance(value, QDate):
            editor.setDate(value)
        elif isinstance(value, str):
            d = QDate.fromString(value, "yyyy-MM-dd")
            if d.isValid():
                editor.setDate(d)
            else:
                editor.setDate(QDate.currentDate())
        else:
            editor.setDate(QDate.currentDate())

    def setModelData(self, editor, model, index):
        editor.interpretText()
        date_val = editor.date()
        date_str = date_val.toString("yyyy-MM-dd")
        model.setData(index, date_str, Qt.ItemDataRole.EditRole)
        model.setData(index, date_str, Qt.ItemDataRole.DisplayRole)