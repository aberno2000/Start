import gmsh
from sys import stdout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from PyQt5.QtGui import QStandardItem, QIcon
from PyQt5.QtCore import QSize, pyqtSignal
from vtk import(
    vtkRenderer, vtkPoints, vtkPolyData, vtkVertexGlyphFilter, vtkPolyLine,
    vtkCellArray, vtkPolyDataMapper, vtkActor, vtkDelaunay2D, vtkSphereSource,
    vtkCubeSource, vtkCylinderSource, vtkAxesActor, vtkOrientationMarkerWidget,
    vtkGenericDataObjectReader, vtkDataSetMapper, vtkCellPicker, vtkUnstructuredGrid,
    vtkCellTypes
)
from PyQt5.QtWidgets import(
    QFrame, QVBoxLayout, QHBoxLayout, 
    QPushButton, QDialog, QSpacerItem,
    QSizePolicy, QMessageBox, QFileDialog,
    QMenu, QAction, QInputDialog
)
from PyQt5.QtGui import QCursor
from .util import(
    PointDialog, LineDialog, SurfaceDialog, 
    SphereDialog, BoxDialog, CylinderDialog,
    AngleDialog, MoveActorDialog
)
from util.util import align_view_by_axis, save_scene, load_scene
from .mesh_dialog import MeshDialog, CaptureGmshLog
from .styles import DEFAULT_ACTOR_COLOR, SELECTED_ACTOR_COLOR


