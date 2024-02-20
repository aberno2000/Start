from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
)
import vtk
from mesh_renderer import MeshRenderer
from hdf5handler import HDF5Handler
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


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
        self.renderer.SetBackground(0.1, 0.2, 0.5) # Light blue
        self.renderer.SetLayer(0)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)

        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
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
        self.vtkWidget.GetRenderWindow().Render()
       
        
    def clear_plot(self):
        self.renderer.RemoveAllViewProps()
        self.vtkWidget.GetRenderWindow().Render()
