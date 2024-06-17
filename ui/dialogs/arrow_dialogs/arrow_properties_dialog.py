from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit,
    QDialogButtonBox, QMessageBox, QLabel,
    QPushButton
)
from vtk import (
    vtkArrowSource, vtkTransform, vtkTransformPolyDataFilter,
    vtkActor, vtkPolyDataMapper, vtkRenderer
)
from styles import *
from constants import *
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from .arrow_size_dialog import ArrowSizeDialog


class ArrowPropertiesDialog(QDialog):
    properties_accepted = pyqtSignal(tuple)

    def __init__(self, vtkWidget: QVTKRenderWindowInteractor, renderer: vtkRenderer, arrowActor: vtkActor, parent=None):
        super(ArrowPropertiesDialog, self).__init__(parent)

        self.vtkWidget = vtkWidget
        self.renderer = renderer
        self.arrowActor = arrowActor
        self.arrowSize = DEFAULT_ARROW_SCALE[0]

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

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
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
            self.create_direction_arrow_manually(
                x, y, z, angle_x, angle_y, angle_z, self.arrowSize)

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
        self.arrowActor.GetProperty().SetColor(DEFAULT_ARROW_ACTOR_COLOR)
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
        self.arrowActor.GetProperty().SetColor(DEFAULT_ARROW_ACTOR_COLOR)

        self.addArrowActor()

    def accept_and_emit(self):
        properties = self.getProperties()
        if properties:
            self.properties_accepted.emit(properties)
            self.accept()
            self.resetArrowActor()
        else:
            QMessageBox.warning(self, "Invalid input",
                                "Please enter valid numerical values.")

    def reject(self):
        self.resetArrowActor()
        super(ArrowPropertiesDialog, self).reject()

    def closeEvent(self, event):
        self.resetArrowActor()
        super(ArrowPropertiesDialog, self).closeEvent(event)
