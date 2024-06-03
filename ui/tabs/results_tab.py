from vtk import ( 
    vtkAxesActor, vtkOrientationMarkerWidget, vtkRenderer,
    vtkPoints, vtkPolyDataMapper, vtkActor,
    vtkGenericDataObjectReader, vtkDataSetMapper,
    vtkVertexGlyphFilter, vtkPolyData
)
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSpacerItem, 
    QSizePolicy, QMenu, QAction, QFontDialog, QDialog, QLabel, 
    QLineEdit, QMessageBox, QColorDialog, QFileDialog
)
import json
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import QIcon
from util.mesh_renderer import MeshRenderer
from data.hdf5handler import HDF5Handler
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from util.util import align_view_by_axis, Point
from util.styles import DEFAULT_QLINEEDIT_STYLE, DEFAULT_ACTOR_COLOR
from logger.log_console import LogConsole


class ResultsTab(QWidget):
    def __init__(self, log_console: LogConsole, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.toolbarLayout = QHBoxLayout()
        
        self.setup_ui()
        self.setup_axes()
        
        self.log_console = log_console
        
        self.sphere_actors = []
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        
        self.current_iteration = 0
        self.max_iterations = 0
        self.repeat_count = 0
        self.max_repeats = 10
        

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
        
        self.layout.addLayout(self.toolbarLayout)
        self.layout.addWidget(self.vtkWidget)
        self.setLayout(self.layout)
        
    
    def create_toolbar_button(self, icon_path, tooltip, callback, layout, icon_size=QSize(32, 32), button_size=QSize(32, 32)):
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
        self.addMeshedObjectButton = self.create_toolbar_button(
            icon_path="icons/custom.png",
            tooltip='Adds meshed object',
            callback=self.add_meshed_object,
            layout=self.toolbarLayout
        )
        
        self.removeAllObjectsButton = self.create_toolbar_button(
            icon_path="icons/eraser.png",
            tooltip='Adds meshed object',
            callback=self.remove_all_actors,
            layout=self.toolbarLayout
        )
        
        self.animationsButton = self.create_toolbar_button(
            icon_path="icons/anim.png",
            tooltip='Shows animation',
            callback=self.show_animation,
            layout=self.toolbarLayout
        )
        
        self.animationClearButton = self.create_toolbar_button(
            icon_path="icons/anim-remove.png",
            tooltip='Removes all the objects from the previous animation',
            callback=self.clear_animation,
            layout=self.toolbarLayout
        )
        
        self.scalarBarSettingsButton = self.create_toolbar_button(
            icon_path="icons/settings.png",
            tooltip='Scalar bar settings',
            callback=self.show_context_menu,
            layout=self.toolbarLayout
        )
        
        self.spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.toolbarLayout.addSpacerItem(self.spacer)


    def update_plot(self, hdf5_filename):
        # Clear any existing actors from the renderer before updating
        self.clear_plot()

        # Load the mesh data from the HDF5 file
        try:
            self.handler = HDF5Handler(hdf5_filename)
            self.mesh = self.handler.read_mesh_from_hdf5()
            self.mesh_renderer = MeshRenderer(self.mesh)
            self.mesh_renderer.renderer = self.renderer
            self.mesh_renderer.render_mesh()
            self.mesh_renderer.add_colorbar('Particle Count')
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
            
    def reset_to_default(self):
        self.mesh_renderer.setup_default_scalarbar_properties()
        self.apply_divs(str(self.mesh_renderer.default_num_labels))
        self.vtkWidget.GetRenderWindow().Render()
        
    
    def create_particle_actor(self, points):
        points_vtk = vtkPoints()
        for point in points:
            points_vtk.InsertNextPoint(point.x, point.y, point.z)

        polydata = vtkPolyData()
        polydata.SetPoints(points_vtk)

        vertex_filter = vtkVertexGlyphFilter()
        vertex_filter.SetInputData(polydata)
        vertex_filter.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(vertex_filter.GetOutputPort())

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1, 0, 0)
        actor.GetProperty().SetPointSize(5)

        return actor
    
    
    def animate_particle_movements(self, particles_movement):
        self.particles_movement = particles_movement
        self.current_iteration = 0
        self.repeat_count = 0
        
        # Determine the maximum number of iterations
        self.max_iterations = max(len(movements) for movements in particles_movement.values())
        self.animation_timer.start(1000)  # Update every second
        
    
    def update_animation(self):
        if self.current_iteration >= self.max_iterations:
            self.repeat_count += 1
            if self.repeat_count >= self.max_repeats:
                self.animation_timer.stop()
                return
            self.current_iteration = 0  # Reset iteration to start over

        # Remove previous actors
        for actor in self.sphere_actors:
            self.renderer.RemoveActor(actor)
        self.sphere_actors.clear()

        # Collect points for the current iteration
        points = []
        for _, movements in self.particles_movement.items():
            if self.current_iteration < len(movements):
                points.append(movements[self.current_iteration])

        # Add new actor for the current iteration
        if points:
            actor = self.create_particle_actor(points)
            self.renderer.AddActor(actor)
            self.sphere_actors.append(actor)
        
        self.vtkWidget.GetRenderWindow().Render()
        self.current_iteration += 1
    
    
    def remove_all_actors(self):
        self.particleSourceArrowActor = None
        
        actors = self.renderer.GetActors()
        actors.InitTraversal()        
        for _ in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()
            self.renderer.RemoveActor(actor)
        
        self.vtkWidget.GetRenderWindow().Render()
    
    def clear_animation(self):
        """
        Clear all actors from the previous animation.
        """
        for actor in self.sphere_actors:
            self.renderer.RemoveActor(actor)
        self.sphere_actors.clear()
        self.vtkWidget.GetRenderWindow().Render()
    
    
    def load_particle_movements(self, filename="particles_movements.json"):
        """
        Load particle movements from a JSON file.

        :param filename: Path to the JSON file.
        :return: Dictionary with particle ID as keys and list of Point objects as values.
        """
        try:
            with open(filename, 'r') as file:
                data = json.load(file)

            particles_movement = {}
            for particle_id, movements in data.items():
                particle_id = int(particle_id)
                particles_movement[particle_id] = [Point(movement['x'], movement['y'], movement['z']) for movement in movements]

            return particles_movement

        except FileNotFoundError:
            self.log_console.printError(f"The file {filename} was not found.")
        except json.JSONDecodeError:
            self.log_console.printError("Error: The file is not a valid JSON.")
        except Exception as e:
            self.log_console.printError(f"Unexpected error: {e}") 

    def show_animation(self):
        particles_movement = self.load_particle_movements()
        if not particles_movement:
            self.log_console.printError("There is nothing to show. Particles haven't been spawned or simulation hasn't been started")
            return
        self.animate_particle_movements(particles_movement)


    def add_meshed_object(self):
        """
        Upload actor from .msh file and add it to the renderer.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Select .msh file", "", "Mesh Files (*.msh);;All Files (*)", options=options)
        
        if not file_path:
            self.log_console.printWarning("No file selected.")
            return
        
        try:
            mesh_actor = self.create_actor_from_msh(file_path)
            if mesh_actor:
                self.renderer.AddActor(mesh_actor)
                mesh_actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
                self.vtkWidget.GetRenderWindow().Render()
                self.log_console.printInfo(f"Mesh loaded from {file_path}")
                self.reset_camera()
            else:
                raise ValueError("Failed to create actor from the provided .msh file.")
        
        except FileNotFoundError:
            self.log_console.printError(f"The file {file_path} was not found.")
        except ValueError as ve:
            self.log_console.printError(f"Error processing the .msh file: {ve}")
        except Exception as e:
            self.log_console.printError(f"Unexpected error: {e}")

    
    def create_actor_from_msh(self, msh_filename):
        """
        Create a VTK actor from a .msh file.
        
        :param msh_filename: Path to the .msh file.
        :return: A VTK actor.
        """
        try:
            vtk_filename = msh_filename.replace('.msh', '.vtk')
        
            reader = vtkGenericDataObjectReader()
            reader.SetFileName(vtk_filename)
            reader.Update()
            
            if reader.IsFilePolyData():
                mapper = vtkPolyDataMapper()
            elif reader.IsFileUnstructuredGrid():
                mapper = vtkDataSetMapper()
            else:
                return None
            mapper.SetInputConnection(reader.GetOutputPort())

            actor = vtkActor()
            actor.SetMapper(mapper)
            return actor
        except Exception as e:
            raise ValueError(f"Failed to create actor: {e}")
