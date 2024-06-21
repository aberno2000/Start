from gmsh import initialize, finalize, isInitialized, model, option
import json
from os import remove
from os.path import isfile, exists
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkFiltersGeneral import vtkBooleanOperationPolyDataFilter
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, pyqtSlot, QItemSelectionModel
from vtk import (
    vtkRenderer, vtkPoints, vtkPolyData, vtkPolyLine, vtkCellArray, vtkPolyDataMapper,
    vtkActor, vtkAxesActor, vtkOrientationMarkerWidget, vtkGenericDataObjectReader, 
    vtkDataSetMapper, vtkCellPicker, vtkCleanPolyData, vtkPlane, vtkClipPolyData,
    vtkCommand, vtkMatrix4x4, vtkInteractorStyleTrackballCamera, vtkInteractorStyleTrackballActor,
    vtkInteractorStyleRubberBandPick, vtkTransformPolyDataFilter
)
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QTreeView,
    QPushButton, QDialog, QSpacerItem, QColorDialog,
    QSizePolicy, QMessageBox, QFileDialog,
    QMenu, QAction, QInputDialog, QStatusBar, QAbstractItemView,
)
from PyQt5.QtGui import QCursor, QStandardItemModel, QBrush
from util import *
from styles import *
from constants import *
from dialogs import *
from .simple_geometry import *
from .interactor import *
from .particle_source_manager import ParticleSourceManager
from .mesh_tree import MeshTreeManager


