import gmsh, tempfile, meshio
import numpy as np
from math import radians, pi
from datetime import datetime
from os import remove
from vtkmodules.vtkCommonCore import vtkMath
from vtk import (
    vtkRenderer, vtkPolyData, vtkPolyDataWriter, vtkAppendPolyData,
    vtkPolyDataReader, vtkPolyDataMapper, vtkActor, vtkPolyDataWriter,
    vtkUnstructuredGrid, vtkGeometryFilter, vtkTransform, vtkCellArray,
    vtkTriangle, vtkPoints, vtkDelaunay2D, vtkPolyLine, vtkVertexGlyphFilter,
    vtkUnstructuredGridWriter, vtkArrowSource, vtkTransformPolyDataFilter,
    vtkPolyDataNormals,
    VTK_TRIANGLE
)
from PyQt5.QtCore import Qt, QSize, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, 
    QVBoxLayout, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QSizePolicy, QLabel, QHBoxLayout,
    QWidget, QScrollArea, QComboBox, QTreeView, QSlider,
    QFileDialog, QGridLayout
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QStandardItemModel, QStandardItem, QFont
from .converter import is_positive_real_number, is_real_number
from os.path import exists, isfile
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from json import dump, load
from .styles import(
    DEFAULT_QLINEEDIT_STYLE, DEFAULT_ACTOR_COLOR, ARROW_ACTOR_COLOR,
    ARROW_DEFAULT_SCALE, DEFAULT_DISABLED_BUTTON_STYLE
)

DEFAULT_TEMP_MESH_FILE = 'temp.msh'
DEFAULT_TEMP_VTK_FILE = 'temp.vtk'
DEFAULT_TEMP_HDF5_FILE = 'temp.hdf5'
DEFAULT_TEMP_CONFIG_FILE = 'temp_config.json'

DEFAULT_COUNT_OF_PROJECT_FILES = 3

figure_types = ['Point', 'Line', 'Surface', 'Sphere', 'Box', 'Cylinder', 'Custom']

CHEMICAL_ELEMENTS = ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
                     'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca',
                     'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
                     'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr',
                     'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn',
                     'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd',
                     'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb',
                     'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg',
                     'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th',
                     'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm',
                     'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds',
                     'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og']

def is_file_valid(path: str):
    if not exists(path) or not isfile(path) or not path:
        return False
    return True

def is_path_accessable(path):
    try:
        with open(path) as _:
            pass
        return True
    except IOError as _:
        return False
    
def convert_msh_to_vtk(msh_filename: str):
    if not msh_filename.endswith('.msh'):
        return None
    
    try:
        gmsh.initialize()
        vtk_filename = msh_filename.replace('.msh', '.vtk')
        gmsh.open(msh_filename)
        gmsh.write(vtk_filename)
        gmsh.finalize()
        return vtk_filename
    except Exception as e:
        print(f"Error converting VTK to Msh: {e}")
        return None
        

def convert_vtk_to_msh(vtk_filename: str):
    """
    Converts a VTK file to a Gmsh (.msh) file.
    
    Args:
        vtk_filename (str): The filename of the VTK file to convert.
    
    Returns:
        str: The filename of the converted Gmsh file if successful, None otherwise.
    """
    if not vtk_filename.endswith('.vtk'):
        return None
    
    msh_filename = vtk_filename.replace('.vtk', '.msh')
    msh_filename = msh_filename.replace('.msh.msh', '.msh')
    try:
        mesh = meshio.read(vtk_filename)
        meshio.write(msh_filename, mesh, file_format="gmsh22")
        return msh_filename
    except Exception as e:
        print(f"Error converting VTK to Msh: {e}")
        return None
    
    
class AngleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Change Actor Angle")
        
        layout = QVBoxLayout(self)
        
        formLayout = QFormLayout()
        
        # Input fields for the angles
        self.xAngleInput = QLineEdit("0.0")
        self.yAngleInput = QLineEdit("0.0")
        self.zAngleInput = QLineEdit("0.0")
        
        self.xAngleInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.yAngleInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.zAngleInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        
        # Add rows for X, Y, and Z angles
        formLayout.addRow("Angle X (degrees):", self.xAngleInput)
        formLayout.addRow("Angle Y (degrees):", self.yAngleInput)
        formLayout.addRow("Angle Z (degrees):", self.zAngleInput)
        
        layout.addLayout(formLayout)
        
        # Dialog buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
    
    def getValues(self):
        # Validate inputs and return angles
        x = self.validate_angle(self.xAngleInput.text())
        y = self.validate_angle(self.yAngleInput.text())
        z = self.validate_angle(self.zAngleInput.text())
        
        if x is not None and y is not None and z is not None:
            return x, y, z
        return None

    @staticmethod
    def validate_angle(value: str):
        if is_real_number(value):
            return float(value)
        else:
            QMessageBox.warning(None, "Invalid Input", f"Angle value must be floating point number")
            return None

class MoveActorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Move Actor")

        layout = QVBoxLayout(self)
        formLayout = QFormLayout()

        self.xOffsetInput = QLineEdit("0.0")
        self.yOffsetInput = QLineEdit("0.0")
        self.zOffsetInput = QLineEdit("0.0")
        
        self.xOffsetInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.yOffsetInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.zOffsetInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)

        formLayout.addRow("X Offset:", self.xOffsetInput)
        formLayout.addRow("Y Offset:", self.yOffsetInput)
        formLayout.addRow("Z Offset:", self.zOffsetInput)

        layout.addLayout(formLayout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def getValues(self):
        try:
            x_offset = float(self.xOffsetInput.text())
            y_offset = float(self.yOffsetInput.text())
            z_offset = float(self.zOffsetInput.text())
            return x_offset, y_offset, z_offset
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Offsets must be valid numbers.")
            return None

class PointDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Create Point")
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form layout for input fields
        formLayout = QFormLayout()
        
        # Input fields for the sphere parameters
        self.xInput = QLineEdit("0.0")
        self.yInput = QLineEdit("0.0")
        self.zInput = QLineEdit("0.0")
        
        self.xInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.yInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.zInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        
        formLayout.addRow("Center X:", self.xInput)
        formLayout.addRow("Center Y:", self.yInput)
        formLayout.addRow("Center Z:", self.zInput)
        
        layout.addLayout(formLayout)
        
        # Dialog buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
    
    def getValues(self):        
        if not is_real_number(self.xInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.xInput.text()} isn't a real number")
            return None
        if not is_real_number(self.yInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.yInput.text()} isn't a real number")
            return None
        if not is_real_number(self.zInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.zInput.text()} isn't a real number")
            return None
        return float(self.xInput.text()), float(self.yInput.text()), float(self.zInput.text())


class LineDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setWindowTitle("Create Line")

        self.mainLayout = QVBoxLayout(self)  # Main layout for the dialog
        self.scrollArea = QScrollArea(self)  # Scroll area to contain the form
        self.scrollArea.setWidgetResizable(True)  # Allow the contained widget to resize

        # Container widget for the form
        self.containerWidget = QWidget()
        self.formLayout = QFormLayout()  # Form layout for point inputs

        self.inputs = []  # Store all QLineEdit inputs

        # Initialize with 2 points as default for a simple line
        self.add_point_fields()
        self.add_point_fields()

        self.addButton = QPushButton("[+]")
        self.addButton.setFixedSize(QSize(32, 32))
        self.addButton.clicked.connect(self.add_point_fields)

        # Set the form layout to the container widget and add it to the scroll area
        self.containerWidget.setLayout(self.formLayout)
        self.scrollArea.setWidget(self.containerWidget)

        # Add the scroll area and the add button to the main layout
        self.mainLayout.addWidget(self.scrollArea)
        self.mainLayout.addWidget(self.addButton)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        # Add dialog buttons to the main layout
        self.mainLayout.addWidget(self.buttons)

    def add_point_fields(self):
        point_number = len(self.inputs) // 3 + 1
        # Create a horizontal layout for the x, y, z inputs
        hLayout = QHBoxLayout()
        
        x_input = QLineEdit("0.0")
        y_input = QLineEdit("0.0")
        z_input = QLineEdit("0.0")
        
        x_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        y_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        z_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        
        self.inputs.extend([x_input, y_input, z_input])
        
        # Add the inputs to the horizontal layout
        hLayout.addWidget(QLabel(f"Point {point_number} X:"))
        hLayout.addWidget(x_input)
        hLayout.addWidget(QLabel("Y:"))
        hLayout.addWidget(y_input)
        hLayout.addWidget(QLabel("Z:"))
        hLayout.addWidget(z_input)
        
        # Create a container widget for the horizontal layout and add it to the form
        containerWidget = QWidget()
        containerWidget.setLayout(hLayout)
        self.formLayout.addRow(containerWidget)

    def getValues(self):
        if not all(is_real_number(input_field.text()) for input_field in self.inputs):
            QMessageBox.warning(self, "Invalid input", "All coordinates must be real numbers.")
            return None
        return [float(field.text()) for field in self.inputs]

class SurfaceDialog(QDialog):
    def __init__(self, parent=None):       
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setWindowTitle("Create Arbitrary Surface")

        self.mainLayout = QVBoxLayout(self)  # Main layout for the dialog
        self.scrollArea = QScrollArea(self)  # Scroll area to contain the form
        self.scrollArea.setWidgetResizable(True)  # Allow the contained widget to resize

        # Container widget for the form
        self.containerWidget = QWidget()
        self.formLayout = QFormLayout()  # Form layout for point inputs

        self.inputs = []  # Store all QLineEdit inputs

        # Initialize with 3 points
        for _ in range(3):
            self.add_point_fields()

        self.addButton = QPushButton("[+]")
        self.addButton.setFixedSize(QSize(32, 32))
        self.addButton.clicked.connect(self.add_point_fields)

        # Set the form layout to the container widget and add it to the scroll area
        self.containerWidget.setLayout(self.formLayout)
        self.scrollArea.setWidget(self.containerWidget)

        # Add the scroll area and the add button to the main layout
        self.mainLayout.addWidget(self.scrollArea)
        self.mainLayout.addWidget(self.addButton)
        
        self.meshSizeInput = QLineEdit("1.0")
        self.meshSizeInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.meshSizeLabel = QLabel("Mesh size:")
        meshLayout = QHBoxLayout()
        meshLayout.addWidget(self.meshSizeLabel)
        meshLayout.addWidget(self.meshSizeInput)
        self.mainLayout.addLayout(meshLayout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        # Add dialog buttons to the main layout
        self.mainLayout.addWidget(self.buttons)
        

    def add_point_fields(self):
        point_number = len(self.inputs) // 3 + 1
        # Create a horizontal layout for the x, y, z inputs
        hLayout = QHBoxLayout()
        
        x_input = QLineEdit("0.0")
        y_input = QLineEdit("0.0")
        z_input = QLineEdit("0.0")
        
        x_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        y_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        z_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        
        self.inputs.extend([x_input, y_input, z_input])
        
        # Add the inputs to the horizontal layout
        hLayout.addWidget(QLabel(f"Point {point_number} X:"))
        hLayout.addWidget(x_input)
        hLayout.addWidget(QLabel("Y:"))
        hLayout.addWidget(y_input)
        hLayout.addWidget(QLabel("Z:"))
        hLayout.addWidget(z_input)
        
        # Create a container widget for the horizontal layout and add it to the form
        containerWidget = QWidget()
        containerWidget.setLayout(hLayout)
        self.formLayout.addRow(containerWidget)


    def getValues(self):
        if not all(is_real_number(input_field.text()) for input_field in self.inputs):
            QMessageBox.warning(self, "Invalid input", "All coordinates must be real numbers.")
            return None
        values = [float(field.text()) for field in self.inputs]
        
        mesh_size = 1.0
        if not is_real_number(self.meshSizeInput.text()):
            QMessageBox.warning(self, "Invalid input", "Mesh size must be floating point number.")
            return None
        mesh_size = float(self.meshSizeInput.text())
            
        return values, mesh_size


class SphereDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Sphere")
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form layout for input fields
        formLayout = QFormLayout()
        
        # Input fields for the sphere parameters
        self.xInput = QLineEdit("0.0")
        self.yInput = QLineEdit("0.0")
        self.zInput = QLineEdit("0.0")
        self.radiusInput = QLineEdit("5.0")
        self.meshSizeInput = QLineEdit("1.0")
        
        self.xInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.yInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.zInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.radiusInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.meshSizeInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        
        formLayout.addRow("Center X:", self.xInput)
        formLayout.addRow("Center Y:", self.yInput)
        formLayout.addRow("Center Z:", self.zInput)
        formLayout.addRow("Radius:", self.radiusInput)
        formLayout.addRow("Mesh size:", self.meshSizeInput)
        
        layout.addLayout(formLayout)
        
        # Dialog buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
        
    def getValues(self):        
        if not is_real_number(self.xInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.xInput.text()} isn't a real number")
            return None
        if not is_real_number(self.yInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.yInput.text()} isn't a real number")
            return None
        if not is_real_number(self.zInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.zInput.text()} isn't a real number")
            return None
        if not is_positive_real_number(self.radiusInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.radiusInput.text()} isn't a real positive number")
            return None
        values = float(self.xInput.text()), float(self.yInput.text()), float(self.zInput.text()), float(self.radiusInput.text())
        
        mesh_size = 0.0
        if not is_real_number(self.meshSizeInput.text()):
            QMessageBox.warning(self, "Invalid input", "Mesh size must be floating point number.")
            return None
        mesh_size = float(self.meshSizeInput.text())
        
        return values, mesh_size


class BoxDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Box")
        
        layout = QVBoxLayout(self)
        formLayout = QFormLayout()
        
        self.xInput = QLineEdit("0.0")
        self.yInput = QLineEdit("0.0")
        self.zInput = QLineEdit("0.0")
        self.lengthInput = QLineEdit("5.0")
        self.widthInput = QLineEdit("5.0")
        self.heightInput = QLineEdit("5.0")
        self.meshSizeInput = QLineEdit("1.0")
        
        self.xInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.yInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.zInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.lengthInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.widthInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.heightInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.meshSizeInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        
        formLayout.addRow("Center X:", self.xInput)
        formLayout.addRow("Center Y:", self.yInput)
        formLayout.addRow("Center Z:", self.zInput)
        formLayout.addRow("Length:", self.lengthInput)
        formLayout.addRow("Width:", self.widthInput)
        formLayout.addRow("Height:", self.heightInput)
        formLayout.addRow("Mesh size:", self.meshSizeInput)
        
        layout.addLayout(formLayout)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
    
    def getValues(self):
        if not is_real_number(self.xInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.xInput.text()} isn't a real number")
            return None
        if not is_real_number(self.yInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.yInput.text()} isn't a real number")
            return None
        if not is_real_number(self.zInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.zInput.text()} isn't a real number")
            return None
        if not is_real_number(self.lengthInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.lengthInput.text()} isn't a real number")
            return None
        if not is_real_number(self.widthInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.widthInput.text()} isn't a real number")
            return None
        if not is_real_number(self.heightInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.heightInput.text()} isn't a real number")
            return None
        values = (float(self.xInput.text()), float(self.yInput.text()), float(self.zInput.text()),
                float(self.lengthInput.text()), float(self.widthInput.text()), float(self.heightInput.text()))
        
        mesh_size = 1.0
        if not is_real_number(self.meshSizeInput.text()):
            QMessageBox.warning(self, "Invalid input", "Mesh size must be floating point number.")
            return None
        mesh_size = float(self.meshSizeInput.text())

        return values, mesh_size


class CylinderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Cylinder")
        
        layout = QVBoxLayout(self)
        formLayout = QFormLayout()
        
        self.xInput = QLineEdit("0.0")
        self.yInput = QLineEdit("0.0")
        self.zInput = QLineEdit("0.0")
        self.radiusInput = QLineEdit("2.5")
        self.dxInput = QLineEdit("5.0")
        self.dyInput = QLineEdit("5.0")
        self.dzInput = QLineEdit("5.0")
        self.meshSizeInput = QLineEdit("1.0")
        
        self.xInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.yInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.zInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.radiusInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.dxInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.dyInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.dzInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.meshSizeInput.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        
        formLayout.addRow("Base center X:", self.xInput)
        formLayout.addRow("Base center Y:", self.yInput)
        formLayout.addRow("Base center Z:", self.zInput)
        formLayout.addRow("Radius:", self.radiusInput)
        formLayout.addRow("Top center X:", self.dxInput)
        formLayout.addRow("Top center Y:", self.dyInput)
        formLayout.addRow("Top center Z:", self.dzInput)
        formLayout.addRow("Mesh size:", self.meshSizeInput)   
        
        layout.addLayout(formLayout)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
    
    def getValues(self):
        if not is_real_number(self.xInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.xInput.text()} isn't a real number")
            return None
        if not is_real_number(self.yInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.yInput.text()} isn't a real number")
            return None
        if not is_real_number(self.zInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.zInput.text()} isn't a real number")
            return None
        if not is_positive_real_number(self.radiusInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.radiusInput.text()} isn't a real positive number")
            return None
        if not is_real_number(self.dxInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.dxInput.text()} isn't a real number")
            return None
        if not is_real_number(self.dyInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.dyInput.text()} isn't a real number")
            return None
        if not is_real_number(self.dzInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.dzInput.text()} isn't a real number")
            return None
        values = (float(self.xInput.text()), float(self.yInput.text()), float(self.zInput.text()),
                float(self.radiusInput.text()), float(self.dxInput.text()), float(self.dyInput.text()), float(self.dzInput.text()))
        
        mesh_size = 1.0
        if not is_real_number(self.meshSizeInput.text()):
            QMessageBox.warning(self, "Invalid input", "Mesh size must be floating point number.")
            return None
        mesh_size = float(self.meshSizeInput.text())
        
        return values, mesh_size

class ShortcutsInfoDialog(QDialog):
    def __init__(self, shortcuts, parent=None):
        super().__init__(parent)
        self.shortcuts = shortcuts
        self.setWindowTitle("Keyboard Shortcuts")
        self.init_ui()


    def init_ui(self):
        self.setMinimumSize(700, 400)
        
        layout = QVBoxLayout(self)
        table = QTableWidget(len(self.shortcuts), 3)
        table.setHorizontalHeaderLabels(["Action", "Shortcut", "Description"])
        table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make the table read-only
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        for i, shortcut_info in enumerate(self.shortcuts):
            action, shortcut, description = shortcut_info
            table.setItem(i, 0, QTableWidgetItem(action))
            table.setItem(i, 1, QTableWidgetItem(shortcut))
            table.setItem(i, 2, QTableWidgetItem(description))
        
        table.resizeColumnsToContents()
        layout.addWidget(table)

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


class ExpansionAngleDialogNonModal(QDialog):
    accepted_signal = pyqtSignal(float)

    def __init__(self, vtkWidget: QVTKRenderWindowInteractor, renderer: vtkRenderer, arrowActor: vtkActor, parent=None):
        super(ExpansionAngleDialogNonModal, self).__init__(parent)
        
        self.arrowActor = arrowActor
        self.vtkWidget = vtkWidget
        self.renderer = renderer
        
        self.setWindowTitle("Set Expansion Angle")
        
        layout = QVBoxLayout(self)
        
        self.theta_input = QLineEdit(self)
        self.theta_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.theta_input.setValidator(QDoubleValidator(0.0, 180.0, 6))
        
        layout.addWidget(QLabel("Expansion Angle θ (degrees):"))
        layout.addWidget(self.theta_input)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.handle_accept)
        button_box.rejected.connect(self.handle_reject)
        
        layout.addWidget(button_box)
        
    def resetArrowActor(self):
        self.renderer.RemoveActor(self.arrowActor)
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
        self.arrowActor = None
    
    def handle_accept(self):
        try:
            theta = float(self.theta_input.text())
            self.accepted_signal.emit(radians(theta))
            self.close()
            self.resetArrowActor()            
        except ValueError:
            QMessageBox.warning(self, "Invalid input", "Please enter a valid numerical value.")
    
    def handle_reject(self):
        self.close()
        self.resetArrowActor()
        
    def closeEvent(self, event):
        self.resetArrowActor()
        super().closeEvent(event)


class ExpansionAngleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Expansion Angle")

        layout = QVBoxLayout(self)

        self.theta_input = QLineEdit(self)
        self.theta_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        layout.addWidget(QLabel("Expansion angle θ (in degrees °)"))
        layout.addWidget(self.theta_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
    
    def getTheta(self):
        theta_str = self.theta_input.text()
        if not is_positive_real_number(theta_str):
            QMessageBox.warning(self, "Invalid Input", f"{self.theta_input.text()} isn't a positive real number")
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
    

class ArrowPropertiesDialog(QDialog):
    properties_accepted = pyqtSignal(tuple)

    def __init__(self, vtkWidget, renderer, arrowActor: vtkActor, parent=None):
        super(ArrowPropertiesDialog, self).__init__(parent)
        
        self.vtkWidget = vtkWidget
        self.renderer = renderer
        self.arrowActor = arrowActor
        self.arrowSize = ARROW_DEFAULT_SCALE[0]
        
        self.setWindowTitle("Set Arrow Properties")
        
        layout = QVBoxLayout(self)
        
        self.x_input = QLineEdit(self)
        self.y_input = QLineEdit(self)
        self.z_input = QLineEdit(self)
        self.angle_x_input = QLineEdit(self)
        self.angle_y_input = QLineEdit(self)
        self.angle_z_input = QLineEdit(self)
        
        self.x_input.setValidator(QDoubleValidator())
        self.y_input.setValidator(QDoubleValidator())
        self.z_input.setValidator(QDoubleValidator())
        self.angle_x_input.setValidator(QDoubleValidator())
        self.angle_y_input.setValidator(QDoubleValidator())
        self.angle_z_input.setValidator(QDoubleValidator())
        
        self.x_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.y_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.z_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.angle_x_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.angle_y_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.angle_z_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        
        layout.addWidget(QLabel("X Coordinate:"))
        layout.addWidget(self.x_input)
        layout.addWidget(QLabel("Y Coordinate:"))
        layout.addWidget(self.y_input)
        layout.addWidget(QLabel("Z Coordinate:"))
        layout.addWidget(self.z_input)
        layout.addWidget(QLabel("Rotation Angle around X-axis (degrees):"))
        layout.addWidget(self.angle_x_input)
        layout.addWidget(QLabel("Rotation Angle around Y-axis (degrees):"))
        layout.addWidget(self.angle_y_input)
        layout.addWidget(QLabel("Rotation Angle around Z-axis (degrees):"))
        layout.addWidget(self.angle_z_input)
        
        size_button = QPushButton("Set Arrow Size")
        size_button.clicked.connect(self.open_size_dialog)
        layout.addWidget(size_button)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout.addWidget(button_box)

        button_box.accepted.connect(self.accept_and_emit)
        button_box.rejected.connect(self.reject)

        self.x_input.textChanged.connect(self.update_arrow)
        self.y_input.textChanged.connect(self.update_arrow)
        self.z_input.textChanged.connect(self.update_arrow)
        self.angle_x_input.textChanged.connect(self.update_arrow)
        self.angle_y_input.textChanged.connect(self.update_arrow)
        self.angle_z_input.textChanged.connect(self.update_arrow)

    def open_size_dialog(self):
        self.size_dialog = ArrowSizeDialog(self.arrowSize, self)
        self.size_dialog.size_changed.connect(self.update_arrow_size)
        self.size_dialog.show()
    
    def update_arrow_size(self, size):
        self.arrowSize = size
        self.update_arrow()
    
    def update_arrow(self):
        properties = self.getProperties()
        if properties:
            x, y, z, angle_x, angle_y, angle_z, size = properties
            self.resetArrowActor()
            self.create_direction_arrow_manually(x, y, z, angle_x, angle_y, angle_z, self.arrowSize)

    def getProperties(self):
        try:
            x = float(self.x_input.text())
            y = float(self.y_input.text())
            z = float(self.z_input.text())
            angle_x = float(self.angle_x_input.text())
            angle_y = float(self.angle_y_input.text())
            angle_z = float(self.angle_z_input.text())
            return x, y, z, angle_x, angle_y, angle_z, self.arrowSize
        except ValueError:
            return None
    
    def resetArrowActor(self):
        if self.arrowActor:
            self.renderer.RemoveActor(self.arrowActor)
            self.renderer.ResetCamera()
            self.vtkWidget.GetRenderWindow().Render()
            self.arrowActor = None
    
    def addArrowActor(self):
        self.renderer.AddActor(self.arrowActor)
        self.arrowActor.GetProperty().SetColor(ARROW_ACTOR_COLOR)
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
        
    def create_direction_arrow_manually(self, x, y, z, angle_x, angle_y, angle_z, size):        
        arrowSource = vtkArrowSource()
        arrowSource.SetTipLength(0.25)
        arrowSource.SetTipRadius(0.1)
        arrowSource.SetShaftRadius(0.01)
        arrowSource.Update()
        arrowSource.SetTipResolution(100)

        arrowTransform = vtkTransform()
        arrowTransform.Translate(x, y, z)
        arrowTransform.RotateX(angle_x)
        arrowTransform.RotateY(angle_y)
        arrowTransform.RotateZ(angle_z)
        arrowTransform.Scale(size, size, size)
        arrowTransformFilter = vtkTransformPolyDataFilter()
        arrowTransformFilter.SetTransform(arrowTransform)
        arrowTransformFilter.SetInputConnection(arrowSource.GetOutputPort())
        arrowTransformFilter.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(arrowTransformFilter.GetOutputPort())
        
        self.arrowActor = vtkActor()
        self.arrowActor.SetMapper(mapper)
        self.arrowActor.GetProperty().SetColor(ARROW_ACTOR_COLOR)
        
        self.addArrowActor()
    
    def accept_and_emit(self):
        properties = self.getProperties()
        if properties:
            self.properties_accepted.emit(properties)
            self.accept()
            self.resetArrowActor()
        else:
            QMessageBox.warning(self, "Invalid input", "Please enter valid numerical values.")
            
    def reject(self):
        self.resetArrowActor()
        super(ArrowPropertiesDialog, self).reject()

    def closeEvent(self, event):
        self.resetArrowActor()
        super(ArrowPropertiesDialog, self).closeEvent(event)

class MethodSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super(MethodSelectionDialog, self).__init__(parent)
        
        self.setWindowTitle("Select Method")
        
        layout = QVBoxLayout(self)
        
        label = QLabel("Do you want to set the parameters manually or interactively?")
        layout.addWidget(label)
        
        button_box = QDialogButtonBox(self)
        self.manual_button = QPushButton("Manually")
        self.interactive_button = QPushButton("Interactively")
        button_box.addButton(self.manual_button, QDialogButtonBox.AcceptRole)
        button_box.addButton(self.interactive_button, QDialogButtonBox.AcceptRole)
        
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


class CustomDoubleValidator(QDoubleValidator):
    def __init__(self, bottom, top, decimals, parent=None):
        super().__init__(bottom, top, decimals, parent)
    
    def validate(self, input_str, pos):
        if not input_str:
            return (self.Intermediate, input_str, pos)
        
        if '.' in input_str:
            try:
                value = float(input_str)
                if self.bottom() <= value <= self.top():
                    return (self.Acceptable, input_str, pos)
                else:
                    return (self.Invalid, input_str, pos)
            except ValueError:
                return (self.Invalid, input_str, pos)
        else:
            try:
                value = int(input_str)
                if self.bottom() <= value <= self.top():
                    return (self.Acceptable, input_str, pos)
                else:
                    return (self.Invalid, input_str, pos)
            except ValueError:
                return (self.Invalid, input_str, pos)
        
        return (self.Intermediate, input_str, pos)
    
class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"Point(x={self.x}, y={self.y}, z={self.z})"

class ActionHistory:
    def __init__(self):
        self.id = 0           # Counter for the current ID of objects
        self.undo_stack = {}  # Stack to keep track of undo actions
        self.redo_stack = {}  # Stack to keep track of redo actions

    def add_action(self, object_on_stack):
        """
        Add a new action to the history. This clears the redo stack.
        """
        self.undo_stack[self.id] = object_on_stack

    def undo(self):
        """
        Undo the last action.
        Returns the row_id and actors for the undone action.
        """
        if not self.undo_stack:
            return None
        last_id = max(self.undo_stack.keys())
        object_on_stack = self.undo_stack.pop(last_id)
        self.redo_stack[last_id] = object_on_stack
        return object_on_stack

    def redo(self):
        """
        Redo the last undone action.
        Returns the row_id and actors for the redone action.
        """
        if not self.redo_stack:
            return None
        last_id = max(self.redo_stack.keys())
        object_on_stack = self.redo_stack.pop(last_id)
        self.undo_stack[last_id] = object_on_stack
        return object_on_stack
    
    def remove_by_id(self, id: int):
        """
        Remove action by ID from both undo and redo stacks.
        """
        if id in self.undo_stack:
            del self.undo_stack[id]
        if id in self.redo_stack:
            del self.redo_stack[id]
    
    def get_id(self):
        return self.id
    
    def decrementIndex(self):
        self.id -= 1
    
    def incrementIndex(self):
        self.id += 1
    
    def clearIndex(self):
        self.id = 0
    

class ParticleSourceDialog(QDialog):
    accepted_signal = pyqtSignal(dict)
    rejected_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Particle Source Parameters")

        layout = QFormLayout(self)

        # Particle type
        self.particle_type_combo = QComboBox()
        self.particle_type_combo.addItems(["Ti", "Al", "Sn", "W", "Au", "Cu", "Ni", "Ag"])
        layout.addRow("Particle Type:", self.particle_type_combo)

        # Energy
        self.energy_input = QLineEdit()
        self.energy_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        energy_validator = QDoubleValidator(0.0, 10000.0, 6, self)  # Range of the energy in [eV]
        self.energy_input.setValidator(energy_validator)
        layout.addRow("Energy (eV):", self.energy_input)

        # Number of particles
        self.num_particles_input = QLineEdit()
        self.num_particles_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        num_particles_validator = QIntValidator(1, 1000000000, self)  # Range of particle count
        self.num_particles_input.setValidator(num_particles_validator)
        layout.addRow("Number of Particles:", self.num_particles_input)

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
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
            QMessageBox.warning(self, "Invalid input", "Please enter valid numerical values.")

    def handle_reject(self):
        self.rejected_signal.emit()
        self.close()

    def closeEvent(self, event):
        super().closeEvent(event)


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
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
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

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def getSelectedSourceType(self):
        return self.comboBox.currentText()


class BoundaryValueInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Set Boundary Value")

        # Create layout and widgets
        layout = QVBoxLayout()
        self.label = QLabel("Enter value:")
        self.input = QLineEdit()
        self.input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)

        # Buttons
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        # Add widgets to layout
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect buttons to dialog slots
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_value(self):
        try:
            value = float(self.input.text())
            return value, True
        except ValueError:
            return None, False


class NormalOrientationDialog(QDialog):
    orientation_accepted = pyqtSignal(bool, float)  # Signal with orientation (bool) and arrow size (float)
    size_changed = pyqtSignal(float)  # Signal for size change in real-time

    def __init__(self, initial_size=1.0, parent=None):
        super(NormalOrientationDialog, self).__init__(parent)
        
        self.setWindowTitle("Normal Orientation and Arrow Size")
        
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
        self.size_changed.emit(size)  # Emit the size change signal

    def update_size_slider(self):
        try:
            size = float(self.size_input.text())
            if 0.01 <= size <= 100:
                self.size_slider.setValue(int(size * 100))
                self.size_changed.emit(size)  # Emit the size change signal
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


class SurfaceAndArrowManager:
    def __init__(self, vtkWidget, renderer, log_console, selected_actors: set, parent=None):
        self.vtkWidget = vtkWidget
        self.renderer = renderer
        self.log_console = log_console
        self.selected_actors = selected_actors
        self.arrow_size = ARROW_DEFAULT_SCALE[0]
        self.selected_actor = None
        self.parent = parent
        
    def render_editor_window(self):
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()

    def set_particle_source_as_surface(self):
        if not self.selected_actors:
            self.log_console.printWarning("There is no selected surfaces to apply particle source on them")
            QMessageBox.information(self.parent, "Set Particle Source", "There is no selected surfaces to apply particle source on them")
            return

        self.selected_actor = list(self.selected_actors)[0]
        self.select_surface_and_normals(self.selected_actor)
        if not self.selected_actor:
            return
        
        self.particle_source_dialog = ParticleSourceDialog(self.parent)
        self.particle_source_dialog.accepted_signal.connect(lambda params: self.handle_particle_source_surface_accepted(params, self.data))
        self.particle_source_dialog.show()

    def handle_particle_source_surface_accepted(self, particle_params, surface_and_normals_dict):
        try:
            particle_type = particle_params["particle_type"]
            energy = particle_params["energy"]
            num_particles = particle_params["num_particles"]
            
            self.log_console.printInfo("Particle source set as surface source\n"
                                    f"Particle Type: {particle_type}\n"
                                    f"Energy: {energy} eV\n"
                                    f"Number of Particles: {num_particles}")
            self.log_console.addNewLine()
            
            self.parent.update_config_with_particle_source(particle_params, surface_and_normals_dict)
        except Exception as e:
            self.log_console.printError(f"Error setting particle source. {e}")
            QMessageBox.warning(self.parent, "Particle Source", f"Error setting particle source. {e}")
            return None

    def add_arrows(self, arrows):
        for arrow_actor, _, _ in arrows:
            self.renderer.AddActor(arrow_actor)
        self.render_editor_window()

    def remove_arrows(self, arrows):
        for arrow_actor, _, _ in arrows:
            self.renderer.RemoveActor(arrow_actor)
        self.render_editor_window()

    def update_arrow_sizes(self, size):
        for arrow_actor, cell_center, normal in self.arrows_outside:
            self.renderer.RemoveActor(arrow_actor)
        for arrow_actor, cell_center, normal in self.arrows_inside:
            self.renderer.RemoveActor(arrow_actor)

        self.arrows_outside = [
            (self.create_arrow_actor(cell_center, normal, size), cell_center, normal)
            for _, cell_center, normal in self.arrows_outside
        ]
        self.arrows_inside = [
            (self.create_arrow_actor(cell_center, normal, size), cell_center, normal)
            for _, cell_center, normal in self.arrows_inside
        ]

        self.add_arrows(self.arrows_outside)

    def populate_data(self, arrows, data):
        for arrow_actor, cell_center, normal in arrows:
            actor_address = hex(id(arrow_actor))
            data[actor_address] = {"cell_center": cell_center, "normal": normal}

    def select_surface_and_normals(self, actor: vtkActor):        
        poly_data = actor.GetMapper().GetInput()
        normals = self.calculate_normals(poly_data)

        if not normals:
            self.log_console.printWarning("No normals found for the selected surface")
            QMessageBox.warning(self.parent, "Normals Calculation", "No normals found for the selected surface")
            return

        self.num_cells = poly_data.GetNumberOfCells()
        self.arrows_outside = []
        self.arrows_inside = []
        self.data = {}

        for i in range(self.num_cells):
            normal = normals.GetTuple(i)
            rev_normal = tuple(-n if n != 0 else 0.0 for n in normal)
            cell = poly_data.GetCell(i)
            cell_center = self.calculate_cell_center(cell)

            arrow_outside = self.create_arrow_actor(cell_center, normal, self.arrow_size)
            arrow_inside = self.create_arrow_actor(cell_center, rev_normal, self.arrow_size)
            
            self.arrows_outside.append((arrow_outside, cell_center, normal))
            self.arrows_inside.append((arrow_inside, cell_center, rev_normal))
        self.add_arrows(self.arrows_outside)
        
        self.normal_orientation_dialog = NormalOrientationDialog(self.arrow_size, self.parent)
        self.normal_orientation_dialog.orientation_accepted.connect(self.handle_outside_confirmation)
        self.normal_orientation_dialog.size_changed.connect(self.update_arrow_sizes)  # Connect the size change signal
        self.normal_orientation_dialog.show()

    def handle_outside_confirmation(self, confirmed, size):
        self.arrow_size = size
        if confirmed:
            self.populate_data(self.arrows_outside, self.data)
            self.finalize_surface_selection()
        else:
            self.remove_arrows(self.arrows_outside)
            self.add_arrows(self.arrows_inside)
            self.normal_orientation_dialog = NormalOrientationDialog(self.arrow_size, self.parent)
            self.normal_orientation_dialog.msg_label.setText("Do you want to set normals inside?")
            self.normal_orientation_dialog.orientation_accepted.connect(self.handle_inside_confirmation)
            self.normal_orientation_dialog.size_changed.connect(self.update_arrow_sizes)  # Connect the size change signal
            self.normal_orientation_dialog.show()

    def handle_inside_confirmation(self, confirmed, size):
        self.arrow_size = size
        if confirmed:
            self.populate_data(self.arrows_inside, self.data)
            self.finalize_surface_selection()
        else:
            self.remove_arrows(self.arrows_inside)

    def finalize_surface_selection(self):
        self.remove_arrows(self.arrows_outside)
        self.remove_arrows(self.arrows_inside)

        if not self.data:
            return

        surface_address = next(iter(self.data))
        self.log_console.printInfo(f"Selected surface <{surface_address}> with {self.num_cells} cells inside:")
        for arrow_address, values in self.data.items():
            cellCentre = values['cell_center']
            normal = values['normal']
            self.log_console.printInfo(f"<{surface_address}> | <{arrow_address}>: [{cellCentre[0]:.2f}, {cellCentre[1]:.2f}, {cellCentre[2]:.2f}] - ({normal[0]:.2f}, {normal[1]:.2f}, {normal[2]:.2f})")
            surface_address = next(iter(self.data))
        
        self.parent.deselect()


    def confirm_normal_orientation(self, orientation):
        msg_box = QMessageBox(self.parent)
        msg_box.setWindowTitle("Normal Orientation")
        msg_box.setText(f"Do you want to set normals {orientation}?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        result = msg_box.exec_()
        
        return result == QMessageBox.Yes

    def calculate_normals(self, poly_data):
        normals_filter = vtkPolyDataNormals()
        normals_filter.SetInputData(poly_data)
        normals_filter.ComputePointNormalsOff()
        normals_filter.ComputeCellNormalsOn()
        normals_filter.Update()

        return normals_filter.GetOutput().GetCellData().GetNormals()

    def calculate_cell_center(self, cell):
        cell_center = [0.0, 0.0, 0.0]
        points = cell.GetPoints()
        num_points = points.GetNumberOfPoints()
        for j in range(num_points):
            point = points.GetPoint(j)
            cell_center[0] += point[0]
            cell_center[1] += point[1]
            cell_center[2] += point[2]
        return [coord / num_points for coord in cell_center]

    def create_arrow_actor(self, position, direction, arrow_size):
        arrow_source = vtkArrowSource()
        arrow_source.SetTipLength(0.2)
        arrow_source.SetShaftRadius(0.02)
        arrow_source.SetTipResolution(100)

        transform = vtkTransform()
        transform.Translate(position)
        transform.Scale(arrow_size, arrow_size, arrow_size)

        direction_list = list(direction)
        norm = vtkMath.Norm(direction_list)
        if norm > 0:
            vtkMath.Normalize(direction_list)
            x_axis = [1, 0, 0]
            angle = vtkMath.AngleBetweenVectors(x_axis, direction_list)
            
            if direction == [-1.0, 0.0, 0.0] or direction == [1.0, 0.0, 0.0]:
                rotation_axis = [0.0, 1.0, 0.0]
            else:
                rotation_axis = [0.0, 0.0, 0.0]
                vtkMath.Cross(x_axis, direction_list, rotation_axis)
                if vtkMath.Norm(rotation_axis) == 0:
                    rotation_axis = [0.0, 1.0, 0.0]
            transform.RotateWXYZ(vtkMath.DegreesFromRadians(angle), *rotation_axis)

        transform_filter = vtkTransformPolyDataFilter()
        transform_filter.SetInputConnection(arrow_source.GetOutputPort())
        transform_filter.SetTransform(transform)
        transform_filter.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(transform_filter.GetOutputPort())

        arrow_actor = vtkActor()
        arrow_actor.SetMapper(mapper)
        arrow_actor.GetProperty().SetColor(ARROW_ACTOR_COLOR)

        return arrow_actor


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
            self.materials_combobox.setItemData(self.materials_combobox.count() - 1, hint, Qt.ToolTipRole)
        
        self.material_names = set(material for material in self.default_materials)
        self.layout.addWidget(QLabel('Select a material:'))
        self.layout.addWidget(self.materials_combobox)
        
        # Plus button for custom material
        self.add_custom_material_button = QPushButton('[+] Add Custom Material')
        self.add_custom_material_button.clicked.connect(self.add_custom_material)
        self.layout.addWidget(self.add_custom_material_button)
        
        # Load materials button
        self.load_materials_button = QPushButton('Load Materials from File')
        self.load_materials_button.clicked.connect(self.load_materials_from_file)
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
                self.materials_combobox.setItemData(self.materials_combobox.count() - 1, hint, Qt.ToolTipRole)
                self.save_custom_materials_to_file()
                self.material_names.add(material_name)

    def save_custom_materials_to_file(self):
        with open('materials.json', 'w') as file:
            dump(self.custom_materials, file, indent=4)
            
    def save_materials_to_file(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, 'Save Materials File', '', 'JSON Files (*.json)')
            if file_path:
                if not file_path.endswith('.json'):
                    file_path += '.json'
                if exists(file_path):
                    reply = QMessageBox.question(self, 'Overwrite File', 'File already exists. Do you want to overwrite it?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply == QMessageBox.No:
                        return
                
                # Collect all materials from the combo box
                all_materials = []
                for i in range(self.materials_combobox.count()):
                    display_name = self.materials_combobox.itemText(i)
                    hint = self.materials_combobox.itemData(i, Qt.ToolTipRole)
                    name, components_str = display_name.split(' (')
                    components_str = components_str[:-1]  # Remove the trailing ')'
                    components = dict([comp.split(': ') for comp in components_str.split(', ')])
                    components = {k: float(v[:-1]) for k, v in components.items()}  # Convert percentages to floats
                    all_materials.append({name: components})

                with open(file_path, 'w') as file:
                    dump(all_materials, file, indent=4)
                
                QMessageBox.information(self, 'Success', f'Materials saved to {file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save materials: {e}')

    def apply_material(self):
        # TODO: implement
        pass

    def load_materials_from_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, 'Open Materials File', '', 'JSON Files (*.json)')
            if file_path:
                with open(file_path, 'r') as file:
                    materials = load(file)

                    existing_names = {self.materials_combobox.itemText(i) for i in range(self.materials_combobox.count())}
                    existing_compositions = {
                        tuple(sorted(components.items())): name
                        for name, components in self.default_materials.items()
                    }
                    for i in range(self.materials_combobox.count()):
                        hint = self.materials_combobox.itemData(i, Qt.ToolTipRole)
                        composition = tuple(sorted((component.split(': ')[0], float(component.split(': ')[1][:-1])) for component in hint.split(', ')))
                        existing_compositions[composition] = self.materials_combobox.itemText(i)

                    name_conflicts = []
                    composition_conflicts = []

                    for material in materials:
                        for name, components in material.items():
                            hint = ', '.join([f'{k}: {v}%' for k, v in components.items()])
                            composition = tuple(sorted(components.items()))

                            if name in existing_names:
                                name_conflicts.append(name)
                            elif composition in existing_compositions:
                                composition_conflicts.append(f'{name} vs {existing_compositions[composition]}')
                            else:
                                display_name = f"{name} ({hint})"
                                self.materials_combobox.addItem(display_name)
                                self.materials_combobox.setItemData(self.materials_combobox.count() - 1, hint, Qt.ToolTipRole)
                                self.custom_materials.append({name: components})
                                self.material_names.add(name)

                    if name_conflicts:
                        QMessageBox.warning(self, 'Name Conflicts', 'These materials have conflicting names:\n' + '\n'.join(name_conflicts))

                    if composition_conflicts:
                        QMessageBox.warning(self, 'Composition Conflicts', 'These materials have conflicting compositions:\n' + '\n'.join(composition_conflicts))


        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load materials: {e}')



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
        element_percentage.textChanged.connect(self.update_remaining_percentage)

        delete_button = QPushButton('Delete')
        delete_button.clicked.connect(lambda: self.remove_element_input(element_layout))

        select_element_button.clicked.connect(lambda: self.open_periodic_table(element_label))
        
        element_layout.addWidget(select_element_button)
        element_layout.addWidget(element_label)
        element_layout.addWidget(element_percentage)
        element_layout.addWidget(delete_button)
        
        self.element_layout.addLayout(element_layout)
        self.update_remaining_percentage()
        
    def open_periodic_table(self, element_label):
        self.periodic_table = PeriodicTableWindow()
        self.periodic_table.element_selected.connect(lambda element: self.set_element(element_label, element))
        self.periodic_table.exec_()
        
    def remove_element_input(self, element_layout):
        if self.element_layout.count() <= 1:
            QMessageBox.warning(self, 'Invalid Operation', 'Cannot remove the last remaining element.')
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
                QMessageBox.warning(self, 'Invalid Input', 'Duplicate elements are not allowed.')
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
            available_elements = [e for e in CHEMICAL_ELEMENTS if e not in selected_elements or e == current_element]

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
            self.remaining_percentage_label.setText(f'Remaining percentage: {self.remaining_percentage:.2f}%')

            # Enable or disable the add element button and change its color
            if self.remaining_percentage <= 0:
                self.add_element_button.setDisabled(True)
                self.add_element_button.setStyleSheet(DEFAULT_DISABLED_BUTTON_STYLE)
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
                QMessageBox.warning(self, 'Invalid Input', 'The name field cannot be empty.')
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
                    QMessageBox.warning(self, 'Invalid Input', 'Element cannot be "None". Please select a valid element.')
                    return
                percentage_edit = layout.itemAt(2).widget()
                total_percentage += float(percentage_edit.text())

            if total_percentage != 100:
                QMessageBox.warning(self, 'Invalid Input', 'Total percentage must be exactly 100%.')
                return

            self.accept()
        except ValueError:
            QMessageBox.warning(self, 'Invalid Input', 'Please enter valid percentages')
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
            'transition_metals': '#FFB6C1',        # Light Pink
            'post_transition_metals': '#C0C0C0',   # Silver
            'metalloids': '#DFFF00',               # Chartreuse Yellow
            'non_metals': '#ADFF2F',               # Green Yellow
            'halogens': '#FFFF66',                 # Light Yellow
            'noble_gases': '#ADD8E6',              # Light Blue
            'lanthanides': '#FFB6C1',              # Light Pink
            'actinides': '#FFB6C1',                # Light Pink
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
            'Cs': (5, 0), 'Ba': (5, 1), 'La': (5, 2), 'Hf': (5, 3), 'Ta': (5, 4), 'W': (5, 5), 'Re': (5, 6), 'Os': (5, 7),
            'Ir': (5, 8), 'Pt': (5, 9), 'Au': (5, 10), 'Hg': (5, 11), 'Tl': (5, 12), 'Pb': (5, 13), 'Bi': (5, 14), 'Po': (5, 15),
            'At': (5, 16), 'Rn': (5, 17),
            'Fr': (6, 0), 'Ra': (6, 1), 'Ac': (6, 2), 'Rf': (6, 3), 'Db': (6, 4), 'Sg': (6, 5), 'Bh': (6, 6), 'Hs': (6, 7),
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
            button.setStyleSheet(f"background-color: {color}; border-radius: 10px;")
            
            font = QFont()
            font.setPointSize(16)
            button.setFont(font)
            
            button.clicked.connect(lambda _, el=element: self.on_element_clicked(el))
            self.layout.addWidget(button, row, col)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create button for {element}: {e}")

    def on_element_clicked(self, element):
        self.element_selected.emit(element)
        self.close()
    

def align_view_by_axis(axis: str, renderer: vtkRenderer, vtkWidget: QVTKRenderWindowInteractor):
    axis = axis.strip().lower()

    if axis not in ['x', 'y', 'z', 'center']:
        return
    
    camera = renderer.GetActiveCamera()
    if axis == 'x':
        camera.SetPosition(1, 0, 0)
        camera.SetViewUp(0, 0, 1)
    elif axis == 'y':
        camera.SetPosition(0, 1, 0)
        camera.SetViewUp(0, 0, 1)
    elif axis == 'z':
        camera.SetPosition(0, 0, 1)
        camera.SetViewUp(0, 1, 0)
    elif axis == 'center':
        camera.SetPosition(1, 1, 1)
        camera.SetViewUp(0, 0, 1)
            
    camera.SetFocalPoint(0, 0, 0)
        
    renderer.ResetCamera()
    vtkWidget.GetRenderWindow().Render()
    

def save_scene(renderer: vtkRenderer, logConsole, fontColor, actors_file='scene_actors.vtk', camera_file='scene_camera.json'):
    if save_actors(renderer, logConsole, fontColor, actors_file) is not None and \
        save_camera_settings(renderer, logConsole, fontColor, camera_file) is not None:
    
        logConsole.insert_colored_text('Successfully: ', 'green')
        logConsole.insert_colored_text(f'Saved scene from to the files: {actors_file} and {camera_file}\n', fontColor)
    

def save_actors(renderer: vtkRenderer, logConsole, fontColor, actors_file='scene_actors.vtk'):
    try:
        append_filter = vtkAppendPolyData()
        actors_collection = renderer.GetActors()
        actors_collection.InitTraversal()
        
        for i in range(actors_collection.GetNumberOfItems()):
            actor = actors_collection.GetNextActor()
            if actor.GetMapper() and actor.GetMapper().GetInput():
                poly_data = actor.GetMapper().GetInput()
                if isinstance(poly_data, vtkPolyData):
                    append_filter.AddInputData(poly_data)
        
        append_filter.Update()

        writer = vtkPolyDataWriter()
        writer.SetFileName(actors_file)
        writer.SetInputData(append_filter.GetOutput())
        writer.Write()

        logConsole.insert_colored_text('Info: ', 'blue')
        logConsole.insert_colored_text(f'Saved all actors to {actors_file}\n', fontColor)
        return 1
    except Exception as e:
        logConsole.insert_colored_text('Error: ', 'red')
        logConsole.insert_colored_text(f'Failed to save actors: {e}\n', fontColor)
        return None
        
        
def save_camera_settings(renderer: vtkRenderer, logConsole, fontColor, camera_file='scene_camera.json'):
    try:
        camera = renderer.GetActiveCamera()
        camera_settings = {
            'position': camera.GetPosition(),
            'focal_point': camera.GetFocalPoint(),
            'view_up': camera.GetViewUp(),
            'clip_range': camera.GetClippingRange(),
        }
        with open(camera_file, 'w') as f:
            dump(camera_settings, f)

        return 1
    except Exception as e:
        logConsole.insert_colored_text('Error: ', 'red')
        logConsole.insert_colored_text(f'Failed to save camera settings: {e}\n', fontColor)
        return None
        

def load_scene(vtkWidget: QVTKRenderWindowInteractor, renderer: vtkRenderer, logConsole, fontColor, actors_file='scene_actors.vtk', camera_file='scene_camera.json'):
    if load_actors(renderer, logConsole, fontColor, actors_file) is not None and \
        load_camera_settings(renderer, logConsole, fontColor, camera_file) is not None:
    
        vtkWidget.GetRenderWindow().Render()
        logConsole.insert_colored_text('Successfully: ', 'green')
        logConsole.insert_colored_text(f'Loaded scene from the files: {actors_file} and {camera_file}\n', fontColor)


def load_actors(renderer: vtkRenderer, logConsole, fontColor, actors_file='scene_actors.vtk'):
    try:
        reader = vtkPolyDataReader()
        reader.SetFileName(actors_file)
        reader.Update()
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputData(reader.GetOutput())
        
        actor = vtkActor()
        actor.SetMapper(mapper)
        renderer.AddActor(actor)
        renderer.ResetCamera()

        logConsole.insert_colored_text('Info: ', 'blue')
        logConsole.insert_colored_text(f'Loaded actors from {actors_file}\n', fontColor)
        return 1
    except Exception as e:
        logConsole.insert_colored_text('Error: ', 'red')
        logConsole.insert_colored_text(f'Failed to load actors: {e}\n', fontColor)
        return None
        
        
def load_camera_settings(renderer: vtkRenderer, logConsole, fontColor, camera_file='scene_camera.json'):
    try:
        with open(camera_file, 'r') as f:
            camera_settings = load(f)
        
        camera = renderer.GetActiveCamera()
        camera.SetPosition(*camera_settings['position'])
        camera.SetFocalPoint(*camera_settings['focal_point'])
        camera.SetViewUp(*camera_settings['view_up'])
        camera.SetClippingRange(*camera_settings['clip_range'])
        
        renderer.ResetCamera()
        return 1
    except Exception as e:
        logConsole.insert_colored_text('Error: ', 'red')
        logConsole.insert_colored_text(f'Failed to load camera settings: {e}\n', fontColor)
        return None

def get_polydata_from_actor(actor: vtkActor):
    mapper = actor.GetMapper()
    if hasattr(mapper, "GetInput"):
        return mapper.GetInput()
    else:
        return None


def write_vtk_polydata_to_file(polyData):
    writer = vtkPolyDataWriter()
    writer.SetInputData(polyData)

    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.vtk')
    temp_file_name = temp_file.name
    temp_file.close()

    # Set the filename in the writer and write
    writer.SetFileName(temp_file_name)
    writer.Write()

    # Return the path to the temporary file
    return temp_file_name

def is_conversion_success(polyData):
    # Check if the polyData is not None
    if polyData is None:
        return False

    # Check if there are any points and cells in the polyData
    numberOfPoints = polyData.GetNumberOfPoints()
    numberOfCells = polyData.GetNumberOfCells()

    if numberOfPoints > 0 and numberOfCells > 0:
        return True # Conversion was successful and resulted in a non-empty polyData
    else:
        return False # Conversion failed to produce meaningful polyData


def convert_vtkUnstructuredGrid_to_vtkPolyData_helper(ugrid: vtkUnstructuredGrid):
    geometryFilter = vtkGeometryFilter()
    geometryFilter.SetInputData(ugrid)
    
    geometryFilter.Update()
    
    polyData = geometryFilter.GetOutput()
    if not is_conversion_success(polyData):
        return None
    
    return polyData

def convert_vtkUnstructuredGrid_to_vtkPolyData(data):
    if data.IsA("vtkUnstructuredGrid"):
        return convert_vtkUnstructuredGrid_to_vtkPolyData_helper(data)
    elif data.IsA("vtkPolyData"):
        return data
    else:
        return None

def convert_unstructured_grid_to_polydata(data):
    converted_part_1 = get_polydata_from_actor(data)
    converted_part_2 = convert_vtkUnstructuredGrid_to_vtkPolyData(converted_part_1)
    return converted_part_2


def convert_vtkPolyData_to_vtkUnstructuredGrid(polydata):
    """
    Converts vtkPolyData to vtkUnstructuredGrid.
    
    Args:
        polydata (vtkPolyData): The polydata to convert.
    
    Returns:
        vtkUnstructuredGrid: The converted unstructured grid.
    """
    if not polydata.IsA("vtkPolyData"):
        return None
    
    ugrid = vtkUnstructuredGrid()
    points = vtkPoints()
    points.SetDataTypeToDouble()
    cells = vtkCellArray()
    
    for i in range(polydata.GetNumberOfPoints()):
        points.InsertNextPoint(polydata.GetPoint(i))
    
    for i in range(polydata.GetNumberOfCells()):
        cell = polydata.GetCell(i)
        cell_type = cell.GetCellType()
        ids = cell.GetPointIds()
        
        if cell_type == VTK_TRIANGLE:
            triangle = vtkTriangle()
            triangle.GetPointIds().SetId(0, ids.GetId(0))
            triangle.GetPointIds().SetId(1, ids.GetId(1))
            triangle.GetPointIds().SetId(2, ids.GetId(2))
            cells.InsertNextCell(triangle)
    
    ugrid.SetPoints(points)
    ugrid.SetCells(VTK_TRIANGLE, cells)
    
    return ugrid

    
def remove_temp_files_helper(filename: str):
    try:
        if exists(filename):
            remove(filename)
    except Exception as ex:
        print(f"Some error occurs: Can't remove file {filename}. Error: {ex}")
        return
    
    
def remove_temp_files():
    # High probability that user don't want to delete temporary config file
    
    # Removing all temporary files excluding temporary config file
    remove_temp_files_helper(DEFAULT_TEMP_MESH_FILE)
    remove_temp_files_helper(DEFAULT_TEMP_VTK_FILE)
    remove_temp_files_helper(DEFAULT_TEMP_HDF5_FILE)
    
def extract_transform_from_actor(actor: vtkActor):
    matrix = actor.GetMatrix()
    
    transform = vtkTransform()
    transform.SetMatrix(matrix)
    
    return transform

def calculate_direction(base, tip):
    from numpy import array, linalg
    
    base = array(base)
    tip = array(tip)
    
    direction = tip - base
    
    norm = linalg.norm(direction)
    if norm == 0:
        raise ValueError("The direction vector cannot be zero.")
    direction /= norm
    
    return direction

def calculate_thetaPhi(base, tip):
    from numpy import arctan2, arccos
    
    direction = calculate_direction(base, tip)
    x, y, z = direction[0], direction[1], direction[2]
    
    theta = arccos(z)
    phi = arctan2(y, x)
    
    return theta, phi

def calculate_thetaPhi_with_angles(x, y, z, angle_x, angle_y, angle_z):
    direction_vector = np.array([np.cos(np.radians(angle_y)) * np.cos(np.radians(angle_z)),
                                 np.sin(np.radians(angle_x)) * np.sin(np.radians(angle_z)),
                                 np.cos(np.radians(angle_x)) * np.cos(np.radians(angle_y))])
    norm = np.linalg.norm(direction_vector)
    theta = np.arccos(direction_vector[2] / norm)
    phi = np.arctan2(direction_vector[1], direction_vector[0])
    return theta, phi

def rad_to_degree(angle: float):
    return angle * 180. / pi

def degree_to_rad(angle: float):
    return angle * pi / 180.

def extract_transformed_points(polydata: vtkPolyData):
    points = polydata.GetPoints()
    return [points.GetPoint(i) for i in range(points.GetNumberOfPoints())]

def get_transformation_matrix(actor: vtkActor):
    return actor.GetMatrix()

def transform_coordinates(points, matrix):
    transform = vtkTransform()
    transform.SetMatrix(matrix)
    transformed_points = []
    for point in points:
        transformed_point = transform.TransformPoint(point[0], point[1], point[2])
        transformed_points.append(transformed_point)
    return transformed_points


def getTreeDict(mesh_filename: str = None, obj_type: str = 'volume') -> dict:
    """
    Extracts the data from Gmsh and returns it in a structured format.

    Parameters:
    mesh_filename (str): The filename of the Gmsh mesh file to read.
    obj_type (str): The type of object to extract ('point', 'line', 'surface', 'volume').

    Returns:
    dict: A dictionary representing the object map.
    """
    if mesh_filename:
        gmsh.open(mesh_filename)
    
    gmsh.model.occ.synchronize()
    
    # Getting all the nodes and their coordinates
    all_node_tags, all_node_coords, _ = gmsh.model.mesh.getNodes()
    node_coords_map = {tag: (all_node_coords[i * 3], all_node_coords[i * 3 + 1], all_node_coords[i * 3 + 2]) 
                       for i, tag in enumerate(all_node_tags)}
    
    if obj_type == 'point':
        point_map = {f'Point[{tag}]': coords for tag, coords in node_coords_map.items()}
        return point_map
    
    if obj_type == 'line':
        lines = gmsh.model.getEntities(dim=1)
        line_map = {}

        for line_dim, line_tag in lines:
            element_types, element_tags, node_tags = gmsh.model.mesh.getElements(line_dim, line_tag)

            for elem_type, elem_tags, elem_node_tags in zip(element_types, element_tags, node_tags):
                if elem_type == 1:  # 1st type for lines
                    for i in range(len(elem_tags)):
                        node_indices = elem_node_tags[i * 2:(i + 1) * 2]
                        line = [
                            (node_indices[0], node_coords_map[node_indices[0]]),
                            (node_indices[1], node_coords_map[node_indices[1]])
                        ]
                        line_map[f'Line[{elem_tags[i]}]'] = line
        return line_map
    
    if obj_type == 'surface':
        surfaces = gmsh.model.getEntities(dim=2)
        surface_map = {}

        for surf_dim, surf_tag in surfaces:
            element_types, element_tags, node_tags = gmsh.model.mesh.getElements(surf_dim, surf_tag)

            triangles = []
            for elem_type, elem_tags, elem_node_tags in zip(element_types, element_tags, node_tags):
                if elem_type == 2:  # 2nd type for the triangles
                    for i in range(len(elem_tags)):
                        node_indices = elem_node_tags[i * 3:(i + 1) * 3]
                        triangle = [
                            (node_indices[0], node_coords_map[node_indices[0]]),
                            (node_indices[1], node_coords_map[node_indices[1]]),
                            (node_indices[2], node_coords_map[node_indices[2]])
                        ]
                        triangles.append((elem_tags[i], triangle))
            surface_map[surf_tag] = triangles
        return surface_map
    
    if obj_type == 'volume':
        volumes = gmsh.model.getEntities(dim=3)
        treedict = {}

        entities = volumes if volumes else gmsh.model.getEntities(dim=2)

        for dim, tag in entities:
            surfaces = gmsh.model.getBoundary([(dim, tag)], oriented=False, recursive=False) if volumes else [(dim, tag)]

            surface_map = {}
            for surf_dim, surf_tag in surfaces:
                element_types, element_tags, node_tags = gmsh.model.mesh.getElements(surf_dim, surf_tag)

                triangles = []
                for elem_type, elem_tags, elem_node_tags in zip(element_types, element_tags, node_tags):
                    if elem_type == 2:  # 2nd type for the triangles
                        for i in range(len(elem_tags)):
                            node_indices = elem_node_tags[i * 3:(i + 1) * 3]
                            triangle = [
                                (node_indices[0], node_coords_map[node_indices[0]]),
                                (node_indices[1], node_coords_map[node_indices[1]]),
                                (node_indices[2], node_coords_map[node_indices[2]])
                            ]
                            triangles.append((elem_tags[i], triangle))
                surface_map[surf_tag] = triangles
            treedict[tag] = surface_map
        return treedict

    

def write_treedict_to_vtk(treedict: dict, filename: str) -> bool:
    """
    Writes the object map to a VTK file.
    
    Args:
        treedict (dict): The object map containing mesh data.
        filename (str): The filename to write the VTK file to.
    
    Returns:
        bool: True if the file was successfully written, False otherwise.
    """
    try:
        if not filename.endswith('.vtk'):
            filename += '.vtk'
        
        points = vtkPoints()
        points.SetDataTypeToDouble()
        triangles = vtkCellArray()
        ugrid = vtkUnstructuredGrid()
        
        point_index_map = {}
        current_index = 0
        
        for volume_id, surfaces in treedict.items():
            for surface_id, triangle_data in surfaces.items():
                for triangle_id, triangle in triangle_data:
                    pts = []
                    for node_id, point in triangle:
                        if node_id not in point_index_map:
                            points.InsertNextPoint(point)
                            point_index_map[node_id] = current_index
                            current_index += 1
                        pts.append(point_index_map[node_id])
                    triangle_cell = vtkTriangle()
                    triangle_cell.GetPointIds().SetId(0, pts[0])
                    triangle_cell.GetPointIds().SetId(1, pts[1])
                    triangle_cell.GetPointIds().SetId(2, pts[2])
                    triangles.InsertNextCell(triangle_cell)
        
        ugrid.SetPoints(points)
        ugrid.SetCells(VTK_TRIANGLE, triangles)
        
        writer = vtkUnstructuredGridWriter()
        writer.SetFileName(filename)
        writer.SetInputData(ugrid)
        
        writer.Write()
        return True, filename
    
    except Exception as e:
        print(f"Error writing VTK file: {e}")
        return False, filename


def createActorsFromTreeDict(treedict: dict, objType: str) -> list:
    """
    Create VTK actors for each surface, volume, or line in the object map.

    Parameters:
    treedict (dict): The object map generated by the getTreeDict function, which contains volumes,
                       surfaces, triangles, and their nodes with coordinates.
    objType (str): The type of the object, which can be 'volume', 'surface', or 'line'.

    Returns:
    list: List of the VTK actors.
    """
    actors = []

    if objType == 'volume':
        for _, surfaces in treedict.items():
            for surface_tag, triangles in surfaces.items():
                points = vtkPoints()
                triangles_array = vtkCellArray()

                # Dictionary to map node tags to point IDs in vtkPoints
                point_id_map = {}

                for triangle_tag, nodes in triangles:
                    point_ids = []
                    for node_tag, coords in nodes:
                        if node_tag not in point_id_map:
                            point_id = points.InsertNextPoint(coords)
                            point_id_map[node_tag] = point_id
                        else:
                            point_id = point_id_map[node_tag]
                        point_ids.append(point_id)

                    # Create a VTK triangle and add it to the vtkCellArray
                    triangle = vtkTriangle()
                    for i, point_id in enumerate(point_ids):
                        triangle.GetPointIds().SetId(i, point_id)
                    triangles_array.InsertNextCell(triangle)

                poly_data = vtkPolyData()
                poly_data.SetPoints(points)
                poly_data.SetPolys(triangles_array)
                mapper = vtkPolyDataMapper()
                mapper.SetInputData(poly_data)

                # Create a vtkActor to represent the surface in the scene
                actor = vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)

                # Add the actor to the list
                actors.append(actor)
    
    elif objType == 'surface':
        for surface_tag, triangles in treedict.items():
            points = vtkPoints()
            triangles_array = vtkCellArray()

            # Dictionary to map node tags to point IDs in vtkPoints
            point_id_map = {}

            for triangle_tag, nodes in triangles:
                point_ids = []
                for node_tag, coords in nodes:
                    if node_tag not in point_id_map:
                        point_id = points.InsertNextPoint(coords)
                        point_id_map[node_tag] = point_id
                    else:
                        point_id = point_id_map[node_tag]
                    point_ids.append(point_id)

                # Create a VTK triangle and add it to the vtkCellArray
                triangle = vtkTriangle()
                for i, point_id in enumerate(point_ids):
                    triangle.GetPointIds().SetId(i, point_id)
                triangles_array.InsertNextCell(triangle)

            poly_data = vtkPolyData()
            poly_data.SetPoints(points)
            poly_data.SetPolys(triangles_array)
            mapper = vtkPolyDataMapper()
            mapper.SetInputData(poly_data)

            # Create a vtkActor to represent the surface in the scene
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)

            # Add the actor to the list
            actors.append(actor)
    
    elif objType == 'line':
        for line_tag, points in treedict.items():
            vtk_points = vtkPoints()
            poly_line = vtkPolyLine()
            poly_line.GetPointIds().SetNumberOfIds(len(points))
            
            # Dictionary to map node tags to point IDs in vtkPoints
            point_id_map = {}

            for i, (node_tag, coords) in enumerate(points):
                if node_tag not in point_id_map:
                    point_id = vtk_points.InsertNextPoint(coords)
                    point_id_map[node_tag] = point_id
                else:
                    point_id = point_id_map[node_tag]

                poly_line.GetPointIds().SetId(i, point_id)

            lines_array = vtkCellArray()
            lines_array.InsertNextCell(poly_line)

            poly_data = vtkPolyData()
            poly_data.SetPoints(vtk_points)
            poly_data.SetLines(lines_array)
            mapper = vtkPolyDataMapper()
            mapper.SetInputData(poly_data)

            # Create a vtkActor to represent the line in the scene
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)

            # Add the actor to the list
            actors.append(actor)

    elif objType == 'point':
        for point_tag, coords in treedict.items():
            vtk_points = vtkPoints()
            vtk_points.InsertNextPoint(coords)
            
            poly_data = vtkPolyData()
            poly_data.SetPoints(vtk_points)

            glyph_filter = vtkVertexGlyphFilter()
            glyph_filter.SetInputData(poly_data)
            glyph_filter.Update()

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(glyph_filter.GetOutputPort())

            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetPointSize(5)
            actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)

            actors.append(actor)

    return actors



