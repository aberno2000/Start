from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox,
    QComboBox
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from styles import *


class ParticleSourceDialog(QDialog):
    accepted_signal = pyqtSignal(dict)
    rejected_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Particle Source Parameters")

        layout = QFormLayout(self)

        # Particle type
        self.particle_type_combo = QComboBox()
        self.particle_type_combo.addItems(
            ["Ti", "Al", "Sn", "W", "Au", "Cu", "Ni", "Ag"])
        layout.addRow("Particle Type:", self.particle_type_combo)

        # Energy
        self.energy_input = QLineEdit()
        self.energy_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        energy_validator = QDoubleValidator(
            0.0, 10000.0, 6, self)  # Range of the energy in [eV]
        self.energy_input.setValidator(energy_validator)
        layout.addRow("Energy (eV):", self.energy_input)

        # Number of particles
        self.num_particles_input = QLineEdit()
        self.num_particles_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        num_particles_validator = QIntValidator(
            1, 1000000000, self)  # Range of particle count
        self.num_particles_input.setValidator(num_particles_validator)
        layout.addRow("Number of Particles:", self.num_particles_input)

        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.handle_accept)
        self.button_box.rejected.connect(self.handle_reject)
        layout.addRow(self.button_box)

    def getValues(self):
        return {
            "particle_type": self.particle_type_combo.currentText(),
            "energy": float(self.energy_input.text()),
            "num_particles": int(self.num_particles_input.text())
        }

    def handle_accept(self):
        try:
            values = self.getValues()
            self.accepted_signal.emit(values)
            self.close()
        except ValueError:
            QMessageBox.warning(self, "Invalid input",
                                "Please enter valid numerical values.")

    def handle_reject(self):
        self.rejected_signal.emit()
        self.close()

    def closeEvent(self, event):
        super().closeEvent(event)
