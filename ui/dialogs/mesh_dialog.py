from styles import *
from PyQt5.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout, QLabel
from field_validators import CustomIntValidator, CustomDoubleValidator


class MeshDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mesh Configuration")

        self.layout = QVBoxLayout(self)

        # Mesh size input
        self.mesh_size_input = QLineEdit(self)
        self.mesh_size_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.mesh_size_input.setValidator(CustomDoubleValidator(1e-3, 1e3, 3))
        self.layout.addWidget(QLabel("Mesh Size:"))
        self.layout.addWidget(self.mesh_size_input)

        # Mesh dimensions input
        self.mesh_dim_input = QLineEdit(self)
        self.mesh_dim_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.mesh_dim_input.setValidator(CustomIntValidator(2, 3))
        self.layout.addWidget(QLabel("Mesh Dimensions (2 or 3):"))
        self.layout.addWidget(self.mesh_dim_input)

        # Submit button
        self.submit_button = QPushButton("Submit", self)
        self.layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.accept)

    def get_values(self):
        return float(self.mesh_size_input.text()), int(self.mesh_dim_input.text())