def populateTreeView(treedict: dict, object_idx: int, tree_model: QStandardItemModel, tree_view: QTreeView, type: str) -> int:
    """
    Populate the tree model with the hierarchical structure of the object map.

    Parameters:
    treedict (dict): The object map generated by the getTreeDict function, which contains volumes,
                       surfaces, triangles, and their nodes with coordinates.
    object_idx (int): Index of the object.
    tree_model (QStandardItemModel): The QStandardItemModel where the hierarchical data will be inserted.
    tree_view (QTreeView): The QTreeView where the tree model will be displayed.
    type (str): The type of the object, which can be 'volume', 'surface', or 'line'.
    
    Returns:
    int: The row index of the volume or surface item.
    """
    rows = []
    root_row_index = -1
    
    if type == 'volume':
        # Case when treedict contains volumes
        for _, surfaces in treedict.items():
            # Add the volume node to the tree model
            volume_item = QStandardItem(f'Volume[{object_idx}]')
            tree_model.appendRow(volume_item)
            
            # Get the index of the volume item
            volume_index = tree_model.indexFromItem(volume_item)
            root_row_index = volume_index.row()
            
            for surface_tag, triangles in surfaces.items():
                # Add the surface node to the tree model under the volume node
                surface_item = QStandardItem(f'Surface[{surface_tag}]')
                volume_item.appendRow(surface_item)
                
                for triangle_tag, nodes in triangles:
                    # Add the triangle node to the tree model under the surface node
                    triangle_item = QStandardItem(f'Triangle[{triangle_tag}]')
                    surface_item.appendRow(triangle_item)
                    
                    # Generate lines for the triangle
                    lines = [
                        (nodes[0], nodes[1]),
                        (nodes[1], nodes[2]),
                        (nodes[2], nodes[0])
                    ]
                    
                    for line_idx, (start, end) in enumerate(lines, start=1):
                        # Add the line node under the triangle node
                        line_item = QStandardItem(f'Line[{line_idx}]')
                        triangle_item.appendRow(line_item)
                        
                        # Add the point data under the line node
                        start_str = f'Point[{start[0]}]: {start[1]}'
                        end_str = f'Point[{end[0]}]: {end[1]}'
                        start_item = QStandardItem(start_str)
                        end_item = QStandardItem(end_str)
                        line_item.appendRow(start_item)
                        line_item.appendRow(end_item)

    elif type == 'surface':
        # Case when treedict contains surfaces directly
        for surface_tag, triangles in treedict.items():
            # Add the surface node to the tree model
            surface_item = QStandardItem(f'Surface[{surface_tag}]')
            tree_model.appendRow(surface_item)
            
            # Get the index of the surface item
            surface_index = tree_model.indexFromItem(surface_item)
            root_row_index = surface_index.row()
            
            for triangle_tag, nodes in triangles:
                # Add the triangle node to the tree model under the surface node
                triangle_item = QStandardItem(f'Triangle[{triangle_tag}]')
                surface_item.appendRow(triangle_item)
                
                # Generate lines for the triangle
                lines = [
                    (nodes[0], nodes[1]),
                    (nodes[1], nodes[2]),
                    (nodes[2], nodes[0])
                ]
                
                for line_idx, (start, end) in enumerate(lines, start=1):
                    # Add the line node under the triangle node
                    line_item = QStandardItem(f'Line[{line_idx}]')
                    triangle_item.appendRow(line_item)
                    
                    # Add the point data under the line node
                    start_str = f'Point[{start[0]}]: {start[1]}'
                    end_str = f'Point[{end[0]}]: {end[1]}'
                    start_item = QStandardItem(start_str)
                    end_item = QStandardItem(end_str)
                    line_item.appendRow(start_item)
                    line_item.appendRow(end_item)
                    
    elif type == 'line':
        # Case when treedict contains lines directly
        for line_tag, points in treedict.items():
            # Add the line node to the tree model
            line_item = QStandardItem(f'{line_tag}')
            tree_model.appendRow(line_item)
            
            # Get the index of the line item
            line_index = tree_model.indexFromItem(line_item)
            root_row_index = line_index.row()
            rows.append(root_row_index)
            
            for point_idx, (point_tag, coords) in enumerate(points, start=1):
                # Add the point node to the tree model under the line node
                point_str = f'Point[{point_tag}]: {coords}'
                point_item = QStandardItem(point_str)
                line_item.appendRow(point_item)
                    
    elif type == 'point':
        for point_tag, coords in treedict.items():
            point_item = QStandardItem(f'{point_tag}: {coords}')
            tree_model.appendRow(point_item)
            point_index = tree_model.indexFromItem(point_item)
            root_row_index = point_index.row()

    tree_view.setModel(tree_model)
    if type != 'line':
        return root_row_index
    else:
        return rows



