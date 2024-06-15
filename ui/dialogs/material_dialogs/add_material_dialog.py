from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QComboBox,
    QLabel, QPushButton, QFileDialog,
    QMessageBox
)
from PyQt5.QtCore import Qt
from json import dump, load
from os.path import exists
from .custom_material_dialog import CustomMaterialDialog


class AddMaterialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Add Material')
        self.setMinimumWidth(250)
        self.setMaximumWidth(250)
        self.layout = QVBoxLayout()

        # ComboBox for default materials
        self.materials_combobox = QComboBox()
        self.default_materials = {
            'Steel Х12МФ': {'Fe': 95.0, 'Cr': 11.0, 'Mo': 0.5, 'Mn': 0.3, 'Ni': 0.35, 'V': 0.225},
            'Steel 12Х18Н9Т': {'Fe': 95.0, 'C': 0.12, 'Mn': 1.9, 'Si': 0.3, 'Cr': 18.0, 'Ni': 9.0, 'Ti': 0.3, 'Nb': 0.1, 'V': 0.1},
            'Steel 08Х18Н10Т': {'Fe': 95.0, 'C': 0.08, 'Mn': 1.8, 'Si': 0.3, 'Cr': 18.0, 'Ni': 10.0, 'Ti': 0.3, 'Nb': 0.1, 'V': 0.1},
        }
        for material, components in self.default_materials.items():
            hint = ', '.join([f'{k}: {v}%' for k, v in components.items()])
            display_name = f"{material} ({hint})"
            self.materials_combobox.addItem(display_name)
            self.materials_combobox.setItemData(
                self.materials_combobox.count() - 1, hint, Qt.ToolTipRole)

        self.material_names = set(
            material for material in self.default_materials)
        self.layout.addWidget(QLabel('Select a material:'))
        self.layout.addWidget(self.materials_combobox)

        # Plus button for custom material
        self.add_custom_material_button = QPushButton(
            '[+] Add Custom Material')
        self.add_custom_material_button.clicked.connect(
            self.add_custom_material)
        self.layout.addWidget(self.add_custom_material_button)

        # Load materials button
        self.load_materials_button = QPushButton('Load Materials from File')
        self.load_materials_button.clicked.connect(
            self.load_materials_from_file)
        self.layout.addWidget(self.load_materials_button)

        self.save_materials_button = QPushButton('Save Materials to File')
        self.save_materials_button.clicked.connect(self.save_materials_to_file)
        self.layout.addWidget(self.save_materials_button)

        self.apply_material_button = QPushButton('Apply Material')
        self.apply_material_button.clicked.connect(self.apply_material)
        self.layout.addWidget(self.apply_material_button)

        self.setLayout(self.layout)

        self.custom_materials = []

    def add_custom_material(self):
        custom_dialog = CustomMaterialDialog(self)
        if custom_dialog.exec_() == QDialog.Accepted:
            custom_material = custom_dialog.get_material()
            if custom_material:
                material_name = custom_material.pop('name')
                components = {k: float(v) for k, v in custom_material.items()}
                self.custom_materials.append({material_name: components})
                hint = ', '.join([f'{k}: {v}%' for k, v in components.items()])
                display_name = f"{material_name} ({hint})"
                self.materials_combobox.addItem(display_name)
                self.materials_combobox.setItemData(
                    self.materials_combobox.count() - 1, hint, Qt.ToolTipRole)
                self.save_custom_materials_to_file()
                self.material_names.add(material_name)

    def save_custom_materials_to_file(self):
        with open('materials.json', 'w') as file:
            dump(self.custom_materials, file, indent=4)

    def save_materials_to_file(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 'Save Materials File', '', 'JSON Files (*.json)')
            if file_path:
                if not file_path.endswith('.json'):
                    file_path += '.json'
                if exists(file_path):
                    reply = QMessageBox.question(
                        self, 'Overwrite File', 'File already exists. Do you want to overwrite it?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply == QMessageBox.No:
                        return

                # Collect all materials from the combo box
                all_materials = []
                for i in range(self.materials_combobox.count()):
                    display_name = self.materials_combobox.itemText(i)
                    hint = self.materials_combobox.itemData(i, Qt.ToolTipRole)
                    name, components_str = display_name.split(' (')
                    # Remove the trailing ')'
                    components_str = components_str[:-1]
                    components = dict([comp.split(': ')
                                      for comp in components_str.split(', ')])
                    # Convert percentages to floats
                    components = {k: float(v[:-1])
                                  for k, v in components.items()}
                    all_materials.append({name: components})

                with open(file_path, 'w') as file:
                    dump(all_materials, file, indent=4)

                QMessageBox.information(
                    self, 'Success', f'Materials saved to {file_path}')
        except Exception as e:
            QMessageBox.critical(
                self, 'Error', f'Failed to save materials: {e}')

    def apply_material(self):
        # TODO: implement
        pass

    def load_materials_from_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 'Open Materials File', '', 'JSON Files (*.json)')
            if file_path:
                with open(file_path, 'r') as file:
                    materials = load(file)

                    existing_names = {self.materials_combobox.itemText(
                        i) for i in range(self.materials_combobox.count())}
                    existing_compositions = {
                        tuple(sorted(components.items())): name
                        for name, components in self.default_materials.items()
                    }
                    for i in range(self.materials_combobox.count()):
                        hint = self.materials_combobox.itemData(
                            i, Qt.ToolTipRole)
                        composition = tuple(sorted((component.split(': ')[0], float(
                            component.split(': ')[1][:-1])) for component in hint.split(', ')))
                        existing_compositions[composition] = self.materials_combobox.itemText(
                            i)

                    name_conflicts = []
                    composition_conflicts = []

                    for material in materials:
                        for name, components in material.items():
                            hint = ', '.join(
                                [f'{k}: {v}%' for k, v in components.items()])
                            composition = tuple(sorted(components.items()))

                            if name in existing_names:
                                name_conflicts.append(name)
                            elif composition in existing_compositions:
                                composition_conflicts.append(
                                    f'{name} vs {existing_compositions[composition]}')
                            else:
                                display_name = f"{name} ({hint})"
                                self.materials_combobox.addItem(display_name)
                                self.materials_combobox.setItemData(
                                    self.materials_combobox.count() - 1, hint, Qt.ToolTipRole)
                                self.custom_materials.append(
                                    {name: components})
                                self.material_names.add(name)

                    if name_conflicts:
                        QMessageBox.warning(
                            self, 'Name Conflicts', 'These materials have conflicting names:\n' + '\n'.join(name_conflicts))

                    if composition_conflicts:
                        QMessageBox.warning(
                            self, 'Composition Conflicts', 'These materials have conflicting compositions:\n' + '\n'.join(composition_conflicts))

        except Exception as e:
            QMessageBox.critical(
                self, 'Error', f'Failed to load materials: {e}')
