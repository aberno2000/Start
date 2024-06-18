from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit,
    QDialogButtonBox, QMessageBox, QLabel
)
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk import vtkRenderer
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from styles import *
from util import is_positive_real_number
from math import pi, radians


class ExpansionAngleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Expansion Angle")

        layout = QVBoxLayout(self)

        self.theta_input = QLineEdit(self)
        self.theta_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        layout.addWidget(QLabel("Expansion angle θ (in degrees °)"))
        layout.addWidget(self.theta_input)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def getTheta(self):
        theta_str = self.theta_input.text()
        if not is_positive_real_number(theta_str):
            QMessageBox.warning(self, "Invalid Input", 
                                f"{self.theta_input.text()} isn't a positive real number")
            return None

        # Converting degrees str to float number.
        theta = float(theta_str)

        # Removing cycles from the degrees.
        if theta > 360:
            cycles = theta / 360.
            theta = theta - 360 * cycles

        # Converting to rad.
        theta = theta * pi / 180.
        return theta


class ExpansionAngleDialogNonModal(QDialog):
    accepted_signal = pyqtSignal(float)

    def __init__(self, vtkWidget: QVTKRenderWindowInteractor, renderer: vtkRenderer, parent=None):
        super(ExpansionAngleDialogNonModal, self).__init__(parent)

        self.parent = parent
        self.vtkWidget = vtkWidget
        self.renderer = renderer

        self.setWindowTitle("Set Expansion Angle")

        layout = QVBoxLayout(self)

        self.theta_input = QLineEdit(self)
        self.theta_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.theta_input.setValidator(QDoubleValidator(0.0, 180.0, 6))

        layout.addWidget(QLabel("Expansion Angle θ (degrees):"))
        layout.addWidget(self.theta_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.handle_accept)
        button_box.rejected.connect(self.handle_reject)

        layout.addWidget(button_box)

    def resetArrowActor(self):
        self.parent.reset_particle_source_arrow()

    def handle_accept(self):
        try:
            theta = float(self.theta_input.text())
            self.accepted_signal.emit(radians(theta))
            self.resetArrowActor()
            self.close()
        except ValueError:
            QMessageBox.warning(self, "Invalid input",
                                "Please enter a valid numerical value.")

    def handle_reject(self):
        self.resetArrowActor()
        self.close()

    def closeEvent(self, event):
        self.resetArrowActor()
        super().closeEvent(event)