class GraphicalEditor(QFrame):
    updateTreeSignal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_toolbar()
        self.setup_ui()
        self.setup_interaction()
        self.setup_axes()
        
        self.action_history = [] # Track added actors
        self.redo_history = []   # Track undone actors for redo
        
    
    def undo_action_actor(self):
        if self.action_history:
            actor = self.action_history.pop()
            self.renderer.RemoveActor(actor)
            self.redo_history.append(actor)
            self.vtkWidget.GetRenderWindow().Render()


    def redo_action_actor(self):
        if self.redo_history:
            actor = self.redo_history.pop()
            self.action_history.append(actor)
            self.renderer.AddActor(actor)
            self.vtkWidget.GetRenderWindow().Render()
        
    
    def setup_toolbar(self):
        self.layout = QVBoxLayout()  # Main layout
        self.toolbarLayout = QHBoxLayout()  # Layout for the toolbar
        
        # Create buttons for the toolbar       
        self.createPointButton = QPushButton()
        self.createPointButton.setIcon(QIcon("icons/point.png"))
        self.createPointButton.setIconSize(QSize(32, 32))
        self.createPointButton.setFixedSize(QSize(32, 32))
        self.createPointButton.setToolTip('Dot')
        
        self.createLineButton = QPushButton()
        self.createLineButton.setIcon(QIcon("icons/line.png"))
        self.createLineButton.setIconSize(QSize(32, 32))
        self.createLineButton.setFixedSize(QSize(32, 32))
        self.createLineButton.setToolTip('Line')
        
        self.createSurfaceButton = QPushButton()
        self.createSurfaceButton.setIcon(QIcon("icons/surface.png"))
        self.createSurfaceButton.setIconSize(QSize(32, 32))
        self.createSurfaceButton.setFixedSize(QSize(32, 32))
        self.createSurfaceButton.setToolTip('Surface')
        
        self.createSphereButton = QPushButton()
        self.createSphereButton.setIcon(QIcon("icons/sphere.png"))
        self.createSphereButton.setIconSize(QSize(32, 32))
        self.createSphereButton.setFixedSize(QSize(32, 32))
        self.createSphereButton.setToolTip('Sphere')
        
        self.createBoxButton = QPushButton()
        self.createBoxButton.setIcon(QIcon("icons/box.png"))
        self.createBoxButton.setIconSize(QSize(32, 32))
        self.createBoxButton.setFixedSize(QSize(32, 32))
        self.createBoxButton.setToolTip('Box')
        
        self.createCylinderButton = QPushButton()
        self.createCylinderButton.setIcon(QIcon("icons/cylinder.png"))
        self.createCylinderButton.setIconSize(QSize(32, 32))
        self.createCylinderButton.setFixedSize(QSize(32, 32))
        self.createCylinderButton.setToolTip('Cylinder')
        
        self.uploadCustomButton = QPushButton()
        self.uploadCustomButton.setIcon(QIcon("icons/custom.png"))
        self.uploadCustomButton.setIconSize(QSize(32, 32))
        self.uploadCustomButton.setFixedSize(QSize(32, 32))
        self.uploadCustomButton.setToolTip('Custom')
        
        # Add buttons to the toolbar layout
        self.toolbarLayout.addWidget(self.createPointButton)
        self.toolbarLayout.addWidget(self.createLineButton)
        self.toolbarLayout.addWidget(self.createSurfaceButton)
        self.toolbarLayout.addWidget(self.createSphereButton)
        self.toolbarLayout.addWidget(self.createBoxButton)
        self.toolbarLayout.addWidget(self.createCylinderButton)
        self.toolbarLayout.addWidget(self.uploadCustomButton)
        
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
            
            self.renderer.AddActor(actor)
            self.vtkWidget.GetRenderWindow().Render()
            
            self.action_history.append(actor)
            self.redo_history.clear()
            
            self.updateTreeSignal.emit('Point', f'Point: ({x}, {y}, {z})')
            
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
            
            self.renderer.AddActor(actor)
            self.vtkWidget.GetRenderWindow().Render()
            
            self.action_history.append(actor)
            self.redo_history.clear()
            
            line_str = 'Line'
            self.updateTreeSignal.emit(line_str, '\n'.join(points_str_list))

    
    def create_surface(self):
        dialog = SurfaceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.getValues()
            
            # Assuming values are flat [x1, y1, z1, x2, y2, z2, ...]
            if values is not None and len(values) >= 9:  # At least 3 points
                points = vtkPoints()
                polyData = vtkPolyData()
                points_str_list = []
                
                # Insert points into vtkPoints
                pid = 1
                for i in range(0, len(values), 3):
                    points.InsertNextPoint(values[i], values[i+1], values[i+2])
                    points_str_list.append(f'Point{pid}: ({values[i]}, {values[i+1]}, {values[i+2]})')
                    pid += 1
                
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
                
                self.renderer.AddActor(actor)
                self.vtkWidget.GetRenderWindow().Render()
                
                # Add to history for undo/redo functionality
                self.action_history.append(actor)
                self.redo_history.clear()
                
                surface_str = 'Surface'
                self.updateTreeSignal.emit(surface_str, '\n'.join(points_str_list))
    
    
    def create_sphere(self):
        dialog = SphereDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z, radius = dialog.getValues()
            sphere_data_str = []
            sphere_data_str.append(f'Center: ({x}, {y}, {z})')
            sphere_data_str.append(f'Radius: {radius}')
            
            sphereSource = vtkSphereSource()
            sphereSource.SetCenter(x, y, z)
            sphereSource.SetRadius(radius)
            sphereSource.Update()
            
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(sphereSource.GetOutputPort())
            
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
            
            # Change history vars
            self.action_history.append(actor)
            self.redo_history.clear()
            
            self.renderer.AddActor(actor)
            self.vtkWidget.GetRenderWindow().Render()
            
            center_str = 'Sphere'
            self.updateTreeSignal.emit(center_str, '\n'.join(sphere_data_str))


    def create_box(self):
        dialog = BoxDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z, length, width, height = dialog.getValues()
            box_data_str = []
            box_data_str.append(f'Primary Point: ({x}, {y}, {z})')
            box_data_str.append(f'Length: {length}')
            box_data_str.append(f'Width: {width}')
            box_data_str.append(f'Height: {height}')
            
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
            
            # Change history vars
            self.action_history.append(actor)
            self.redo_history.clear()
            
            self.renderer.AddActor(actor)
            self.vtkWidget.GetRenderWindow().Render()
            
            box_str = 'Box'
            self.updateTreeSignal.emit(box_str, '\n'.join(box_data_str))


    def create_cylinder(self):
        dialog = CylinderDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z, radius, height = dialog.getValues()
            cylinder_data_str = []
            cylinder_data_str.append(f'Primary Point: ({x}, {y}, {z})')
            cylinder_data_str.append(f'Radius: {radius}')
            cylinder_data_str.append(f'Height: {height}')
        
            cylinderSource = vtkCylinderSource()
            cylinderSource.SetRadius(radius)
            cylinderSource.SetHeight(height)
            cylinderSource.SetCenter(x, y, z)
            cylinderSource.Update()
            
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(cylinderSource.GetOutputPort())
            
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)
            
            # Change history vars
            self.action_history.append(actor)
            self.redo_history.clear()
            
            self.renderer.AddActor(actor)
            self.vtkWidget.GetRenderWindow().Render()
            
            cylinder_str = 'Cylinder'
            self.updateTreeSignal.emit(cylinder_str, '\n'.join(cylinder_data_str))
            
    
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
            dialog = MeshDialog(self)  # Assuming MeshDialog is implemented to get mesh_size and mesh_dim
            if dialog.exec() == QDialog.Accepted:
                mesh_size, mesh_dim = dialog.get_values()
                try:
                    mesh_size = float(mesh_size)
                    mesh_dim = int(mesh_dim)
                    if mesh_dim not in [2, 3]:
                        raise ValueError("Mesh dimensions must be 2 or 3.")
                    converted_file_name = self.convert_stp_to_msh(file_name, mesh_size, mesh_dim)
                    if converted_file_name:
                        actor = self.add_custom(converted_file_name)
                except ValueError as e:
                    QMessageBox.warning(self, "Invalid Input", str(e))
            else:
                QMessageBox.critical(self, "Error", "Dialog was closed by user. Invalid mesh size or mesh dimensions.")
        elif file_name.endswith('.msh') or file_name.endswith('.vtk'):
            actor = self.add_custom(file_name)
            
        self.action_history.append(actor)
        self.redo_history.clear()
            
    
    def convert_stp_to_msh(self, file_path, mesh_size, mesh_dim):        
        original_stdout = stdout  # Save a reference to the original standard output
        redirected_output = CaptureGmshLog()
        stdout = redirected_output  # Redirect stdout to capture Gmsh logs

        try:
            gmsh.initialize()
            gmsh.model.add("model")
            gmsh.model.occ.importShapes(file_path)
            gmsh.model.occ.synchronize()
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)

            if mesh_dim == 2:
                gmsh.model.mesh.generate(2)
            elif mesh_dim == 3:
                gmsh.model.mesh.generate(3)

            output_file = file_path.replace(".stp", ".msh")
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
        
    
    def add_actor(self, actor):
        self.renderer.AddActor(actor)
        self.vtkWidget.GetRenderWindow().Render()
        
    
    def remove_actor(self, actor):
        self.renderer.RemoveActor(actor)
        self.vtkWidget.GetRenderWindow().Render()
        

    def remove_all_actors(self):
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        for i in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()
            self.renderer.RemoveActor(actor)
        
        self.vtkWidget.GetRenderWindow().Render()


    def display_mesh(self, mesh_file_path: str):
        vtk_file_path = mesh_file_path.replace('.msh', '.vtk')
        
        reader = vtkGenericDataObjectReader()
        reader.SetFileName(vtk_file_path)
        reader.Update()  # Make sure to update the reader to actually read the file
        
        if reader.IsFilePolyData():
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
        elif reader.IsFileUnstructuredGrid():
            mapper = vtkDataSetMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
        else:
            print("Unsupported dataset type", file=stdout)
            return

        # Add new actor
        actor = vtkActor()
        actor.SetMapper(mapper)
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
        
        return actor
    

    def add_custom(self, mesh_file_path: str):
        vtk_file_path = mesh_file_path.replace('.msh', '.vtk')
        
        reader = vtkGenericDataObjectReader()
        reader.SetFileName(vtk_file_path)
        reader.Update()
        
        if reader.IsFilePolyData():
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
            geometry_type = "PolyData"
        elif reader.IsFileUnstructuredGrid():
            mapper = vtkDataSetMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
            geometry_type = "UnstructuredGrid"
        else:
            print("Unsupported dataset type", file=stdout)
            return None

        actor = vtkActor()
        actor.SetMapper(mapper)
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
        
        geometry_info = f"{geometry_type} from {vtk_file_path}"
        self.updateTreeSignal.emit(geometry_type, geometry_info)
        
        return actor
        
        
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
            self.interactorStyle.OnRightButtonDown()

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

            
    def parse_vtk_polydata_and_populate_tree(self, vtk_file_path, tree_model):
        reader = vtkGenericDataObjectReader()
        reader.SetFileName(vtk_file_path)
        reader.Update()
        
        data = reader.GetOutput()
        if not data.IsA("vtkUnstructuredGrid"):
            print("Data is not an unstructured grid.", file=stdout)
            return
                
        unstructuredGrid = vtkUnstructuredGrid.SafeDownCast(data)

        pointsItem = QStandardItem("Points")
        tree_model.appendRow(pointsItem)
        
        for i in range(unstructuredGrid.GetNumberOfPoints()):
            point = unstructuredGrid.GetPoint(i)
            pointItem = QStandardItem(f"Point {i}: ({point[0]:.3f}, {point[1]:.3f}, {point[2]:.3f})")
            pointsItem.appendRow(pointItem)
        
        cellsItem = QStandardItem("Cells")
        tree_model.appendRow(cellsItem)
        
        for i in range(unstructuredGrid.GetNumberOfCells()):
            cell = unstructuredGrid.GetCell(i)
            cellType = vtkCellTypes.GetClassNameFromTypeId(cell.GetCellType())
            cellPoints = cell.GetPointIds()
            cellPointsStr = ', '.join([str(cellPoints.GetId(j)) for j in range(cellPoints.GetNumberOfIds())])
            cellItem = QStandardItem(f"Cell {i} ({cellType}): Points [{cellPointsStr}]")
            cellsItem.appendRow(cellItem)
        
        return data
        
    
    def save_scene(self, logConsole, fontColor, actors_file='scene_actors_meshTab.vtk', camera_file='scene_camera_meshTab.json'):
        save_scene(self.renderer, logConsole, fontColor, actors_file, camera_file)
            
            
    def load_scene(self, logConsole, fontColor, actors_file='scene_actors_meshTab.vtk', camera_file='scene_camera_meshTab.json'):
        load_scene(self.vtkWidget, self.renderer, logConsole, fontColor, actors_file, camera_file)

