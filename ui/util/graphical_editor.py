import gmsh, meshio
from os import remove
from os.path import isfile, exists, basename
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from PyQt5.QtGui import QStandardItem, QIcon
from PyQt5.QtCore import QSize
from vtk import(
    vtkRenderer, vtkPoints, vtkPolyData, vtkVertexGlyphFilter, vtkPolyLine,
    vtkCellArray, vtkPolyDataMapper, vtkActor, vtkSphereSource, vtkUnstructuredGrid,
    vtkCylinderSource, vtkAxesActor, vtkOrientationMarkerWidget, vtkCellTypes,
    vtkGenericDataObjectReader, vtkDataSetMapper, vtkCellPicker, vtkDelaunay2D,
    vtkCubeSource,
    VTK_TRIANGLE, VTK_QUAD
)
from PyQt5.QtWidgets import(
    QFrame, QVBoxLayout, QHBoxLayout, QTreeView,
    QPushButton, QDialog, QSpacerItem,
    QSizePolicy, QMessageBox, QFileDialog,
    QMenu, QAction, QInputDialog
)
from PyQt5.QtGui import QCursor, QStandardItemModel
from .util import(
    PointDialog, LineDialog, SurfaceDialog, 
    SphereDialog, BoxDialog, CylinderDialog,
    AngleDialog, MoveActorDialog
)
from util.util import align_view_by_axis, save_scene, load_scene, convert_msh_to_vtk
from .mesh_dialog import MeshDialog, CaptureGmshLog
from .styles import DEFAULT_ACTOR_COLOR, SELECTED_ACTOR_COLOR


def get_action(id: int, data, actor: vtkActor, isDifficultObj: bool = False, figure_type: str = '', mesh_file: str = ''):
    if isDifficultObj:
        action = {
            'action': 'add_difficult_object',
            'mesh_file': mesh_file,
            'row': id,
            'data': data,
            'actor': actor
        }
    else:
        action = {
            'action': 'add',
            'row': id,
            'data': data,
            'actor': actor,
            'figure_type': figure_type,
        }
    return action


