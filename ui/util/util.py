import gmsh, tempfile
from math import pi
from datetime import datetime
from os import remove
from vtk import (
    vtkRenderer, vtkPolyData, vtkPolyDataWriter, vtkAppendPolyData,
    vtkPolyDataReader, vtkPolyDataMapper, vtkActor, vtkPolyDataWriter,
    vtkUnstructuredGrid, vtkGeometryFilter, vtkTransform, vtkCellArray,
    vtkTriangle, vtkPoints, vtkDelaunay2D, vtkPolyLine, vtkVertexGlyphFilter
)
from PyQt5.QtCore import QSize, QModelIndex
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, 
    QVBoxLayout, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QSizePolicy, QLabel, QHBoxLayout,
    QWidget, QScrollArea, QComboBox, QTreeView
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QStandardItemModel, QStandardItem
from .converter import is_positive_real_number, is_real_number
from os.path import exists, isfile
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from json import dump, load
from .styles import DEFAULT_QLINEEDIT_STYLE, DEFAULT_ACTOR_COLOR

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
    gmsh.initialize()
    
    vtk_filename = msh_filename.replace('.msh', '.vtk')
    gmsh.open(msh_filename)
    gmsh.write(vtk_filename)
    
    gmsh.finalize()
    return vtk_filename
    
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
        self.undo_stack = []  # Stack to keep track of undo actions
        self.redo_stack = []  # Stack to keep track of redo actions

    def add_action(self, object_on_stack):
        """
        Add a new action to the history. This clears the redo stack.
        """
        self.undo_stack.append(object_on_stack)

    def undo(self):
        """
        Undo the last action.
        Returns the row_id and actors for the undone action.
        """
        if not self.undo_stack:
            return None
        object_on_stack = self.undo_stack.pop()
        self.redo_stack.append(object_on_stack)
        self.id -= 1
        return object_on_stack

    def redo(self):
        """
        Redo the last undone action.
        Returns the row_id and actors for the redone action.
        """
        if not self.redo_stack:
            return None
        object_on_stack = self.redo_stack.pop()
        self.undo_stack.append(object_on_stack)
        self.id += 1
        return object_on_stack
    

class ParticleSourceDialog(QDialog):
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
        energy_validator = QDoubleValidator(0.0, 10000.0, 2, self)  # Range of the energy in [eV]
        self.energy_input.setValidator(energy_validator)
        layout.addRow("Energy (eV):", self.energy_input)

        # Number of particles
        self.num_particles_input = QLineEdit()
        self.num_particles_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        num_particles_validator = QIntValidator(1, 1000000000, self) # Range of particle count
        self.num_particles_input.setValidator(num_particles_validator)
        layout.addRow("Number of Particles:", self.num_particles_input)

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def getValues(self):
        return {
            "particle_type": self.particle_type_combo.currentText(),
            "energy": float(self.energy_input.text()),
            "num_particles": int(self.num_particles_input.text())
        }


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


def getObjectMap(mesh_filename: str = None, obj_type: str = 'volume') -> dict:
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
        object_map = {}

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
            object_map[tag] = surface_map
        return object_map


def createActorsFromObjectMap(object_map: dict, objType: str) -> list:
    """
    Create VTK actors for each surface, volume, or line in the object map.

    Parameters:
    object_map (dict): The object map generated by the getObjectMap function, which contains volumes,
                       surfaces, triangles, and their nodes with coordinates.
    objType (str): The type of the object, which can be 'volume', 'surface', or 'line'.

    Returns:
    list: List of the VTK actors.
    """
    actors = []

    if objType == 'volume':
        for _, surfaces in object_map.items():
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
        for surface_tag, triangles in object_map.items():
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
        for line_tag, points in object_map.items():
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
        for point_tag, coords in object_map.items():
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



def populateTreeView(object_map: dict, object_idx: int, tree_model: QStandardItemModel, tree_view: QTreeView, type: str) -> int:
    """
    Populate the tree model with the hierarchical structure of the object map.

    Parameters:
    object_map (dict): The object map generated by the getObjectMap function, which contains volumes,
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

    if type == 'line':
        # Case when object_map contains lines directly
        for line_tag, points in object_map.items():
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
    
    elif type == 'volume':
        # Case when object_map contains volumes
        for _, surfaces in object_map.items():
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
        # Case when object_map contains surfaces directly
        for surface_tag, triangles in object_map.items():
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
                    
    elif type == 'point':
        for point_tag, coords in object_map.items():
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
    

def formActorNodesDictionary(objectMap: dict, tree_item_actor_map: dict, objType: str):
    actor_nodes_dict = {}

    # Iterate through the tree item actor map
    for parent_key, value in tree_item_actor_map.items():
        if isinstance(value, list):
            for internal_row, actor, color in value:
                if actor not in actor_nodes_dict:
                    actor_nodes_dict[actor] = set()

                # Depending on the objType, extract the nodes from the objectMap
                if objType == 'volume':
                    for volume_tag, surfaces in objectMap.items():
                        for surface_tag, triangles in surfaces.items():
                            if surface_tag - 1 == internal_row:
                                for triangle_tag, nodes in triangles:
                                    for node in nodes:
                                        actor_nodes_dict[actor].add(node[0])
                elif objType == 'surface':
                    for surface_tag, triangles in objectMap.items():
                        if surface_tag - 1 == internal_row:
                            for triangle_tag, nodes in triangles:
                                for node in nodes:
                                    actor_nodes_dict[actor].add(node[0])
                elif objType == 'line':
                    for line_tag, line_nodes in objectMap.items():
                        if internal_row == int(line_tag.split('[')[1][:-1]):
                            for node in line_nodes:
                                actor_nodes_dict[actor].add(node[0])
                elif objType == 'point':
                    if f'Point[{internal_row}]' in objectMap:
                        actor_nodes_dict[actor].add(internal_row)

    return actor_nodes_dict


def get_cur_datetime() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
