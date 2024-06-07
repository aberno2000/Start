import gmsh, json
from numpy import cross
from os import remove
from os.path import isfile, exists
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkCommonCore import vtkMath
from vtkmodules.vtkInteractionStyle import(
    vtkInteractorStyleTrackballCamera, 
    vtkInteractorStyleTrackballActor, 
    vtkInteractorStyleRubberBandPick
)
from vtkmodules.vtkFiltersGeneral import vtkBooleanOperationPolyDataFilter
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, pyqtSlot, QItemSelectionModel, QThread
from vtk import(
    vtkRenderer, vtkPoints, vtkPolyData, vtkPolyLine, vtkCellArray, vtkPolyDataMapper, 
    vtkActor, vtkSphereSource, vtkAxesActor, vtkOrientationMarkerWidget, 
    vtkGenericDataObjectReader, vtkDataSetMapper, vtkCellPicker, 
    vtkCleanPolyData, vtkPlane, vtkClipPolyData, vtkTransform, vtkTransformPolyDataFilter, 
    vtkArrowSource, vtkCommand, vtkPolyDataNormals, vtkMatrix4x4
)
from PyQt5.QtWidgets import(
    QFrame, QVBoxLayout, QHBoxLayout, QTreeView,
    QPushButton, QDialog, QSpacerItem, QColorDialog,
    QSizePolicy, QMessageBox, QFileDialog,
    QMenu, QAction, QInputDialog, QStatusBar,
    QListWidget, QListWidgetItem, QAbstractItemView,
)
from PyQt5.QtGui import QCursor, QStandardItemModel
from .util import(
    PointDialog, LineDialog, SurfaceDialog, 
    SphereDialog, BoxDialog, CylinderDialog,
    AngleDialog, MoveActorDialog, AxisSelectionDialog,
    ExpansionAngleDialogNonModal, ParticleSourceDialog, 
    ParticleSourceTypeDialog, BoundaryValueInputDialog,
    ArrowPropertiesDialog, MethodSelectionDialog,
    pi
)
from util.util import(
    align_view_by_axis, save_scene, load_scene, convert_unstructured_grid_to_polydata,
    can_create_line, extract_transform_from_actor, calculate_thetaPhi, 
    rad_to_degree, getTreeDict, createActorsFromTreeDict, populateTreeView, 
    can_create_surface, formActorNodesDictionary, compare_matrices,
    write_treedict_to_vtk, convert_vtk_to_msh, copy_children, rename_first_selected_row,
    merge_actors,
    ActionHistory,
    DEFAULT_TEMP_MESH_FILE
)
from .mesh_dialog import MeshDialog
from tabs.gedit_tab import ConfigTab
from .styles import DEFAULT_ACTOR_COLOR, SELECTED_ACTOR_COLOR, ARROW_ACTOR_COLOR
from logger.log_console import LogConsole


INTERACTOR_STYLE_TRACKBALL_CAMERA = 'trackball_camera'
INTERACTOR_STYLE_TRACKBALL_ACTOR = 'trackball_actor'
INTERACTOR_STYLE_RUBBER_AND_PICK = 'rubber_and_pick'

ACTION_ACTOR_CREATING = 'create_actor'
ACTION_ACTOR_TRANSFORMATION = 'transform'

