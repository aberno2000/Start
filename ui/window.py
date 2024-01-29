import sys
from PyQt5.QtWidgets import (
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox,
    QLabel,
    QLineEdit,
    QFormLayout,
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from subprocess import run
from hdf5handler import HDF5Handler
from mesh_renderer import MeshRenderer


def compile_cpp():
    run(["./compile.sh"], check=True)


def run_cpp(args: str) -> None:
    cmd = ["./main"] + args.split()
    run(cmd, check=True)


def show_mesh(hdf5_filename: str) -> None:
    handler = HDF5Handler(hdf5_filename)
    mesh = handler.read_mesh_from_hdf5()
    renderer = MeshRenderer(mesh)
    renderer.show()


class WindowApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Particle Collision Simulator")
        self.setGeometry(100, 100, 1200, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create a form layout for inputs
        form_layout = QFormLayout()

        # Particle count input
        self.particles_count_input = QLineEdit()
        form_layout.addRow(QLabel("Particles Count:"), self.particles_count_input)

        # Time step input
        self.time_step_input = QLineEdit()
        form_layout.addRow(QLabel("Time Step:"), self.time_step_input)

        # Time interval input
        self.time_interval_input = QLineEdit()
        form_layout.addRow(QLabel("Time Interval:"), self.time_interval_input)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.upload_button = QPushButton("Upload")
        self.upload_button.clicked.connect(self.upload_file)
        buttons_layout.addWidget(self.upload_button)

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_simulation)
        buttons_layout.addWidget(self.run_button)

        self.help_button = QPushButton("Help")
        self.help_button.clicked.connect(self.show_help)
        buttons_layout.addWidget(self.help_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.exit)
        buttons_layout.addWidget(self.exit_button)

        # Combine form layout and buttons layout into a vertical layout
        left_layout = QVBoxLayout()
        left_layout.addLayout(form_layout)
        left_layout.addLayout(buttons_layout)

        # Matplotlib plot
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        # Create a horizontal layout to include everything
        h_layout = QHBoxLayout(central_widget)
        h_layout.addLayout(left_layout, 1)
        h_layout.addWidget(self.canvas, 2)  # Give more space to the canvas

        # Set the central widget's layout
        central_widget.setLayout(h_layout)

        self.file_path = ""
        # compile_cpp()

    def upload_file(self):
        self.file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Mesh File", "", "Mesh files (*.msh)"
        )

    def run_simulation(self):
        if self.file_path:
            # Retrieve user input
            particles_count = self.particles_count_input.text()
            time_step = self.time_step_input.text()
            time_interval = self.time_interval_input.text()

            # Validate input
            if not (
                particles_count.isdigit()
                and time_step.replace(".", "", 1).isdigit()
                and time_interval.replace(".", "", 1).isdigit()
            ):
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Please enter valid numeric values for particles count, time step, and time interval.",
                )
                return

            hdf5_filename = self.file_path.replace(".msh", ".hdf5")
            args = f"{particles_count} {time_step} {time_interval} {self.file_path}"
            run_cpp(args)
            self.update_plot(hdf5_filename)
        else:
            QMessageBox.warning(self, "Warning", "Please upload a .msh file first.")

    def ColorBar(self, mesh_renderer):
        # Create a color map based on the mesh_renderer's colors
        colormap = plt.cm.ScalarMappable(cmap=plt.cm.viridis)
        colormap.set_array([])

        # Create a color bar next to the 3D plot
        color_bar = plt.colorbar(colormap, ax=self.canvas, fraction=0.046, pad=0.04)
        color_bar.set_label("Color Scale")

        # Show the color bar
        color_bar.ax.get_yaxis().labelpad = 15
        self.canvas.draw()

    def update_plot(self, hdf5_filename):
        # Clear the current plot
        self.figure.clear()

        # Load and render the mesh
        handler = HDF5Handler(hdf5_filename)
        mesh = handler.read_mesh_from_hdf5()
        renderer = MeshRenderer(mesh)
        renderer.ax = self.figure.add_subplot(111, projection="3d")
        renderer._setup_plot()
        self.canvas.mpl_connect("scroll_event", renderer.on_scroll)

        # Refresh the canvas
        self.canvas.draw()

    def show_help(self):
        QMessageBox.information(
            self,
            "Help",
            "This is help message. Don't forget to write a desc to ur app here pls!!!",
        )

    def exit(self):
        sys.exit(0)
