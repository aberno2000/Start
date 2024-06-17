from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QDialogButtonBox, QMessageBox)
from field_validators import CustomSignedDoubleValidator
from PyQt5.QtGui import QDoubleValidator
from styles import *
from tabs.graphical_editor.simple_geometry.simple_geometry_constraints import *


class PointDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Create Point")

        # Create layout
        layout = QVBoxLayout(self)

        # Create form layout for input fields
        formLayout = QFormLayout()

        # Input fields for the point parameters
        self.xInput = QLineEdit("0.0")
        self.yInput = QLineEdit("0.0")
        self.zInput = QLineEdit("0.0")

        self.xInput.setValidator(
            CustomSignedDoubleValidator(SIMPLE_GEOMETRY_POINT_XMIN,
                                        SIMPLE_GEOMETRY_POINT_XMAX,
                                        SIMPLE_GEOMETRY_POINT_FIELD_PRECISION))
        self.yInput.setValidator(
            CustomSignedDoubleValidator(SIMPLE_GEOMETRY_POINT_YMIN,
                                        SIMPLE_GEOMETRY_POINT_YMAX,
                                        SIMPLE_GEOMETRY_POINT_FIELD_PRECISION))
        self.zInput.setValidator(
            CustomSignedDoubleValidator(SIMPLE_GEOMETRY_POINT_ZMIN,
                                        SIMPLE_GEOMETRY_POINT_ZMAX,
                                        SIMPLE_GEOMETRY_POINT_FIELD_PRECISION))

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
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def validate_and_accept(self):
        inputs = [self.xInput, self.yInput, self.zInput]
        all_valid = True

        for input_field in inputs:
            if input_field.validator().validate(
                    input_field.text(), 0)[0] != QDoubleValidator.Acceptable:
                input_field.setStyleSheet(INVALID_QLINEEDIT_STYLE)
                all_valid = False
            else:
                input_field.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)

        if all_valid:
            self.accept()
        else:
            QMessageBox.warning(self, "Invalid input",
                                "Please correct the highlighted fields.")

    def getValues(self):
        values = (float(self.xInput.text()), float(self.yInput.text()),
                  float(self.zInput.text()))
        return values
