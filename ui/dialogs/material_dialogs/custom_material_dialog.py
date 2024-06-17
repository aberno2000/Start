from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit,
    QLabel, QPushButton, QHBoxLayout,
    QMessageBox
)
from PyQt5.QtGui import QDoubleValidator
from styles import *
from .chemical_elements_lsit import CHEMICAL_ELEMENTS
from .periodic_table_window import PeriodicTableWindow


class CustomMaterialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Custom Material')
        self.setMinimumWidth(180)
        self.layout = QVBoxLayout()
        self.ok_button = QPushButton('OK')

        self.name_label = QLabel('Name:')
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)

        self.add_element_button = QPushButton('[+] Add Element')
        self.add_element_button.clicked.connect(self.add_element_input)

        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_edit)

        self.element_layout = QVBoxLayout()
        self.layout.addLayout(self.element_layout)

        self.remaining_percentage_label = QLabel('Remaining percentage: 100%')
        self.layout.addWidget(self.remaining_percentage_label)
        self.remaining_percentage = 100.0

        self.add_element_input()

        self.layout.addWidget(self.add_element_button)
        self.button_box = QHBoxLayout()
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)

        self.button_box.addWidget(self.ok_button)
        self.button_box.addWidget(self.cancel_button)

        self.layout.addLayout(self.button_box)
        self.setLayout(self.layout)

    def add_element_input(self):
        element_layout = QHBoxLayout()
        select_element_button = QPushButton('Select Element')
        element_label = QLabel('None')
        element_percentage = QLineEdit()
        element_percentage.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        element_percentage.setValidator(QDoubleValidator(0, 100, 3))
        element_percentage.textChanged.connect(
            self.update_remaining_percentage)

        delete_button = QPushButton('Delete')
        delete_button.clicked.connect(
            lambda: self.remove_element_input(element_layout))

        select_element_button.clicked.connect(
            lambda: self.open_periodic_table(element_label))

        element_layout.addWidget(select_element_button)
        element_layout.addWidget(element_label)
        element_layout.addWidget(element_percentage)
        element_layout.addWidget(delete_button)

        self.element_layout.addLayout(element_layout)
        self.update_remaining_percentage()

    def open_periodic_table(self, element_label):
        self.periodic_table = PeriodicTableWindow()
        self.periodic_table.element_selected.connect(
            lambda element: self.set_element(element_label, element))
        self.periodic_table.exec_()

    def remove_element_input(self, element_layout):
        if self.element_layout.count() <= 1:
            QMessageBox.warning(self, 'Invalid Operation',
                                'Cannot remove the last remaining element.')
            return

        for i in reversed(range(element_layout.count())):
            widget = element_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        self.element_layout.removeItem(element_layout)
        self.update_remaining_percentage()

    def set_element(self, element_label, element):
        # Check for duplicate elements
        for i in range(self.element_layout.count()):
            layout = self.element_layout.itemAt(i).layout()
            existing_label = layout.itemAt(1).widget()
            if existing_label.text() == element:
                QMessageBox.warning(self, 'Invalid Input',
                                    'Duplicate elements are not allowed.')
                return
        element_label.setText(element)
        self.update_remaining_percentage()

    def update_combo_boxes(self):
        selected_elements = set()
        for i in range(self.element_layout.count()):
            layout = self.element_layout.itemAt(i).layout()
            element_label = layout.itemAt(1).widget()
            selected_elements.add(element_label.text())

        for i in range(self.element_layout.count()):
            layout = self.element_layout.itemAt(i).layout()
            element_label = layout.itemAt(1).widget()
            current_element = element_label.text()
            available_elements = [
                e for e in CHEMICAL_ELEMENTS if e not in selected_elements or e == current_element]

    def update_remaining_percentage(self):
        try:
            total_percentage = 0
            for i in range(self.element_layout.count()):
                layout = self.element_layout.itemAt(i).layout()
                percentage_edit = layout.itemAt(2).widget()
                try:
                    total_percentage += float(percentage_edit.text())
                except ValueError:
                    continue

            self.remaining_percentage = 100 - total_percentage
            self.remaining_percentage_label.setText(
                f'Remaining percentage: {self.remaining_percentage:.2f}%')

            # Enable or disable the add element button and change its color
            if self.remaining_percentage <= 0:
                self.add_element_button.setDisabled(True)
                self.add_element_button.setStyleSheet(
                    DEFAULT_DISABLED_BUTTON_STYLE)
            else:
                self.add_element_button.setDisabled(False)
                self.add_element_button.setStyleSheet("")

            # Enable or disable the OK button based on the remaining percentage
            if self.remaining_percentage < 0:
                self.ok_button.setDisabled(True)
                self.ok_button.setStyleSheet(DEFAULT_DISABLED_BUTTON_STYLE)
            else:
                self.ok_button.setDisabled(False)
                self.ok_button.setStyleSheet("")

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred: {e}')

    def validate_and_accept(self):
        try:
            material_name = self.name_edit.text().strip()

            if not material_name:
                QMessageBox.warning(self, 'Invalid Input',
                                    'The name field cannot be empty.')
                return

            parent_dialog = self.parent()
            if material_name in parent_dialog.material_names:
                QMessageBox.warning(self, 'Invalid Input', f'The name "{material_name}" is already taken.')
                return

            total_percentage = 0
            for i in range(self.element_layout.count()):
                layout = self.element_layout.itemAt(i).layout()
                element_label = layout.itemAt(1).widget()
                if element_label.text() == 'None':
                    QMessageBox.warning(
                        self, 'Invalid Input', 'Element cannot be "None". Please select a valid element.')
                    return
                percentage_edit = layout.itemAt(2).widget()
                total_percentage += float(percentage_edit.text())

            if total_percentage != 100:
                QMessageBox.warning(self, 'Invalid Input',
                                    'Total percentage must be exactly 100%.')
                return

            self.accept()
        except ValueError:
            QMessageBox.warning(self, 'Invalid Input',
                                'Please enter valid percentages')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred: {e}')

    def get_material(self):
        material = {'name': self.name_edit.text()}
        for i in range(self.element_layout.count()):
            layout = self.element_layout.itemAt(i).layout()
            element_label = layout.itemAt(1).widget()
            percentage_edit = layout.itemAt(2).widget()
            material[element_label.text()] = percentage_edit.text()
        return material
