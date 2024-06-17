from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QDialogButtonBox, QMessageBox, QScrollArea,
                             QWidget, QPushButton, QHBoxLayout, QLabel)
from PyQt5.QtCore import QSize
from field_validators import CustomSignedDoubleValidator
from PyQt5.QtGui import QDoubleValidator
from styles import *
from tabs.graphical_editor.simple_geometry.simple_geometry_constraints import *


class SurfaceDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setWindowTitle("Create Arbitrary Surface")

        self.mainLayout = QVBoxLayout(self)  # Main layout for the dialog
        self.scrollArea = QScrollArea(self)  # Scroll area to contain the form
        # Allow the contained widget to resize
        self.scrollArea.setWidgetResizable(True)

        # Container widget for the form
        self.containerWidget = QWidget()
        self.formLayout = QFormLayout()  # Form layout for point inputs

        self.inputs = []  # Store all QLineEdit inputs

        # Initialize with 3 points
        for _ in range(3):
            self.add_point_fields()

        self.addButton = QPushButton("[+]")
        self.addButton.setFixedSize(QSize(32, 32))
        self.addButton.clicked.connect(self.add_point_fields)

        # Set the form layout to the container widget and add it to the scroll area
        self.containerWidget.setLayout(self.formLayout)
        self.scrollArea.setWidget(self.containerWidget)

        # Add the scroll area and the add button to the main layout
        self.mainLayout.addWidget(self.scrollArea)
        self.mainLayout.addWidget(self.addButton)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

        # Add dialog buttons to the main layout
        self.mainLayout.addWidget(self.buttons)

    def add_point_fields(self):
        point_number = len(self.inputs) // 3 + 1
        # Create a horizontal layout for the x, y, z inputs
        hLayout = QHBoxLayout()

        x_input = QLineEdit("0.0")
        y_input = QLineEdit("0.0")
        z_input = QLineEdit("0.0")

        x_input.setValidator(
            CustomSignedDoubleValidator(
                SIMPLE_GEOMETRY_SURFACE_XMIN, SIMPLE_GEOMETRY_SURFACE_XMAX,
                SIMPLE_GEOMETRY_SURFACE_FIELD_PRECISION))
        y_input.setValidator(
            CustomSignedDoubleValidator(
                SIMPLE_GEOMETRY_SURFACE_YMIN, SIMPLE_GEOMETRY_SURFACE_YMAX,
                SIMPLE_GEOMETRY_SURFACE_FIELD_PRECISION))
        z_input.setValidator(
            CustomSignedDoubleValidator(
                SIMPLE_GEOMETRY_SURFACE_ZMIN, SIMPLE_GEOMETRY_SURFACE_ZMAX,
                SIMPLE_GEOMETRY_SURFACE_FIELD_PRECISION))

        x_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        y_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        z_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)

        self.inputs.extend([x_input, y_input, z_input])

        # Add the inputs to the horizontal layout
        hLayout.addWidget(QLabel(f"Point {point_number} X:"))
        hLayout.addWidget(x_input)
        hLayout.addWidget(QLabel("Y:"))
        hLayout.addWidget(y_input)
        hLayout.addWidget(QLabel("Z:"))
        hLayout.addWidget(z_input)

        # Create a container widget for the horizontal layout and add it to the form
        containerWidget = QWidget()
        containerWidget.setLayout(hLayout)
        self.formLayout.addRow(containerWidget)

    def validate_and_accept(self):
        all_valid = True

        for input_field in self.inputs:
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
        values = [float(field.text()) for field in self.inputs]
        return values
