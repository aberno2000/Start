import vtk
from sys import stdout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import(
    QFrame, QVBoxLayout, QHBoxLayout, 
    QPushButton, QDialog, QSpacerItem,
    QSizePolicy
)
from PyQt5.QtGui import QStandardItem, QMouseEvent, QKeyEvent, QIcon
from PyQt5.QtCore import Qt, QSize
from util import SphereDialog, BoxDialog, CylinderDialog


class GraphicalEditor(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_toolbar()
        self.setup_ui()
        self.setup_interaction()
        self.setup_axes()
        self.selected_actor = None
        
        self.action_history = [] # Track added actors
        self.redo_history = []   # Track undone actors for redo
        
    
    def undo_action(self):
        if self.action_history:
            actor = self.action_history.pop()
            self.renderer.RemoveActor(actor)
            self.redo_history.append(actor)
            self.vtkWidget.GetRenderWindow().Render()


    def redo_action(self):
        if self.redo_history:
            actor = self.redo_history.pop()
            self.action_history.append(actor)
            self.renderer.AddActor(actor)
            self.vtkWidget.GetRenderWindow().Render()
        
    
    def setup_toolbar(self):
        self.layout = QVBoxLayout()  # Main layout
        self.toolbarLayout = QHBoxLayout()  # Layout for the toolbar
        
        # Create buttons for the toolbar        
        self.createSphereButton = QPushButton()
        self.createSphereButton.setIcon(QIcon("imgs/sphere.png"))
        self.createSphereButton.setIconSize(QSize(32, 32))
        self.createSphereButton.setFixedSize(QSize(32, 32))
        self.createBoxButton = QPushButton()
        self.createBoxButton.setIcon(QIcon("imgs/box.png"))
        self.createBoxButton.setIconSize(QSize(32, 32))
        self.createBoxButton.setFixedSize(QSize(32, 32))
        self.createCylinderButton = QPushButton()
        self.createCylinderButton.setIcon(QIcon("imgs/cylinder.png"))
        self.createCylinderButton.setIconSize(QSize(32, 32))
        self.createCylinderButton.setFixedSize(QSize(32, 32))
        
        # Add buttons to the toolbar layout
        self.toolbarLayout.addWidget(self.createSphereButton)
        self.toolbarLayout.addWidget(self.createBoxButton)
        self.toolbarLayout.addWidget(self.createCylinderButton)
        
        self.spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.toolbarLayout.addSpacerItem(self.spacer)
        
        # Connect buttons to methods
        self.createSphereButton.clicked.connect(self.create_sphere)
        self.createBoxButton.clicked.connect(self.create_box)
        self.createCylinderButton.clicked.connect(self.create_cylinder)
        

    def setup_ui(self):
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.layout.addLayout(self.toolbarLayout)
        self.layout.addWidget(self.vtkWidget)
        self.setLayout(self.layout)

        self.renderer = vtk.vtkRenderer()        
        self.renderer.SetBackground(0.1, 0.2, 0.5) # Light blue
        self.renderer.SetLayer(0)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        
    
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
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        for i in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()
            self.renderer.RemoveActor(actor)

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


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            print('Ctrl+Z pressed')
            self.undo_action()
        elif event.key() == Qt.Key_Y and event.modifiers() & Qt.ControlModifier:
            self.redo_action()
        else:
            super().keyPressEvent(event)


    def eventFilter(self, source, event):
        if event.type() == QMouseEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self.on_mouse_press(event)
        elif event.type() == QKeyEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.deselect_actor()
        return super(GraphicalEditor, self).eventFilter(source, event)


    def on_mouse_press(self, event):
        click_pos = self.vtkWidget.mapFromGlobal(event.globalPos())
        self.picker.Pick(click_pos.x(), click_pos.y(), 0, self.renderer)

        pickedCellID = self.picker.GetCellId()
        pickedActor = self.picker.GetActor()
        if pickedCellID != -1 and pickedActor:
            # Red color when selected
            self.highlight_cell(pickedActor, pickedCellID)
            
    
    def highlight_cell(self, actor, cellId):
        if self.selected_actor:
            # Remove previously selected actor's highlight
            self.renderer.RemoveActor(self.selected_actor)
            self.selected_actor = None
        
        # Create an IdList and add the cell ID
        idList = vtk.vtkIdList()
        idList.InsertNextId(cellId)
        
        # Use vtkExtractCells to extract the specified cell
        cellExtractor = vtk.vtkExtractCells()
        cellExtractor.SetInputData(actor.GetMapper().GetInput())
        cellExtractor.SetCellList(idList)  # Use SetCellList instead of AddCellId
        cellExtractor.Update()
        
        # Map the extracted cell and create an actor for it
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputConnection(cellExtractor.GetOutputPort())
        
        self.selected_actor = vtk.vtkActor()
        self.selected_actor.SetMapper(mapper)
        self.selected_actor.GetProperty().SetColor(1, 0, 0)  # Highlight with red
        self.selected_actor.GetProperty().SetLineWidth(2)
        
        # Add the actor for the highlighted cell to the renderer
        self.renderer.AddActor(self.selected_actor)
        self.vtkWidget.GetRenderWindow().Render()


    def select_actor(self, actor):
        # Reset prev selection
        if self.selected_actor is not None:
            self.deselect_actor()
        self.selected_actor = actor
        actor.GetProperty().SetColor(1, 0, 0)
        self.vtkWidget.GetRenderWindow().Render()
    

    def deselect_actor(self):
        # Reset selection
        if self.selected_actor:
            self.selected_actor.GetProperty().DeepCopy(vtk.vtkProperty())
            self.vtkWidget.GetRenderWindow().Render()
            self.selected_actor = None
    
    
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

