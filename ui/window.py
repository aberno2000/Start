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
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from subprocess import run
from hdf5handler import HDF5Handler
from mesh_renderer import MeshRenderer


def run_cpp(args: str) -> None:
    run(["./compile.sh"], check=True)
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

        # Create a horizontal layout
        h_layout = QHBoxLayout(central_widget)

        # Create a vertical layout for inputs and buttons
        input_layout = QVBoxLayout()

        # Particle count input
        self.particles_count_label = QLabel("Particles Count:")
        input_layout.addWidget(self.particles_count_label)
        self.particles_count_input = QLineEdit()
        input_layout.addWidget(self.particles_count_input)

        # Time step input
        self.time_step_label = QLabel("Time Step:")
        input_layout.addWidget(self.time_step_label)
        self.time_step_input = QLineEdit()
        input_layout.addWidget(self.time_step_input)

        # Time interval input
        self.time_interval_label = QLabel("Time Interval:")
        input_layout.addWidget(self.time_interval_label)
        self.time_interval_input = QLineEdit()
        input_layout.addWidget(self.time_interval_input)

        # Upload .msh file button
        self.upload_button = QPushButton("Upload")
        self.upload_button.clicked.connect(self.upload_file)
        input_layout.addWidget(self.upload_button)

        # Run button
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_simulation)
        input_layout.addWidget(self.run_button)

        # Help button
        self.help_button = QPushButton("Help")
        self.help_button.clicked.connect(self.show_help)
        input_layout.addWidget(self.help_button)

        # Exit button
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.exit)
        input_layout.addWidget(self.exit_button)

        # Add input layout to the horizontal layout
        h_layout.addLayout(input_layout)

        # Matplotlib plot
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        h_layout.addWidget(self.canvas)

        self.file_path = ""

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
