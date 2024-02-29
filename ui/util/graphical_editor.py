import vtk
from sys import stdout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from PyQt5.QtGui import QStandardItem, QIcon
from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtWidgets import(
    QFrame, QVBoxLayout, QHBoxLayout, 
    QPushButton, QDialog, QSpacerItem,
    QSizePolicy
)
from util import(
    PointDialog, LineDialog, SurfaceDialog, 
    SphereDialog, BoxDialog, CylinderDialog,
)
from util.util import align_view_by_axis, save_scene, load_scene


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
        
        self.eraserButton = QPushButton()
        self.eraserButton.setIcon(QIcon("icons/eraser.png"))
        self.eraserButton.setIconSize(QSize(32, 32))
        self.eraserButton.setFixedSize(QSize(32, 32))
        self.eraserButton.setToolTip('Erase all')
        
        # Add buttons to the toolbar layout
        self.toolbarLayout.addWidget(self.createPointButton)
        self.toolbarLayout.addWidget(self.createLineButton)
        self.toolbarLayout.addWidget(self.createSurfaceButton)
        self.toolbarLayout.addWidget(self.createSphereButton)
        self.toolbarLayout.addWidget(self.createBoxButton)
        self.toolbarLayout.addWidget(self.createCylinderButton)
        self.toolbarLayout.addWidget(self.eraserButton)
        
        self.spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.toolbarLayout.addSpacerItem(self.spacer)
        
        # Connect buttons to methods
        self.createPointButton.clicked.connect(self.create_point)
        self.createLineButton.clicked.connect(self.create_line)
        self.createSurfaceButton.clicked.connect(self.create_surface)
        self.createSphereButton.clicked.connect(self.create_sphere)
        self.createBoxButton.clicked.connect(self.create_box)
        self.createCylinderButton.clicked.connect(self.create_cylinder)
        self.eraserButton.clicked.connect(lambda: self.remove_all_actors())
        

    def setup_ui(self):
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.layout.addLayout(self.toolbarLayout)
        self.layout.addWidget(self.vtkWidget)
        self.setLayout(self.layout)

        self.renderer = vtk.vtkRenderer()
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
            points = vtk.vtkPoints()
            points.InsertNextPoint(x, y, z)
            
            # Create a PolyData object
            polyData = vtk.vtkPolyData()
            polyData.SetPoints(points)
            
            # Use vtkVertexGlyphFilter to make the points visible
            glyphFilter = vtk.vtkVertexGlyphFilter()
            glyphFilter.SetInputData(polyData)
            glyphFilter.Update()
            
            # Create a mapper and actor for the point
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(glyphFilter.GetOutputPort())
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetPointSize(5)    # Set the size of the point
            actor.GetProperty().SetColor(1, 0, 0)  # Set the color of the point (red)
            
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
            points = vtk.vtkPoints()
            line = vtk.vtkPolyLine()
            
            # The number of points in the polyline
            line.GetPointIds().SetNumberOfIds(len(values) // 3)
            
            # Add points and set ids
            for i in range(0, len(values), 3):
                point_id = points.InsertNextPoint(values[i], values[i + 1], values[i + 2])
                line.GetPointIds().SetId(i // 3, point_id)
            
            lines = vtk.vtkCellArray()
            lines.InsertNextCell(line)
            
            polyData = vtk.vtkPolyData()
            polyData.SetPoints(points)
            polyData.SetLines(lines)
            
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polyData)
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            
            self.renderer.AddActor(actor)
            self.vtkWidget.GetRenderWindow().Render()
            
            self.action_history.append(actor)
            self.redo_history.clear()

    
    def create_surface(self):
        dialog = SurfaceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.getValues()
            
            # Assuming values are flat [x1, y1, z1, x2, y2, z2, ...]
            if values is not None and len(values) >= 9:  # At least 3 points
                points = vtk.vtkPoints()
                polyData = vtk.vtkPolyData()
                
                # Insert points into vtkPoints
                for i in range(0, len(values), 3):
                    points.InsertNextPoint(values[i], values[i+1], values[i+2])
                
                polyData.SetPoints(points)
                
                # Use Delaunay2D to create the surface
                delaunay = vtk.vtkDelaunay2D()
                delaunay.SetInputData(polyData)
                delaunay.Update()
                
                # Create mapper and actor for the surface
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(delaunay.GetOutputPort())
                
                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                
                self.renderer.AddActor(actor)
                self.vtkWidget.GetRenderWindow().Render()
                
                # Add to history for undo/redo functionality
                self.action_history.append(actor)
                self.redo_history.clear()
    
    
    def create_sphere(self):
        dialog = SphereDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z, radius = dialog.getValues()
            
            sphereSource = vtk.vtkSphereSource()
            sphereSource.SetCenter(x, y, z)
            sphereSource.SetRadius(radius)
            sphereSource.Update()
            
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(sphereSource.GetOutputPort())
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            
            # Change history vars
            self.action_history.append(actor)
            self.redo_history.clear()
            
            self.renderer.AddActor(actor)
            self.vtkWidget.GetRenderWindow().Render()


    def create_box(self):
        dialog = BoxDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z, length, width, height = dialog.getValues()
            
            boxSource = vtk.vtkCubeSource()
            boxSource.SetBounds(x - length / 2., x + length / 2., 
                                y - width / 2., y + width / 2., 
                                z - height / 2., z + height / 2.)
            boxSource.Update()
            
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(boxSource.GetOutputPort())
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            
            # Change history vars
            self.action_history.append(actor)
            self.redo_history.clear()
            
            self.renderer.AddActor(actor)
            self.vtkWidget.GetRenderWindow().Render()


    def create_cylinder(self):
        dialog = CylinderDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.getValues() is not None:
            x, y, z, radius, height = dialog.getValues()
        
            cylinderSource = vtk.vtkCylinderSource()
            cylinderSource.SetRadius(radius)
            cylinderSource.SetHeight(height)
            cylinderSource.SetCenter(0, 0, 0)
            cylinderSource.Update()
            
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(cylinderSource.GetOutputPort())
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.SetPosition(x, y, z)
            
            # Change history vars
            self.action_history.append(actor)
            self.redo_history.clear()
            
            self.renderer.AddActor(actor)
            self.vtkWidget.GetRenderWindow().Render()


    def setup_axes(self):
        self.axes_actor = vtk.vtkAxesActor()
        self.axes_widget = vtk.vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(self.axes_actor)
        self.axes_widget.SetInteractor(self.vtkWidget.GetRenderWindow().GetInteractor())
        self.axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        self.axes_widget.EnabledOn()
        self.axes_widget.InteractiveOff()


    def remove_all_actors(self):
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        for i in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()
            self.renderer.RemoveActor(actor)
        
        self.vtkWidget.GetRenderWindow().Render()


    def display_mesh(self, mesh_file_path: str):
        vtk_file_path = mesh_file_path.replace('.msh', '.vtk')
        
        reader = vtk.vtkGenericDataObjectReader()
        reader.SetFileName(vtk_file_path)
        reader.Update()  # Make sure to update the reader to actually read the file
        
        if reader.IsFilePolyData():
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
        elif reader.IsFileUnstructuredGrid():
            mapper = vtk.vtkDataSetMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
        else:
            print("Unsupported dataset type", file=stdout)
            return

        # Remove all previous actors
        self.remove_all_actors()

        # Add new actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
        
        
    def setup_interaction(self):        
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.005)

        self.vtkWidget.GetRenderWindow().GetInteractor().SetPicker(self.picker)
        self.vtkWidget.installEventFilter(self) # Capturing mouse events
    
    
    def align_view_by_axis(self, axis: str):
        align_view_by_axis(axis, self.renderer, self.vtkWidget)

            
    def parse_vtk_polydata_and_populate_tree(self, vtk_file_path, tree_model):
        reader = vtk.vtkGenericDataObjectReader()
        reader.SetFileName(vtk_file_path)
        reader.Update()
        
        data = reader.GetOutput()
        if not data.IsA("vtkUnstructuredGrid"):
            print("Data is not an unstructured grid.", file=stdout)
            return
                
        unstructuredGrid = vtk.vtkUnstructuredGrid.SafeDownCast(data)

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
            cellType = vtk.vtkCellTypes.GetClassNameFromTypeId(cell.GetCellType())
            cellPoints = cell.GetPointIds()
            cellPointsStr = ', '.join([str(cellPoints.GetId(j)) for j in range(cellPoints.GetNumberOfIds())])
            cellItem = QStandardItem(f"Cell {i} ({cellType}): Points [{cellPointsStr}]")
            cellsItem.appendRow(cellItem)
            
    
    def save_scene(self, logConsole, actors_file='scene_actors_meshTab.vtk', camera_file='scene_camera_meshTab.json'):
        save_scene(self.renderer, logConsole, actors_file, camera_file)
            
            
    def load_scene(self, logConsole, actors_file='scene_actors_meshTab.vtk', camera_file='scene_camera_meshTab.json'):
        load_scene(self.vtkWidget, self.renderer, logConsole, actors_file, camera_file)

