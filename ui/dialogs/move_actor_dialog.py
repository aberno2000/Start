from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox
)
from styles import *


class MoveActorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Move Actor")

        layout = QVBoxLayout(self)
        formLayout = QFormLayout()

        self.xOffsetInput = QLineEdit("0.0")
        self.yOffsetInput = QLineEdit("0.0")
        self.zOffsetInput = QLineEdit("0.0")

        self.xOffsetInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.yOffsetInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.zOffsetInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)

        formLayout.addRow("X Offset:", self.xOffsetInput)
        formLayout.addRow("Y Offset:", self.yOffsetInput)
        formLayout.addRow("Z Offset:", self.zOffsetInput)

        layout.addLayout(formLayout)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def getValues(self):
        try:
            x_offset = float(self.xOffsetInput.text())
            y_offset = float(self.yOffsetInput.text())
            z_offset = float(self.zOffsetInput.text())
            return x_offset, y_offset, z_offset
        except ValueError:
            QMessageBox.warning(self, "Invalid Input",
                                "Offsets must be valid numbers.")
            return None
