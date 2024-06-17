from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox
)
from styles import *
from util import is_real_number


class AngleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Change Actor Angle")

        layout = QVBoxLayout(self)

        formLayout = QFormLayout()

        # Input fields for the angles
        self.xAngleInput = QLineEdit("0.0")
        self.yAngleInput = QLineEdit("0.0")
        self.zAngleInput = QLineEdit("0.0")

        self.xAngleInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.yAngleInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.zAngleInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)

        # Add rows for X, Y, and Z angles
        formLayout.addRow("Angle X (degrees):", self.xAngleInput)
        formLayout.addRow("Angle Y (degrees):", self.yAngleInput)
        formLayout.addRow("Angle Z (degrees):", self.zAngleInput)

        layout.addLayout(formLayout)

        # Dialog buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def getValues(self):
        # Validate inputs and return angles
        x = self.validate_angle(self.xAngleInput.text())
        y = self.validate_angle(self.yAngleInput.text())
        z = self.validate_angle(self.zAngleInput.text())

        if x is not None and y is not None and z is not None:
            return x, y, z
        return None

    @staticmethod
    def validate_angle(value: str):
        if is_real_number(value):
            return float(value)
        else:
            QMessageBox.warning(None, "Invalid Input",
                                f"Angle value must be floating point number")
            return None
