from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox
)
from styles import *
from util import is_real_number


class BoxDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Box")

        layout = QVBoxLayout(self)
        formLayout = QFormLayout()

        self.xInput = QLineEdit("0.0")
        self.yInput = QLineEdit("0.0")
        self.zInput = QLineEdit("0.0")
        self.lengthInput = QLineEdit("5.0")
        self.widthInput = QLineEdit("5.0")
        self.heightInput = QLineEdit("5.0")

        self.xInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.yInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.zInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.lengthInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.widthInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.heightInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)

        formLayout.addRow("Center X:", self.xInput)
        formLayout.addRow("Center Y:", self.yInput)
        formLayout.addRow("Center Z:", self.zInput)
        formLayout.addRow("Length:", self.lengthInput)
        formLayout.addRow("Width:", self.widthInput)
        formLayout.addRow("Height:", self.heightInput)

        layout.addLayout(formLayout)

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
        if not is_real_number(self.lengthInput.text()):
            QMessageBox.warning(self, "Invalid input", 
                                f"{self.lengthInput.text()} isn't a real number")
            return None
        if not is_real_number(self.widthInput.text()):
            QMessageBox.warning(self, "Invalid input", 
                                f"{self.widthInput.text()} isn't a real number")
            return None
        if not is_real_number(self.heightInput.text()):
            QMessageBox.warning(self, "Invalid input", 
                                f"{self.heightInput.text()} isn't a real number")
            return None
        values = (float(self.xInput.text()), float(self.yInput.text()), float(self.zInput.text()),
                  float(self.lengthInput.text()), float(self.widthInput.text()), float(self.heightInput.text()))

        return values