class GraphicalEditor(QFrame):    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.treeView = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Mesh Tree'])
        
        self.setup_toolbar()
        self.setup_ui()
        self.setup_interaction()
        self.setup_axes()
        
        self.object_idx = 0
        self.undo_stack = []
        self.redo_stack = []        
        
    
    def initialize_tree(self):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Mesh Tree'])
        rootItem = QStandardItem(basename(self.mesh_file))

        self.vtk_file = convert_msh_to_vtk(self.mesh_file)
        data = self.parse_vtk_polydata_and_populate_tree(self.vtk_file, self.model, rootItem)
        self.treeView.setModel(self.model)
        
        action = get_action(self.object_idx, data, self.actor_from_mesh, isDifficultObj=True, mesh_file=self.mesh_file)
        self.undo_stack.append(action)
        self.object_idx += 1
    
    
    def set_mesh_file(self, file_path):        
        if exists(file_path) and isfile(file_path):
            self.mesh_file = file_path
            self.actor_from_mesh = self.get_actor_from_mesh(self.mesh_file)
            self.initialize_tree()
        else:
            QMessageBox.warning(self, "Warning", f"Unable to open file {file_path}")
            return None
    
    
    def erase_all_from_tree_view(self):
        self.model.clear()
        
    
    def undo_action_tree_view(self):
        if self.undo_stack:
            action = self.undo_stack.pop()
            
            # Getting values from action
            row = action.get('row')
            actor = action.get('actor')
            data = action.get('data')
            
            # Perform some actions with values
            self.model.removeRow(row)
            self.remove_actor(actor)
                    
            if action.get('action') == 'add':
                redo_action = get_action(row, data, actor, isDifficultObj=False, figure_type=action.get('figure_type'))
            elif action.get('action') == 'add_difficult_object':
                redo_action = get_action(row, data, actor, isDifficultObj=True, mesh_file=action.get('mesh_file'))
            
            self.redo_stack.append(redo_action)
            self.object_idx -= 1
            

    def redo_action_tree_view(self):
        if self.redo_stack:
            # Getting values from the redo stack
            action = self.redo_stack.pop()
            actor = action.get('actor')
            data = action.get('data')
            mesh_file = action.get('mesh_file')
            
            self.add_actor(action.get('actor'))
            
            if action.get('action') == 'add':
                # Filling tree view
                items = QStandardItem(f'Created objects[{self.object_idx}]: ' + action.get('figure_type'))
                item = QStandardItem(data)
                items.appendRow(item)
                self.model.appendRow(items)
                self.treeView.setModel(self.model)

                # Creating undo action
                undo_action = get_action(self.object_idx, data, actor, isDifficultObj=False, figure_type=action.get('figure_type'))
            elif action.get('action') == 'add_difficult_object':
                if not data.IsA("vtkUnstructuredGrid"):
                    return
                unstructuredGrid = vtkUnstructuredGrid.SafeDownCast(data)

                # Filling tree view
                rootItem = QStandardItem(basename(mesh_file))
                pointsItem = QStandardItem("Points")
                for i in range(unstructuredGrid.GetNumberOfPoints()):
                    point = unstructuredGrid.GetPoint(i)
                    pointItem = QStandardItem(f"Point {i}: ({point[0]:.3f}, {point[1]:.3f}, {point[2]:.3f})")
                    pointsItem.appendRow(pointItem)
                
                cellsItem = QStandardItem("Cells")
                for i in range(unstructuredGrid.GetNumberOfCells()):
                    cell = unstructuredGrid.GetCell(i)
                    cellType = vtkCellTypes.GetClassNameFromTypeId(cell.GetCellType())
                    cellPoints = cell.GetPointIds()
                    cellPointsStr = ', '.join([str(cellPoints.GetId(j)) for j in range(cellPoints.GetNumberOfIds())])
                    cellItem = QStandardItem(f"Cell {i} ({cellType}): Points [{cellPointsStr}]")
                    cellsItem.appendRow(cellItem)
                    
                rootItem.appendRow(pointsItem)
                rootItem.appendRow(cellsItem)
                self.model.appendRow(rootItem)
                undo_action = get_action(self.object_idx, data, actor, isDifficultObj=True, mesh_file=action.get('mesh_file'))
            
            self.treeView.setModel(self.model)
            self.undo_stack.append(undo_action)
            self.object_idx += 1
                
    def get_actor_from_mesh(self, mesh_file_path: str):
        vtk_file_path = mesh_file_path.replace('.msh', '.vtk')
        
        reader = vtkGenericDataObjectReader()
        reader.SetFileName(vtk_file_path)
        reader.Update()
        
        if reader.IsFilePolyData():
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
        elif reader.IsFileUnstructuredGrid():
            mapper = vtkDataSetMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
        else:
            return

        actor = vtkActor()
        actor.SetMapper(mapper)
        self.add_actor(actor)
        
        return actor
        
    def create_button(self, icon_path, tooltip, size=(32, 32)):
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
        self.createPointButton = self.create_button('icons/point.png', 'Dot')
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

    def setup_ui(self):
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.layout.addLayout(self.toolbarLayout)
        self.layout.addWidget(self.vtkWidget)
        self.setLayout(self.layout)

        self.renderer = vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.interactorStyle = vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(self.interactorStyle)
        self.interactor.Initialize()
        
    
    def create_point(self):
        dialog = PointDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z = dialog.getValues()
            
            # Create a vtkPoints object and insert the point
            points = vtkPoints()
            points.InsertNextPoint(x, y, z)
            
            # Create a PolyData object
            polyData = vtkPolyData()
            polyData.SetPoints(points)
            
            # Use vtkVertexGlyphFilter to make the points visible
            glyphFilter = vtkVertexGlyphFilter()
            glyphFilter.SetInputData(polyData)
            glyphFilter.Update()
            
            # Create a mapper and actor for the point
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(glyphFilter.GetOutputPort())
            
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetPointSize(5)    # Set the size of the point
            actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)  # Set the color of the point (red)
            
            self.add_actor(actor)
            self.update_tree_model('Point', f'Point: ({x}, {y}, {z})', actor)
            
    def create_line(self):
        dialog = LineDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            values = dialog.getValues()
            
            # Create points
            points = vtkPoints()
            line = vtkPolyLine()
            points_str_list = []
            
            # The number of points in the polyline
            line.GetPointIds().SetNumberOfIds(len(values) // 3)
            
            # Add points and set ids
            for i in range(0, len(values), 3):
                point_id = points.InsertNextPoint(values[i], values[i + 1], values[i + 2])
                line.GetPointIds().SetId(i // 3, point_id)
                points_str_list.append(f'Point{i // 3 + 1}: {values[i]} {values[i + 1]} {values[i + 2]}')
            
            lines = vtkCellArray()
            lines.InsertNextCell(line)
            
            polyData = vtkPolyData()
            polyData.SetPoints(points)
            polyData.SetLines(lines)
            
            mapper = vtkPolyDataMapper()
            mapper.SetInputData(polyData)
            
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
            
            self.add_actor(actor)
            
            line_str = 'Line'
            self.update_tree_model(line_str, '\n'.join(points_str_list), actor)

    
    def create_surface(self):
        dialog = SurfaceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            values, mesh_size, checked = dialog.getValues()
            
            # Check if the meshing option is provided and valid
            if values is not None and len(values) >= 9 and mesh_size:
                polyData = vtkPolyData()
                points = vtkPoints()
                points_str_list = []
                
                # Insert points into vtkPoints
                pid = 1
                for i in range(0, len(values), 3):
                    points.InsertNextPoint(values[i], values[i+1], values[i+2])
                    points_str_list.append(f'Point{pid}: ({values[i]}, {values[i+1]}, {values[i+2]})')
                    pid += 1
                
                # Prepare point data for Gmsh
                point_data = []
                for i in range(0, len(values), 3):
                    point_data.append((values[i], values[i+1], values[i+2]))
                
                if checked:
                    try:
                        actor = self.create_surface_with_gmsh(point_data, mesh_size)
                    except Exception as e:
                        QMessageBox.warning(self, 'Meshing error', 'Can\'t mesh the surface with specified points')
                        return
                else:
                    polyData.SetPoints(points)
                
                    # Use Delaunay2D to create the surface
                    delaunay = vtkDelaunay2D()
                    delaunay.SetInputData(polyData)
                    delaunay.Update()
                    
                    # Create mapper and actor for the surface
                    mapper = vtkPolyDataMapper()
                    mapper.SetInputConnection(delaunay.GetOutputPort())
                    
                    actor = vtkActor()
                    actor.SetMapper(mapper)
                    actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
                    
                self.add_actor(actor)
                
                surface_str = 'Surface'
                self.update_tree_model(surface_str, '\n'.join(points_str_list), actor)

    def create_surface_with_gmsh(self, points, mesh_size):
        gmsh.initialize()
        gmsh.model.add("surface")

        # Define the points and lines in Gmsh
        for idx, (x, y, z) in enumerate(points, start=1):
            gmsh.model.geo.addPoint(x, y, z, meshSize=mesh_size, tag=idx)
        
        for i in range(len(points)):
            gmsh.model.geo.addLine(i + 1, ((i + 1) % len(points)) + 1)

        loop = gmsh.model.geo.addCurveLoop(list(range(1, len(points) + 1)))
        gmsh.model.geo.addPlaneSurface([loop])

        gmsh.model.geo.synchronize()
        gmsh.model.mesh.generate(2)

        # Specify a filename to write the mesh to
        msh_filename = "temp.msh"
        gmsh.write(msh_filename)

        # Now, read the mesh file using meshio
        mesh = meshio.read(msh_filename)

        # Display the mesh in VTK
        actor = self.display_meshio_mesh(mesh)

        gmsh.finalize()
        remove(msh_filename)
        return actor
        
    def display_meshio_mesh(self, mesh):
        vtk_points = vtkPoints()
        vtk_cells = vtkCellArray()

        for point in mesh.points:
            vtk_points.InsertNextPoint(*point)

        # Check cell types present in the mesh and create cells accordingly
        if 'triangle' in mesh.cells_dict:
            for cell in mesh.cells_dict['triangle']:
                vtk_cells.InsertNextCell(3, cell)
            cell_type = VTK_TRIANGLE
        elif 'quad' in mesh.cells_dict:
            for cell in mesh.cells_dict['quad']:
                vtk_cells.InsertNextCell(4, cell)
            cell_type = VTK_QUAD
        else:
            raise ValueError("Unsupported cell type in the mesh")

        poly_data = vtkPolyData()
        poly_data.SetPoints(vtk_points)

        if cell_type == VTK_TRIANGLE:
            poly_data.SetPolys(vtk_cells)
        elif cell_type == VTK_QUAD:
            poly_data.SetPolys(vtk_cells)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(poly_data)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
                
        return actor

    
    def create_sphere(self):
        def create_sphere_with_gmsh(mesh_size: float):
            gmsh.initialize()
            gmsh.model.add('custom_box')
            gmsh.model.occ.add_sphere(x, y, z, radius)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
            gmsh.model.occ.synchronize()
            gmsh.model.mesh.generate(2)
            msh_filename = 'temp.msh'
            gmsh.write(msh_filename)
            gmsh.finalize()
            return msh_filename
        
        dialog = SphereDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            values, mesh_size, checked = dialog.getValues()
            if mesh_size == 0.0:
                mesh_size = 1.0
            x, y, z, radius = values
            
            sphere_data_str = []
            sphere_data_str.append(f'Center: ({x}, {y}, {z})')
            sphere_data_str.append(f'Radius: {radius}')
            
            if checked:
                msh_filename = create_sphere_with_gmsh(mesh_size)
                mesh = meshio.read(msh_filename)
                actor = self.display_meshio_mesh(mesh)
            else:
                sphereSource = vtkSphereSource()
                sphereSource.SetCenter(x, y, z)
                sphereSource.SetRadius(radius)
                sphereSource.Update()
                
                mapper = vtkPolyDataMapper()
                mapper.SetInputConnection(sphereSource.GetOutputPort())
                
                actor = vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
                
            self.add_actor(actor)
            
            center_str = 'Sphere'
            self.update_tree_model(center_str, '\n'.join(sphere_data_str), actor)
            if checked:
                remove(msh_filename)


    def create_box(self):
        def create_box_with_gmsh(mesh_size: float):
            gmsh.initialize()
            gmsh.model.add('custom_box')
            gmsh.model.occ.add_box(x, y, z, length, width, height)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
            gmsh.model.occ.synchronize()
            gmsh.model.mesh.generate(2)
            msh_filename = 'temp.msh'
            gmsh.write(msh_filename)
            gmsh.finalize()
            return msh_filename
        
        dialog = BoxDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            values, mesh_size, checked = dialog.getValues()
            x, y, z, length, width, height = values
            
            box_data_str = []
            box_data_str.append(f'Primary Point: ({x}, {y}, {z})')
            box_data_str.append(f'Length: {length}')
            box_data_str.append(f'Width: {width}')
            box_data_str.append(f'Height: {height}')
            
            if checked:
                msh_filename = create_box_with_gmsh(mesh_size)
                mesh = meshio.read(msh_filename)
                actor = self.display_meshio_mesh(mesh)
            else:
                boxSource = vtkCubeSource()
                boxSource.SetBounds(x - length / 2., x + length / 2., 
                                    y - width / 2., y + width / 2., 
                                    z - height / 2., z + height / 2.)
                boxSource.Update()
                
                mapper = vtkPolyDataMapper()
                mapper.SetInputConnection(boxSource.GetOutputPort())
                
                actor = vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
                
            self.add_actor(actor)
            
            box_str = 'Box'
            self.update_tree_model(box_str, '\n'.join(box_data_str), actor)
            if checked:
                remove(msh_filename)


    def create_cylinder(self):
        def create_cylinder_with_gmsh(mesh_size: float):
            gmsh.initialize()
            gmsh.model.add('custom_box')
            gmsh.model.occ.add_cylinder(x, y, z, dx, dy, dz, radius)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
            gmsh.model.occ.synchronize()
            gmsh.model.mesh.generate(2)
            msh_filename = 'temp.msh'
            gmsh.write(msh_filename)
            gmsh.finalize()
            return msh_filename
        
        dialog = CylinderDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            values, mesh_size, checked = dialog.getValues()
            x, y, z, radius, dx, dy, dz = values
            cylinder_data_str = []
            cylinder_data_str.append(f'Primary Point: ({x}, {y}, {z})')
            cylinder_data_str.append(f'Radius: {radius}')
            cylinder_data_str.append(f'Length: {dx}')
            cylinder_data_str.append(f'Width: {dy}')
            cylinder_data_str.append(f'Height: {dz}')

            if checked:
                msh_filename = create_cylinder_with_gmsh(mesh_size)
                mesh = meshio.read(msh_filename)
                actor = self.display_meshio_mesh(mesh)
            else:
                cylinderSource = vtkCylinderSource()
                cylinderSource.SetRadius(radius)
                cylinderSource.SetHeight(dz)
                cylinderSource.SetCenter(x, y, z)
                cylinderSource.Update()
                
                mapper = vtkPolyDataMapper()
                mapper.SetInputConnection(cylinderSource.GetOutputPort())
                
                actor = vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
                
            self.add_actor(actor)
            
            cylinder_str = 'Cylinder'
            self.update_tree_model(cylinder_str, '\n'.join(cylinder_data_str), actor)
            if checked:
                remove(msh_filename)
            
    
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
            
    
    def convert_stp_to_msh(self, filename, mesh_size, mesh_dim):        
        original_stdout = stdout  # Save a reference to the original standard output
        redirected_output = CaptureGmshLog()
        stdout = redirected_output  # Redirect stdout to capture Gmsh logs

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
            stdout = original_stdout  # Restore stdout to its original state

        log_output = redirected_output.output
        if "Error" in log_output:
            QMessageBox.critical(
                self, "Conversion Error", "An error occurred during mesh generation. Please check the file and parameters.")
            return None
        else:
            QMessageBox.information(
                self, "Conversion Completed", f"Mesh generated: {output_file}")
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
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
        
        
    def remove_actor(self, actor: vtkActor):
        if actor in self.renderer.GetActors():
            self.renderer.RemoveActor(actor)
            self.vtkWidget.GetRenderWindow().Render()

    def remove_all_actors(self):
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        for i in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()
            self.renderer.RemoveActor(actor)
        
        self.vtkWidget.GetRenderWindow().Render()
        

    def add_custom(self, msh_filename: str):
        vtk_filename = msh_filename.replace('.msh', '.vtk')
        
        reader = vtkGenericDataObjectReader()
        reader.SetFileName(vtk_filename)
        reader.Update()
        
        if reader.IsFilePolyData():
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
        elif reader.IsFileUnstructuredGrid():
            mapper = vtkDataSetMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
        else:
            return None

        actor = vtkActor()
        actor.SetMapper(mapper)
        self.add_actor(actor)
        
        rootItem = QStandardItem(basename(msh_filename))
        data = self.parse_vtk_polydata_and_populate_tree(vtk_filename, self.model, rootItem)
        
        action = get_action(self.object_idx, data, actor, isDifficultObj=True, mesh_file=msh_filename)
        self.undo_stack.append(action)
        self.object_idx += 1
    
    
    def update_tree_model(self, figure_type: str, data: str, actor: vtkActor):
        items = QStandardItem(f'Created objects[{self.object_idx}]: ' + figure_type)
        self.model.appendRow(items)
        item = QStandardItem(data)
        items.appendRow(item)
        self.treeView.setModel(self.model)
        
        # Record the action in undo stack
        action = get_action(self.object_idx, data, actor, isDifficultObj=False, figure_type=figure_type)
        self.undo_stack.append(action)
        self.object_idx += 1
        
        
    def setup_interaction(self):
        self.picker = vtkCellPicker()
        self.picker.SetTolerance(0.005)

        self.selected_actor = None
        self.original_color = None

        self.interactor.SetInteractorStyle(self.interactorStyle)

        def pick_actor(obj, event):
            click_pos = self.interactor.GetEventPosition()
            self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)

            # If there is already a selected actor, reset its color
            if self.selected_actor:
                self.selected_actor.GetProperty().SetColor(self.original_color)

            actor = self.picker.GetActor()
            if actor:
                # Store the original color and the selected actor
                self.original_color = actor.GetProperty().GetColor()
                self.selected_actor = actor

                # Change the actor's color to orange
                actor.GetProperty().SetColor(SELECTED_ACTOR_COLOR)
                self.vtkWidget.GetRenderWindow().Render()
            # Call the original OnLeftButtonDown event handler to maintain default interaction behavior
            self.interactorStyle.OnLeftButtonDown()
        
        def on_right_button_press(obj, event):
            click_pos = self.interactor.GetEventPosition()
            self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)

            actor = self.picker.GetActor()
            if actor:
                self.selected_actor = actor
                self.original_color = actor.GetProperty().GetColor()
                self.context_menu()

        self.interactorStyle.AddObserver("LeftButtonPressEvent", pick_actor)
        self.interactorStyle.AddObserver("RightButtonPressEvent", on_right_button_press)
        self.interactor.AddObserver("KeyPressEvent", self.on_key_press)
        self.interactor.Initialize()
        
    def context_menu(self):
        if self.selected_actor:
            menu = QMenu(self)

            move_action = QAction('Move', self)
            move_action.triggered.connect(self.move_actor)
            menu.addAction(move_action)

            change_angle_action = QAction('Rotate', self)
            change_angle_action.triggered.connect(self.change_actor_angle)
            menu.addAction(change_angle_action)

            adjust_size_action = QAction('Adjust size', self)
            adjust_size_action.triggered.connect(self.adjust_actor_size)
            menu.addAction(adjust_size_action)
            
            remove_object_action = QAction('Remove', self)
            remove_object_action.triggered.connect(lambda: self.remove_actor(self.selected_actor))
            menu.addAction(remove_object_action)

            menu.exec_(QCursor.pos())
            
    def deselect(self):
        self.selected_actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
        self.vtkWidget.GetRenderWindow().Render()
        self.selected_actor = None

    def move_actor(self):
        if self.selected_actor:
            dialog = MoveActorDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                offsets = dialog.getValues()
                if offsets:
                    x_offset, y_offset, z_offset = offsets
                    position = self.selected_actor.GetPosition()
                    new_position = (position[0] + x_offset, position[1] + y_offset, position[2] + z_offset)
                    self.selected_actor.SetPosition(new_position)
                    self.vtkWidget.GetRenderWindow().Render()
                    
                    self.deselect()

    def adjust_actor_size(self):
        if self.selected_actor:
            scale_factor, ok = QInputDialog.getDouble(self, "Adjust size", "Scale:", 1.0, 0.01, 100.0, 2)
            if ok:
                self.selected_actor.SetScale(scale_factor, scale_factor, scale_factor)
                self.vtkWidget.GetRenderWindow().Render()
                
                self.deselect()

    def change_actor_angle(self):
        if self.selected_actor:
            dialog = AngleDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                angles = dialog.getValues()
                if angles:
                    angle_x, angle_y, angle_z = angles
                    self.selected_actor.RotateX(angle_x)
                    self.selected_actor.RotateY(angle_y)
                    self.selected_actor.RotateZ(angle_z)
                    self.vtkWidget.GetRenderWindow().Render()
                    
                    self.deselect()

    def on_key_press(self, obj, event):
        key = self.interactor.GetKeySym()
        if key == 'Escape' and self.selected_actor:
            # Reset the selected actor's color
            self.selected_actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
            self.vtkWidget.GetRenderWindow().Render()
            self.selected_actor = None
        elif key == 'Return' and self.selected_actor:
            self.interactorStyle.OnRotate()
        self.interactorStyle.OnKeyPress()
    
    def align_view_by_axis(self, axis: str):
        align_view_by_axis(axis, self.renderer, self.vtkWidget)

            
    def parse_vtk_polydata_and_populate_tree(self, vtk_filename, tree_model, rootItem):
        reader = vtkGenericDataObjectReader()
        reader.SetFileName(vtk_filename)
        reader.Update()
        
        data = reader.GetOutput()
        if not data.IsA("vtkUnstructuredGrid"):
            return
                
        unstructuredGrid = vtkUnstructuredGrid.SafeDownCast(data)

        pointsItem = QStandardItem("Points")
        for i in range(unstructuredGrid.GetNumberOfPoints()):
            point = unstructuredGrid.GetPoint(i)
            pointItem = QStandardItem(f"Point {i}: ({point[0]:.3f}, {point[1]:.3f}, {point[2]:.3f})")
            pointsItem.appendRow(pointItem)
        
        cellsItem = QStandardItem("Cells")
        for i in range(unstructuredGrid.GetNumberOfCells()):
            cell = unstructuredGrid.GetCell(i)
            cellType = vtkCellTypes.GetClassNameFromTypeId(cell.GetCellType())
            cellPoints = cell.GetPointIds()
            cellPointsStr = ', '.join([str(cellPoints.GetId(j)) for j in range(cellPoints.GetNumberOfIds())])
            cellItem = QStandardItem(f"Cell {i} ({cellType}): Points [{cellPointsStr}]")
            cellsItem.appendRow(cellItem)
            
        rootItem.appendRow(pointsItem)
        rootItem.appendRow(cellsItem)
        tree_model.appendRow(rootItem)
        
        return data
        
    
    def save_scene(self, logConsole, fontColor, actors_file='scene_actors_meshTab.vtk', camera_file='scene_camera_meshTab.json'):
        save_scene(self.renderer, logConsole, fontColor, actors_file, camera_file)
            
            
    def load_scene(self, logConsole, fontColor, actors_file='scene_actors_meshTab.vtk', camera_file='scene_camera_meshTab.json'):
        load_scene(self.vtkWidget, self.renderer, logConsole, fontColor, actors_file, camera_file)
        
    
    def clear_scene_and_tree_view(self):
        self.erase_all_from_tree_view()
        self.remove_all_actors()

        self.undo_stack.clear()
        self.redo_stack.clear()
        self.object_idx = 0
