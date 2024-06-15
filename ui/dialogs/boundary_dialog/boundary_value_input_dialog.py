from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit,
    QLabel, QPushButton, QHBoxLayout
)
from styles import *


class BoundaryValueInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Set Boundary Value")

        # Create layout and widgets
        layout = QVBoxLayout()
        self.label = QLabel("Enter value:")
        self.input = QLineEdit()
        self.input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)

        # Buttons
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        # Add widgets to layout
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect buttons to dialog slots
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_value(self):
        try:
            value = float(self.input.text())
            return value, True
        except ValueError:
            return None, False