class GraphicalEditor(QFrame):    
    def __init__(self, log_console: LogConsole, config_tab: ConfigTab, parent=None):
        super().__init__(parent)
        self.config_tab = config_tab
        
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
        
        self.treeView = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Mesh Tree'])
        self.mesh_file = None
        
        self.selected_actors = set()
        self.isBoundaryNodeSelectionMode = False
        
        self.picker = vtkCellPicker()
        self.picker.SetTolerance(0.005)
        
        self.setup_toolbar()
        self.setup_ui()
        self.setup_interaction()
        self.setup_axes()
        
        self.objectsAddingHistory = ActionHistory()
        self.global_undo_stack = []
        self.global_redo_stack = []
        
        self.isPerformOperation = (False, None)
        self.firstObjectToPerformOperation = None
        self.statusBar = QStatusBar()
        self.layout.addWidget(self.statusBar)
        
        self.init_node_selection_attributes()
        self.isBoundaryNodeSelectionMode = False

        self.log_console = log_console
        
        self.crossSectionLinePoints = []  # To store points for the cross-section line
        self.isDrawingLine = False        # To check if currently drawing the line
        self.tempLineActor = None         # Temporary actor for the line visualization
        
        self.particleSourceArrowActor = None
    
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
                self.actor_matrix[actor_to_add] = (actor_to_add.GetMatrix(), actor_to_add.GetMatrix())
                self.meshfile_actors.setdefault(filename, []).append(actor_to_add)
    
    @pyqtSlot()
    def activate_selection_boundary_conditions_mode_slot(self):
        self.setBoundaryConditionsButton.click()
    
    
    def initialize_tree(self):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Mesh Tree'])
        self.setTreeViewModel()
        

    def setTreeViewModel(self):
        self.treeView.setModel(self.model)
        self.treeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeView.selectionModel().selectionChanged.connect(self.on_tree_selection_changed)


    def initialize_node_map(self):
        gmsh.initialize()
        gmsh.open(self.mesh_file)
        node_ids, node_coords, _ = gmsh.model.mesh.getNodesByElementType(2)
        it = iter(node_coords)  # Iterator over the node coordinates
        for node_id in node_ids:
            coords = (next(it), next(it), next(it))
            sphere = vtkSphereSource()
            sphere.SetCenter(coords)
            sphere.SetRadius(0.75)
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
            self.nodeMap[node_id] = {'actor': actor, 'coords': coords}
        gmsh.finalize()
        
    def populate_node_list(self):
        self.nodeListWidget.clear()        
        for node_id in set(self.nodeMap.keys()):
            item = QListWidgetItem(str(node_id))
            self.nodeListWidget.addItem(item)
            
    def add_actors_from_node_list(self):
        if not self.nodeMap:
            return
        
        for node_data in self.nodeMap.values():
            actor = node_data['actor']
            self.renderer.AddActor(actor)
        
        self.render_editor_window()
        
    def remove_actors_from_node_list(self):
        if not self.nodeMap:
            return
        
        for node_data in self.nodeMap.values():
            actor = node_data['actor']
            self.renderer.RemoveActor(actor)
        
        self.nodeMap.clear()
        self.render_editor_window()
    
    
    def upload_mesh_file(self, file_path):        
        if exists(file_path) and isfile(file_path):
            self.mesh_file = file_path
            self.initialize_tree()
            gmsh.initialize()
            treedict = getTreeDict(self.mesh_file)
            gmsh.finalize()
            self.add_actors_and_populate_tree_view(treedict, file_path)
            self.initialize_node_map()
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
        self.setBoundaryConditionsButton = self.create_button('icons/boundary-conditions.png', 'Turning on mode to select boundary nodes')
        self.setBoundaryConditionsSurfaceButton = self.create_button('icons/boundary-conditions-surface.png', 'Turning on mode to select boundary nodes on surface')
        self.setParticleSourceButton = self.create_button('icons/particle-source.png', 'Set particle source as surface')
        
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
        self.setBoundaryConditionsButton.clicked.connect(self.activate_selection_boundary_conditions_mode)
        self.setBoundaryConditionsSurfaceButton.clicked.connect(self.activate_selection_boundary_conditions_mode_for_surface)
        self.setParticleSourceButton.clicked.connect(self.set_particle_source)
        
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
        
        self.change_interactor(INTERACTOR_STYLE_TRACKBALL_CAMERA)
        
        
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

        move_action.triggered.connect(self.move_actors)
        rotate_action.triggered.connect(self.rotate_actors)
        adjust_size_action.triggered.connect(self.adjust_actors_size)
        remove_action.triggered.connect(self.permanently_remove_actors)
        colorize_action.triggered.connect(self.colorize_actors)
        merge_surfaces_action.triggered.connect(self.merge_surfaces)

        menu.addAction(move_action)
        menu.addAction(rotate_action)
        menu.addAction(adjust_size_action)
        menu.addAction(remove_action)
        menu.addAction(colorize_action)
        menu.addAction(merge_surfaces_action)

        menu.exec_(self.treeView.viewport().mapToGlobal(position))
    
    
    def get_filename_from_dialog(self) -> str:
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getSaveFileName(None, "Save Mesh File", "", "Mesh Files (*.msh);;All Files (*)", options=options)
           
        if not filename:
            return None
        if not filename.endswith('.msh'):
            filename += '.msh'
        
        return filename
    
    
    def create_point(self):
        def create_point_with_gmsh(x, y, z, mesh_size):
            gmsh.initialize()
            gmsh.model.add("point")
            gmsh.model.geo.addPoint(x, y, z, meshSize=mesh_size, tag=1)
            gmsh.model.geo.synchronize()
            gmsh.model.mesh.generate(3)
            
            pointMap = getTreeDict(obj_type='point')
            filename = self.get_filename_from_dialog()
            if not filename:
                return None
            
            gmsh.write(filename)
            gmsh.finalize()
            return pointMap, filename

        dialog = PointDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z = dialog.getValues()
            
            # Prepare the point data for Gmsh
            mesh_size = 1.0  # Default mesh size for point
            res = create_point_with_gmsh(x, y, z, mesh_size)
            if not res:
                return
            pointMap, filename = res
            self.add_actors_and_populate_tree_view(pointMap, filename, 'point')
            
            self.log_console.printInfo(f'Successfully created point: ({x}, {y}, {z})')
            self.log_console.addNewLine()
            
            
    def create_line(self):
        def create_line_with_gmsh(points, mesh_size):
            gmsh.initialize()
            gmsh.model.add("line")

            for idx, (x, y, z) in enumerate(points, start=1):
                gmsh.model.geo.addPoint(x, y, z, meshSize=mesh_size, tag=idx)
            for i in range(len(points) - 1):
                gmsh.model.geo.addLine(i + 1, i + 2)

            gmsh.model.geo.synchronize()
            gmsh.model.mesh.generate(3)
            
            lineMap = getTreeDict(obj_type='line')
            filename = self.get_filename_from_dialog()
            if not filename:
                return None
            
            gmsh.write(filename)
            gmsh.finalize()
            return lineMap, filename

        dialog = LineDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.getValues()
            if values is not None and len(values) >= 6:
                points = vtkPoints()
                points_str_list = []
                
                # Insert points into vtkPoints
                pid = 1
                for i in range(0, len(values), 3):
                    points.InsertNextPoint(values[i], values[i + 1], values[i + 2])
                    points_str_list.append(f'Point{pid}: ({values[i]}, {values[i + 1]}, {values[i + 2]})')
                    pid += 1
                tmp = '\n'.join(points_str_list)
                
                # Prepare point data for Gmsh
                point_data = []
                for i in range(0, len(values), 3):
                    point_data.append((values[i], values[i + 1], values[i + 2]))
                    
                # Check if the line can be created with the specified points
                if not can_create_line(point_data):
                    self.log_console.printWarning(f"Can't create line with specified points:\n{tmp}")
                    QMessageBox.warning(self, "Create Line", f"Can't create line with specified points")
                    return
                
                mesh_size = 1.0  # Default mesh size for line
                res = create_line_with_gmsh(point_data, mesh_size)
                if not res:
                    return
                lineMap, filename = res
                self.add_actors_and_populate_tree_view(lineMap, filename, 'line')
                
                self.log_console.printInfo(f'Successfully created line:\n{tmp}')
                self.log_console.addNewLine()

    
    def create_surface(self):
        def create_surface_with_gmsh(points, mesh_size):
            gmsh.initialize()
            gmsh.model.add("surface")
            for idx, (x, y, z) in enumerate(points, start=1):
                gmsh.model.geo.addPoint(x, y, z, meshSize=mesh_size, tag=idx)
            for i in range(len(points)):
                gmsh.model.geo.addLine(i + 1, ((i + 1) % len(points)) + 1)
            loop = gmsh.model.geo.addCurveLoop(list(range(1, len(points) + 1)))
            gmsh.model.geo.addPlaneSurface([loop])
            gmsh.model.geo.synchronize()
            gmsh.model.mesh.generate(3)
            
            surfaceMap = getTreeDict(obj_type='surface')
            filename = self.get_filename_from_dialog()
            if not filename:
                return None
            
            gmsh.write(filename)
            gmsh.finalize()
            return surfaceMap, filename

        dialog = SurfaceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            values, mesh_size = dialog.getValues()
            
            # Check if the meshing option is provided and valid
            if values is not None and len(values) >= 9 and mesh_size:
                points = vtkPoints()
                points_str_list = []
                
                # Insert points into vtkPoints
                pid = 1
                for i in range(0, len(values), 3):
                    points.InsertNextPoint(values[i], values[i+1], values[i+2])
                    points_str_list.append(f'Point{pid}: ({values[i]}, {values[i+1]}, {values[i+2]})')
                    pid += 1
                tmp = '\n'.join(points_str_list)
                
                # Prepare point data for Gmsh
                point_data = []
                for i in range(0, len(values), 3):
                    point_data.append((values[i], values[i+1], values[i+2]))
                    
                # Checking of availability to create surface with specified points
                if not can_create_surface(point_data):
                    self.log_console.printWarning(f"Can't create surface with specified points:\n{tmp}")
                    QMessageBox.warning(self, "Create Surface", f"Can't create surface with specified points")
                    return
                
                res = create_surface_with_gmsh(point_data, mesh_size)
                if not res:
                    return
                surfaceMap, filename = res
                self.add_actors_and_populate_tree_view(surfaceMap, filename, 'surface')
                
                self.log_console.printInfo(f'Successfully created surface:\n{tmp}')
                self.log_console.addNewLine()
                

    
    def create_sphere(self):
        def create_sphere_with_gmsh(mesh_size: float):
            gmsh.initialize()
            gmsh.model.add('custom_sphere')
            gmsh.model.occ.add_sphere(x, y, z, radius)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
            gmsh.model.occ.synchronize()
            gmsh.model.mesh.generate(3)
            
            sphereMap = getTreeDict()
            filename = self.get_filename_from_dialog()
            if not filename:
                return None
            
            gmsh.write(filename)
            gmsh.finalize()
            return sphereMap, filename
        
        dialog = SphereDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            values, mesh_size = dialog.getValues()
            if mesh_size == 0.0:
                mesh_size = 1.0
            x, y, z, radius = values
            
            sphere_data_str = []
            sphere_data_str.append(f'Center: ({x}, {y}, {z})')
            sphere_data_str.append(f'Radius: {radius}')
            tmp = '\n'.join(sphere_data_str)
            
            res = create_sphere_with_gmsh(mesh_size)
            if not res:
                return
            sphereMap, filename = res
            self.add_actors_and_populate_tree_view(sphereMap, filename, 'volume')
            
            self.log_console.printInfo(f'Successfully created sphere:\n{tmp}')
            self.log_console.addNewLine()
            


    def create_box(self):
        def create_box_with_gmsh(mesh_size: float):
            gmsh.initialize()
            gmsh.model.occ.add_box(x, y, z, length, width, height)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
            gmsh.model.occ.synchronize()
            gmsh.model.mesh.generate(3)
            
            boxMap = getTreeDict()
            filename = self.get_filename_from_dialog()
            if not filename:
                return None
            
            gmsh.write(filename)
            gmsh.finalize()
            return boxMap, filename
        
        dialog = BoxDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            values, mesh_size = dialog.getValues()
            x, y, z, length, width, height = values
            
            box_data_str = []
            box_data_str.append(f'Primary Point: ({x}, {y}, {z})')
            box_data_str.append(f'Length: {length}')
            box_data_str.append(f'Width: {width}')
            box_data_str.append(f'Height: {height}')
            tmp = '\n'.join(box_data_str)
            
            res = create_box_with_gmsh(mesh_size)
            if not res:
                return
            boxMap, filename = res
            self.add_actors_and_populate_tree_view(boxMap, filename, 'volume')
            
            self.log_console.printInfo(f'Successfully created box:\n{tmp}')
            self.log_console.addNewLine()
            


    def create_cylinder(self):
        def create_cylinder_with_gmsh(mesh_size: float):
            gmsh.initialize()
            gmsh.model.add('custom_cylinder')
            gmsh.model.occ.add_cylinder(x, y, z, dx, dy, dz, radius)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
            gmsh.model.occ.synchronize()
            gmsh.model.mesh.generate(3)
            
            cylinderMap = getTreeDict()
            filename = self.get_filename_from_dialog()
            if not filename:
                return None
            
            gmsh.write(filename)
            gmsh.finalize()
            return cylinderMap, filename
        
        dialog = CylinderDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            values, mesh_size = dialog.getValues()
            x, y, z, radius, dx, dy, dz = values
            cylinder_data_str = []
            cylinder_data_str.append(f'Primary Point: ({x}, {y}, {z})')
            cylinder_data_str.append(f'Radius: {radius}')
            cylinder_data_str.append(f'Length: {dx}')
            cylinder_data_str.append(f'Width: {dy}')
            cylinder_data_str.append(f'Height: {dz}')
            tmp = '\n'.join(cylinder_data_str)

            res = create_cylinder_with_gmsh(mesh_size)
            if not res:
                return
            cylinderMap, filename = res
            self.add_actors_and_populate_tree_view(cylinderMap, filename, 'volume')
            
            self.log_console.printInfo(f'Successfully created cylinder:\n{tmp}')
            self.log_console.addNewLine()
            
    
    
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
                    converted_file_name = self.convert_stp_to_msh(file_name, mesh_size, mesh_dim)
                    if converted_file_name:
                        self.add_custom(converted_file_name)
                except ValueError as e:
                    QMessageBox.warning(self, "Invalid Input", str(e))
            else:
                QMessageBox.critical(self, "Error", "Dialog was closed by user. Invalid mesh size or mesh dimensions.")
        elif file_name.endswith('.msh') or file_name.endswith('.vtk'):
            self.add_custom(file_name)
            self.log_console.printInfo(f'Successfully uploaded custom object from {file_name}')
    
    
    def convert_stp_to_msh(self, filename, mesh_size, mesh_dim):
        try:
            gmsh.initialize()
            gmsh.model.add("model")
            gmsh.model.occ.importShapes(filename)
            gmsh.model.occ.synchronize()
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)

            if mesh_dim == 2:
                gmsh.model.mesh.generate(2)
            elif mesh_dim == 3:
                gmsh.model.mesh.generate(3)

            output_file = filename.replace(".stp", ".msh")
            gmsh.write(output_file)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"An error occurred during conversion: {str(e)}")
            return None
        finally:
            gmsh.finalize()
            return output_file


    def setup_axes(self):
        self.axes_actor = vtkAxesActor()
        self.axes_widget = vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(self.axes_actor)
        self.axes_widget.SetInteractor(self.vtkWidget.GetRenderWindow().GetInteractor())
        self.axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        self.axes_widget.EnabledOn()
        self.axes_widget.InteractiveOff()
    
    
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
        msgBox.setText("Are you sure you want to delete the object? It will be permanently deleted.")
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
                        self.log_console.printInternalError(f"Can't find tree view row [{row}] by actor <{hex(id(actor))}>")
                        return
                    
                    actors = self.get_actor_from_volume_row(row)
                    if not actors:
                        self.log_console.printInternalError(f"Can't find actors <{hex(id(actors))}> by tree view row [{row}]>")
                        return
                    
                    self.remove_row_from_tree(row)
                    self.remove_actors(actors)
                    self.objectsAddingHistory.remove_by_id(self.objectsAddingHistory.get_id())
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
        self.particleSourceArrowActor = None
        
        actors = self.renderer.GetActors()
        actors.InitTraversal()        
        for i in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()
            self.renderer.RemoveActor(actor)
        
        self.render_editor_window()
        

    def add_custom(self, meshfilename: str):
        gmsh.initialize()
        customTreeDict = getTreeDict(meshfilename)
        self.add_actors_and_populate_tree_view(customTreeDict, meshfilename, 'volume')
        gmsh.finalize()
    
    
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
            gmsh.initialize()
            treedict = getTreeDict(filename)
            if not treedict:
                continue
            
            success, vtk_filename = write_treedict_to_vtk(treedict, filename)
            if not success:
                self.log_console.printWarning(f"Failed to update Gmsh file for temporary filename {vtk_filename}")
                QMessageBox.warning(self, "Gmsh Update Warning", f"Failed to update Gmsh file for temporary filename {vtk_filename}")
                gmsh.finalize()
                return
            else:
                self.log_console.printInfo(f"Object in temporary mesh file {vtk_filename} was successfully written")
            
            msh_filename = convert_vtk_to_msh(vtk_filename)
            if not msh_filename:
                self.log_console.printWarning(f"Failed to write data from the {vtk_filename} to {msh_filename}")
                QMessageBox.warning(self, "Gmsh Update Warning", f"Failed to write data from the {vtk_filename} to {msh_filename}")
                gmsh.finalize()
                return
            
            self.log_console.printInfo(f"Successfully updated object in {msh_filename}")
            
            try:
                remove(vtk_filename)
                self.log_console.printInfo(f"Successfully removed temporary vtk mesh file: {vtk_filename}")
            except Exception as e:
                self.log_console.printError(f"Can't remove temporary vtk mesh file {vtk_filename}: {e}")
                gmsh.finalize()
            
            gmsh.finalize()
    

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
                    self.actor_matrix[actor] = (initial_transform, initial_transform)
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
                    self.actor_matrix[actor] = (initial_transform, initial_transform)
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
                    self.actor_matrix[actor] = (initial_transform, initial_transform)
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
        actors = [actor for actor, (vol_idx, _) in self.actor_rows.items() if vol_idx == volume_row]
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
        self.actor_nodes.update(formActorNodesDictionary(treedict, self.actor_rows, objType))
    
    
    def populate_tree(self, treedict: dict, objType: str, filename: str) -> list:
        row = populateTreeView(treedict, self.objectsAddingHistory.id, self.model, self.treeView, objType)
        self.treeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeView.selectionModel().selectionChanged.connect(self.on_tree_selection_changed)
        actors = createActorsFromTreeDict(treedict, objType)
        
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
            self.render_editor_window()
        except Exception as e:
            self.log_console.printError(f"Error in restore_actor_colors: {e}")

    
    def highlight_actors(self, actors):
        for actor in actors:
            actor.GetProperty().SetColor(SELECTED_ACTOR_COLOR)
        self.render_editor_window()


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

            # Highlight the actor if it is the arrow actor
            if actor == self.particleSourceArrowActor:
                actor.GetProperty().SetColor(SELECTED_ACTOR_COLOR)
                self.selected_actors.add(actor)
                self.render_editor_window()
                return

            # Select the rows in the tree view if rows_to_select is not empty
            if rows_to_select:
                index = self.model.index(rows_to_select[1], 0, self.model.index(rows_to_select[0], 0))
                self.treeView.selectionModel().select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                self.selected_actors.add(actor)
                actor.GetProperty().SetColor(SELECTED_ACTOR_COLOR)
                self.render_editor_window()
            else:
                QMessageBox.warning(self, "Selection Error", "Selected actor not found in the actor rows mapping.")

        # Check if boundary node selection mode is active
        if self.isBoundaryNodeSelectionMode:
            for node_id, data in self.nodeMap.items():
                actor_coords = data['coords']
                picked_actor = data['actor']
                
                if actor == picked_actor:
                    if picked_actor.GetProperty().GetColor() == (SELECTED_ACTOR_COLOR):  # Check if the node is already selected
                        picked_actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
                        self.selected_node_ids.remove(node_id)
                    else:
                        picked_actor.GetProperty().SetColor(SELECTED_ACTOR_COLOR) 
                        self.selected_node_ids.add(node_id)
                        self.select_node_in_list_widget(node_id)
                        self.log_console.printInfo(f"Selected node {node_id} at {actor_coords}")
                    self.render_editor_window()
                    break

        # Call the original OnLeftButtonDown event handler to maintain default interaction behavior
        self.interactorStyle.OnLeftButtonDown()

        if self.isPerformOperation[0]:
            operationDescription = self.isPerformOperation[1]

            if not self.firstObjectToPerformOperation:
                self.firstObjectToPerformOperation = self.selected_actors[0]
                self.statusBar.showMessage(f"With which object to perform {operationDescription}?")
            else:
                secondObjectToPerformOperation = self.selected_actors[0]
                if self.firstObjectToPerformOperation and secondObjectToPerformOperation:
                    operationType = self.isPerformOperation[1]

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


    def select_node_in_list_widget(self, node_id):
        items = self.nodeListWidget.findItems(str(node_id), Qt.MatchExactly)
        if items:
            item = items[0]
            item.setSelected(True)
            
    
    def setup_interaction(self):
        self.original_color = None
        self.change_interactor(INTERACTOR_STYLE_TRACKBALL_CAMERA)
        self.interactor.AddObserver(vtkCommand.KeyPressEvent, self.on_key_press)
        
    
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
            self.original_color = actor.GetProperty().GetColor()
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

        menu.exec_(QCursor.pos())
    
    
    def reset_selection_treeview(self):
        self.treeView.clearSelection()
        
    
    def render_editor_window(self):
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
    
    
    def deselect(self):
        try:
            for actor in self.renderer.GetActors():
                if actor in self.actor_color:
                    original_color = self.actor_color[actor]
                else:
                    original_color = DEFAULT_ACTOR_COLOR
                actor.GetProperty().SetColor(original_color)
            
            self.selected_actors.clear()
            self.render_editor_window()
            self.reset_selection_treeview()
        except Exception as e:
            self.log_console.printError(f"Error in deselect: {e}")


    def move_actors(self):
        dialog = MoveActorDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            offsets = dialog.getValues()
            if offsets:
                x_offset, y_offset, z_offset = offsets
                
                for actor in self.selected_actors:
                    if actor and isinstance(actor, vtkActor):               
                        position = actor.GetPosition()
                        new_position = (position[0] + x_offset, position[1] + y_offset, position[2] + z_offset)
                        actor.SetPosition(new_position)
                        
        self.deselect()


    def adjust_actors_size(self):      
        scale_factor, ok = QInputDialog.getDouble(self, "Adjust size", "Scale:", 1.0, 0.01, 100.0, 2)
        if ok:            
            for actor in self.selected_actors:
                if actor and isinstance(actor, vtkActor):
                    actor.SetScale(scale_factor, scale_factor, scale_factor)
            self.deselect()
    
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
            self.log_console.printInfo("Nothing to merge, selected only 1 surface")
            QMessageBox.warning(self, "Merge Surfaces", "Nothing to merge, selected only 1 surface")
            return

        # Extracting indices for the actors to be merged
        volume_row, surface_indices = self.extract_indices(self.selected_actors)
        if not surface_indices or volume_row is None:
            self.log_console.printError("No valid surface indices found for selected actors")
            return

        print(f"Before")
        for a, rows in self.actor_rows.items():
            print(f"<{hex(id(a))}> - ({rows[0]};{rows[1]})")

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
        
        print(f"After")
        for a, rows in self.actor_rows.items():
            print(f"<{hex(id(a))}> - ({rows[0]};{rows[1]})")

        self.log_console.printInfo(f"Successfully merged selected surfaces: {set([i + 1 for i in surface_indices])} to object with id <{hex(id(merged_actor))}>")
        self.deselect()

        
    def update_tree_view(self, volume_row, surface_indices, merged_actor):
        model = self.treeView.model()
        surface_indices = sorted(surface_indices)
        rename_first_selected_row(model, volume_row, surface_indices)
        parent_index = model.index(volume_row, 0)

        # Copying the hierarchy from the rest of the selected rows to the first selected row
        for surface_index in surface_indices[1:]:
            child_index = model.index(surface_index, 0, parent_index)
            child_item = model.itemFromIndex(child_index)
            copy_children(child_item, model.itemFromIndex(model.index(surface_indices[0], 0, parent_index)))

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
        current_surface_indices = [rows[1] for actor, rows in self.actor_rows.items() if rows[0] == volume_row]
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
        save_scene(self.renderer, logConsole, fontColor, actors_file, camera_file)
    
            
    def load_scene(self, logConsole, fontColor, actors_file='scene_actors_meshTab.vtk', camera_file='scene_camera_meshTab.json'):
        load_scene(self.vtkWidget, self.renderer, logConsole, fontColor, actors_file, camera_file)
    
    
    def clear_scene_and_tree_view(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowTitle("Deleting All The Data")
        msgBox.setText("Are you sure you want to delete all the objects? They will be permanently deleted.")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        choice = msgBox.exec()
        if (choice == QMessageBox.Yes):        
            self.erase_all_from_tree_view()
            self.remove_all_actors()
        self.reset_selection_nodes()
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
        if not self.selected_actors[0]:
            QMessageBox.warning(self, "Warning", "You need to select object first")
            return
        
        self.start_line_drawing()
        self.statusBar.showMessage("Click two points to define the cross-section plane.")
    
    
    def object_operation_executor_helper(self, obj_from: vtkActor, obj_to: vtkActor, operation: vtkBooleanOperationPolyDataFilter):
        # TODO: fix
        try:
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
        polydata = convert_unstructured_grid_to_polydata(self.selected_actors[0])
        if not polydata:
            QMessageBox.warning(self, "Error", "Selected object is not suitable for cross-section.")
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

        # Removing actor and corresponding row in a tree view
        self.remove_actor(self.selected_actors[0])
        
        # Adding 2 new objects
        
        self.log_console.printInfo("Successfully created a cross-section")
    

    def savePointParticleSourceToConfig(self):
        try:
            base_coords = self.getParticleSourceBaseCoords()
            if base_coords is None:
                raise ValueError("Base coordinates are not defined")

            if not self.expansion_angle:
                self.log_console.printError("Expansion angle θ is undefined")
                raise ValueError("Expansion angle θ is undefined")

            if self.getParticleSourceDirection() is None:
                return
            theta, phi = self.getParticleSourceDirection()

            config_file = self.config_tab.config_file_path
            if not config_file:
                QMessageBox.warning(self, "Saving Particle Source as Point", "Can't save pointed particle source, first you need to choose a configuration file, then set the source")
                self.resetParticleSourceArrow()
                return

            # Read the existing configuration file
            with open(config_file, 'r') as file:
                config_data = json.load(file)

            # Check for existing sources and ask user if they want to remove them
            sources_to_remove = []
            if "ParticleSourcePoint" in config_data:
                sources_to_remove.append("ParticleSourcePoint")
            if "ParticleSourceSurface" in config_data:
                sources_to_remove.append("ParticleSourceSurface")

            if sources_to_remove:
                reply = QMessageBox.question(self, "Remove Existing Sources",
                                            f"The configuration file contains existing sources: {', '.join(sources_to_remove)}. Do you want to remove them?",
                                            QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    for source in sources_to_remove:
                        del config_data[source]
            
            dialog = ParticleSourceDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                particle_params = dialog.getValues()
                particle_type = particle_params["particle_type"]
                energy = particle_params["energy"]
                num_particles = particle_params["num_particles"]
            else:
                self.resetParticleSourceArrow()
                return

            # Prepare new ParticleSourcePoint entry
            if "ParticleSourcePoint" not in config_data:
                config_data["ParticleSourcePoint"] = {}

            new_point_index = str(len(config_data["ParticleSourcePoint"]) + 1)
            config_data["ParticleSourcePoint"][new_point_index] = {
                "Type": particle_type,
                "Count": num_particles,
                "Energy": energy,
                "phi": phi,
                "theta": theta,
                "expansionAngle": self.expansion_angle,
                "BaseCoordinates": [base_coords[0], base_coords[1], base_coords[2]]
            }

            # Write the updated configuration back to the file
            with open(config_file, 'w') as file:
                json.dump(config_data, file, indent=4)

            self.statusBar.showMessage("Successfully set particle source as point source and calculated direction angles")
            self.log_console.printInfo(f"Successfully written coordinates of the particle source:\n"
                                    f"Base: {base_coords}\n"
                                    f"Expansion angle θ: {self.expansion_angle} ({rad_to_degree(self.expansion_angle)}°)\n"
                                    f"Polar (colatitude) angle θ: {theta} ({rad_to_degree(theta)}°)\n"
                                    f"Azimuthal angle φ: {phi} ({rad_to_degree(phi)}°)\n"
                                    f"Particle Type: {particle_type}\n"
                                    f"Energy: {energy} eV\n"
                                    f"Number of Particles: {num_particles}")
            self.log_console.addNewLine()

            self.resetParticleSourceArrow()
            return 1

        except Exception as e:
            self.log_console.printError(f"Error defining particle source. {e}")
            QMessageBox.warning(self, "Particle Source", f"Error defining particle source. {e}")
            return None

        
    def resetParticleSourceArrow(self):
        self.remove_actor(self.particleSourceArrowActor)
        self.particleSourceArrowActor = None
        
        
    def getParticleSourceBaseCoords(self):
        if not self.particleSourceArrowActor or not isinstance(self.particleSourceArrowActor, vtkActor):
            return None
        return self.particleSourceArrowActor.GetPosition()
    
    
    def getParticleSourceArrowTipCoords(self):
        if not self.particleSourceArrowActor:
            return
        
        transform = extract_transform_from_actor(self.particleSourceArrowActor)
        init_tip_coords = [0, 0, 1]
        global_tip_coords = transform.TransformPoint(init_tip_coords)
        
        return global_tip_coords
    
    def getParticleSourceDirection(self):
        if not self.particleSourceArrowActor:
            return
    
        base_coords = self.getParticleSourceBaseCoords()
        tip_coords = self.getParticleSourceArrowTipCoords()
        
        try:
            theta, phi = calculate_thetaPhi(base_coords, tip_coords)
        except Exception as e:
            self.log_console.printError(f"An error occured when calculating polar (colatitude) θ and azimuthal φ: {e}\n")
            QMessageBox.warning(self, "Invalid Angles", f"An error occured when calculating polar (colatitude) θ and azimuthal φ: {e}")
            return None
        
        return theta, phi
    
    
    def create_direction_arrow_interactively(self):
        arrowSource = vtkArrowSource()
        arrowSource.SetTipLength(0.25)
        arrowSource.SetTipRadius(0.1)
        arrowSource.SetShaftRadius(0.01)
        arrowSource.Update()
        arrowSource.SetTipResolution(100)

        arrowTransform = vtkTransform()
        arrowTransform.RotateX(90)
        arrowTransform.RotateWXYZ(90, 0, 0, 1) # Initial direction by Z-axis.
        arrowTransform.Scale(50, 50, 50)
        arrowTransformFilter = vtkTransformPolyDataFilter()
        arrowTransformFilter.SetTransform(arrowTransform)
        arrowTransformFilter.SetInputConnection(arrowSource.GetOutputPort())
        arrowTransformFilter.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(arrowTransformFilter.GetOutputPort())
        
        self.particleSourceArrowActor = vtkActor()
        self.particleSourceArrowActor.SetMapper(mapper)
        self.particleSourceArrowActor.GetProperty().SetColor(ARROW_ACTOR_COLOR)
        
        self.renderer.AddActor(self.particleSourceArrowActor)
        self.render_editor_window()
    
 
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
        
        self.particleSourceArrowActor = vtkActor()
        self.particleSourceArrowActor.SetMapper(mapper)
        self.particleSourceArrowActor.GetProperty().SetColor(ARROW_ACTOR_COLOR)
        
        self.renderer.AddActor(self.particleSourceArrowActor)
        self.render_editor_window()


    def init_node_selection_attributes(self):
        self.nodeMap = {}
        self.selected_node_ids = set()
        
        self.nodeListWidget = QListWidget()
        self.nodeListWidget.setMinimumHeight(150)
        self.nodeListWidget.setMaximumHeight(150)
        self.nodeListWidget.setMinimumWidth(167.5)
        self.nodeListWidget.setMaximumWidth(167.5)
        self.nodeListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.nodeListWidget.itemSelectionChanged.connect(self.on_node_selection_changed)
        self.nodeListWidget.setVisible(False)
        
        self.setBoundaryNodeValuesButton = QPushButton('Set Value')
        self.setBoundaryNodeValuesButton.setVisible(False)
        self.setBoundaryNodeValuesButton.setFixedSize(QSize(80, 27.5))
        self.setBoundaryNodeValuesButton.setToolTip('Check this tab and move to the next with starting the simulation')
        self.setBoundaryNodeValuesButton.clicked.connect(self.setBoundaryNodeValuesButtonClicked)
        
        self.resetNodeSelectionButton = QPushButton('Cancel')
        self.resetNodeSelectionButton.setVisible(False)
        self.resetNodeSelectionButton.setFixedSize(QSize(80, 27.5))
        self.resetNodeSelectionButton.setToolTip('Cancel selection of the nodes')
        self.resetNodeSelectionButton.clicked.connect(self.cancelNodeSelection)
        
        self.layout.addWidget(self.nodeListWidget)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.setBoundaryNodeValuesButton)
        hlayout.addWidget(self.resetNodeSelectionButton)
        
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlayout.addSpacerItem(spacer)

        self.layout.addLayout(hlayout)
        
    
    def cancelNodeSelection(self):
        self.reset_selection_nodes()
        
    
    def reset_selection_nodes(self):
        self.isBoundaryNodeSelectionMode = False
        
        self.deselect()
        self.statusBar.clearMessage()
        self.nodeListWidget.setVisible(False)
        
        self.remove_actors_from_node_list()
        
        self.render_editor_window()
        if self.selected_node_ids:
            self.selected_node_ids.clear()
        self.setBoundaryNodeValuesButton.setVisible(False)
        self.resetNodeSelectionButton.setVisible(False)
        self.change_interactor(INTERACTOR_STYLE_TRACKBALL_CAMERA)
    
    
    def setBoundaryNodeValuesButtonClicked(self):        
        if not self.selected_node_ids:
            QMessageBox.warning(self, "No Selection", "Please select at least one node")
            self.log_console.printWarning("Please select at least one node")
            return

        # Open a dialog to get the double value
        value, ok = QInputDialog.getDouble(self, "Set Node Value", "Enter value:", decimals=3)
        if ok:
            formatted_nodes = ", ".join(map(str, self.selected_node_ids))
            self.log_console.printInfo(f"Applying value {value} to nodes: ({formatted_nodes})")
            self.saveBoundaryConditions(self.selected_node_ids, value)
        
        self.reset_selection_nodes()

    def saveBoundaryConditions(self, node_ids, value):
        try:
            with open(self.config_tab.config_file_path, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error", f"Error parsing JSON file '{self.config_tab.config_file_path}': {e}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while reading the configuration file '{self.config_tab.config_file_path}': {e}")
            return

        if "Boundary Conditions" not in data:
            data["Boundary Conditions"] = {}

        node_key = ','.join(map(str, node_ids))
        data["Boundary Conditions"][node_key] = value

        try:
            with open(self.config_tab.config_file_path, 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")

    def activate_selection_boundary_conditions_mode(self):
        if not self.selected_actors:
            QMessageBox.warning(self, "Set Boundary Conditions", "To begin with setting boundary conditions you'll need to select object")
            self.log_console.printWarning("To begin with setting boundary conditions you'll need to select object")
            return
        
        if not self.mesh_file:
            QMessageBox.warning(self, "Set Boundary Conditions", "To begin with setting boundary conditions you'll need to select mesh file in .msh/.stp format")
            self.log_console.printWarning("To begin with setting boundary conditions you'll need to select mesh file in .msh/.stp format")
            return
    
        if not exists(self.mesh_file):
            QMessageBox.warning(self, "Set Boundary Conditions", f"Make sure, that path {self.mesh_file} is really exists")
            self.log_console.printWarning(f"Make sure, that path {self.mesh_file} is really exists")
            return
        
        if not self.mesh_file.endswith('.msh'):
            QMessageBox.warning(self, "Set Boundary Conditions", f"File {self.mesh_file} have to ends with .msh format. Tip: if you upload mesh in .stp format program will automatically convert it to .msh format")
            self.log_console.printWarning(f"File {self.mesh_file} have to ends with .msh format. Tip: if you upload mesh in .stp format program will automatically convert it to .msh format")
            return
        
        if not self.setBoundaryNodeValuesButton.isVisible():
            self.setBoundaryNodeValuesButton.setVisible(True)
        if not self.resetNodeSelectionButton.isVisible():
            self.resetNodeSelectionButton.setVisible(True)
        if not self.nodeListWidget.isVisible():
            self.nodeListWidget.setVisible(True)
        
        try:
            self.isBoundaryNodeSelectionMode = True
            self.statusBar.showMessage("Select boundary nodes:")
            self.populate_node_list()
            self.add_actors_from_node_list()
        except Exception as e:
            QMessageBox.critical(self, "Set Boundary Conditions", f"Error was occured: {e}")
            self.log_console.printError(f"Error was occured: {e}")
            self.reset_selection_nodes()
            return
            
    def on_node_selection_changed(self):
        selected_items = self.nodeListWidget.selectedItems()
        self.selected_node_ids = {int(item.text()) for item in selected_items}

        for node_id, data in self.nodeMap.items():
            actor = data['actor']
            actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)  # Yellow color for unselected nodes

        for node_id in self.selected_node_ids:
            if node_id in self.nodeMap:
                actor = self.nodeMap[node_id]['actor']
                actor.GetProperty().SetColor(SELECTED_ACTOR_COLOR)

        self.render_editor_window()


    def activate_selection_boundary_conditions_mode_for_surface(self):
        if not self.selected_actors:
            QMessageBox.information(self, "Set Boundary Conditions", "There is no selected surfaces to apply boundary conditions on them")
            return
        
        dialog = BoundaryValueInputDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            value, ok = dialog.get_value()
            if not ok:
                QMessageBox.warning(self, "Set Boundary Conditions Value", "Failed to apply value, retry please")
                return
        else:
            return
        
        for actor in self.selected_actors:
            if actor in self.actor_nodes:
                nodes = self.actor_nodes[actor]
                self.saveBoundaryConditions(nodes, value)
                self.log_console.printInfo(f"Object: {hex(id(actor))}, Nodes: {nodes}, Value: {value}")
        self.deselect()

    
    def update_config_with_particle_source(self, particle_params, surface_and_normals_dict):
        config_file = self.config_tab.config_file_path
        if not config_file:
            QMessageBox.warning(self, "Configuration File", "No configuration file selected.")
            return

        # Read the existing configuration file
        with open(config_file, 'r') as file:
            config_data = json.load(file)

        # Check for existing sources
        sources_to_remove = []
        if "ParticleSourcePoint" in config_data:
            sources_to_remove.append("ParticleSourcePoint")
        if "ParticleSourceSurface" in config_data:
            sources_to_remove.append("ParticleSourceSurface")

        # Ask user if they want to remove existing sources
        if sources_to_remove:
            reply = QMessageBox.question(self, "Remove Existing Sources",
                                        f"The configuration file contains existing sources: {', '.join(sources_to_remove)}. Do you want to remove them?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                for source in sources_to_remove:
                    del config_data[source]

        # Prepare new ParticleSourceSurface entry
        if "ParticleSourceSurface" not in config_data:
            config_data["ParticleSourceSurface"] = {}

        new_surface_row = str(len(config_data["ParticleSourceSurface"]) + 1)
        config_data["ParticleSourceSurface"][new_surface_row] = {
            "Type": particle_params["particle_type"],
            "Count": particle_params["num_particles"],
            "Energy": particle_params["energy"],
            "BaseCoordinates": {}
        }

        # Add cell center coordinates and normals to the entry
        for arrow_address, values in surface_and_normals_dict.items():
            cell_center = values['cell_center']
            normal = values['normal']
            coord_key = f"{cell_center[0]:.2f}, {cell_center[1]:.2f}, {cell_center[2]:.2f}"
            config_data["ParticleSourceSurface"][new_surface_row]["BaseCoordinates"][coord_key] = normal

        # Write the updated configuration back to the file
        with open(config_file, 'w') as file:
            json.dump(config_data, file, indent=4)

        self.log_console.printInfo(f"Particle source surface added to configuration file: {config_file}")


    def set_particle_source(self):
        dialog = ParticleSourceTypeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected_source_type = dialog.getSelectedSourceType()

            if selected_source_type == "Point Source with Conical Distribution":
                self.set_particle_source_as_point()
            elif selected_source_type == "Surface Source":
                self.set_particle_source_as_surface()


    def set_particle_source_as_point(self):
        if not self.particleSourceArrowActor:
            method_dialog = MethodSelectionDialog(self)
            if method_dialog.exec_() == QDialog.Accepted:
                method = method_dialog.get_selected_method()
                if method == "manual":
                    dialog = ArrowPropertiesDialog(self)
                    if dialog.exec_() == QDialog.Accepted:
                        properties = dialog.getProperties()
                        if properties:
                            x, y, z, angle_x, angle_y, angle_z = properties
                            self.create_direction_arrow_manually(x, y, z, angle_x, angle_y, angle_z)
                        else:
                            self.resetParticleSourceArrow()
                            QMessageBox.warning(self, "Invalid input", "Please enter valid numerical values.")
                            return
                    else:
                        self.resetParticleSourceArrow()
                        return
                elif method == "interactive":
                    self.create_direction_arrow_interactively()
                else:
                    self.resetParticleSourceArrow()
                    return

        self.expansion_angle_dialog = ExpansionAngleDialogNonModal(self.vtkWidget, self.renderer, self.particleSourceArrowActor, self)
        self.expansion_angle_dialog.accepted_signal.connect(self.handle_theta_signal)
        self.expansion_angle_dialog.show()


    def handle_theta_signal(self, thetaMax):
        try:
            self.expansion_angle = thetaMax
            
            if self.getParticleSourceDirection() is None:
                self.resetParticleSourceArrow()
                return
            _, phi = self.getParticleSourceDirection()
            
            if thetaMax > pi / 2.:
                self.log_console.printWarning(f"The θ angle exceeds 90°, so some particles can distribute in the opposite direction\nθ = {thetaMax} ({thetaMax * 180. / pi}°)")    
            self.log_console.printInfo(f"Successfully assigned values to the expansion angle and calculated φ angle\nθ = {thetaMax} ({thetaMax * 180. / pi}°)\nφ = {phi} ({phi * 180. / pi}°)\n")
        
            self.savePointParticleSourceToConfig()
        
        except Exception as e:
            self.resetParticleSourceArrow()
            QMessageBox.critical(self, "Scattering angles", f"Exception while assigning expansion angle θ: {e}")
            self.log_console.printError(f"Exception while assigning expansion angle θ: {e}\n")
            return


    def set_particle_source_as_surface(self):
        if not self.selected_actors:
            self.log_console.printWarning("There is no selected surfaces to apply boundary conditions on them")
            QMessageBox.information(self, "Set Boundary Conditions", "There is no selected surfaces to apply boundary conditions on them")
            return

        selected_actor = list(self.selected_actors)[0]
        surface_and_normals_dict = self.select_surface_and_normals(selected_actor)
        if not surface_and_normals_dict:
            return
        
        dialog = ParticleSourceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            particle_params = dialog.getValues()
            particle_type = particle_params["particle_type"]
            energy = particle_params["energy"]
            num_particles = particle_params["num_particles"]
            
            self.log_console.printInfo("Particle source set as surface source\n"
                                       f"Particle Type: {particle_type}\n"
                                       f"Energy: {energy} eV\n"
                                       f"Number of Particles: {num_particles}")
            self.log_console.addNewLine()
        else:
            return
        
        self.update_config_with_particle_source(particle_params, surface_and_normals_dict)

    def confirm_normal_orientation(self, orientation):
        return QMessageBox.question(
            self, 
            "Normal Orientation", 
            f"Do you want to set normals {orientation}?", 
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes

    def add_arrows(self, arrows):
        for arrow_actor, _, _ in arrows:
            self.renderer.AddActor(arrow_actor)
        self.render_editor_window()

    def remove_arrows(self, arrows):
        for arrow_actor, _, _ in arrows:
            self.renderer.RemoveActor(arrow_actor)
        self.render_editor_window()

    def populate_data(self, arrows, data):
        for arrow_actor, cell_center, normal in arrows:
            actor_address = hex(id(arrow_actor))
            data[actor_address] = {"cell_center": cell_center, "normal": normal}


    def select_surface_and_normals(self, actor: vtkActor):
        poly_data = actor.GetMapper().GetInput()
        normals = self.calculate_normals(poly_data)

        if not normals:
            self.log_console.printWarning("No normals found for the selected surface")
            QMessageBox.warning(self, "Normals Calculation", "No normals found for the selected surface")
            return

        num_cells = poly_data.GetNumberOfCells()
        arrows_outside = []
        arrows_inside = []
        data = {}

        for i in range(num_cells):
            normal = normals.GetTuple(i)
            rev_normal = tuple(-n if n != 0 else 0.0 for n in normal)
            cell = poly_data.GetCell(i)
            cell_center = self.calculate_cell_center(cell)

            arrow_outside = self.create_arrow_actor(cell_center, normal)
            arrow_inside = self.create_arrow_actor(cell_center, rev_normal)
            
            arrows_outside.append((arrow_outside, cell_center, normal))
            arrows_inside.append((arrow_inside, cell_center, rev_normal))
        self.add_arrows(arrows_outside)
        
        if not self.confirm_normal_orientation("outside"):
            self.remove_arrows(arrows_outside)
            self.add_arrows(arrows_inside)
            if not self.confirm_normal_orientation("inside"):
                self.remove_arrows(arrows_inside)
                return
            else:
                self.populate_data(arrows_inside, data)
        else:
            self.populate_data(arrows_outside, data)
            
        self.remove_arrows(arrows_outside)
        self.remove_arrows(arrows_inside)

        surface_address = next(iter(data))
        self.log_console.printInfo(f"Selected surface <{surface_address}> with {num_cells} cells inside:")
        for arrow_address, values in data.items():
            cellCentre = values['cell_center']
            normal = values['normal']
            self.log_console.printInfo(f"<{surface_address}> | <{arrow_address}>: [{cellCentre[0]:.2f}, {cellCentre[1]:.2f}, {cellCentre[2]:.2f}] - ({normal[0]:.2f}, {normal[1]:.2f}, {normal[2]:.2f})")
            surface_address = next(iter(data))
        
        self.deselect()
        return data


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
    
    
    def create_arrow_actor(self, position, direction):
        arrow_source = vtkArrowSource()
        arrow_source.SetTipLength(0.2)
        arrow_source.SetShaftRadius(0.02)
        arrow_source.SetTipResolution(100)

        transform = vtkTransform()
        transform.Translate(position)

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

    def test(self):
        self.update_gmsh_files()