def can_create_surface(point_data):
    """
    Check if a surface can be created from the given set of points using VTK.

    Parameters:
    point_data (list of tuples): List of (x, y, z) coordinates of the points.

    Returns:
    bool: True if the surface can be created, False otherwise.
    """    
    # Create a vtkPoints object and add the points
    points = vtkPoints()
    for x, y, z in point_data:
        points.InsertNextPoint(x, y, z)
    
    # Create a polydata object and set the points
    poly_data = vtkPolyData()
    poly_data.SetPoints(points)

    # Create a Delaunay2D object and set the input
    delaunay = vtkDelaunay2D()
    delaunay.SetInputData(poly_data)
    
    # Try to create the surface
    delaunay.Update()
    
    # Check if the surface was created
    output = delaunay.GetOutput()
    if output.GetNumberOfCells() > 0:
        return True
    else:
        return False


def can_create_line(point_data):
    """
    Check if a line can be created from the given set of points using VTK.

    Parameters:
    point_data (list of tuples): List of (x, y, z) coordinates of the points.

    Returns:
    bool: True if the line can be created, False otherwise.
    """
    # Check if all points are the same
    if all(point == point_data[0] for point in point_data):
        return False
    
    # Create a vtkPoints object and add the points
    points = vtkPoints()
    for x, y, z in point_data:
        points.InsertNextPoint(x, y, z)
    
    # Create a polyline object
    line = vtkPolyLine()
    line.GetPointIds().SetNumberOfIds(len(point_data))
    
    for i in range(len(point_data)):
        line.GetPointIds().SetId(i, i)
    
    # Create a vtkCellArray and add the line to it
    lines = vtkCellArray()
    lines.InsertNextCell(line)
    
    # Create a polydata object and set the points and lines
    poly_data = vtkPolyData()
    poly_data.SetPoints(points)
    poly_data.SetLines(lines)
    
    # Check if the line was created
    if poly_data.GetNumberOfLines() > 0:
        return True
    else:
        return False
    

