from vtk import ( 
    vtkAxesActor, vtkOrientationMarkerWidget, vtkRenderer
)
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSpacerItem, 
    QSizePolicy, QMenu, QAction, QFontDialog, QDialog, QLabel, 
    QLineEdit, QMessageBox, QColorDialog
)
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from util.mesh_renderer import MeshRenderer
from data.hdf5handler import HDF5Handler
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from util.util import align_view_by_axis
from util.styles import DEFAULT_QLINEEDIT_STYLE


class ResultsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.toolbarLayout = QHBoxLayout(self)
        
        self.setup_ui()
        self.setup_axes()
        

    def setup_axes(self):
        self.axes_actor = vtkAxesActor()
        self.axes_widget = vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(self.axes_actor)
        self.axes_widget.SetInteractor(self.vtkWidget.GetRenderWindow().GetInteractor())
        self.axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        self.axes_widget.EnabledOn()
        self.axes_widget.InteractiveOff()
        

    def setup_ui(self):
        self.setup_toolbar()
        
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.renderer = vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)

        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.interactorStyle = vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(self.interactorStyle)
        self.interactor.Initialize()
        
        self.toolbarLayout.addWidget(self.scalarBarSettingsButton)
        self.layout.addLayout(self.toolbarLayout)
        self.layout.addWidget(self.vtkWidget)
        self.setLayout(self.layout)
        
    
    def setup_toolbar(self):       
        self.scalarBarSettingsButton = QPushButton()
        self.scalarBarSettingsButton.clicked.connect(self.show_context_menu)
        self.scalarBarSettingsButton.setIcon(QIcon("icons/settings.png"))
        self.scalarBarSettingsButton.setIconSize(QSize(32, 32))
        self.scalarBarSettingsButton.setFixedSize(QSize(32, 32))
        self.scalarBarSettingsButton.setToolTip('Scalar bar settings')
        
        self.spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.toolbarLayout.addSpacerItem(self.spacer)


    def update_plot(self, hdf5_filename):
        # Clear any existing actors from the renderer before updating
        self.clear_plot()

        # Load the mesh data from the HDF5 file
        self.handler = HDF5Handler(hdf5_filename)
        self.mesh = self.handler.read_mesh_from_hdf5()
        self.mesh_renderer = MeshRenderer(self.mesh)
        self.mesh_renderer.renderer = self.renderer
        self.mesh_renderer.render_mesh()
        self.mesh_renderer.add_colorbar('Particle Count')
        
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
        
        
    def clear_plot(self):
        self.renderer.RemoveAllViewProps()
        self.vtkWidget.GetRenderWindow().Render()
        
    
    def align_view_by_axis(self, axis: str):
        align_view_by_axis(axis, self.renderer, self.vtkWidget)


    def show_context_menu(self):
        context_menu = QMenu(self)

        # Add actions for changing scale, font, and division number
        action_change_scale = QAction('Change Scale', self)
        action_change_font = QAction('Change Font', self)
        action_change_divs = QAction('Change Number of Divisions', self)

        action_change_scale.triggered.connect(self.change_scale)
        action_change_font.triggered.connect(self.change_font)
        action_change_divs.triggered.connect(self.change_division_number)

        context_menu.addAction(action_change_scale)
        context_menu.addAction(action_change_font)
        context_menu.addAction(action_change_divs)

        context_menu.exec_(self.mapToGlobal(self.scalarBarSettingsButton.pos()))

    
    def change_scale(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Change Scalar Bar Scale')
        layout = QVBoxLayout(dialog)

        # Width input
        width_label = QLabel('Width (as fraction of window width, 0-1):', dialog)
        layout.addWidget(width_label)
        width_input = QLineEdit(dialog)
        width_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        layout.addWidget(width_input)

        # Height input
        height_label = QLabel('Height (as fraction of window height, 0-1):', dialog)
        layout.addWidget(height_label)
        height_input = QLineEdit(dialog)
        height_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        layout.addWidget(height_input)

        apply_button = QPushButton('Apply', dialog)
        layout.addWidget(apply_button)
        apply_button.clicked.connect(lambda: self.apply_scale(width_input.text(), height_input.text()))

        dialog.setLayout(layout)
        dialog.exec_()

    def apply_scale(self, width_str, height_str):
        try:
            width = float(width_str)
            height = float(height_str)
            if 0 <= width <= 1 and 0 <= height <= 1:
                self.mesh_renderer.scalarBar.SetWidth(width)
                self.mesh_renderer.scalarBar.SetHeight(height)
                self.vtkWidget.GetRenderWindow().Render()
            else:
                QMessageBox.warning(self, "Invalid Scale", "Width and height must be between 0 and 1")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Width and height must be numeric")

    def change_font(self):
        font, ok = QFontDialog.getFont()
        if ok:
            color = QColorDialog.getColor()
            if color.isValid():
                # Convert QColor to a normalized RGB tuple that VTK expects (range 0 to 1)
                color_rgb = (color.red() / 255, color.green() / 255, color.blue() / 255)
                
                text_property = self.mesh_renderer.scalarBar.GetLabelTextProperty()
                text_property.SetFontFamilyAsString(font.family())
                text_property.SetFontSize(font.pointSize())
                text_property.SetBold(font.bold())
                text_property.SetItalic(font.italic())
                text_property.SetColor(color_rgb)

                # Apply changes to title text property if needed
                title_text_property = self.mesh_renderer.scalarBar.GetTitleTextProperty()
                title_text_property.SetFontFamilyAsString(font.family())
                title_text_property.SetFontSize(font.pointSize())
                title_text_property.SetBold(font.bold())
                title_text_property.SetItalic(font.italic())
                title_text_property.SetColor(color_rgb)

                self.vtkWidget.GetRenderWindow().Render()
                
    def change_division_number(self):
        dialog = QDialog(self)
        dialog.setFixedWidth(250)
        dialog.setWindowTitle('Change Division Number')
        layout = QVBoxLayout(dialog)

        # Width input
        divs_label = QLabel('Count of divisions:', dialog)
        layout.addWidget(divs_label)
        divs_input = QLineEdit(dialog)
        divs_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        layout.addWidget(divs_input)

        apply_button = QPushButton('Apply', dialog)
        layout.addWidget(apply_button)
        apply_button.clicked.connect(lambda: self.apply_divs(divs_input.text()))

        dialog.setLayout(layout)
        dialog.exec_()
    
    def apply_divs(self, divs_str):
        try:
            divs = int(divs_str)
            self.mesh_renderer.scalarBar.SetNumberOfLabels(divs)
            self.mesh_renderer.set_annotations(divs)
            self.vtkWidget.GetRenderWindow().Render()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Division number must be numeric")
