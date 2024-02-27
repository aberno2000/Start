from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt

class CommandLineHistory(QLineEdit):
    def __init__(self, *args, **kwargs):
        super(CommandLineHistory, self).__init__(*args, **kwargs)
        self.history = []
        self.history_idx = -1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            if self.history_idx > 0:
                self.history_idx -= 1
                self.setText(self.history[self.history_idx])
            elif self.history:
                self.history_idx = 0
                self.setText(self.history[0])
        elif event.key() == Qt.Key_Down:
            if self.history_idx < len(self.history) - 1:
                self.history_idx += 1
                self.setText(self.history[self.history_idx])
            else:
                self.history_idx = len(self.history)
                self.clear()
        else:
            super().keyPressEvent(event)