def print_tree_structure(self, tree_view: QTreeView):
    model = tree_view.model()

    def iterate(index, level):
        if not index.isValid():
            return
            
        print(' ' * level * 4 + str(index.row()))
        
        # Iterate over children
        for i in range(model.rowCount(index)):
            child_index = model.index(i, 0, index)
            iterate(child_index, level + 1)

    root_index = model.index(0, 0, QModelIndex())
    iterate(root_index, 0)
    

def formActorNodesDictionary(treedict: dict, actor_rows: dict, objType: str):
    actor_nodes_dict = {}

    for actor, (volume_index, surface_index) in actor_rows.items():
        if actor not in actor_nodes_dict:
            actor_nodes_dict[actor] = set()

        if objType == 'volume':
            for volume_tag, surfaces in treedict.items():
                for surface_tag, triangles in surfaces.items():
                    if surface_tag - 1 == surface_index:
                        for triangle_tag, nodes in triangles:
                            for node in nodes:
                                actor_nodes_dict[actor].add(node[0])
        elif objType == 'surface':
            for surface_tag, triangles in treedict.items():
                if surface_tag - 1 == surface_index:
                    for triangle_tag, nodes in triangles:
                        for node in nodes:
                            actor_nodes_dict[actor].add(node[0])
        elif objType == 'line':
            for line_tag, line_nodes in treedict.items():
                if surface_index == int(line_tag.split('[')[1][:-1]):
                    for node in line_nodes:
                        actor_nodes_dict[actor].add(node[0])
        elif objType == 'point':
            if f'Point[{surface_index}]' in treedict:
                actor_nodes_dict[actor].add(surface_index)

    return actor_nodes_dict




