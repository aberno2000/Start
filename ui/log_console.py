from PyQt5.QtWidgets import (
    QVBoxLayout, QPlainTextEdit,
    QWidget, QDockWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCharFormat, QColor
    

class LogConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setup_ui()


    def setup_ui(self):
        self.log_console = QPlainTextEdit()
        self.log_console.setReadOnly(True)  # Make the console read-only

        self.log_dock_widget = QDockWidget("Log Console", self)
        self.log_dock_widget.setWidget(self.log_console)
        self.log_dock_widget.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.log_dock_widget.setVisible(True)


    def insert_colored_text(self, text: str, color: str):
        """
        Inserts colored text into a QPlainTextEdit widget.

        Parameters:
        - widget: QPlainTextEdit, the widget where the text will be inserted.
        - text: str, the text to insert.
        - color: str, the name of the color to use for the text.
        """
        cursor = self.log_console.textCursor()
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))
        cursor.mergeCharFormat(text_format)
        cursor.insertText(text, text_format)
        cursor.movePosition(cursor.End)
        self.log_console.setTextCursor(cursor)
        default_format = QTextCharFormat()
        cursor.mergeCharFormat(default_format)
