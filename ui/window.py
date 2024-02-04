from PyQt5.QtWidgets import (
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QComboBox,
    QMessageBox,
    QLabel,
    QLineEdit,
    QFormLayout,
    QTabWidget,
    QGroupBox,
    QFileDialog,
    QProgressBar,
)
from PyQt5 import QtCore
from PyQt5.QtCore import QProcess
import sys
import gmsh
from multiprocessing import cpu_count
from platform import platform
from time import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from converter import Converter
from subprocess import run, Popen
from hdf5handler import HDF5Handler
from mesh_renderer import MeshRenderer

def get_thread_count():
    return cpu_count()

def get_os_info():
    return platform()

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
        self.converter = Converter()

        # Create tab widget and tabs
        self.tab_widget = QTabWidget()
        self.mesh_tab = QWidget()
        self.results_tab = QWidget()
        self.config_tab = QWidget()

        # Setup Tabs
        self.setup_tabs()

        # Set the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.tab_widget)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.process = QProcess(self)
        self.process.finished.connect(self.on_finished)

        self.file_path = ""

    def setup_tabs(self):
        self.tab_widget.addTab(self.mesh_tab, "Mesh")
        self.tab_widget.addTab(self.results_tab, "Results")
        self.tab_widget.addTab(self.config_tab, "Config")

        self.setup_mesh_tab()
        self.setup_results_tab()
        self.setup_config_tab()

    def setup_mesh_tab(self):
        layout = QVBoxLayout()
        self.mesh_tab.setLayout(layout)

        self.launch_gmsh_button = QPushButton("Launch GMSH")
        self.launch_gmsh_button.clicked.connect(self.launch_gmsh)
        layout.addWidget(self.launch_gmsh_button)
        
        # TODO: implement

    def launch_gmsh(self):
        gmsh.initialize()
        Popen(["gmsh"])
        gmsh.finalize()

    def setup_results_tab(self):
        # Matplotlib plot
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        self.results_tab.setLayout(layout)
        layout.addWidget(self.canvas, 2)
    
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

    def setup_config_tab(self):
        layout = QVBoxLayout()

        # Particles section
        particles_group_box = QGroupBox("Particles")
        particles_layout = QFormLayout()

        self.particles_count_input = QLineEdit()
        particles_layout.addRow(QLabel("Count:"), self.particles_count_input)

        # Comboboxes for particle types
        self.projective_input = QComboBox()
        self.gas_input = QComboBox()
        projective_particles = ["Ti", "Al", "Sn", "W", "Au", "Cu", "Ni", "Ag"]
        gas_particles = ["Ar", "N", "He"]
        self.projective_input.addItems(projective_particles)
        self.gas_input.addItems(gas_particles)
        particles_layout.addRow(QLabel("Projective:"), self.projective_input)
        particles_layout.addRow(QLabel("Gas:"), self.gas_input)

        particles_group_box.setLayout(particles_layout)
        layout.addWidget(particles_group_box)

        # Scattering model section
        scattering_group_box = QGroupBox("Scattering Model")
        scattering_layout = QVBoxLayout()

        self.model_input = QComboBox()
        self.model_input.addItems(["HS", "VHS", "VSS"])
        scattering_layout.addWidget(self.model_input)

        scattering_group_box.setLayout(scattering_layout)
        layout.addWidget(scattering_group_box)

        # Simulation Parameters section with units
        line_edit_width = 175
        combobox_width = 85
        simulation_group_box = QGroupBox("Simulation Parameters")
        simulation_layout = QFormLayout()
        
        # Thread count
        self.thread_count_input = QLineEdit()
        self.thread_count_available = QLabel(f"Your {get_os_info()} has {get_thread_count()} threads")
        thread_count_layout = QHBoxLayout()
        thread_count_layout.addWidget(self.thread_count_input)
        thread_count_layout.addWidget(self.thread_count_available, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        simulation_layout.addRow(QLabel("Thread count:"), thread_count_layout)
        self.thread_count_input.setFixedWidth(line_edit_width)

        # Time Step with units
        self.time_step_input = QLineEdit()
        self.time_step_units = QComboBox()
        self.time_step_units.addItems(["ns", "μs", "ms", "s", "min"])
        self.time_step_units.setCurrentText("ms")
        self.time_step_converted = QLabel("0.0 s")  # Default display 0s
        time_step_layout = QHBoxLayout()
        time_step_layout.addWidget(self.time_step_input)
        time_step_layout.addWidget(
            self.time_step_units, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        time_step_layout.addWidget(
            self.time_step_converted, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        simulation_layout.addRow(QLabel("Time Step:"), time_step_layout)
        self.time_step_input.setFixedWidth(line_edit_width)
        self.time_step_units.setFixedWidth(combobox_width)

        # Simulation time with units
        self.simulation_time_input = QLineEdit()
        self.simulation_time_units = QComboBox()
        self.simulation_time_units.addItems(["ns", "μs", "ms", "s", "min"])
        self.simulation_time_units.setCurrentText("s")
        self.simulation_time_converted = QLabel("0.0 s")  # Default display 0s
        simulation_time_layout = QHBoxLayout()
        simulation_time_layout.addWidget(self.simulation_time_input)
        simulation_time_layout.addWidget(
            self.simulation_time_units, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        simulation_time_layout.addWidget(
            self.simulation_time_converted, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        simulation_layout.addRow(
            QLabel("Simulation Time:"), simulation_time_layout)
        self.simulation_time_input.setFixedWidth(line_edit_width)
        self.simulation_time_units.setFixedWidth(combobox_width)

        # Temperature with units
        self.temperature_input = QLineEdit()
        self.temperature_units = QComboBox()
        self.temperature_units.addItems(["K", "F", "C"])
        self.temperature_converted = QLabel("0.0 K")
        temperature_layout = QHBoxLayout()
        temperature_layout.addWidget(self.temperature_input)
        temperature_layout.addWidget(
            self.temperature_units, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        temperature_layout.addWidget(
            self.temperature_converted, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        simulation_layout.addRow(QLabel("Temperature:"), temperature_layout)
        self.temperature_input.setFixedWidth(line_edit_width)
        self.temperature_units.setFixedWidth(combobox_width)

        # Pressure with units
        self.pressure_input = QLineEdit()
        self.pressure_units = QComboBox()
        self.pressure_units.addItems(["mPa", "Pa", "kPa", "psi"])
        self.pressure_units.setCurrentText("Pa")
        self.pressure_converted = QLabel("0.0 Pa")
        pressure_layout = QHBoxLayout()
        pressure_layout.addWidget(self.pressure_input)
        pressure_layout.addWidget(
            self.pressure_units, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        pressure_layout.addWidget(
            self.pressure_converted, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        simulation_layout.addRow(QLabel("Pressure:"), pressure_layout)
        self.pressure_input.setFixedWidth(line_edit_width)
        self.pressure_units.setFixedWidth(combobox_width)

        # Volume with units
        self.volume_input = QLineEdit()
        self.volume_units = QComboBox()
        self.volume_units.addItems(["mm³", "cm³", "m³"])
        self.volume_units.setCurrentText("m³")
        self.volume_converted = QLabel("0.0 m³")
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(self.volume_input)
        volume_layout.addWidget(
            self.volume_units, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        volume_layout.addWidget(self.volume_converted,
                                alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        simulation_layout.addRow(QLabel("Volume:"), volume_layout)
        self.volume_input.setFixedWidth(line_edit_width)
        self.volume_units.setFixedWidth(combobox_width)

        # Energy with units
        self.energy_input = QLineEdit()
        self.energy_units = QComboBox()
        self.energy_units.addItems(["eV", "J"])
        self.energy_converted = QLabel("0.0 eV")
        energy_layout = QHBoxLayout()
        energy_layout.addWidget(self.energy_input)
        energy_layout.addWidget(
            self.energy_units, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        energy_layout.addWidget(self.energy_converted,
                                alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        simulation_layout.addRow(QLabel("Energy:"), energy_layout)
        self.energy_input.setFixedWidth(line_edit_width)
        self.energy_units.setFixedWidth(combobox_width)

        self.upload_mesh_button = QPushButton("Upload Mesh File")
        self.upload_mesh_button.clicked.connect(self.upload_mesh_file)
        simulation_layout.addRow(self.upload_mesh_button)

        simulation_group_box.setLayout(simulation_layout)
        layout.addWidget(simulation_group_box)

        # Connect signals to the slot that updates converted value labels
        self.time_step_input.textChanged.connect(self.update_converted_values)
        self.time_step_units.currentIndexChanged.connect(
            self.update_converted_values)
        self.simulation_time_input.textChanged.connect(
            self.update_converted_values)
        self.simulation_time_units.currentIndexChanged.connect(
            self.update_converted_values)
        self.temperature_input.textChanged.connect(
            self.update_converted_values)
        self.temperature_units.currentIndexChanged.connect(
            self.update_converted_values)
        self.pressure_input.textChanged.connect(self.update_converted_values)
        self.pressure_units.currentIndexChanged.connect(
            self.update_converted_values)
        self.volume_input.textChanged.connect(self.update_converted_values)
        self.volume_units.currentIndexChanged.connect(
            self.update_converted_values)
        self.energy_input.textChanged.connect(self.update_converted_values)
        self.energy_units.currentIndexChanged.connect(
            self.update_converted_values)

        # Add run and exit buttons to config tab
        buttons_layout = QHBoxLayout()
        self.save_config_button = QPushButton("Save Config")
        self.save_config_button.clicked.connect(self.save_config_to_file)
        buttons_layout.addWidget(self.save_config_button)

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_simulation)
        buttons_layout.addWidget(self.run_button)

        self.help_button = QPushButton("Help")
        self.help_button.clicked.connect(self.show_help)
        buttons_layout.addWidget(self.help_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.exit)
        buttons_layout.addWidget(self.exit_button)

        layout.addLayout(buttons_layout)
        self.config_tab.setLayout(layout)

    def update_converted_values(self):
        # Time Step conversion and update label
        self.time_step_converted.setText(f"{self.converter.to_seconds(
            self.time_step_input.text(), self.time_step_units.currentText()
        )} s")
        self.simulation_time_converted.setText(f"{self.converter.to_seconds(
            self.simulation_time_input.text(), self.simulation_time_units.currentText()
        )} s")
        self.temperature_converted.setText(f"{self.converter.to_kelvin(
            self.temperature_input.text(), self.temperature_units.currentText()
        )} K")
        self.pressure_converted.setText(f"{self.converter.to_pascal(
            self.pressure_input.text(), self.pressure_units.currentText()
        )} Pa")
        self.volume_converted.setText(f"{self.converter.to_cubic_meters(
            self.volume_input.text(), self.volume_units.currentText()
        )} m³")
        self.energy_converted.setText(f"{self.converter.to_electron_volts(
            self.energy_input.text(), self.energy_units.currentText()
        )} eV")

    def upload_mesh_file(self):
        # Open a file dialog when the button is clicked and filter for .msh files
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "Select Mesh File",
            "",
            "Mesh Files (*.msh);;All Files (*)",
            options=options,
        )
        if fileName:
            self.file_path = fileName
            # You can update a label or directly use the file_path for your simulation
            QMessageBox.information(
                self, "Mesh File Selected", f"File: {self.file_path}"
            )

    def run_simulation(self):
        if self.file_path:
            # Retrieve user input
            thread_count = self.thread_count_input.text()            
            particles_count = self.particles_count_input.text()
            time_step = self.converter.to_seconds(
                self.time_step_input.text(), self.time_step_units.currentText()
            )
            simulation_time = self.converter.to_seconds(
                self.simulation_time_input.text(), self.simulation_time_units.currentText()
            )
            temperature = self.converter.to_kelvin(
                self.temperature_input.text(), self.temperature_units.currentText()
            )
            pressure = self.converter.to_pascal(
                self.pressure_input.text(), self.pressure_units.currentText()
            )
            volume = self.converter.to_cubic_meters(
                self.volume_input.text(), self.volume_units.currentText()
            )
            energy = self.converter.to_electron_volts(
                self.energy_input.text(), self.energy_units.currentText()
            )

            if time_step > simulation_time:
                QMessageBox.warning(self, "Invalid Time", f"Time step can't be greater than total simulation time: {
                                    time_step} > {simulation_time}")

            empty_fields = []
            if not particles_count:
                empty_fields.append("Particles Count")
            if not time_step:
                empty_fields.append("Time Step")
            if not simulation_time:
                empty_fields.append("Simulation Time")
            if not temperature:
                empty_fields.append("Temperature")
            if not pressure:
                empty_fields.append("Pressure")
            if not volume:
                empty_fields.append("Volume")
            if not energy:
                empty_fields.append("Energy")

            # If there are any empty fields, alert the user and abort the save
            if empty_fields:
                QMessageBox.warning(
                    self,
                    "Incomplete Configuration",
                    "Please fill in the following fields before saving:\n"
                    + "\n".join(empty_fields),
                )
                return

            if not thread_count or not thread_count.isdigit() or int(thread_count) > get_thread_count() or int(thread_count) < 1:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Please enter valid numeric values for count of threads.",
                )
                return

            # Validate input
            if not (
                particles_count.isdigit()
                and str(time_step).replace(".", "", 1).isdigit()
                and str(simulation_time).replace(".", "", 1).isdigit()
            ):
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Please enter valid numeric values for particles count, time step, and time interval.",
                )
                return

            # Disable UI components
            self.set_ui_enabled(False)

            hdf5_filename = self.file_path.replace(".msh", ".hdf5")
            args = f"{particles_count} {time_step} {
                simulation_time} {self.file_path} {thread_count}"
            self.progress_bar.setRange(0, 0)
            self.start_time = time()
            self.process.start("./main", args.split())
            self.update_plot(hdf5_filename)

        else:
            QMessageBox.warning(
                self, "Warning", "Please upload a .msh file first.")

    def on_finished(self):
        end_time = time()
        execution_time = end_time - self.start_time
        
        # Re-enable UI components
        self.set_ui_enabled(True)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        QMessageBox.information(self, 
                                "Process Finished", 
                                f"The simulation has completed in {execution_time:.6f}s.")
        
    def set_ui_enabled(self, enabled):
        """Enable or disable UI components."""
        self.tab_widget.setEnabled(enabled)
        self.run_button.setEnabled(enabled)
        self.save_config_button.setEnabled(enabled)
        self.exit_button.setEnabled(enabled)

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

    def save_config_to_file(self):
        # Gather input values
        temperature = self.converter.to_kelvin(
            self.temperature_input.text(), self.temperature_units.currentText()
        )
        pressure = self.converter.to_pascal(
            self.pressure_input.text(), self.pressure_units.currentText()
        )
        volume = self.converter.to_cubic_meters(
            self.volume_input.text(), self.volume_units.currentText()
        )
        energy = self.converter.to_electron_volts(
            self.energy_input.text(), self.energy_units.currentText()
        )

        projective_particle = self.projective_input.currentText()
        gas_particle = self.gas_input.currentText()
        model = self.model_input.currentText()

        # Check for empty fields
        empty_fields = []
        if not temperature:
            empty_fields.append("Temperature")
        if not pressure:
            empty_fields.append("Pressure")
        if not volume:
            empty_fields.append("Volume")
        if not energy:
            empty_fields.append("Energy")

        # If there are any empty fields, alert the user and abort the save
        if empty_fields:
            QMessageBox.warning(
                self,
                "Incomplete Configuration",
                "Please fill in the following fields before saving:\n"
                + "\n".join(empty_fields),
            )
            return

        # Combine the particles input
        particles = f"{projective_particle} {gas_particle}"

        # Format the configuration content
        config_content = (
            f"T: {temperature}\n"
            f"P: {pressure}\n"
            f"V: {volume}\n"
            f"Particles: {particles}\n"
            f"Energy: {energy}\n"
            f"Model: {model}\n"
        )

        # Ask the user where to save the file
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        config_file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            "",  # Start directory
            "Config Files (*.txt);;All Files (*)",
            options=options,
        )

        # Write the configuration content to the file
        try:
            with open(config_file_path, "w") as file:
                file.write(config_content)
            QMessageBox.information(
                self, "Success", f"Configuration saved to {config_file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save configuration: {e}")

    def show_help(self):
        QMessageBox.information(
            self,
            "Help",
            "This is help message. Don't forget to write a desc to ur app here pls!!!",
        )

    def exit(self):
        sys.exit(0)