def get_cur_datetime() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def compare_matrices(mat1, mat2):
    """
    Compare two vtkMatrix4x4 matrices for equality.
        
    Args:
        mat1 (vtkMatrix4x4): The first matrix.
        mat2 (vtkMatrix4x4): The second matrix.
        
    Returns:
        bool: True if the matrices are equal, False otherwise.
    """
    for i in range(4):
        for j in range(4):
            if mat1.GetElement(i, j) != mat2.GetElement(i, j):
                return False
    return True


def rename_first_selected_row(model, volume_row, surface_indices):
    """
    Rename the first selected row in the tree view with the merged surface name.

    Args:
        model (QStandardItemModel): The model of the tree view.
        volume_row (int): The row index of the volume item in the tree view.
        surface_indices (list): The list of indices of the surface items to be merged.
    """
    # Creating the new merged item name
    merged_surface_name = f"Surface_merged_{'_'.join(map(str, sorted([i + 1 for i in surface_indices])))}"
    parent_index = model.index(volume_row, 0)

    # Replacing the name of the first selected row with the new name
    first_surface_index = surface_indices[0]
    first_child_index = model.index(first_surface_index, 0, parent_index)
    first_item = model.itemFromIndex(first_child_index)
    first_item.setText(merged_surface_name)


def copy_children(source_item, target_item):
    """
    Recursively copy children from source_item to target_item.

    Args:
        source_item (QStandardItem): The item from which to copy children.
        target_item (QStandardItem): The item to which the children will be copied.
    """
    # Iterate through all rows (children) of the source item
    for row in range(source_item.rowCount()):
        # Clone the child item at the current row
        child = source_item.child(row).clone()
        
        # Append the cloned child to the target item
        target_item.appendRow(child)
        
        # Recursively call copy_children to copy the children of the current child
        copy_children(source_item.child(row), child)


