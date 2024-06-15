from PyQt5.QtWidgets import QDialog, QGridLayout, QPushButton, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSize, pyqtSignal


class PeriodicTableWindow(QDialog):
    element_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Periodic Table")
        self.setGeometry(100, 100, 800, 600)
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.element_colors = {
            'alkali_metals': '#FF6666',            # Light Red
            'alkaline_earth_metals': '#FFDEAD',    # Navajo White
            'transition_metals': '#FFC0C0',        # Light Pink
            'post_transition_metals': '#CCCCCC',   # Silver
            'metalloids': '#CCCC99',               # Chartreuse Yellow
            'non_metals': '#A0FFA0',               # Green Yellow
            'halogens': '#FFFF99',                 # Light Yellow
            'noble_gases': '#C0FFFF',              # Light Blue
            'lanthanides': '#FFBFFF',              # Light Pink
            'actinides': '#FF99CC',                # Light Pink
            'unknown': '#FFFFFF'                   # White
        }

        self.element_groups = {
            'alkali_metals': ['Li', 'Na', 'K', 'Rb', 'Cs', 'Fr'],
            'alkaline_earth_metals': ['Be', 'Mg', 'Ca', 'Sr', 'Ba', 'Ra'],
            'transition_metals': ['Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
                                  'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd',
                                  'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Rf',
                                  'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn'],
            'post_transition_metals': ['Al', 'Ga', 'In', 'Sn', 'Tl', 'Pb', 'Bi', 'Nh', 'Fl', 'Mc', 'Lv'],
            'metalloids': ['B', 'Si', 'Ge', 'As', 'Sb', 'Te', 'Po'],
            'non_metals': ['H', 'C', 'N', 'O', 'P', 'S', 'Se'],
            'halogens': ['F', 'Cl', 'Br', 'I', 'At', 'Ts'],
            'noble_gases': ['He', 'Ne', 'Ar', 'Kr', 'Xe', 'Rn', 'Og'],
            'lanthanides': ['La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu'],
            'actinides': ['Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr'],
            'unknown': []
        }

        self.create_buttons()

    def create_buttons(self):
        # Coordinates for element placement
        coordinates = {
            'H': (0, 0), 'He': (0, 17),
            'Li': (1, 0), 'Be': (1, 1), 'B': (1, 12), 'C': (1, 13), 'N': (1, 14), 'O': (1, 15), 'F': (1, 16), 'Ne': (1, 17),
            'Na': (2, 0), 'Mg': (2, 1), 'Al': (2, 12), 'Si': (2, 13), 'P': (2, 14), 'S': (2, 15), 'Cl': (2, 16), 'Ar': (2, 17),
            'K': (3, 0), 'Ca': (3, 1), 'Sc': (3, 2), 'Ti': (3, 3), 'V': (3, 4), 'Cr': (3, 5), 'Mn': (3, 6), 'Fe': (3, 7),
            'Co': (3, 8), 'Ni': (3, 9), 'Cu': (3, 10), 'Zn': (3, 11), 'Ga': (3, 12), 'Ge': (3, 13), 'As': (3, 14), 'Se': (3, 15),
            'Br': (3, 16), 'Kr': (3, 17),
            'Rb': (4, 0), 'Sr': (4, 1), 'Y': (4, 2), 'Zr': (4, 3), 'Nb': (4, 4), 'Mo': (4, 5), 'Tc': (4, 6), 'Ru': (4, 7),
            'Rh': (4, 8), 'Pd': (4, 9), 'Ag': (4, 10), 'Cd': (4, 11), 'In': (4, 12), 'Sn': (4, 13), 'Sb': (4, 14), 'Te': (4, 15),
            'I': (4, 16), 'Xe': (4, 17),
            'Cs': (5, 0), 'Ba': (5, 1), 'La': (7, 2), 'Hf': (5, 3), 'Ta': (5, 4), 'W': (5, 5), 'Re': (5, 6), 'Os': (5, 7),
            'Ir': (5, 8), 'Pt': (5, 9), 'Au': (5, 10), 'Hg': (5, 11), 'Tl': (5, 12), 'Pb': (5, 13), 'Bi': (5, 14), 'Po': (5, 15),
            'At': (5, 16), 'Rn': (5, 17),
            'Fr': (6, 0), 'Ra': (6, 1), 'Ac': (8, 2), 'Rf': (6, 3), 'Db': (6, 4), 'Sg': (6, 5), 'Bh': (6, 6), 'Hs': (6, 7),
            'Mt': (6, 8), 'Ds': (6, 9), 'Rg': (6, 10), 'Cn': (6, 11), 'Nh': (6, 12), 'Fl': (6, 13), 'Mc': (6, 14), 'Lv': (6, 15),
            'Ts': (6, 16), 'Og': (6, 17),
            'Ce': (7, 3), 'Pr': (7, 4), 'Nd': (7, 5), 'Pm': (7, 6), 'Sm': (7, 7), 'Eu': (7, 8), 'Gd': (7, 9), 'Tb': (7, 10),
            'Dy': (7, 11), 'Ho': (7, 12), 'Er': (7, 13), 'Tm': (7, 14), 'Yb': (7, 15), 'Lu': (7, 16),
            'Th': (8, 3), 'Pa': (8, 4), 'U': (8, 5), 'Np': (8, 6), 'Pu': (8, 7), 'Am': (8, 8), 'Cm': (8, 9), 'Bk': (8, 10),
            'Cf': (8, 11), 'Es': (8, 12), 'Fm': (8, 13), 'Md': (8, 14), 'No': (8, 15), 'Lr': (8, 16)
        }

        for group, elements in self.element_groups.items():
            for element in elements:
                if element in coordinates:
                    row, col = coordinates[element]
                    color = self.element_colors.get(group, '#FFFFFF')
                    self.create_element_button(element, row, col, color)

    def create_element_button(self, element, row, col, color):
        try:
            button = QPushButton(element, self)
            button.setFixedSize(QSize(70, 70))
            button.setStyleSheet(
                f"background-color: {color}; border-radius: 10px;")

            font = QFont()
            font.setPointSize(16)
            button.setFont(font)

            button.clicked.connect(
                lambda _, el=element: self.on_element_clicked(el))
            self.layout.addWidget(button, row, col)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to create button for {element}: {e}")

    def on_element_clicked(self, element):
        self.element_selected.emit(element)
        self.close()
