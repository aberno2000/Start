from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox, QScrollArea,
    QWidget, QPushButton, QHBoxLayout, QLabel
)
from PyQt5.QtCore import QSize
from styles import *
from util import is_real_number


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

        self.meshSizeInput = QLineEdit("1.0")
        self.meshSizeInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.meshSizeLabel = QLabel("Mesh size:")
        meshLayout = QHBoxLayout()
        meshLayout.addWidget(self.meshSizeLabel)
        meshLayout.addWidget(self.meshSizeInput)
        self.mainLayout.addLayout(meshLayout)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
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

    def getValues(self):
        if not all(is_real_number(input_field.text()) for input_field in self.inputs):
            QMessageBox.warning(self, "Invalid input",
                                "All coordinates must be real numbers.")
            return None
        values = [float(field.text()) for field in self.inputs]

        mesh_size = 1.0
        if not is_real_number(self.meshSizeInput.text()):
            QMessageBox.warning(self, "Invalid input",
                                "Mesh size must be floating point number.")
            return None
        mesh_size = float(self.meshSizeInput.text())

        return values, mesh_size
