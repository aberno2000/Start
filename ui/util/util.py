import gmsh, tempfile, meshio
import numpy as np
from math import radians, pi
from datetime import datetime
from os import remove
from vtk import (
    vtkRenderer, vtkPolyData, vtkPolyDataWriter, vtkAppendPolyData,
    vtkPolyDataReader, vtkPolyDataMapper, vtkActor, vtkPolyDataWriter,
    vtkUnstructuredGrid, vtkGeometryFilter, vtkTransform, vtkCellArray,
    vtkTriangle, vtkPoints, vtkDelaunay2D, vtkPolyLine, vtkVertexGlyphFilter,
    vtkUnstructuredGridWriter, vtkArrowSource, vtkTransformPolyDataFilter,
    VTK_TRIANGLE
)
from PyQt5.QtCore import QSize, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, 
    QVBoxLayout, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QSizePolicy, QLabel, QHBoxLayout,
    QWidget, QScrollArea, QComboBox, QTreeView,
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QStandardItemModel, QStandardItem
from .converter import is_positive_real_number, is_real_number
from os.path import exists, isfile
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from json import dump, load
from .styles import DEFAULT_QLINEEDIT_STYLE, DEFAULT_ACTOR_COLOR, ARROW_ACTOR_COLOR

DEFAULT_TEMP_MESH_FILE = 'temp.msh'
DEFAULT_TEMP_VTK_FILE = 'temp.vtk'
DEFAULT_TEMP_HDF5_FILE = 'temp.hdf5'
DEFAULT_TEMP_CONFIG_FILE = 'temp_config.json'

DEFAULT_COUNT_OF_PROJECT_FILES = 3

figure_types = ['Point', 'Line', 'Surface', 'Sphere', 'Box', 'Cylinder', 'Custom']

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
        
        button_box = QDialogButtonBox(self)
        button_box.addButton(QDialogButtonBox.Ok)
        button_box.addButton(QDialogButtonBox.Cancel)
        
        button_box.accepted.connect(self.accept_and_emit)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)

        self.x_input.textChanged.connect(self.update_arrow)
        self.y_input.textChanged.connect(self.update_arrow)
        self.z_input.textChanged.connect(self.update_arrow)
        self.angle_x_input.textChanged.connect(self.update_arrow)
        self.angle_y_input.textChanged.connect(self.update_arrow)
        self.angle_z_input.textChanged.connect(self.update_arrow)

    def update_arrow(self):
        properties = self.getProperties()
        if properties:
            x, y, z, angle_x, angle_y, angle_z = properties
            self.resetArrowActor()
            self.create_direction_arrow_manually(x, y, z, angle_x, angle_y, angle_z)

    def getProperties(self):
        try:
            x = float(self.x_input.text())
            y = float(self.y_input.text())
            z = float(self.z_input.text())
            angle_x = float(self.angle_x_input.text())
            angle_y = float(self.angle_y_input.text())
            angle_z = float(self.angle_z_input.text())
            return x, y, z, angle_x, angle_y, angle_z
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
        
    def create_direction_arrow_manually(self, x, y, z, angle_x, angle_y, angle_z):
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
        arrowTransform.Scale(5, 5, 5)
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


def get_smallest_cell_size(filename: str):
    """
    This function takes the name of a .msh file as a string argument
    and returns the size of the smallest cell (triangle) in the mesh,
    defined as the smallest side length of any triangle in the mesh.
    """
    
    def compute_distance(coord1, coord2):
        """
        Compute the Euclidean distance between two points in 3D space.
        """
        return np.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2 + (coord1[2] - coord2[2])**2)

    try:
        if not gmsh.isInitialized():
            gmsh.initialize()
        gmsh.open(filename)

        node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
        node_coords = np.reshape(node_coords, (-1, 3))
        element_types, element_tags, element_node_tags = gmsh.model.mesh.getElements()
        min_length = float('inf')

        # Process all triangular elements (type 2 - triangles)
        for elem_type, elem_nodes in zip(element_types, element_node_tags):
            if elem_type == 2:  # 2 means triangular elements
                elem_nodes = np.reshape(elem_nodes, (-1, 3))
                for triangle in elem_nodes:
                    # Get the coordinates of the triangle vertices
                    p1 = node_coords[triangle[0] - 1]  # Indexing starts from 0
                    p2 = node_coords[triangle[1] - 1]
                    p3 = node_coords[triangle[2] - 1]

                    # Calculate the lengths of the sides of the triangle
                    length1 = compute_distance(p1, p2)
                    length2 = compute_distance(p2, p3)
                    length3 = compute_distance(p3, p1)

                    # Find the minimum side length in this triangle
                    min_triangle_length = min(length1, length2, length3)

                    # Update the minimum side length among all triangles
                    if min_triangle_length < min_length:
                        min_length = min_triangle_length

        if gmsh.isInitialized():
            gmsh.finalize()
        return min_length
        
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found")
    except gmsh.GmshException as e:
        print(f"Gmsh API error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if gmsh.isInitialized():
            gmsh.finalize()

    return None
