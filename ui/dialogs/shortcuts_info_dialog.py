from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QSizePolicy
)


class ShortcutsInfoDialog(QDialog):
    def __init__(self, shortcuts, parent=None):
        super().__init__(parent)
        self.shortcuts = shortcuts
        self.setWindowTitle("Keyboard Shortcuts")
        self.init_ui()

    def init_ui(self):
        self.setMinimumSize(700, 400)

        layout = QVBoxLayout(self)
        table = QTableWidget(len(self.shortcuts), 3)
        table.setHorizontalHeaderLabels(["Action", "Shortcut", "Description"])
        # Make the table read-only
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        for i, shortcut_info in enumerate(self.shortcuts):
            action, shortcut, description = shortcut_info
            table.setItem(i, 0, QTableWidgetItem(action))
            table.setItem(i, 1, QTableWidgetItem(shortcut))
            table.setItem(i, 2, QTableWidgetItem(description))

        table.resizeColumnsToContents()
        layout.addWidget(table)
