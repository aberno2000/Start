from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QDialogButtonBox, QLabel, QSlider
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from styles import *


class ArrowSizeDialog(QDialog):
    size_changed = pyqtSignal(float)
    size_accepted = pyqtSignal(float)

    def __init__(self, initial_size=1.0, parent=None):
        super(ArrowSizeDialog, self).__init__(parent)

        self.setWindowTitle("Set Arrow Size")

        layout = QVBoxLayout(self)

        self.size_slider = QSlider(Qt.Horizontal, self)
        self.size_slider.setRange(1, 10000)
        self.size_slider.setValue(int(initial_size * 100))

        self.size_input = QLineEdit(self)
        self.size_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.size_input.setValidator(QDoubleValidator(0.01, 100.0, 3, self))
        self.size_input.setText(f"{initial_size:.2f}")

        size_layout = QHBoxLayout()
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_input)

        layout.addWidget(QLabel("Arrow Size:"))
        layout.addLayout(size_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.size_slider.valueChanged.connect(self.update_size_input)
        self.size_input.textChanged.connect(self.update_size_slider)

    def update_size_input(self, value):
        size = value / 100.0
        self.size_input.setText(f"{size:.2f}")
        self.size_changed.emit(size)

    def update_size_slider(self):
        try:
            size = float(self.size_input.text())
            if 0.01 <= size <= 100:
                self.size_slider.setValue(int(size * 100))
                self.size_changed.emit(size)
        except ValueError:
            pass

    def on_accept(self):
        size = float(self.size_input.text())
        self.size_accepted.emit(size)
        self.accept()
