import vtk
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from util.mesh_renderer import MeshRenderer
from data.hdf5handler import HDF5Handler
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from util.util import align_view_by_axis


class ResultsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setup_ui()
        self.setup_axes()


    def setup_axes(self):
        self.axes_actor = vtk.vtkAxesActor()
        self.axes_widget = vtk.vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(self.axes_actor)
        self.axes_widget.SetInteractor(self.vtkWidget.GetRenderWindow().GetInteractor())
        self.axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        self.axes_widget.EnabledOn()
        self.axes_widget.InteractiveOff()
        

    def setup_ui(self):
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.layout.addWidget(self.vtkWidget)

        self.renderer = vtk.vtkRenderer()
        self.renderer.SetLayer(0)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)

        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.interactorStyle = vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(self.interactorStyle)
        self.interactor.Initialize()

    
    def add_colorbar(self, title='Color Scale'):
        scalarBar = vtk.vtkScalarBarActor()
        scalarBar.SetTitle(title)
        scalarBar.SetNumberOfLabels(4)
        
        # Assuming you have a lookup table set up for your mesh actor
        scalarBar.SetLookupTable(self.actor.GetMapper().GetLookupTable())
        
        self.renderer.AddActor2D(scalarBar)
        self.vtkWidget.GetRenderWindow().Render()


    def update_plot(self, hdf5_filename):
        # Clear any existing actors from the renderer before updating
        self.clear_plot()

        # Load the mesh data from the HDF5 file
        self.handler = HDF5Handler(hdf5_filename)
        self.mesh = self.handler.read_mesh_from_hdf5()
        self.mesh_renderer = MeshRenderer(self.mesh)
        self.mesh_renderer.renderer = self.renderer
        self.mesh_renderer.render_mesh()
        self.mesh_renderer.add_scalar_bar()
        
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
       
        
    def clear_plot(self):
        self.renderer.RemoveAllViewProps()
        self.vtkWidget.GetRenderWindow().Render()
        
    
    def align_view_by_axis(self, axis: str):
        align_view_by_axis(axis, self.renderer, self.vtkWidget)
