from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QDialogButtonBox, QMessageBox)
from field_validators import CustomIntValidator, CustomSignedDoubleValidator
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from styles import *
from tabs.graphical_editor.simple_geometry.simple_geometry_constraints import *
from tabs.graphical_editor.simple_geometry.simple_geometry_constants import SIMPLE_GEOMETRY_MESH_RESOLUTION_HINT, SIMPLE_GEOMETRY_MESH_RESOLUTION_VALUE


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
        self.meshResolutionInput = QLineEdit(f"{SIMPLE_GEOMETRY_MESH_RESOLUTION_VALUE}")

        self.xInput.setValidator(
            CustomSignedDoubleValidator(SIMPLE_GEOMETRY_BOX_XMIN,
                                        SIMPLE_GEOMETRY_BOX_XMAX,
                                        SIMPLE_GEOMETRY_BOX_FIELD_PRECISION))
        self.yInput.setValidator(
            CustomSignedDoubleValidator(SIMPLE_GEOMETRY_BOX_YMIN,
                                        SIMPLE_GEOMETRY_BOX_YMAX,
                                        SIMPLE_GEOMETRY_BOX_FIELD_PRECISION))
        self.zInput.setValidator(
            CustomSignedDoubleValidator(SIMPLE_GEOMETRY_BOX_ZMIN,
                                        SIMPLE_GEOMETRY_BOX_ZMAX,
                                        SIMPLE_GEOMETRY_BOX_FIELD_PRECISION))
        self.lengthInput.setValidator(
            CustomSignedDoubleValidator(SIMPLE_GEOMETRY_BOX_LENGTH_MIN,
                                        SIMPLE_GEOMETRY_BOX_LENGTH_MAX,
                                        SIMPLE_GEOMETRY_BOX_FIELD_PRECISION))
        self.widthInput.setValidator(
            CustomSignedDoubleValidator(SIMPLE_GEOMETRY_BOX_WIDTH_MIN,
                                        SIMPLE_GEOMETRY_BOX_WIDTH_MAX,
                                        SIMPLE_GEOMETRY_BOX_FIELD_PRECISION))
        self.heightInput.setValidator(
            CustomSignedDoubleValidator(SIMPLE_GEOMETRY_BOX_HEIGHT_MIN,
                                        SIMPLE_GEOMETRY_BOX_HEIGHT_MAX,
                                        SIMPLE_GEOMETRY_BOX_FIELD_PRECISION))
        self.meshResolutionInput.setValidator(
            CustomIntValidator(SIMPLE_GEOMETRY_BOX_MESH_RESOLUTION_MIN,
                               SIMPLE_GEOMETRY_BOX_MESH_RESOLUTION_MAX))

        self.xInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.yInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.zInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.lengthInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.widthInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.heightInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.meshResolutionInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.meshResolutionInput.setToolTip(SIMPLE_GEOMETRY_MESH_RESOLUTION_HINT)

        formLayout.addRow("Center X:", self.xInput)
        formLayout.addRow("Center Y:", self.yInput)
        formLayout.addRow("Center Z:", self.zInput)
        formLayout.addRow("Length:", self.lengthInput)
        formLayout.addRow("Width:", self.widthInput)
        formLayout.addRow("Height:", self.heightInput)
        formLayout.addRow("Mesh resolution: ", self.meshResolutionInput)

        layout.addLayout(formLayout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def validate_and_accept(self):
        inputs = [
            self.xInput, self.yInput, self.zInput, self.lengthInput,
            self.widthInput, self.heightInput, self.meshResolutionInput
        ]
        all_valid = True

        for input_field in inputs:
            validator = input_field.validator()
            state, _, _ = validator.validate(input_field.text(), 0)

            if isinstance(validator, QDoubleValidator) or isinstance(validator, QIntValidator):
                if state != QDoubleValidator.Acceptable:
                    input_field.setStyleSheet(INVALID_QLINEEDIT_STYLE)
                    all_valid = False
                else:
                    input_field.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)

        if all_valid:
            self.accept()
        else:
            QMessageBox.warning(self, "Invalid input", "Please correct the highlighted fields.")

    def getValues(self):
        values = (float(self.xInput.text()), float(self.yInput.text()),
                  float(self.zInput.text()), float(self.lengthInput.text()),
                  float(self.widthInput.text()),
                  float(self.heightInput.text()),
                  int(self.meshResolutionInput.text()))

        return values
