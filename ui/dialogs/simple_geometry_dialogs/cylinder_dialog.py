from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox
)
from styles import *
from util import is_real_number, is_positive_real_number


class CylinderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Cylinder")

        layout = QVBoxLayout(self)
        formLayout = QFormLayout()

        self.xInput = QLineEdit("0.0")
        self.yInput = QLineEdit("0.0")
        self.zInput = QLineEdit("0.0")
        self.radiusInput = QLineEdit("2.5")
        self.dxInput = QLineEdit("5.0")
        self.dyInput = QLineEdit("5.0")
        self.dzInput = QLineEdit("5.0")
        self.meshSizeInput = QLineEdit("1.0")

        self.xInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.yInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.zInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.radiusInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.dxInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.dyInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.dzInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.meshSizeInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)

        formLayout.addRow("Base center X:", self.xInput)
        formLayout.addRow("Base center Y:", self.yInput)
        formLayout.addRow("Base center Z:", self.zInput)
        formLayout.addRow("Radius:", self.radiusInput)
        formLayout.addRow("Top center X:", self.dxInput)
        formLayout.addRow("Top center Y:", self.dyInput)
        formLayout.addRow("Top center Z:", self.dzInput)
        formLayout.addRow("Mesh size:", self.meshSizeInput)

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
        if not is_positive_real_number(self.radiusInput.text()):
            QMessageBox.warning(self, "Invalid input", 
                                f"{self.radiusInput.text()} isn't a real positive number")
            return None
        if not is_real_number(self.dxInput.text()):
            QMessageBox.warning(self, "Invalid input", 
                                f"{self.dxInput.text()} isn't a real number")
            return None
        if not is_real_number(self.dyInput.text()):
            QMessageBox.warning(self, "Invalid input", 
                                f"{self.dyInput.text()} isn't a real number")
            return None
        if not is_real_number(self.dzInput.text()):
            QMessageBox.warning(self, "Invalid input", 
                                f"{self.dzInput.text()} isn't a real number")
            return None
        values = (float(self.xInput.text()), float(self.yInput.text()), float(self.zInput.text()),
                  float(self.radiusInput.text()), float(self.dxInput.text()), float(self.dyInput.text()), float(self.dzInput.text()))

        mesh_size = 1.0
        if not is_real_number(self.meshSizeInput.text()):
            QMessageBox.warning(self, "Invalid input",
                                "Mesh size must be floating point number.")
            return None
        mesh_size = float(self.meshSizeInput.text())

        return values, mesh_size
