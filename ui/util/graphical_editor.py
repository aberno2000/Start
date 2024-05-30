import gmsh, json
from numpy import cross
from os.path import isfile, exists
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import(
    vtkInteractorStyleTrackballCamera, 
    vtkInteractorStyleTrackballActor, 
    vtkInteractorStyleRubberBandPick
)
from vtkmodules.vtkFiltersGeneral import vtkBooleanOperationPolyDataFilter
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, pyqtSlot
from vtk import(
    vtkRenderer, vtkPoints, vtkPolyData, vtkPolyLine, vtkCellArray, vtkPolyDataMapper, 
    vtkActor, vtkSphereSource, vtkAxesActor, vtkOrientationMarkerWidget, 
    vtkGenericDataObjectReader, vtkDataSetMapper, vtkCellPicker, 
    vtkCleanPolyData, vtkPlane, vtkClipPolyData, vtkTransform, vtkTransformPolyDataFilter, 
    vtkArrowSource, vtkCommand
)
from PyQt5.QtWidgets import(
    QFrame, QVBoxLayout, QHBoxLayout, QTreeView,
    QPushButton, QDialog, QSpacerItem, QColorDialog,
    QSizePolicy, QMessageBox, QFileDialog,
    QMenu, QAction, QInputDialog, QStatusBar,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt5.QtGui import QCursor, QStandardItemModel
from .util import(
    PointDialog, LineDialog, SurfaceDialog, 
    SphereDialog, BoxDialog, CylinderDialog,
    AngleDialog, MoveActorDialog, AxisSelectionDialog,
    ExpansionAngleDialog, pi
)
from util.util import(
    align_view_by_axis, save_scene, load_scene, convert_unstructured_grid_to_polydata,
    can_create_line, getObjectMapForPoint, extract_transform_from_actor, calculate_thetaPhi, 
    rad_to_degree, getObjectMap, createActorsFromObjectMap, populateTreeView, 
    getObjectMapForSurface, can_create_surface, getObjectMapForLine,
    ActionHistory,
    DEFAULT_TEMP_MESH_FILE, DEFAULT_TEMP_FILE_FOR_PARTICLE_SOURCE_AND_THETA
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
        
        self.tree_item_actor_map = {}
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
        
        self.objectsHistory = ActionHistory()
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
    
    
    @pyqtSlot()
    def activate_selection_boundary_conditions_mode_slot(self):
        self.setBoundaryConditionsButton.click()
    
    
    def initialize_tree(self):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Mesh Tree'])
        self.setTreeViewModel(self.model)
        

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
        
        self.vtkWidget.GetRenderWindow().Render()
        
    def remove_actors_from_node_list(self):
        if not self.nodeMap:
            return
        
        for node_data in self.nodeMap.values():
            actor = node_data['actor']
            self.renderer.RemoveActor(actor)
        
        self.nodeMap.clear()
        self.vtkWidget.GetRenderWindow().Render()
    
    
    def set_mesh_file(self, file_path):        
        if exists(file_path) and isfile(file_path):
            self.mesh_file = file_path
            self.actor_from_mesh = self.get_actor_from_mesh(self.mesh_file)
            self.initialize_tree()
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
        self.directParticleButton = self.create_button('icons/particle-source-direction.png', 'Set particle source and direction of this source')
        self.setBoundaryConditionsButton = self.create_button('icons/boundary-conditions.png', 'Turning on mode to select boundary nodes')
        
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
        self.directParticleButton.clicked.connect(self.activate_particle_direction_mode)
        self.setBoundaryConditionsButton.clicked.connect(self.activate_selection_boundary_conditions_mode)

    def setup_ui(self):
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.layout.addLayout(self.toolbarLayout)
        self.layout.addWidget(self.vtkWidget)
        self.setLayout(self.layout)

        self.renderer = vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        
        self.change_interactor(INTERACTOR_STYLE_TRACKBALL_CAMERA)
        
    
    def create_point(self):
        def create_point_with_gmsh(x, y, z, mesh_size, filename: str = DEFAULT_TEMP_MESH_FILE):
            gmsh.initialize()
            gmsh.model.add("point")
            gmsh.model.geo.addPoint(x, y, z, meshSize=mesh_size, tag=1)
            gmsh.model.geo.synchronize()
            gmsh.model.mesh.generate(3)
            pointMap = getObjectMapForPoint()
            gmsh.write(filename)
            gmsh.finalize()
            return pointMap

        dialog = PointDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z = dialog.getValues()
            
            # Prepare the point data for Gmsh
            mesh_size = 1.0  # Default mesh size
            meshfilename = self.retrieve_mesh_filename()
            pointMap = create_point_with_gmsh(x, y, z, mesh_size, meshfilename)
            self.add_actors_and_populate_tree_view(pointMap, 'point')
            
            self.log_console.printInfo(f'Successfully created point: ({x}, {y}, {z})')
            self.log_console.addNewLine()
            
            
    def create_line(self):
        def create_line_with_gmsh(points, mesh_size, filename: str = DEFAULT_TEMP_MESH_FILE):
            gmsh.initialize()
            gmsh.model.add("line")

            for idx, (x, y, z) in enumerate(points, start=1):
                gmsh.model.geo.addPoint(x, y, z, meshSize=mesh_size, tag=idx)
            for i in range(len(points) - 1):
                gmsh.model.geo.addLine(i + 1, i + 2)

            gmsh.model.geo.synchronize()
            gmsh.model.mesh.generate(3)
            lineMap = getObjectMapForLine()
            gmsh.write(filename)
            gmsh.finalize()
            return lineMap

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
                
                mesh_size = 1.0  # Default mesh size
                meshfilename = self.retrieve_mesh_filename()
                lineMap = create_line_with_gmsh(point_data, mesh_size, meshfilename)
                self.add_actors_and_populate_tree_view(lineMap, 'line')
                
                self.log_console.printInfo(f'Successfully created line:\n{tmp}')
                self.log_console.addNewLine()

    
    def create_surface(self):
        def create_surface_with_gmsh(points, mesh_size, filename: str = DEFAULT_TEMP_MESH_FILE):
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
            surfaceMap = getObjectMapForSurface()
            gmsh.write(filename)     
            gmsh.finalize()
            return surfaceMap
    
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
                
                meshfilename = self.retrieve_mesh_filename()
                surfaceMap = create_surface_with_gmsh(point_data, mesh_size, meshfilename)
                self.add_actors_and_populate_tree_view(surfaceMap, 'surface')
                
                self.log_console.printInfo(f'Successfully created surface:\n{tmp}')
                self.log_console.addNewLine()

    
    def create_sphere(self):
        def create_sphere_with_gmsh(mesh_size: float, filename: str = DEFAULT_TEMP_MESH_FILE):
            gmsh.initialize()
            gmsh.model.add('custom_sphere')
            gmsh.model.occ.add_sphere(x, y, z, radius)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
            gmsh.model.occ.synchronize()
            gmsh.model.mesh.generate(3)
            sphereMap = getObjectMap()
            gmsh.write(filename)
            gmsh.finalize()
            return sphereMap
        
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
            
            meshfilename = self.retrieve_mesh_filename()
            sphereMap = create_sphere_with_gmsh(mesh_size, meshfilename)
            self.add_actors_and_populate_tree_view(sphereMap, 'volume')
            
            self.log_console.printInfo(f'Successfully created sphere:\n{tmp}')
            self.log_console.addNewLine()


    def create_box(self):
        def create_box_with_gmsh(mesh_size: float, filename: str = DEFAULT_TEMP_MESH_FILE):
            gmsh.initialize()
            gmsh.model.occ.add_box(x, y, z, length, width, height)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
            gmsh.model.occ.synchronize()
            gmsh.model.mesh.generate(3)
            boxMap = getObjectMap()
            gmsh.write(filename)
            gmsh.finalize()
            return boxMap
        
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
            
            meshfilename = self.retrieve_mesh_filename()
            boxMap = create_box_with_gmsh(mesh_size, meshfilename)
            self.add_actors_and_populate_tree_view(boxMap, 'volume')
            
            self.log_console.printInfo(f'Successfully created box:\n{tmp}')
            self.log_console.addNewLine()


    def create_cylinder(self):
        def create_cylinder_with_gmsh(mesh_size: float, filename: str = DEFAULT_TEMP_MESH_FILE):
            gmsh.initialize()
            gmsh.model.add('custom_cylinder')
            gmsh.model.occ.add_cylinder(x, y, z, dx, dy, dz, radius)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
            gmsh.model.occ.synchronize()
            gmsh.model.mesh.generate(3)
            cylinderMap = getObjectMap()
            gmsh.write(filename)
            gmsh.finalize()
            return cylinderMap
        
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

            meshfilename = self.retrieve_mesh_filename()
            cylinderMap = create_cylinder_with_gmsh(mesh_size, meshfilename)
            self.add_actors_and_populate_tree_view(cylinderMap, 'volume')
            
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
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
    
    
    def add_actors(self, actors: list):
        for actor in actors:
            self.renderer.AddActor(actor)
            actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
        
        
    def remove_actor(self, actor: vtkActor):
        if actor in self.renderer.GetActors():
            self.renderer.RemoveActor(actor)
            self.renderer.ResetCamera()
            self.vtkWidget.GetRenderWindow().Render()      
    
    
    def remove_actors(self, actors: list):
        for actor in actors:
            if actor in self.renderer.GetActors():
                self.renderer.RemoveActor(actor)
                
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
    
    
    def remove_objects_with_restore(self, actors: list):
        # TODO: implement
        if actors:
            # Saving previous actors:
            prev_state = actors
            self.objectsHistory.add_action((prev_state, ))
            
            for actor in actors:
                pass
                
        
        if actor in self.renderer.GetActors():
            # Getting current added object
            action = self.undo_stack.pop()
            row = action.get('row')
            self.redo_stack.append(action)
            
            # Removing actor from the scene, row from the tree view and decrementing the ID of objects
            self.remove_actor(actor)
            self.model.removeRow(row)
            
            # Resetting camera view and rendering scene after performing deletion of actor
            self.renderer.ResetCamera()
            self.vtkWidget.GetRenderWindow().Render()
    
    
    def permanently_remove_actor(self, actor: vtkActor):
        # TODO: fix
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText("Are you sure you want to delete the object? It will be permanently deleted.")
        msgBox.setWindowTitle("Permanently Object Deletion")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        choice = msgBox.exec()
        if choice == QMessageBox.No:
            return
        else: 
            if actor in self.renderer.GetActors():
                action = self.undo_stack.pop()
                row = action.get('row')
                
                self.model.removeRow(row)            
                self.renderer.RemoveActor(actor)
                self.vtkWidget.GetRenderWindow().Render()
    
    
    def colorize_actor(self, actor: vtkActor):
        actorColor = QColorDialog.getColor()
        if actorColor.isValid():
            actor.GetProperty().SetColor(actorColor.redF(), actorColor.greenF(), actorColor.blueF())
            self.renderer.ResetCamera()
            self.vtkWidget.GetRenderWindow().Render()
        else:
            return


    def remove_all_actors(self):
        self.particleSourceArrowActor = None
        
        actors = self.renderer.GetActors()
        actors.InitTraversal()        
        for i in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()
            self.renderer.RemoveActor(actor)
        
        self.vtkWidget.GetRenderWindow().Render()
        

    def add_custom(self, meshfilename: str):
        gmsh.initialize()
        customObjectMap = getObjectMap(meshfilename)
        self.add_actors_and_populate_tree_view(customObjectMap, 'volume')
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
        res = self.objectsHistory.undo()
        if not res:
            return
        row, actors, object_map, objType = res
        
        self.remove_actors(actors)
        
        if objType != 'line':
            self.remove_row_from_tree(row)
        else:
            self.remove_rows_from_tree(row)
    

    def redo_object_creating(self):
        res = self.objectsHistory.redo()
        if not res:
            return
        row, actors, object_map, objType = res
        
        self.add_actors(actors)
        self.populate_tree(object_map, objType)
    
    
    def remove_row_from_tree(self, row):
        self.model.removeRow(row)
        self.setTreeViewModel()
    
    def remove_rows_from_tree(self, rows):
        row = rows[0]
        for _ in range(len(rows)):
            self.model.removeRow(row)
        self.setTreeViewModel()
    
    def fill_row_actor_map(self, row, actors, objType: str):
        if objType == 'volume':
            volume_index = row
            self.tree_item_actor_map[volume_index] = []
            for i, actor in enumerate(actors):
                surface_index = volume_index + i + 1
                actor_color = actor.GetProperty().GetColor()
                self.tree_item_actor_map[surface_index] = [(surface_index, actor, actor_color)]
                self.tree_item_actor_map[volume_index].append((surface_index, actor, actor_color))
        elif objType == 'line':
            for i, r in enumerate(row):
                actor_color = actors[i].GetProperty().GetColor()
                self.tree_item_actor_map[r] = [(r, actors[i], actor_color)]
        else:
            actor_color = actors[0].GetProperty().GetColor()
            self.tree_item_actor_map[row] = [(row, actors[0], actor_color)]
    
    
    def populate_tree(self, objectMap: dict, objType: str) -> list:
        row = populateTreeView(objectMap, self.objectsHistory.id, self.model, self.treeView, objType)
        self.treeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeView.selectionModel().selectionChanged.connect(self.on_tree_selection_changed)
        actors = createActorsFromObjectMap(objectMap, objType)
        
        self.fill_row_actor_map(row, actors, objType)
        
        return row, actors
    
    
    def add_actors_and_populate_tree_view(self, objectMap: dict, objType: str):
        self.objectsHistory.id += 1
        row, actors = self.populate_tree(objectMap, objType)
        self.add_actors(actors)        
        self.objectsHistory.add_action((row, actors, objectMap, objType))
        self.global_undo_stack.append(ACTION_ACTOR_CREATING)
        
    
    def highlight_actor(self, actor: vtkActor):
        actor.GetProperty().SetColor(SELECTED_ACTOR_COLOR)
        self.vtkWidget.GetRenderWindow().Render()


    def unhighlight_actor(self, actor: vtkActor):
        actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
        self.vtkWidget.GetRenderWindow().Render()

    
    def on_tree_selection_changed(self):
        selected_indexes = self.treeView.selectedIndexes()
        if not selected_indexes:
            return
        
        selected_row = selected_indexes[0].row()
        selected_item = self.tree_item_actor_map[selected_row] if selected_row in self.tree_item_actor_map else None

        # Unhighlight previously selected actors
        for actor in self.selected_actors:
            self.unhighlight_actor(actor)
        
        self.selected_actors.clear()

        # Highlight selected actors
        if selected_item:
            if isinstance(selected_item, list):
                for actor in selected_item:
                    self.highlight_actor(actor)
                    self.selected_actors.add(actor)
            else:
                self.highlight_actor(selected_item)
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
        self.vtkWidget.GetRenderWindow().Render()

    def start_line_drawing(self):
        self.crossSectionLinePoints.clear()
        self.isDrawingLine = True

    def endLineDrawing(self):
        self.isDrawingLine = False
        if self.tempLineActor:
            self.renderer.RemoveActor(self.tempLineActor)
            self.tempLineActor = None
        self.vtkWidget.GetRenderWindow().Render()
    
    def pick_actor(self, obj, event):
        click_pos = self.interactor.GetEventPosition()
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)

        actor = self.picker.GetActor()
        if actor:
            self.original_color = actor.GetProperty().GetColor()
            self.selected_actor = actor
            actor.GetProperty().SetColor(SELECTED_ACTOR_COLOR)
            self.selected_actors = {actor}  # Reset multiple selection

            self.vtkWidget.GetRenderWindow().Render()

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
                    self.vtkWidget.GetRenderWindow().Render()
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
            self.selected_actors[0] = actor
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
        if self.selected_actors[0]:
            menu = QMenu(self)

            move_action = QAction('Move', self)
            move_action.triggered.connect(self.move_actors)
            menu.addAction(move_action)

            change_angle_action = QAction('Rotate', self)
            change_angle_action.triggered.connect(self.change_actor_angle)
            menu.addAction(change_angle_action)

            adjust_size_action = QAction('Adjust size', self)
            adjust_size_action.triggered.connect(self.adjust_actor_size)
            menu.addAction(adjust_size_action)
            
            remove_object_action = QAction('Remove', self)
            remove_object_action.triggered.connect(lambda: self.permanently_remove_actor(self.selected_actors[0]))
            menu.addAction(remove_object_action)
            
            colorize_object_action = QAction('Colorize', self)
            colorize_object_action.triggered.connect(lambda: self.colorize_actor(self.selected_actors[0]))
            menu.addAction(colorize_object_action)

            menu.exec_(QCursor.pos())
    
    
    def deselect(self):
        try:
            for actor in self.renderer.GetActors():
                actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
            
            self.selected_actors.clear()
            
            self.vtkWidget.GetRenderWindow().Render()
        except Exception as _:
            return


    def move_actors(self):
        if self.selected_actors:
            for actor in self.selected_actors:
                self.move_actor(actor)

    def move_actor(self, actor: vtkActor):        
        if actor:
            dialog = MoveActorDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                offsets = dialog.getValues()
                if offsets:
                    x_offset, y_offset, z_offset = offsets
                    position = actor.GetPosition()
                    new_position = (position[0] + x_offset, position[1] + y_offset, position[2] + z_offset)
                    
                    polydata = convert_unstructured_grid_to_polydata(actor)
                    if not polydata:
                        return
                    
                    # Moving points
                    points = polydata.GetPoints()
                    for i in range(points.GetNumberOfPoints()):
                        x, y, z = points.GetPoint(i)
                        points.SetPoint(i, x + x_offset, y + y_offset, z + z_offset)
                    polydata.SetPoints(points)
                    polydata.Modified()
                    
                    # Moving actor on the scene
                    actor.SetPosition(new_position)
                    self.vtkWidget.GetRenderWindow().Render()
                    
                    self.deselect()


    def adjust_actor_size(self, actor: vtkActor):
        if actor:
            scale_factor, ok = QInputDialog.getDouble(self, "Adjust size", "Scale:", 1.0, 0.01, 100.0, 2)
            if ok:
                actor.SetScale(scale_factor, scale_factor, scale_factor)
                self.vtkWidget.GetRenderWindow().Render()
                
                self.deselect()

    
    def change_actor_angle(self, actor: vtkActor):
        if actor:
            dialog = AngleDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                angles = dialog.getValues()
                if angles:
                    angle_x, angle_y, angle_z = angles
                    actor.RotateX(angle_x)
                    actor.RotateY(angle_y)
                    actor.RotateZ(angle_z)
                    self.vtkWidget.GetRenderWindow().Render()
                    
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
        self.remove_row_from_tree_view()
        
        # Adding 2 new objects
        self.add_actor_and_row(actor1)
        self.add_actor_and_row(actor2)
        
        self.log_console.printInfo("Successfully created a cross-section")
    
    
    def writeParticleSouceAndDirectionToFile(self):
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

            with open(DEFAULT_TEMP_FILE_FOR_PARTICLE_SOURCE_AND_THETA, "w") as f:
                f.write(f"{base_coords[0]} {base_coords[1]} {base_coords[2]} {self.expansion_angle} {phi} {theta}")
            
            self.statusBar.showMessage("Successfully set particle source and calculated direction angles")
            self.log_console.printInfo(f"Successfully written coordinates of the particle source:\nBase: {base_coords}\nExpansion angle θ: {self.expansion_angle} ({rad_to_degree(self.expansion_angle)}°)\nPolar (colatitude) angle θ: {theta} ({rad_to_degree(theta)}°)\nAzimuthal angle φ: {phi} ({rad_to_degree(phi)}°)\n")
            self.log_console.addNewLine()
            
            self.resetParticleSourceArrow()
            return 1

        except Exception as e:
            error_message = f"Error defining particle source. {e}"
            self.log_console.printError(error_message)
            QMessageBox.warning(self, "Particle Source", error_message)
            return None

        
    def resetParticleSourceArrow(self):
        self.remove_actor(self.particleSourceArrowActor)
        self.particleSourceArrowActor = None
        
        
    def getParticleSourceBaseCoords(self):
        if not self.particleSourceArrowActor:
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
    
    def activate_particle_direction_mode(self):
        if not self.particleSourceArrowActor:
            self.particleSourceArrowActor = self.create_direction_arrow()
        
        dialog = ExpansionAngleDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getTheta() is not None:
            try:
                thetaMax = dialog.getTheta()
                
                if self.getParticleSourceDirection() is None:
                    return
                _, phi = self.getParticleSourceDirection()
                
                if thetaMax > pi / 2.:
                    self.log_console.printWarning(f"The θ angle exceeds 90°, so some particles can distribute in the opposite direction\nθ = {thetaMax} ({thetaMax * 180. / pi}°)")    
                self.log_console.printInfo(f"Successfully assigned values to the expansion angle and calculated φ angle\nθ = {thetaMax} ({thetaMax * 180. / pi}°)\nφ = {phi} ({phi * 180. / pi}°)\n")
            
            except Exception as e:
                QMessageBox.critical(self, "Scattering angles", f"Exception while assigning expansion angle θ: {e}")
                self.log_console.printError(f"Exception while assigning expansion angle θ: {e}\n")
                return

            self.expansion_angle = thetaMax
        else:
            self.resetParticleSourceArrow()
            
 
    def create_direction_arrow(self):
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
        
        arrowActor = vtkActor()
        arrowActor.SetMapper(mapper)
        arrowActor.GetProperty().SetColor(ARROW_ACTOR_COLOR)
        
        self.renderer.AddActor(arrowActor)
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()

        return arrowActor

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
        
        self.vtkWidget.GetRenderWindow().Render()
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
        if not self.selected_actors[0]:
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
            self.initialize_node_map()
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

        self.vtkWidget.GetRenderWindow().Render()


