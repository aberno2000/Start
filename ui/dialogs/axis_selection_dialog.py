from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QPushButton


class AxisSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super(AxisSelectionDialog, self).__init__(parent)
        self.setWindowTitle("Select Axis for Cross-Section")
        self.setFixedSize(250, 150)
        layout = QVBoxLayout(self)

        # Combo box for axis selection
        self.axisComboBox = QComboBox()
        self.axisComboBox.addItems(["X-axis", "Y-axis", "Z-axis"])
        layout.addWidget(self.axisComboBox)

        # OK button
        okButton = QPushButton("OK")
        okButton.clicked.connect(self.accept)
        layout.addWidget(okButton)

    def getSelectedAxis(self):
        return self.axisComboBox.currentText()
