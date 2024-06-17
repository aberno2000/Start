from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox, QLabel, QComboBox


class ParticleSourceTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Particle Source Type")
        self.setFixedWidth(265)

        layout = QVBoxLayout(self)

        label = QLabel("Please select the type of particle source:")
        layout.addWidget(label)

        self.comboBox = QComboBox(self)
        self.comboBox.addItem("Point Source with Conical Distribution")
        self.comboBox.addItem("Surface Source")
        layout.addWidget(self.comboBox)

        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def getSelectedSourceType(self):
        return self.comboBox.currentText()