class GraphicalEditor(QFrame):
    def __init__(self, log_console: LogConsole, config_tab, parent=None):
        super().__init__(parent)
        
        self.config_tab = config_tab
        self.log_console = log_console
        self.mesh_file = None

        self.setup_dicts()
        self.setup_tree_view()
        self.setup_selected_actors()
        self.setup_difficult_geometry_actors()
        self.setup_picker(log_console)
        self.setup_toolbar()
        self.setup_ui()
        self.setup_interaction()
        self.setup_status_bar()
        self.setup_particle_source_manager()
        self.setup_axes()

        self.objectsAddingHistory = ActionHistory()
        self.global_undo_stack = []
        self.global_redo_stack = []

        self.isPerformOperation = (False, None)
        self.firstObjectToPerformOperation = None
        self.statusBar = QStatusBar()
        self.layout.addWidget(self.statusBar)

        self.crossSectionLinePoints = []  # To store points for the cross-section line
        self.isDrawingLine = False        # To check if currently drawing the line
        self.tempLineActor = None         # Temporary actor for the line visualization
        
    def setup_dicts(self):
        # External row - is the 1st row in the tree view (volume, excluding objects like: line, point)
        # Internal row - is the 2nd row in the tree view (surface)
        # Tree dictionary (treedict) - own invented dictionary that stores data to fill the mesh tree
        self.externRow_treedict = {}   # Key = external row        |  value = treedict
        self.externRow_actors = {}     # Key = external row        |  value = list of actors
        self.actor_rows = {}           # Key = actor               |  value = pair(external row, internal row)
        self.actor_color = {}          # Key = actor               |  value = color
        self.actor_nodes = {}          # Key = actor               |  value = list of nodes
        self.actor_matrix = {}         # Key = actor               |  value = transformation matrix: pair(initial, current)
        self.meshfile_actors = {}      # Key = mesh filename       |  value = list of actors
        
    def setup_tree_view(self):
        self.treeView = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Mesh Tree'])
    
    def setup_selected_actors(self):
        self.selected_actors = set()
        
    def setup_difficult_geometry_actors(self):
        self.difficult_geometries = set()

    def setup_picker(self, log_console):
        self.picker = vtkCellPicker()
        self.picker.SetTolerance(0.005)
        self.log_console = log_console
        
    def setup_toolbar(self):
        self.layout = QVBoxLayout()  # Main layout
        self.toolbarLayout = QHBoxLayout()  # Layout for the toolbar

        # Create buttons for the toolbar
        self.createPointButton = self.create_button('icons/point.png', 'Point')
        self.createLineButton = self.create_button('icons/line.png', 'Line')
        self.createSurfaceButton = self.create_button('icons/surface.png', 'Surface')
        self.createSphereButton = self.create_button('icons/sphere.png', 'Sphere')
        self.createBoxButton = self.create_button('icons/box.png', 'Box')
        self.createCylinderButton = self.create_button('icons/cylinder.png', 'Cylinder')
        self.uploadCustomButton = self.create_button('icons/custom.png', 'Upload mesh object')
        self.eraseAllObjectsButton = self.create_button('icons/eraser.png', 'Erase all')
        self.xAxisButton = self.create_button('icons/x-axis.png', 'Set camera view to X-axis')
        self.yAxisButton = self.create_button('icons/y-axis.png', 'Set camera view to Y-axis')
        self.zAxisButton = self.create_button('icons/z-axis.png', 'Set camera view to Z-axis')
        self.centerAxisButton = self.create_button('icons/center-axis.png', 'Set camera view to center of axes')
        self.subtractObjectsButton = self.create_button('icons/subtract.png', 'Subtract objects')
        self.unionObjectsButton = self.create_button('icons/union.png', 'Combine (union) objects')
        self.intersectObjectsButton = self.create_button('icons/intersection.png', 'Intersection of two objects')
        self.crossSectionButton = self.create_button('icons/cross-section.png', 'Cross section of the object')
        self.setBoundaryConditionsSurfaceButton = self.create_button('icons/boundary-conditions-surface.png', 'Turning on mode to select boundary nodes on surface')
        self.setParticleSourceButton = self.create_button('icons/particle-source.png', 'Set particle source as surface')
        self.meshCreatedObjectsButton = self.create_button('icons/mesh-objects.png', 'Mesh created objects. WARNING: After this action list of the created objects will be zeroed up')

        self.spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.toolbarLayout.addSpacerItem(self.spacer)

        # Connect buttons to methods
        self.createPointButton.clicked.connect(self.create_point)
        self.createLineButton.clicked.connect(self.create_line)
        self.createSurfaceButton.clicked.connect(self.create_surface)
        self.createSphereButton.clicked.connect(self.create_sphere)
        self.createBoxButton.clicked.connect(self.create_box)
        self.createCylinderButton.clicked.connect(self.create_cylinder)
        self.uploadCustomButton.clicked.connect(self.upload_custom)
        self.eraseAllObjectsButton.clicked.connect(self.clear_scene_and_tree_view)
        self.xAxisButton.clicked.connect(lambda: self.align_view_by_axis('x'))
        self.yAxisButton.clicked.connect(lambda: self.align_view_by_axis('y'))
        self.zAxisButton.clicked.connect(lambda: self.align_view_by_axis('z'))
        self.centerAxisButton.clicked.connect(lambda: self.align_view_by_axis('center'))
        self.subtractObjectsButton.clicked.connect(self.subtract_button_clicked)
        self.unionObjectsButton.clicked.connect(self.combine_button_clicked)
        self.intersectObjectsButton.clicked.connect(self.intersection_button_clicked)
        self.crossSectionButton.clicked.connect(self.cross_section_button_clicked)
        self.setBoundaryConditionsSurfaceButton.clicked.connect(self.activate_selection_boundary_conditions_mode_for_surface)
        self.setParticleSourceButton.clicked.connect(self.set_particle_source)
        self.meshCreatedObjectsButton.clicked.connect(self.save_and_mesh_objects)

        self.tmpButton = self.create_button('', '')
        self.tmpButton.clicked.connect(self.test)
        
    def setup_ui(self):
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.layout.addLayout(self.toolbarLayout)
        self.layout.addWidget(self.vtkWidget)
        self.setLayout(self.layout)

        self.renderer = vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)

        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.on_treeView_context_menu)
    
    def setup_interaction(self):
        self.change_interactor(INTERACTOR_STYLE_TRACKBALL_CAMERA)
        self.interactor.AddObserver(vtkCommand.KeyPressEvent, self.on_key_press)
        
    def setup_status_bar(self):
        self.statusBar = QStatusBar()
        self.layout.addWidget(self.statusBar)

    def setup_particle_source_manager(self):
        self.particle_source_manager = ParticleSourceManager(self.vtkWidget, self.renderer, self.log_console, self.config_tab, self.selected_actors, self.statusBar, self)
        
    def setup_axes(self):
        self.axes_actor = vtkAxesActor()
        self.axes_widget = vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(self.axes_actor)
        self.axes_widget.SetInteractor(self.vtkWidget.GetRenderWindow().GetInteractor())
        self.axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        self.axes_widget.EnabledOn()
        self.axes_widget.InteractiveOff()

    def get_treedict_by_extern_row(self, extern_row):
        return self.externRow_treedict.get(extern_row, None)

    def get_extern_row_by_treedict(self, treedict):
        for extern_row, td in self.externRow_treedict.items():
            if td == treedict:
                return extern_row
        return None

    def get_actors_by_extern_row(self, extern_row):
        return self.externRow_actors.get(extern_row, [])

    def get_extern_row_by_actor(self, actor):
        for extern_row, actors in self.externRow_actors.items():
            if actor in actors:
                return extern_row
        return None

    def get_rows_by_actor(self, actor):
        return self.actor_rows.get(actor, None)

    def get_actors_by_extern_row_from_actorRows(self, extern_row):
        return [actor for actor, (ext_row, _) in self.actor_rows.items() if ext_row == extern_row]

    def get_color_by_actor(self, actor):
        return self.actor_color.get(actor, None)

    def get_actors_by_color(self, color):
        return [actor for actor, clr in self.actor_color.items() if clr == color]

    def get_nodes_by_actor(self, actor):
        return self.actor_nodes.get(actor, [])

    def get_actors_by_node(self, node):
        return [actor for actor, nodes in self.actor_nodes.items() if node in nodes]

    def get_matrix_by_actor(self, actor):
        return self.actor_matrix.get(actor, None)

    def get_actors_by_matrix(self, matrix):
        return [actor for actor, matrices in self.actor_matrix.items() if matrices == matrix]

    def get_actors_by_filename(self, filename):
        return self.meshfile_actors.get(filename, [])

    def get_filename_by_actor(self, actor):
        for filename, actors in self.meshfile_actors.items():
            if actor in actors:
                return filename
        return None
    
    def get_filenames_from_dict(self) -> list:
        filenames = []
        for filename, actors in self.meshfile_actors.items():
            filenames.append(filename)
        return filenames

    def get_index_from_rows(self, external_row, internal_row):
        # Get the external index
        external_index = self.treeView.model().index(external_row, 0)
        if not external_index.isValid():
            return None

        # Get the internal index using the external index as parent
        internal_index = self.treeView.model().index(internal_row, 0, external_index)
        if not internal_index.isValid():
            return None

        return internal_index

    def update_actor_dictionaries(self, actor_to_add: vtkActor, volume_row: int, surface_row: int, filename: str):
        self.actor_rows[actor_to_add] = (volume_row, surface_row)
        self.actor_color[actor_to_add] = DEFAULT_ACTOR_COLOR
        self.actor_matrix[actor_to_add] = (actor_to_add.GetMatrix(), actor_to_add.GetMatrix())
        self.meshfile_actors.setdefault(filename, []).append(actor_to_add)

    def update_actor_dictionaries(self, actor_to_remove: vtkActor, actor_to_add=None):
        """
        Remove actor_to_remove from all dictionaries and add actor_to_add to those dictionaries if provided.

        Args:
            actor_to_remove (vtkActor): The actor to remove from all dictionaries.
            actor_to_add (vtkActor, optional): The actor to add to all dictionaries. Defaults to None.
        """
        if actor_to_remove in self.actor_rows:
            volume_row, surface_row = self.actor_rows[actor_to_remove]

            # Remove actor from actor_rows
            del self.actor_rows[actor_to_remove]

            # Remove actor from actor_color
            if actor_to_remove in self.actor_color:
                del self.actor_color[actor_to_remove]

            # Remove actor from actor_matrix
            if actor_to_remove in self.actor_matrix:
                del self.actor_matrix[actor_to_remove]

            # Remove actor from meshfile_actors
            for filename, actors in self.meshfile_actors.items():
                if actor_to_remove in actors:
                    actors.remove(actor_to_remove)
                    break

            # If an actor to add is provided, add it to the dictionaries
            if actor_to_add:
                self.actor_rows[actor_to_add] = (volume_row, surface_row)
                self.actor_color[actor_to_add] = DEFAULT_ACTOR_COLOR
                self.actor_matrix[actor_to_add] = (
                    actor_to_add.GetMatrix(), actor_to_add.GetMatrix())
                self.meshfile_actors.setdefault(
                    filename, []).append(actor_to_add)

    @pyqtSlot()
    def activate_selection_boundary_conditions_mode_slot(self):
        self.setBoundaryConditionsSurfaceButton.click()

    def initialize_tree(self):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Mesh Tree'])
        self.setTreeViewModel()

    def setTreeViewModel(self):
        self.treeView.setModel(self.model)
        self.treeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeView.selectionModel().selectionChanged.connect(
            self.on_tree_selection_changed)

    def upload_mesh_file(self, file_path):
        if exists(file_path) and isfile(file_path):
            self.clear_scene_and_tree_view()
            self.mesh_file = file_path
            self.initialize_tree()
            
            if not isInitialized():
                initialize()
            treedict = MeshTreeManager.get_tree_dict(self.mesh_file)
            if isInitialized():
                finalize()
            
            self.add_actors_and_populate_tree_view(treedict, file_path)
        else:
            QMessageBox.warning(self, "Warning", f"Unable to open file {file_path}")
            return None

    def erase_all_from_tree_view(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Mesh Tree'])

    def get_actor_from_mesh(self, mesh_file_path: str):
        vtk_file_path = mesh_file_path.replace('.msh', '.vtk')

        reader = vtkGenericDataObjectReader()
        reader.SetFileName(vtk_file_path)
        reader.Update()

        if reader.IsFilePolyData():
            mapper = vtkPolyDataMapper()
        elif reader.IsFileUnstructuredGrid():
            mapper = vtkDataSetMapper()
        else:
            return
        mapper.SetInputConnection(reader.GetOutputPort())

        actor = vtkActor()
        actor.SetMapper(mapper)
        self.add_actor(actor)

        return actor

    def create_button(self, icon_path, tooltip, size=(40, 40)):
        button = QPushButton()
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(*size))
        button.setFixedSize(QSize(*size))
        button.setToolTip(tooltip)
        self.toolbarLayout.addWidget(button)
        return button

    def on_treeView_context_menu(self, position):
        indexes = self.treeView.selectedIndexes()
        if not indexes:
            return

        menu = QMenu()

        move_action = QAction('Move', self)
        rotate_action = QAction('Rotate', self)
        adjust_size_action = QAction('Adjust size', self)
        remove_action = QAction('Remove', self)
        colorize_action = QAction('Colorize', self)
        merge_surfaces_action = QAction('Merge surfaces', self)
        add_material_action = QAction('Add Material', self)
        hide_action = QAction('Hide', self)

        move_action.triggered.connect(self.move_actors)
        rotate_action.triggered.connect(self.rotate_actors)
        adjust_size_action.triggered.connect(self.adjust_actors_size)
        remove_action.triggered.connect(self.permanently_remove_actors)
        colorize_action.triggered.connect(self.colorize_actors)
        merge_surfaces_action.triggered.connect(self.merge_surfaces)
        add_material_action.triggered.connect(self.add_material)
        hide_action.triggered.connect(self.hide_actors)

        # Determine if all selected actors are visible or not
        all_visible = all(actor.GetVisibility() for actor in self.selected_actors if actor and isinstance(actor, vtkActor))
        hide_action.setText('Hide' if all_visible else 'Show')

        menu.addAction(move_action)
        menu.addAction(rotate_action)
        menu.addAction(adjust_size_action)
        menu.addAction(remove_action)
        menu.addAction(colorize_action)
        menu.addAction(merge_surfaces_action)
        menu.addAction(add_material_action)
        menu.addAction(hide_action)

        menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def hide_actors(self):
        action = self.sender()
        all_visible = all(actor.GetVisibility() for actor in self.selected_actors if actor and isinstance(actor, vtkActor))

        for actor in self.selected_actors:
            if actor and isinstance(actor, vtkActor):
                cur_visibility = actor.GetVisibility()
                actor.SetVisibility(not cur_visibility)
                self.update_tree_item_visibility(actor, not cur_visibility)

        if all_visible:
            action.setText('Show')
        else:
            action.setText('Hide')

        self.render_editor_window_without_resetting_camera()

    def update_tree_item_visibility(self, actor, visible):
        rows = self.get_rows_by_actor(actor)
        if rows:
            external_row, internal_row = rows
            index = self.get_index_from_rows(external_row, internal_row)
            if index.isValid():
                item = self.treeView.model().itemFromIndex(index)
                if item:
                    original_name = item.text()
                    if visible:
                        if original_name.endswith(" (hidden)"):
                            # Remove " (hidden)"
                            item.setText(original_name[:-9])
                        item.setForeground(QBrush(DEFAULT_TREE_VIEW_ROW_COLOR))
                    else:
                        if not original_name.endswith(" (hidden)"):
                            # Add " (hidden)"
                            item.setText(original_name + " (hidden)")
                        item.setForeground(
                            QBrush(DEFAULT_TREE_VIEW_ROW_COLOR_HIDED_ACTOR))

    def rename_tree_item(self, rows, new_name):
        """
        Rename a tree view item identified by the provided rows.

        :param rows: A tuple containing the external and internal rows.
        :param new_name: The new name to set for the tree view item.
        """
        external_row, internal_row = rows
        index = self.get_index_from_rows(external_row, internal_row)
        if index.isValid():
            item = self.treeView.model().itemFromIndex(index)
            if item:
                item.setText(new_name)

    def get_filename_from_dialog(self) -> str:
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getSaveFileName(
            None, "Save Mesh File", "", "Mesh Files (*.msh);;All Files (*)", options=options)

        if not filename:
            return None
        if not filename.endswith('.msh'):
            filename += '.msh'

        return filename

    def create_point(self):
        dialog = PointDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z = dialog.getValues()

            try:
                point_actor = SimpleGeometryManager.create_point(self.log_console, x, y, z)
                if point_actor:
                    self.add_actor(point_actor)
            except ValueError as e:
                QMessageBox.warning(self, "Create Point", str(e))

    def create_line(self):
        dialog = LineDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.getValues()
            if values is not None and len(values) >= 6:
                points = [(values[i], values[i + 1], values[i + 2]) for i in range(0, len(values), 3)]

                try:
                    line_actor = SimpleGeometryManager.create_line(self.log_console, points)
                    if line_actor:
                        self.add_actor(line_actor)
                except ValueError as e:
                    QMessageBox.warning(self, "Create Line", str(e))

    def create_surface(self):
        dialog = SurfaceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.getValues()

            if values is not None and len(values) >= 9:
                points = [(values[i], values[i + 1], values[i + 2]) for i in range(0, len(values), 3)]

                try:
                    surface_actor = SimpleGeometryManager.create_surface(self.log_console, points)
                    if surface_actor:
                        self.add_actor(surface_actor)
                except ValueError as e:
                    QMessageBox.warning(self, "Create Surface", str(e))

    def create_sphere(self):
        dialog = SphereDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z, radius, phi_resolution, theta_resolution = dialog.getValues()

            try:
                sphere_actor = SimpleGeometryManager.create_sphere(self.log_console, x, y, z, radius, phi_resolution, theta_resolution)
                if sphere_actor:
                    self.add_actor(sphere_actor)
            except ValueError as e:
                QMessageBox.warning(self, "Create Sphere", str(e))

    def create_box(self):
        dialog = BoxDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z, length, width, height = dialog.getValues()

            try:
                box_actor = SimpleGeometryManager.create_box(self.log_console, x, y, z, length, width, height)
                if box_actor:
                    self.add_actor(box_actor)
                    
            except ValueError as e:
                QMessageBox.warning(self, "Create Box", str(e))

    def create_cylinder(self):
        dialog = CylinderDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z, radius, dx, dy, dz, resolution = dialog.getValues()

            try:
                cylinder_actor = SimpleGeometryManager.create_cylinder(self.log_console, x, y, z, radius, dx, dy, dz, resolution)
                if cylinder_actor:
                    self.add_actor(cylinder_actor)
            except ValueError as e:
                QMessageBox.warning(self, "Create Cylinder", str(e))

    def upload_custom(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Mesh or Geometry File",
            "",
            "Mesh Files (*.msh);;Step Files (*.stp);;VTK Files (*.vtk);;All Files (*)",
            options=options,
        )

        if not file_name:
            return

        # If the selected file is a STEP file, prompt for conversion parameters.
        if file_name.endswith('.stp'):
            dialog = MeshDialog(self)
            if dialog.exec() == QDialog.Accepted:
                mesh_size, mesh_dim = dialog.get_values()
                try:
                    mesh_size = float(mesh_size)
                    mesh_dim = int(mesh_dim)
                    if mesh_dim not in [2, 3]:
                        raise ValueError("Mesh dimensions must be 2 or 3.")
                    converted_file_name = self.convert_stp_to_msh(
                        file_name, mesh_size, mesh_dim)
                    if converted_file_name:
                        self.add_custom(converted_file_name)
                except ValueError as e:
                    QMessageBox.warning(self, "Invalid Input", str(e))
            else:
                QMessageBox.critical(
                    self, "Error", "Dialog was closed by user. Invalid mesh size or mesh dimensions.")
        elif file_name.endswith('.msh') or file_name.endswith('.vtk'):
            self.add_custom(file_name)
            self.log_console.printInfo(
                f'Successfully uploaded custom object from {file_name}')

    def convert_stp_to_msh(self, filename, mesh_size, mesh_dim):
        try:
            if not isInitialized():
                initialize()
            
            initialize()
            model.add("model")
            model.occ.importShapes(filename)
            model.occ.synchronize()
            option.setNumber("Mesh.MeshSizeMin", mesh_size)
            option.setNumber("Mesh.MeshSizeMax", mesh_size)

            if mesh_dim == 2:
                model.mesh.generate(2)
            elif mesh_dim == 3:
                model.mesh.generate(3)

            output_file = filename.replace(".stp", ".msh")
            write(output_file)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"An error occurred during conversion: {str(e)}")
            return None
        finally:
            finalize()
            return output_file

    def add_actor(self, actor: vtkActor):
        self.renderer.AddActor(actor)
        actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
        self.render_editor_window()

    def add_actors(self, actors: list):
        for actor in actors:
            self.renderer.AddActor(actor)
            actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
        self.render_editor_window()

    def remove_actor(self, actor):
        if actor and isinstance(actor, vtkActor) and actor in self.renderer.GetActors():
            self.renderer.RemoveActor(actor)
            self.render_editor_window()

    def remove_actors(self, actors: list):
        for actor in actors:
            if actor in self.renderer.GetActors():
                self.renderer.RemoveActor(actor)
        self.render_editor_window()

    def remove_objects_with_restore(self, actors: list):
        # TODO: implement
        pass

    def permanently_remove_actors(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText(
            "Are you sure you want to delete the object? It will be permanently deleted.")
        msgBox.setWindowTitle("Permanently Object Deletion")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        choice = msgBox.exec()
        if choice == QMessageBox.No:
            return
        else:
            for actor in self.selected_actors:
                if actor and isinstance(actor, vtkActor):
                    row = self.get_volume_row(actor)
                    if row is None:
                        self.remove_actor(actor)
                        return

                    actors = self.get_actor_from_volume_row(row)
                    if not actors:
                        self.log_console.printInternalError(f"Can't find actors <{hex(id(actors))}> by tree view row [{row}]>")
                        return

                    self.remove_row_from_tree(row)
                    self.remove_actors(actors)
                    self.objectsAddingHistory.remove_by_id(
                        self.objectsAddingHistory.get_id())
                    self.objectsAddingHistory.decrementIndex()

    def colorize_actors(self):
        actorColor = QColorDialog.getColor()
        if actorColor.isValid():
            r, g, b = actorColor.redF(), actorColor.greenF(), actorColor.blueF()

            for actor in self.selected_actors:
                if actor and isinstance(actor, vtkActor):
                    actor.GetProperty().SetColor(r, g, b)
                    self.actor_color[actor] = (r, g, b)
            self.deselect()

    def remove_all_actors(self):
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        for i in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()
            self.renderer.RemoveActor(actor)

        self.render_editor_window()

    def add_custom(self, meshfilename: str):
        initialize()
        customTreeDict = MeshTreeManager.get_tree_dict(meshfilename)
        self.add_actors_and_populate_tree_view(
            customTreeDict, meshfilename, 'volume')
        finalize()

    def global_undo(self):
        if not self.global_undo_stack:
            return
        action = self.global_undo_stack.pop()
        self.global_redo_stack.append(action)

        if action == ACTION_ACTOR_CREATING:
            self.undo_object_creating()
        elif action == ACTION_ACTOR_TRANSFORMATION:
            self.undo_transform()
        # TODO: Make other actions

    def global_redo(self):
        if not self.global_redo_stack:
            return
        action = self.global_redo_stack.pop()
        self.global_undo_stack.append(action)

        if action == ACTION_ACTOR_CREATING:
            self.redo_object_creating()
        elif action == ACTION_ACTOR_TRANSFORMATION:
            self.redo_transform()
        # TODO: Make other actions

    def undo_transform(self):
        # TODO: implement
        pass

    def redo_transform(self):
        # TODO: implement
        pass

    def undo_object_creating(self):
        res = self.objectsAddingHistory.undo()
        if not res:
            return
        row, actors, treedict, objType = res

        self.remove_actors(actors)

        if objType != 'line':
            self.remove_row_from_tree(row)
        else:
            self.remove_rows_from_tree(row)

    def redo_object_creating(self):
        res = self.objectsAddingHistory.redo()
        if not res:
            return
        row, actors, treedict, objType = res

        self.add_actors(actors)
        self.populate_tree(treedict, objType)

    def remove_row_from_tree(self, row):
        self.model.removeRow(row)

    def remove_rows_from_tree(self, rows):
        row = rows[0]
        for _ in range(len(rows)):
            self.model.removeRow(row)

    def get_transformed_actors(self):
        """
        Identify all actors that have been transformed and update the actor_matrix.

        Returns:
            list: A list of transformed actors along with their filenames.
        """
        transformed_actors = set()

        for actor, (initial_transform, _) in self.actor_matrix.items():
            current_transform = actor.GetMatrix()

            if not compare_matrices(current_transform, initial_transform):
                filename = None
                for fn, actors in self.meshfile_actors.items():
                    if actor in actors:
                        filename = fn
                        break
                transformed_actors.add((actor, filename))

                # Update the actor_matrix with the new transform
                new_transform = vtkMatrix4x4()
                new_transform.DeepCopy(current_transform)
                self.actor_matrix[actor] = (initial_transform, new_transform)

        return transformed_actors

    def update_gmsh_files(self):
        """
        Update Gmsh files for all transformed actors.
        """
        transformed_actors = self.get_transformed_actors()
        if not transformed_actors:
            return

        for actor, key, filename in transformed_actors:
            if not isInitialized():
                initialize()
            
            treedict = MeshTreeManager.get_tree_dict(filename)
            if not treedict:
                continue

            success, vtk_filename = MeshTreeManager.write_treedict_to_vtk(treedict, filename)
            if not success:
                self.log_console.printWarning(
                    f"Failed to update Gmsh file for temporary filename {vtk_filename}")
                QMessageBox.warning(
                    self, "Gmsh Update Warning", f"Failed to update Gmsh file for temporary filename {vtk_filename}")
                
                if isInitialized():
                    finalize()
                return
            else:
                self.log_console.printInfo(f"Object in temporary mesh file {vtk_filename} was successfully written")

            msh_filename = convert_vtk_to_msh(vtk_filename)
            if not msh_filename:
                self.log_console.printWarning(f"Failed to write data from the {vtk_filename} to {msh_filename}")
                QMessageBox.warning(self, "Gmsh Update Warning", 
                                    f"Failed to write data from the {vtk_filename} to {msh_filename}")
                if isInitialized():
                    finalize()
                return

            self.log_console.printInfo(
                f"Successfully updated object in {msh_filename}")

            try:
                remove(vtk_filename)
                self.log_console.printInfo(f"Successfully removed temporary vtk mesh file: {vtk_filename}")
            except Exception as e:
                self.log_console.printError(f"Can't remove temporary vtk mesh file {vtk_filename}: {e}")
            finally:
                if isInitialized():
                    finalize()


    def fill_dicts(self, row, actors, objType: str, filename: str):
        """
        Populate the new dictionaries with actors and their initial transformations.

        Args:
            row (int): The row index in the tree view.
            actors (list): List of vtkActor objects.
            objType (str): The type of object ('volume', 'line', etc.).
            filename (str): The mesh filename associated with the actors.
        """
        if objType == 'volume':
            volume_row = row
            for i, actor in enumerate(actors):
                if actor and isinstance(actor, vtkActor):
                    surface_row = volume_row + i
                    actor_color = actor.GetProperty().GetColor()
                    initial_transform = vtkMatrix4x4()
                    initial_transform.DeepCopy(actor.GetMatrix())

                    self.actor_rows[actor] = (volume_row, surface_row)
                    self.actor_color[actor] = actor_color
                    self.actor_matrix[actor] = (
                        initial_transform, initial_transform)
                    if filename in self.meshfile_actors:
                        self.meshfile_actors[filename].append(actor)
                    else:
                        self.meshfile_actors[filename] = [actor]

        elif objType == 'line':
            for i, r in enumerate(row):
                actor = actors[i]
                if actor and isinstance(actor, vtkActor):
                    actor_color = actor.GetProperty().GetColor()
                    initial_transform = vtkMatrix4x4()
                    initial_transform.DeepCopy(actor.GetMatrix())

                    self.actor_rows[actor] = (r, r)
                    self.actor_color[actor] = actor_color
                    self.actor_matrix[actor] = (
                        initial_transform, initial_transform)
                    if filename in self.meshfile_actors:
                        self.meshfile_actors[filename].append(actor)
                    else:
                        self.meshfile_actors[filename] = [actor]

        else:
            for actor in actors:
                if actor and isinstance(actor, vtkActor):
                    actor_color = actor.GetProperty().GetColor()
                    initial_transform = vtkMatrix4x4()
                    initial_transform.DeepCopy(actor.GetMatrix())

                    self.actor_rows[actor] = (row, row)
                    self.actor_color[actor] = actor_color
                    self.actor_matrix[actor] = (
                        initial_transform, initial_transform)
                    if filename in self.meshfile_actors:
                        self.meshfile_actors[filename].append(actor)
                    else:
                        self.meshfile_actors[filename] = [actor]

    def get_volume_row(self, actor):
        """
        Get the volume index for the given actor.

        Args:
            actor (vtkActor): The actor for which to get the volume index.

        Returns:
            int: The volume index, or None if the actor is not found.
        """
        if actor in self.actor_rows:
            return self.actor_rows[actor][0]
        return None

    def get_surface_row(self, actor):
        """
        Get the surface index for the given actor.

        Args:
            actor (vtkActor): The actor for which to get the surface index.

        Returns:
            int: The surface index, or None if the actor is not found.
        """
        if actor in self.actor_rows:
            return self.actor_rows[actor][1]
        return None

    def get_actor_from_volume_row(self, volume_row):
        """
        Get the list of actors for the given volume index.

        Args:
            volume_row (int): The volume index for which to get the actors.

        Returns:
            list: A list of actors for the given volume index, or None if not found.
        """
        actors = [actor for actor, (vol_idx, _) in self.actor_rows.items(
        ) if vol_idx == volume_row]
        return actors if actors else None

    def get_actor_from_surface_row(self, surface_row):
        """
        Get the actor for the given surface index.

        Args:
            surface_row (int): The surface index for which to get the actor.

        Returns:
            vtkActor: The actor for the given surface index, or None if not found.
        """
        for actor, (_, surf_idx) in self.actor_rows.items():
            if surf_idx == surface_row:
                return actor
        return None

    def fill_actor_nodes(self, treedict: dict, objType: str):
        # Ensure the dictionary exists
        if not hasattr(self, 'actor_nodes'):
            self.actor_nodes = {}

        # Update the actor_nodes with the new data
        self.actor_nodes.update(MeshTreeManager.form_actor_nodes_dictionary(treedict, self.actor_rows, objType))

    def populate_tree(self, treedict: dict, objType: str, filename: str) -> list:
        row = MeshTreeManager.populate_tree_view(
            treedict, self.objectsAddingHistory.id, self.model, self.treeView, objType)
        self.treeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeView.selectionModel().selectionChanged.connect(
            self.on_tree_selection_changed)
        actors = MeshTreeManager.create_actors_from_tree_dict(treedict, objType)

        self.fill_dicts(row, actors, objType, filename)
        self.fill_actor_nodes(treedict, objType)

        return row, actors

    def add_actors_and_populate_tree_view(self, treedict: dict, filename: str, objType: str = 'volume'):
        self.objectsAddingHistory.incrementIndex()
        row, actors = self.populate_tree(treedict, objType, filename)
        self.add_actors(actors)

        self.externRow_treedict[row] = treedict
        if row not in self.externRow_actors:
            self.externRow_actors[row] = []
        self.externRow_actors[row].append(actors)

        self.objectsAddingHistory.add_action((row, actors, treedict, objType))
        self.global_undo_stack.append(ACTION_ACTOR_CREATING)

    def restore_actor_colors(self):
        try:
            for actor, color in self.actor_color.items():
                actor.GetProperty().SetColor(color)
            self.render_editor_window_without_resetting_camera()
        except Exception as e:
            self.log_console.printError(f"Error in restore_actor_colors: {e}")

    def highlight_actors(self, actors):
        for actor in actors:
            actor.GetProperty().SetColor(DEFAULT_SELECTED_ACTOR_COLOR)
        self.render_editor_window_without_resetting_camera()

    def unhighlight_actors(self):
        self.restore_actor_colors()

    def on_tree_selection_changed(self):
        selected_indexes = self.treeView.selectedIndexes()
        if not selected_indexes:
            return

        self.unhighlight_actors()
        self.selected_actors.clear()

        for index in selected_indexes:
            selected_row = index.row()
            parent_index = index.parent().row()

            selected_item = None
            if parent_index == -1:
                for actor, (volume_row, _) in self.actor_rows.items():
                    if volume_row == selected_row:
                        selected_item = actor
                        break
            else:
                for actor, (volume_row, surface_row) in self.actor_rows.items():
                    if volume_row == parent_index and surface_row == selected_row:
                        selected_item = actor
                        break

            if selected_item:
                self.highlight_actors([selected_item])
                self.selected_actors.add(selected_item)

    def retrieve_mesh_filename(self) -> str:
        """
        Retrieve the mesh filename from the configuration tab.

        If a mesh file is specified in the configuration tab, use it as the filename.
        Otherwise, use the default temporary mesh file.

        Returns:
        str: The mesh filename to be used.
        """
        mesh_filename = DEFAULT_TEMP_MESH_FILE
        if self.config_tab.mesh_file:
            mesh_filename = self.config_tab.mesh_file
        return mesh_filename

    def handle_drawing_line(self):
        click_pos = self.interactor.GetEventPosition()
        picker = vtkCellPicker()
        picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)

        pickedPosition = picker.GetPickPosition()
        self.crossSectionLinePoints.append(pickedPosition)

        if len(self.crossSectionLinePoints) == 1:
            # First point, just update the scene to show the point
            self.updateTempLine()
        elif len(self.crossSectionLinePoints) == 2:
            # Second point, complete the line and proceed to create cross-section
            self.updateTempLine()
            self.create_cross_section()
            self.endLineDrawing()  # Reset drawing state

    def updateTempLine(self):
        if self.tempLineActor:
            self.renderer.RemoveActor(self.tempLineActor)

        if len(self.crossSectionLinePoints) < 1:
            return

        # Create a line between the two points
        points = vtkPoints()
        line = vtkPolyLine()
        line.GetPointIds().SetNumberOfIds(len(self.crossSectionLinePoints))
        for i, pos in enumerate(self.crossSectionLinePoints):
            pid = points.InsertNextPoint(*pos)
            line.GetPointIds().SetId(i, pid)

        lines = vtkCellArray()
        lines.InsertNextCell(line)

        polyData = vtkPolyData()
        polyData.SetPoints(points)
        polyData.SetLines(lines)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polyData)

        self.tempLineActor = vtkActor()
        self.tempLineActor.SetMapper(mapper)
        self.tempLineActor.GetProperty().SetColor(1, 0, 0)  # red color

        self.renderer.AddActor(self.tempLineActor)
        self.render_editor_window()

    def start_line_drawing(self):
        self.crossSectionLinePoints.clear()
        self.isDrawingLine = True

    def endLineDrawing(self):
        self.isDrawingLine = False
        if self.tempLineActor:
            self.renderer.RemoveActor(self.tempLineActor)
            self.tempLineActor = None
        self.render_editor_window()

    def pick_actor(self, obj, event):
        click_pos = self.interactor.GetEventPosition()
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)

        actor = self.picker.GetActor()
        if actor:
            if not (self.interactor.GetControlKey() or self.interactor.GetShiftKey()):
                # Reset selection of all previous actors and tree view items
                self.unhighlight_actors()
                self.reset_selection_treeview()
                self.selected_actors.clear()

            rows_to_select = ()

            # Find the corresponding rows
            for act, (volume_row, surface_row) in self.actor_rows.items():
                if actor == act:
                    rows_to_select = (volume_row, surface_row)
                    break

            # Select the rows in the tree view if rows_to_select is not empty
            if rows_to_select:
                index = self.model.index(
                    rows_to_select[1], 0, self.model.index(rows_to_select[0], 0))
                self.treeView.selectionModel().select(
                    index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
            
            actor.GetProperty().SetColor(DEFAULT_SELECTED_ACTOR_COLOR)
            self.selected_actors.add(actor)
            self.render_editor_window_without_resetting_camera()

        # Call the original OnLeftButtonDown event handler to maintain default interaction behavior
        self.interactorStyle.OnLeftButtonDown()

        if self.isPerformOperation[0]:
            operationDescription = self.isPerformOperation[1]
            
            if not self.firstObjectToPerformOperation:
                self.firstObjectToPerformOperation = list(self.selected_actors)[0]
                self.statusBar.showMessage(f"With which object to perform {operationDescription}?")
            else:
                secondObjectToPerformOperation = list(self.selected_actors)[0]
                if self.firstObjectToPerformOperation and secondObjectToPerformOperation:
                    operationType = self.isPerformOperation[1]

                    print("OPERATION HELPER:")
                    print(f"1st actor pos: {self.firstObjectToPerformOperation.GetPosition()}")
                    print(f"2nd actor pos: {secondObjectToPerformOperation.GetPosition()}")

                    if operationType == 'subtract':
                        self.subtract_objects(self.firstObjectToPerformOperation, secondObjectToPerformOperation)
                    elif operationType == 'union':
                        self.combine_objects(self.firstObjectToPerformOperation, secondObjectToPerformOperation)
                    elif operationType == 'intersection':
                        self.intersect_objects(self.firstObjectToPerformOperation, secondObjectToPerformOperation)
                else:
                    QMessageBox.warning(self, "Warning", "No objects have been selected for the operation.")

                self.firstObjectToPerformOperation = None
                self.isPerformOperation = (False, None)
                self.statusBar.clearMessage()

    def on_left_button_press(self, obj, event):
        if self.isDrawingLine:
            self.handle_drawing_line()
        else:
            self.pick_actor(obj, event)

    def on_right_button_press(self, obj, event):
        click_pos = self.interactor.GetEventPosition()
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)

        actor = self.picker.GetActor()
        if actor:
            self.selected_actors.add(actor)
            self.context_menu()

    def on_key_press(self, obj, event):
        key = self.interactor.GetKeySym()

        if key == 'Escape':
            self.change_interactor(INTERACTOR_STYLE_TRACKBALL_CAMERA)
            self.deselect()

        if key == 'Delete' or key == 'BackSpace':
            if self.selected_actors:
                self.remove_objects_with_restore(self.selected_actors)

        # C - controlling the object.
        if key == 'c' or key == 'C':
            if self.selected_actors:
                self.change_interactor(INTERACTOR_STYLE_TRACKBALL_ACTOR)

        self.interactorStyle.OnKeyPress()

    def context_menu(self):
        menu = QMenu(self)

        move_action = QAction('Move', self)
        move_action.triggered.connect(self.move_actors)
        menu.addAction(move_action)

        change_angle_action = QAction('Rotate', self)
        change_angle_action.triggered.connect(self.rotate_actors)
        menu.addAction(change_angle_action)

        adjust_size_action = QAction('Adjust size', self)
        adjust_size_action.triggered.connect(self.adjust_actors_size)
        menu.addAction(adjust_size_action)

        remove_object_action = QAction('Remove', self)
        remove_object_action.triggered.connect(self.permanently_remove_actors)
        menu.addAction(remove_object_action)

        colorize_object_action = QAction('Colorize', self)
        colorize_object_action.triggered.connect(self.colorize_actors)
        menu.addAction(colorize_object_action)

        merge_surfaces_action = QAction('Merge surfaces', self)
        merge_surfaces_action.triggered.connect(self.merge_surfaces)
        menu.addAction(merge_surfaces_action)

        add_material_action = QAction('Add Material', self)
        add_material_action.triggered.connect(self.add_material)
        menu.addAction(add_material_action)

        hide_action = QAction('Hide', self)
        hide_action.triggered.connect(self.hide_actors)
        menu.addAction(hide_action)

        menu.exec_(QCursor.pos())

    def reset_selection_treeview(self):
        self.treeView.clearSelection()
        
    def render_editor_window_without_resetting_camera(self):
        self.vtkWidget.GetRenderWindow().Render()

    def render_editor_window(self):
        self.renderer.ResetCamera()
        self.render_editor_window_without_resetting_camera()
    
    def set_color(self, actor: vtkActor, color):
        try:
            actor.GetProperty().SetColor(color)
        except:
            self.log_console.printInternalError(f"Can't set color [{color}] to actor <{hex(id(actor))}>")
            return
        
    def set_particle_source(self):
        self.particle_source_manager.set_particle_source()

    def reset_particle_source_arrow(self):
        self.particle_source_manager.reset_particle_source_arrow()

    def deselect(self):
        try:
            for actor in self.renderer.GetActors():
                if actor in self.actor_color:
                    original_color = self.actor_color[actor]
                else:
                    original_color = DEFAULT_ACTOR_COLOR
                actor.GetProperty().SetColor(original_color)

            self.selected_actors.clear()
            self.vtkWidget.GetRenderWindow().Render()
            self.reset_selection_treeview()
        except Exception as e:
            self.log_console.printError(f"Error in deselect: {e}")

    def move_actors(self):
        dialog = MoveActorDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            offsets = dialog.getValues()
            if offsets:
                x_offset, y_offset, z_offset = offsets
                print("MOVING")
                print(f"Offsets are: {offsets}")

                for actor in self.selected_actors:
                    if actor and isinstance(actor, vtkActor):
                        print(f"Init <{hex(id(actor))}> pos: {actor.GetPosition()}")
                        print(f"Init <{hex(id(actor))}> centre: {actor.GetCenter()}")
                        print(f"Init <{hex(id(actor))}> origin: {actor.GetOrigin()}")
                        
                        position = actor.GetPosition()
                        new_position = (position[0] + x_offset, position[1] + y_offset, position[2] + z_offset)
                        actor.SetPosition(new_position)
                        actor.Modified()
                        
                        transform = vtkTransform()
                        transform.Translate(x_offset, y_offset, z_offset)
                        transform_filter = vtkTransformPolyDataFilter()
                        transform_filter.SetTransform(transform)
                        transform_filter.SetInputData(actor.GetMapper().GetInput())
                        transform_filter.Update()

                        print(f"After <{hex(id(actor))}> pos: {actor.GetPosition()}")
                        print(f"After <{hex(id(actor))}> centre: {actor.GetCenter()}")
                        print(f"After <{hex(id(actor))}> origin: {actor.GetOrigin()}")
                        
            self.deselect()

    def adjust_actors_size(self):
        scale_factor, ok = QInputDialog.getDouble(
            self, "Adjust size", "Scale:", 1.0, 0.01, 100.0, 2)
        if ok:
            for actor in self.selected_actors:
                if actor and isinstance(actor, vtkActor):
                    actor.SetScale(scale_factor, scale_factor, scale_factor)
            self.deselect()
            
    def change_interactor(self, style: str):
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        if style == INTERACTOR_STYLE_TRACKBALL_CAMERA:
            self.interactorStyle = vtkInteractorStyleTrackballCamera()
            self.picker = vtkCellPicker()  # Use single object picker
            self.interactorStyle.AddObserver(vtkCommand.LeftButtonPressEvent, self.on_left_button_press)
            self.interactorStyle.AddObserver(vtkCommand.RightButtonPressEvent, self.on_right_button_press)
        elif style == INTERACTOR_STYLE_TRACKBALL_ACTOR:
            self.interactorStyle = vtkInteractorStyleTrackballActor()
            self.picker = vtkCellPicker()  # Use single object picker
            self.log_console.printWarning("Interactor style changed: Be careful with arbitrary object transformation! If you want to set boundary conditions for this object, they will apply to the old coordinates of the nodes. Because the program does not provide for changes to key objects for which boundary conditions are set")
        elif style == INTERACTOR_STYLE_RUBBER_AND_PICK:
            self.interactorStyle = vtkInteractorStyleRubberBandPick()
            self.interactorStyle.AddObserver(vtkCommand.LeftButtonPressEvent, self.on_left_button_press)
        else:
            QMessageBox.warning(self, "Change Interactor", f"Can't change current interactor style. There is no such interactor: {style}")
            self.log_console.printWarning(f"Can't change current interactor style. There is no such interactor: {style}")

        self.interactor.SetInteractorStyle(self.interactorStyle)
        self.interactor.Initialize()
        self.interactor.Start()

    def extract_indices(self, actors):
        """
        Extract surface indices and volume row for the provided list of actors.

        Args:
            actors (list): List of vtkActor objects.

        Returns:
            tuple: A tuple containing the list of surface indices and the volume row.
        """
        surface_indices = []
        volume_row = None
        for actor in actors:
            surface_row = self.get_surface_row(actor)
            if surface_row is not None:
                surface_indices.append(surface_row)
                if volume_row is None:
                    volume_row = self.get_volume_row(actor)
        return volume_row, surface_indices

    def merge_surfaces(self):
        if len(self.selected_actors) == 1:
            self.log_console.printInfo(
                "Nothing to merge, selected only 1 surface")
            QMessageBox.warning(self, "Merge Surfaces",
                                "Nothing to merge, selected only 1 surface")
            return

        # Extracting indices for the actors to be merged
        volume_row, surface_indices = self.extract_indices(self.selected_actors)
        if not surface_indices or volume_row is None:
            self.log_console.printError(
                "No valid surface indices found for selected actors")
            return

        # Remove selected actors and save the first one for future use
        saved_actor = vtkActor()
        for actor in self.selected_actors:
            self.update_actor_dictionaries(actor)
            saved_actor = actor
        self.remove_actors(self.selected_actors)
        merged_actor = merge_actors(self.selected_actors)

        # Adding the merged actor to the scene
        self.add_actor(merged_actor)
        self.update_actor_dictionaries(saved_actor, merged_actor)
        self.update_tree_view(volume_row, surface_indices, merged_actor)

        self.log_console.printInfo(f"Successfully merged selected surfaces: {set([i + 1 for i in surface_indices])} to object with id <{hex(id(merged_actor))}>")
        self.deselect()

    def update_tree_view(self, volume_row, surface_indices, merged_actor):
        model = self.treeView.model()
        surface_indices = sorted(surface_indices)
        MeshTreeManager.rename_first_selected_row(model, volume_row, surface_indices)
        parent_index = model.index(volume_row, 0)

        # Copying the hierarchy from the rest of the selected rows to the first selected row
        for surface_index in surface_indices[1:]:
            child_index = model.index(surface_index, 0, parent_index)
            child_item = model.itemFromIndex(child_index)
            MeshTreeManager.copy_children(child_item, model.itemFromIndex(
                model.index(surface_indices[0], 0, parent_index)))

        # Deleting the rest of the selected rows from the tree view
        for surface_index in surface_indices[1:][::-1]:
            child_index = model.index(surface_index, 0, parent_index)
            model.removeRow(child_index.row(), parent_index)

        # Updating the actor_rows dictionary with the new internal row index
        self.actor_rows[merged_actor] = (volume_row, surface_indices[0])

        # Adjusting indices in actor_rows after removal
        self.adjust_actor_rows(volume_row, surface_indices)

    def adjust_actor_rows(self, volume_row, removed_indices):
        """
        Adjust the actor_rows dictionary to maintain sequential numbering of surface indices after merging.

        Args:
            volume_row (int): The row index of the volume item in the tree view.
            removed_indices (list): The list of indices that were removed.
        """
        # Sort removed indices for proper processing
        removed_indices = sorted(removed_indices)

        # Initialize a list of current surface indices
        current_surface_indices = [
            rows[1] for actor, rows in self.actor_rows.items() if rows[0] == volume_row]
        current_surface_indices.sort()

        # Create a new list of sequential indices
        new_indices = []
        new_index = 0
        for i in range(len(current_surface_indices) + len(removed_indices)):
            if i not in removed_indices:
                new_indices.append(new_index)
                new_index += 1

        # Update actor_rows with new sequential indices
        index_mapping = dict(zip(current_surface_indices, new_indices))
        for actor, (vol_row, surf_row) in list(self.actor_rows.items()):
            if vol_row == volume_row and surf_row in index_mapping:
                self.actor_rows[actor] = (vol_row, index_mapping[surf_row])

    def rotate_actors(self):
        dialog = AngleDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            angles = dialog.getValues()
            if angles:
                angle_x, angle_y, angle_z = angles

                for actor in self.selected_actors:
                    if actor and isinstance(actor, vtkActor):
                        actor.RotateX(angle_x)
                        actor.RotateY(angle_y)
                        actor.RotateZ(angle_z)

        self.deselect()

    def align_view_by_axis(self, axis: str):
        align_view_by_axis(axis, self.renderer, self.vtkWidget)

    def save_scene(self, logConsole, fontColor, actors_file='scene_actors_meshTab.vtk', camera_file='scene_camera_meshTab.json'):
        ProjectManager.save_scene(self.renderer, logConsole, fontColor, actors_file, camera_file)

    def load_scene(self, logConsole, fontColor, actors_file='scene_actors_meshTab.vtk', camera_file='scene_camera_meshTab.json'):
        ProjectManager.load_scene(self.vtkWidget, self.renderer, logConsole, fontColor, actors_file, camera_file)

    def get_total_count_of_actors(self):
        return self.renderer.GetActors().GetNumberOfItems()

    def clear_scene_and_tree_view(self):
        # There is no need to ask about assurance of deleting when len(actors) = 0
        if self.get_total_count_of_actors() == 0:
            return

        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowTitle("Deleting All The Data")
        msgBox.setText("Are you sure you want to delete all the objects? They will be permanently deleted.")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        choice = msgBox.exec()
        if (choice == QMessageBox.Yes):
            self.erase_all_from_tree_view()
            self.remove_all_actors()
        self.objectsAddingHistory.clearIndex()

    def subtract_button_clicked(self):
        self.deselect()
        self.isPerformOperation = (True, 'subtract')
        self.statusBar.showMessage("From which obejct subtract?")
        self.operationType = 'subtraction'

    def combine_button_clicked(self):
        self.deselect()
        self.isPerformOperation = (True, 'union')
        self.statusBar.showMessage("What object to combine?")
        self.operationType = 'union'

    def intersection_button_clicked(self):
        self.deselect()
        self.isPerformOperation = (True, 'intersection')
        self.statusBar.showMessage("What object to intersect?")
        self.operationType = 'intersection'

    def cross_section_button_clicked(self):
        if not list(self.selected_actors)[0]:
            QMessageBox.warning(self, "Warning", "You need to select object first")
            return

        self.start_line_drawing()
        self.statusBar.showMessage("Click two points to define the cross-section plane.")

    def object_operation_executor_helper(self, obj_from: vtkActor, obj_to: vtkActor, operation: vtkBooleanOperationPolyDataFilter):
        try:
            print(f"<{hex(id(obj_from))}> pos: {obj_from.GetPosition()}")
            print(f"<{hex(id(obj_from))}> centre: {obj_from.GetCenter()}")
            print(f"<{hex(id(obj_from))}> origin: {obj_from.GetOrigin()}")
            
            print(f"<{hex(id(obj_to))}> pos: {obj_to.GetPosition()}")
            print(f"<{hex(id(obj_to))}> centre: {obj_to.GetCenter()}")
            print(f"<{hex(id(obj_to))}> origin: {obj_to.GetOrigin()}")
            
            obj_from_subtract_polydata = convert_unstructured_grid_to_polydata(obj_from)
            obj_to_subtract_polydata = convert_unstructured_grid_to_polydata(obj_to)

            cleaner1 = vtkCleanPolyData()
            cleaner1.SetInputData(obj_from_subtract_polydata)
            cleaner1.Update()
            cleaner2 = vtkCleanPolyData()
            cleaner2.SetInputData(obj_to_subtract_polydata)
            cleaner2.Update()

            # Set the input objects for the operation
            operation.SetInputData(0, cleaner1.GetOutput())
            operation.SetInputData(1, cleaner2.GetOutput())

            # Update the filter to perform the subtraction
            operation.Update()

            # Retrieve the result of the subtraction
            resultPolyData = operation.GetOutput()

            # Check if subtraction was successful
            if resultPolyData is None or resultPolyData.GetNumberOfPoints() == 0:
                QMessageBox.warning(self, "Operation Failed", "No result from the operation operation.")
                return

            mapper = vtkPolyDataMapper()
            mapper.SetInputData(resultPolyData)

            actor = vtkActor()
            actor.SetMapper(mapper)
            self.add_actor(actor)

            # Removing subtracting objects only after adding resulting object
            self.remove_actor(obj_from)
            self.remove_actor(obj_to)
            
            self.difficult_geometries.add(actor)
            
            return actor
        
        except Exception as e:
            self.log_console.printError(str(e))
            return None

    def subtract_objects(self, obj_from: vtkActor, obj_to: vtkActor):
        booleanOperation = vtkBooleanOperationPolyDataFilter()
        booleanOperation.SetOperationToDifference()
        self.object_operation_executor_helper(obj_from, obj_to, booleanOperation)

    def combine_objects(self, obj_from: vtkActor, obj_to: vtkActor):
        booleanOperation = vtkBooleanOperationPolyDataFilter()
        booleanOperation.SetOperationToUnion()
        self.object_operation_executor_helper(obj_from, obj_to, booleanOperation)

    def intersect_objects(self, obj_from: vtkActor, obj_to: vtkActor):
        booleanOperation = vtkBooleanOperationPolyDataFilter()
        booleanOperation.SetOperationToIntersection()
        self.object_operation_executor_helper(obj_from, obj_to, booleanOperation)

    def create_cross_section(self):
        from numpy import cross
        
        if len(self.crossSectionLinePoints) != 2:
            QMessageBox.warning(self, "Warning", "Please define two points for the cross-section.")
            return

        point1, point2 = self.crossSectionLinePoints
        direction = [point2[i] - point1[i] for i in range(3)]  # Direction vector of the line

        dialog = AxisSelectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selectedAxis = dialog.getSelectedAxis()
            plane = vtkPlane()
            plane.SetOrigin(0, 0, 0)
            viewDirection = [0, 0, 0]

            # Adjust the normal of the plane based on the selected axis
            if selectedAxis == "X-axis":
                viewDirection = [1, 0, 0]
            elif selectedAxis == "Y-axis":
                viewDirection = [0, 1, 0]
            elif selectedAxis == "Z-axis":
                viewDirection = [0, 0, 1]

        normal = cross(direction, viewDirection)
        plane.SetOrigin(point1)
        plane.SetNormal(normal)

        self.perform_cut(plane)

    def perform_cut(self, plane):
        polydata = convert_unstructured_grid_to_polydata(
            list(self.selected_actors)[0])
        if not polydata:
            QMessageBox.warning(
                self, "Error", "Selected object is not suitable for cross-section.")
            return

        clipper1 = vtkClipPolyData()
        clipper1.SetInputData(polydata)
        clipper1.SetClipFunction(plane)
        clipper1.InsideOutOn()
        clipper1.Update()

        clipper2 = vtkClipPolyData()
        clipper2.SetInputData(polydata)
        clipper2.SetClipFunction(plane)
        clipper2.InsideOutOff()
        clipper2.Update()

        mapper1 = vtkPolyDataMapper()
        mapper1.SetInputData(clipper1.GetOutput())
        actor1 = vtkActor()
        actor1.SetMapper(mapper1)
        actor1.GetProperty().SetColor(0.8, 0.3, 0.3)

        mapper2 = vtkPolyDataMapper()
        mapper2.SetInputData(clipper2.GetOutput())
        actor2 = vtkActor()
        actor2.SetMapper(mapper2)
        actor2.GetProperty().SetColor(0.8, 0.3, 0.3)

        self.remove_actor(list(self.selected_actors)[0])
        self.add_actor(actor1)
        self.add_actor(actor2)

        self.log_console.printInfo("Successfully created a cross-section")        

    def save_boundary_conditions(self, node_ids, value):
        try:
            with open(self.config_tab.config_file_path, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error", 
                                 f"Error parsing JSON file '{self.config_tab.config_file_path}': {e}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                                 f"An error occurred while reading the configuration file '{self.config_tab.config_file_path}': {e}")
            return

        if "Boundary Conditions" not in data:
            data["Boundary Conditions"] = {}

        node_key = ','.join(map(str, node_ids))
        data["Boundary Conditions"][node_key] = value

        try:
            with open(self.config_tab.config_file_path, 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save configuration: {e}")

    def activate_selection_boundary_conditions_mode_for_surface(self):
        if not self.selected_actors:
            QMessageBox.information(self, "Set Boundary Conditions",
                                    "There is no selected surfaces to apply boundary conditions on them")
            return

        dialog = BoundaryValueInputDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            value, ok = dialog.get_value()
            if not ok:
                QMessageBox.warning(
                    self, "Set Boundary Conditions Value", "Failed to apply value, retry please")
                return
        else:
            return

        for actor in self.selected_actors:
            if actor in self.actor_nodes:
                nodes = self.actor_nodes[actor]
                self.save_boundary_conditions(nodes, value)
                self.log_console.printInfo(f"Object: {hex(id(actor))}, Nodes: {nodes}, Value: {value}")
        self.deselect()

    def save_and_mesh_objects(self):
        mesh_filename = self.get_filename_from_dialog()
        if mesh_filename:
            dialog = mesh_dialog.MeshDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                mesh_size, mesh_dim = dialog.get_values()
                success = SimpleGeometryManager.save_and_mesh_objects(self.log_console, mesh_filename, mesh_size, mesh_dim)
                
                if not success:
                    self.log_console.printWarning("Something went wrong while saving and meshing created objects")
                    return
                else:
                    self.log_console.printInfo("Deleting objects from the list of the created objects...")
                    SimpleGeometryManager.clear_geometry_objects()

    def add_material(self):
        dialog = AddMaterialDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected_material = dialog.materials_combobox.currentText()
            if not selected_material:
                QMessageBox.warning(
                    self, "Add Material", "Can't add material, you need to assign name to the material first")
                return
            # TODO: Handle the selected material here (e.g., add it to the application)
            pass

    def test(self):
        actor = list(self.selected_actors)[0]
        polydata = get_polydata_from_actor(actor)
    