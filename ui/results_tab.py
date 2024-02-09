from PyQt5.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QComboBox,
    QMessageBox,
    QLabel,
    QLineEdit,
    QFormLayout,
    QGroupBox,
    QFileDialog,
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from mesh_renderer import MeshRenderer
from hdf5handler import HDF5Handler


class ResultsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        # Matplotlib plot
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas, 2)

    def ColorBar(self, mesh_renderer):
        # Create a color map based on the mesh_renderer's colors
        self.colormap = plt.cm.ScalarMappable(cmap=plt.cm.viridis)
        self.colormap.set_array([])

        # Create a color bar next to the 3D plot
        self.color_bar = plt.colorbar(
            self.colormap, ax=self.canvas, fraction=0.046, pad=0.04)
        self.color_bar.set_label("Color Scale")

        # Show the color bar
        self.color_bar.ax.get_yaxis().labelpad = 15
        self.canvas.draw()

    def update_plot(self, hdf5_filename):
        # Clear the current plot
        self.figure.clear()

        # Load and render the mesh
        self.handler = HDF5Handler(hdf5_filename)
        self.mesh = self.handler.read_mesh_from_hdf5()
        self.renderer = MeshRenderer(self.mesh)
        self.renderer.ax = self.figure.add_subplot(111, projection="3d")
        self.renderer._setup_plot()
        self.canvas.mpl_connect("scroll_event", self.renderer.on_scroll)

        # Refresh the canvas
        self.canvas.draw()