def merge_actors(actors):
    """
    Merge the provided list of actors into a single actor.

    Args:
        actors (list): List of vtkActor objects to be merged.

    Returns:
        vtkActor: A new actor that is the result of merging the provided actors.
    """
    # Merging actors
    append_filter = vtkAppendPolyData()
    for actor in actors:
        poly_data = actor.GetMapper().GetInput()
        append_filter.AddInputData(poly_data)
    append_filter.Update()

    # Creating a new merged actor
    merged_mapper = vtkPolyDataMapper()
    merged_mapper.SetInputData(append_filter.GetOutput())

    merged_actor = vtkActor()
    merged_actor.SetMapper(merged_mapper)
    merged_actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)

    return merged_actor


def compute_distance_between_points(coord1, coord2):
    """
    Compute the Euclidean distance between two points in 3D space.
    """
    try:
        result = np.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2 + (coord1[2] - coord2[2])**2)
    except Exception as e:
        print_warning_none_result()
        return None
    return result


def pretty_function_details() -> str:
    """
    Prints the details of the calling function in the format:
    <file name>: line[<line number>]: <func name>(<args>)
    """
    from inspect import currentframe, getargvalues
    
    current_frame = currentframe()
    caller_frame = current_frame.f_back
    function_name = caller_frame.f_code.co_name
    args, _, _, values = getargvalues(caller_frame)
    function_file = caller_frame.f_code.co_filename
    formatted_args = ', '.join([f"{arg}={values[arg]}" for arg in args])
    return f"{function_file}: {function_name}({formatted_args})"

def print_warning_none_result():
    print(f"Warning, {pretty_function_details()} returned {None} result")
