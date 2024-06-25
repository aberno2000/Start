from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit,
    QDialogButtonBox, QLabel,
    QSlider, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from styles import *


class NormalOrientationDialog(QDialog):
    # Signal with orientation (bool) and arrow size (float)
    orientation_accepted = pyqtSignal(bool, float)
    size_changed = pyqtSignal(float)  # Signal for size change in real-time

    def __init__(self, initial_size=1.0, geditor=None):
        super(NormalOrientationDialog, self).__init__(geditor)
        self.geditor = geditor

        self.setWindowTitle("Normal Orientation and Arrow Size")
        self.setMinimumWidth(300)
        self.setMaximumWidth(300)

        layout = QVBoxLayout(self)

        self.msg_label = QLabel("Do you want to set normals outside?")
        layout.addWidget(self.msg_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No, self)
        layout.addWidget(button_box)

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

        button_box.accepted.connect(self.accepted_yes)
        button_box.rejected.connect(self.accepted_no)

        self.size_slider.valueChanged.connect(self.update_size_input)
        self.size_slider.valueChanged.connect(lambda: self.size_changed.emit(float(self.size_input.text())))
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

    def accepted_yes(self):
        size = float(self.size_input.text())
        self.orientation_accepted.emit(True, size)
        self.accept()

    def accepted_no(self):
        size = float(self.size_input.text())
        self.orientation_accepted.emit(False, size)
        self.accept()
