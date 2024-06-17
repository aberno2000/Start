from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QDialogButtonBox, QLabel, QPushButton
)


class ArrowMethodSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super(ArrowMethodSelectionDialog, self).__init__(parent)

        self.setWindowTitle("Select Method")

        layout = QVBoxLayout(self)

        label = QLabel(
            "Do you want to set the parameters manually or interactively?")
        layout.addWidget(label)

        button_box = QDialogButtonBox(self)
        self.manual_button = QPushButton("Manually")
        self.interactive_button = QPushButton("Interactively")
        button_box.addButton(self.manual_button, QDialogButtonBox.AcceptRole)
        button_box.addButton(self.interactive_button,
                             QDialogButtonBox.AcceptRole)

        self.manual_button.clicked.connect(self.accept_manual)
        self.interactive_button.clicked.connect(self.accept_interactive)

        layout.addWidget(button_box)
        self.selected_method = None

    def accept_manual(self):
        self.selected_method = "manual"
        self.accept()

    def accept_interactive(self):
        self.selected_method = "interactive"
        self.accept()

    def get_selected_method(self):
        return self.selected_method
