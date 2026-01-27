from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument
from html import escape
import re

class HighlightDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, original_delegate=None):
        super().__init__(parent)
        self.search_query = ""
        self.neon_color = "#69f0ae" 
        self.original_delegate = original_delegate

    def setSearchQuery(self, query):
        self.search_query = query

    def paint(self, painter, option, index):
        text = index.data(Qt.ItemDataRole.DisplayRole)
        
        should_highlight = (text and self.search_query and 
                            self.search_query.lower() in text.lower())
        
        if not should_highlight:
            if self.original_delegate:
                self.original_delegate.paint(painter, option, index)
            else:
                super().paint(painter, option, index)
            return

        escaped_text = escape(text)
        escaped_query = escape(self.search_query)
        pattern = re.compile(re.escape(escaped_query), re.IGNORECASE)
        
        highlighted_html = pattern.sub(
            lambda m: f'<span style="color: {self.neon_color}; font-weight: bold; text-shadow: 0 0 5px {self.neon_color}, 0 0 15px {self.neon_color};">{m.group(0)}</span>',
            escaped_text
        )

        painter.save()
        
        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        text_color = option.palette.text().color().name()
        doc.setDefaultStyleSheet(f"body {{ color: {text_color}; }}")
        doc.setHtml(highlighted_html)

        align = option.displayAlignment
        rect = option.rect
        doc_height = doc.size().height()
        y_offset = (rect.height() - doc_height) / 2
        translate_x = rect.left()
        translate_y = rect.top()

        if align & Qt.AlignmentFlag.AlignVCenter:
            translate_y += y_offset

        if align & Qt.AlignmentFlag.AlignRight:
            translate_x = rect.right() - doc.idealWidth()
        elif align & Qt.AlignmentFlag.AlignHCenter:
             translate_x = rect.left() + (rect.width() - doc.idealWidth()) / 2
        
        painter.translate(translate_x, translate_y)
        doc.drawContents(painter)
        painter.restore()

    def createEditor(self, parent, option, index):
        if self.original_delegate:
            return self.original_delegate.createEditor(parent, option, index)
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if self.original_delegate:
            self.original_delegate.setEditorData(editor, index)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if self.original_delegate:
            self.original_delegate.setModelData(editor, model, index)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        if self.original_delegate:
            self.original_delegate.updateEditorGeometry(editor, option, index)
        else:
            super().updateEditorGeometry(editor, option, index)