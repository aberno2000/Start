from vtk import (
    vtkAxesActor, vtkOrientationMarkerWidget, vtkRenderer, 
    vtkWindowToImageFilter, vtkPNGWriter, vtkJPEGWriter
)
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSpacerItem,
    QSizePolicy, QMenu, QAction, QFontDialog, QDialog, QLabel,
    QLineEdit, QMessageBox, QColorDialog, QFileDialog
)
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from tabs import MeshVisualizer, ColorbarManager
from data import HDF5Handler
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from logger.log_console import LogConsole
from styles import DEFAULT_QLINEEDIT_STYLE
from field_validators import CustomIntValidator, CustomDoubleValidator
from .results import ParticleAnimator


class ResultsTab(QWidget):
    def __init__(self, log_console: LogConsole, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.toolbarLayout = QHBoxLayout()
        self.log_console = log_console

        self.setup_ui()
        self.setup_axes()
        self.setup_particle_animator()

    def setup_ui(self):
        self.setup_toolbar()

        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.renderer = vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)

        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.interactorStyle = vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(self.interactorStyle)
        self.interactor.Initialize()

        self.layout.addLayout(self.toolbarLayout)
        self.layout.addWidget(self.vtkWidget)
        self.setLayout(self.layout)
        
    def setup_axes(self):
        self.axes_actor = vtkAxesActor()
        self.axes_widget = vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(self.axes_actor)
        self.axes_widget.SetInteractor(self.vtkWidget.GetRenderWindow().GetInteractor())
        self.axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        self.axes_widget.EnabledOn()
        self.axes_widget.InteractiveOff()
        
    def setup_particle_animator(self):
        self.particle_animator = ParticleAnimator(self.vtkWidget, self.log_console, self.renderer, self)

    def create_toolbar_button(self, icon_path, tooltip, callback, layout, icon_size=QSize(40, 40), button_size=QSize(40, 40)):
        """
        Create a toolbar button and add it to the specified layout.

        :param icon_path: Path to the icon image.
        :param tooltip: Tooltip text for the button.
        :param callback: Function to connect to the button's clicked signal.
        :param layout: Layout to add the button to.
        :param icon_size: Size of the icon (QSize).
        :param button_size: Size of the button (QSize).
        :return: The created QPushButton instance.
        """
        button = QPushButton()
        button.clicked.connect(callback)
        button.setIcon(QIcon(icon_path))
        button.setIconSize(icon_size)
        button.setFixedSize(button_size)
        button.setToolTip(tooltip)
        layout.addWidget(button)
        return button

    def setup_toolbar(self):
        self.animationsButton = self.create_toolbar_button(
            icon_path="icons/anim.png",
            tooltip='Shows animation',
            callback=self.show_animation,
            layout=self.toolbarLayout
        )

        self.animationClearButton = self.create_toolbar_button(
            icon_path="icons/anim-remove.png",
            tooltip='Removes all the objects from the previous animation',
            callback=self.stop_animation,
            layout=self.toolbarLayout
        )

        self.scalarBarSettingsButton = self.create_toolbar_button(
            icon_path="icons/settings.png",
            tooltip='Scalar bar settings',
            callback=self.show_context_menu,
            layout=self.toolbarLayout
        )

        self.savePictureButton = self.create_toolbar_button(
            icon_path="icons/save-picture.png",
            tooltip='Save results as screenshot',
            callback=self.save_screenshot,
            layout=self.toolbarLayout
        )

        self.spacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.toolbarLayout.addSpacerItem(self.spacer)
        
    def show_animation(self):
        self.particle_animator.show_animation()
        
    def stop_animation(self):
        self.particle_animator.stop_animation()
        
    def edit_fps(self):
        self.particle_animator.edit_fps()

    def update_plot(self, hdf5_filename):
        # Clear any existing actors from the renderer before updating
        self.clear_plot()

        # Load the mesh data from the HDF5 file
        try:
            self.handler = HDF5Handler(hdf5_filename)
            self.mesh_data = self.handler.read_mesh_from_hdf5()
            self.mesh_visualizer = MeshVisualizer(self.renderer, self.mesh_data)
            colored_actor = self.mesh_visualizer.render_mesh()
            
            self.colorbar_manger = ColorbarManager(self.vtkWidget, self.renderer, self.mesh_data, colored_actor)
            self.colorbar_manger.add_colorbar('Particle Count')
            
        except Exception as e:
            QMessageBox.warning(self, "HDF5 Error", f"Something went wrong while hdf5 processing. Error: {e}")

        self.reset_camera()

    def reset_camera(self):
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()

    def clear_plot(self):
        self.renderer.RemoveAllViewProps()
        self.vtkWidget.GetRenderWindow().Render()

    def align_view_by_axis(self, axis: str):
        from util import align_view_by_axis
        align_view_by_axis(axis, self.renderer, self.vtkWidget)

    def show_context_menu(self):
        context_menu = QMenu(self)

        # Add actions for changing scale, font, and division number
        action_change_scale = QAction('Change Scale', self)
        action_change_font = QAction('Change Font', self)
        action_change_divs = QAction('Change Number of Divisions', self)
        action_reset = QAction('Reset To Default Settings', self)

        action_change_scale.triggered.connect(self.change_scale)
        action_change_font.triggered.connect(self.change_font)
        action_change_divs.triggered.connect(self.change_division_number)
        action_reset.triggered.connect(self.reset_to_default)

        context_menu.addAction(action_change_scale)
        context_menu.addAction(action_change_font)
        context_menu.addAction(action_change_divs)
        context_menu.addAction(action_reset)

        context_menu.exec_(self.mapToGlobal(self.scalarBarSettingsButton.pos()))

    def change_scale(self):
        if not hasattr(self, 'colorbar_manger'):
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle('Change Scalar Bar Scale')
        layout = QVBoxLayout(dialog)

        # Width input
        width_label = QLabel('Width (as fraction of window width, 0-1):', dialog)
        layout.addWidget(width_label)
        width_input = QLineEdit(dialog)
        width_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        width_input.setValidator(CustomDoubleValidator(0, 1, 9))
        layout.addWidget(width_input)

        # Height input
        height_label = QLabel('Height (as fraction of window height, 0-1):', dialog)
        layout.addWidget(height_label)
        height_input = QLineEdit(dialog)
        height_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        height_input.setValidator(CustomDoubleValidator(0, 1, 9))
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
                self.colorbar_manger.apply_scale(width, height)
                self.vtkWidget.GetRenderWindow().Render()
            else:
                QMessageBox.warning(self, "Invalid Scale", "Width and height must be between 0 and 1")
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", f"Width and height must be numeric: {e}")

    def change_font(self):
        if not hasattr(self, 'colorbar_manger'):
            return
        
        font, ok = QFontDialog.getFont()
        if ok:
            color = QColorDialog.getColor()
            if color.isValid():
                # Convert QColor to a normalized RGB tuple that VTK expects (range 0 to 1)
                color_rgb = (color.red() / 255, color.green() / 255, color.blue() / 255)

                self.colorbar_manger.change_font(font, color_rgb)
                self.vtkWidget.GetRenderWindow().Render()

    def change_division_number(self):
        if not hasattr(self, 'colorbar_manger'):
            return
        
        dialog = QDialog(self)
        dialog.setFixedWidth(250)
        dialog.setWindowTitle('Change Division Number')
        layout = QVBoxLayout(dialog)

        # Width input
        divs_label = QLabel('Count of divisions:', dialog)
        layout.addWidget(divs_label)
        divs_input = QLineEdit(dialog)
        divs_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        divs_input.setValidator(CustomIntValidator(1, 1000))
        layout.addWidget(divs_input)

        apply_button = QPushButton('Apply', dialog)
        layout.addWidget(apply_button)
        apply_button.clicked.connect(lambda: self.apply_divs(divs_input.text()))

        dialog.setLayout(layout)
        dialog.exec_()

    def apply_divs(self, divs_str):
        try:
            divs = int(divs_str)
            self.colorbar_manger.change_divs(divs)
            self.vtkWidget.GetRenderWindow().Render()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input",
                                "Division number must be numeric")

    def reset_to_default(self):
        if not hasattr(self, 'colorbar_manger'):
            return
        
        self.colorbar_manger.reset_to_default()
        self.apply_divs(str(self.default_num_labels))
        self.vtkWidget.GetRenderWindow().Render()

    def save_screenshot(self):
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Screenshot",
                "",
                "Images (*.png *.jpg *.jpeg)",
                options=options
            )
            if file_path:
                render_window = self.vtkWidget.GetRenderWindow()
                w2i = vtkWindowToImageFilter()
                w2i.SetInput(render_window)
                w2i.Update()

                writer = None
                if file_path.endswith('.png'):
                    writer = vtkPNGWriter()
                elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                    writer = vtkJPEGWriter()
                else:
                    raise ValueError("Unsupported file extension")

                writer.SetFileName(file_path)
                writer.SetInputConnection(w2i.GetOutputPort())
                writer.Write()

                QMessageBox.information(
                    self, "Success", f"Screenshot saved to {file_path}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save screenshot: {e}")
