from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox
)
from styles import *
from util import is_real_number


class PointDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Create Point")

        # Create layout
        layout = QVBoxLayout(self)

        # Create form layout for input fields
        formLayout = QFormLayout()

        # Input fields for the sphere parameters
        self.xInput = QLineEdit("0.0")
        self.yInput = QLineEdit("0.0")
        self.zInput = QLineEdit("0.0")

        self.xInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.yInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.zInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)

        formLayout.addRow("Center X:", self.xInput)
        formLayout.addRow("Center Y:", self.yInput)
        formLayout.addRow("Center Z:", self.zInput)

        layout.addLayout(formLayout)

        # Dialog buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def getValues(self):
        if not is_real_number(self.xInput.text()):
            QMessageBox.warning(self, "Invalid input", 
                                f"{self.xInput.text()} isn't a real number")
            return None
        if not is_real_number(self.yInput.text()):
            QMessageBox.warning(self, "Invalid input", 
                                f"{self.yInput.text()} isn't a real number")
            return None
        if not is_real_number(self.zInput.text()):
            QMessageBox.warning(self, "Invalid input", 
                                f"{self.zInput.text()} isn't a real number")
            return None
        return float(self.xInput.text()), float(self.yInput.text()), float(self.zInput.text())
