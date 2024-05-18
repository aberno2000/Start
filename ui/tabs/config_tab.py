from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QComboBox,
    QMessageBox, QLabel, QLineEdit, QFormLayout,
    QGroupBox, QFileDialog, QPushButton,
    QSizePolicy, QSpacerItem, QDialog
)
from PyQt5.QtGui import QIntValidator, QRegExpValidator
import gmsh
from os.path import dirname
from PyQt5 import QtCore
from PyQt5.QtCore import QSize, pyqtSignal, QRegExp
from json import load, dump, JSONDecodeError
from multiprocessing import cpu_count
from platform import platform
from util.converter import Converter, is_positive_real_number
from util.mesh_dialog import MeshDialog
from util import is_file_valid
from util.util import(
    is_path_accessable, CustomDoubleValidator,
    DEFAULT_TEMP_CONFIG_FILE,
    DEFAULT_TEMP_SOLVER_PARAMS_FILE
)
from util.styles import(
    DEFAULT_QLINEEDIT_STYLE, DEFAULT_COMBOBOX_STYLE,
    DEFAULT_DISABLED_QLINEEDIT_STYLE, DEFAULT_DISABLED_COMBOBOX_STYLE
)

MIN_TIME = 1e-9
MAX_PRESSURE = 300.0

DEFAULT_LINE_EDIT_WIDTH = 175
DEFAULT_COMBOBOX_WIDTH = 85

def get_thread_count():
    return cpu_count()


def get_os_info():
    return platform()


class ConfigTab(QWidget):
    # Signal to check if mesh file was selected by user
    meshFileSelected = pyqtSignal(str)
    requestToMoveToTheNextTab = pyqtSignal()
    requestToStartSimulation = pyqtSignal()
    selectBoundaryConditionsSignal = pyqtSignal()

    def __init__(self, log_console, parent=None):
        super().__init__(parent)        
        self.layout = QVBoxLayout(self)
        
        self.converter = Converter()
        self.setup_ui()
        self.mesh_file = ""
        self.config_file_path = ""
        
        self.log_console = log_console
        self.log_console.logSignal.connect(self.log_console.appendLog)

    def setup_ui(self):
        self.setup_mesh_group()
        self.setup_particles_group()
        self.setup_scattering_model_group()
        self.setup_simulation_parameters_group()
        self.setup_next_button()
        
        
    def setup_next_button(self):
        button_layout = QHBoxLayout()
        nextButton = QPushButton('Next >')
        nextButton.setFixedSize(QSize(50, 25))
        nextButton.setToolTip('Check this tab and move to the next with starting the simulation')
        nextButton.clicked.connect(self.next_button_on_clicked)
        
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout.addSpacerItem(spacer)
        
        button_layout.addWidget(nextButton)
        self.layout.addLayout(button_layout)
        
    
    def next_button_on_clicked(self):
        self.validate_input_with_highlight()
        self.save_solver_params_to_json(DEFAULT_TEMP_SOLVER_PARAMS_FILE)
        
    
    def save_solver_params_to_json(self, filename: str):
        params = {}
        for key, (input_field, units_combobox) in self.solver_parameters.items():
            if isinstance(input_field, QLineEdit):
                params[key] = input_field.text()
            elif isinstance(input_field, QComboBox):
                params[key] = input_field.currentText()

        params["solverName"] = self.solver_selection.currentText()
        with open(filename, 'w') as file:
            dump(params, file, indent=4)
        
        
    def setup_mesh_group(self):
        self.mesh_file_label = QLabel("No file selected")
        self.mesh_file_label.setWordWrap(True)
        
        button_layout = QVBoxLayout()
        self.upload_mesh_button = QPushButton("Upload Mesh File")
        self.upload_mesh_button.clicked.connect(self.ask_to_upload_mesh_file)
        button_layout.addWidget(self.upload_mesh_button)
        button_layout.addWidget(self.mesh_file_label)
        self.layout.addLayout(button_layout)

    def setup_particles_group(self):      
        particles_group_box = QGroupBox("Particles")
        particles_layout = QFormLayout()

        self.particles_count_input = QLineEdit()
        self.particles_count_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        particles_layout.addRow(QLabel("Count:"), self.particles_count_input)

        self.projective_input = QComboBox()
        self.gas_input = QComboBox()
        projective_particles = ["Ti", "Al", "Sn", "W", "Au", "Cu", "Ni", "Ag"]
        gas_particles = ["Ar", "Ne", "He"]
        self.projective_input.addItems(projective_particles)
        self.gas_input.addItems(gas_particles)
        particles_layout.addRow(QLabel("Projective:"), self.projective_input)
        particles_layout.addRow(QLabel("Gas:"), self.gas_input)

        particles_group_box.setLayout(particles_layout)
        self.layout.addWidget(particles_group_box)

    def setup_scattering_model_group(self):
        scattering_group_box = QGroupBox("Scattering Model")
        scattering_layout = QVBoxLayout()

        self.model_input = QComboBox()
        self.model_input.addItems(["HS", "VHS", "VSS"])
        scattering_layout.addWidget(self.model_input)

        scattering_group_box.setLayout(scattering_layout)
        self.layout.addWidget(scattering_group_box)
        
    def create_simulation_field(self, label_text, input_type, units=None, default_unit=None, default_value="0.0"):
        input_field = QLineEdit()
        input_field.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        input_field.setFixedWidth(DEFAULT_LINE_EDIT_WIDTH)

        layout = QHBoxLayout()
        layout.addWidget(input_field)

        if units:
            units_combobox = QComboBox()
            units_combobox.addItems(units)
            if default_unit:
                units_combobox.setCurrentText(default_unit)
            units_combobox.setFixedWidth(DEFAULT_COMBOBOX_WIDTH)
            layout.addWidget(units_combobox, alignment=QtCore.Qt.AlignLeft)

        converted_label = QLabel(f"{default_value} {units[0] if units else ''}")
        layout.addWidget(converted_label, alignment=QtCore.Qt.AlignRight)

        self.simulation_layout.addRow(QLabel(label_text), layout)

        return input_field, units_combobox if units else None, converted_label
    
    def create_solver_params_field(self, parent_layout, label_text, default_value, units=None, is_combobox=False):
        DEFAULT_LINE_EDIT_WIDTH = 175
        DEFAULT_COMBOBOX_WIDTH = 85

        if is_combobox:
            input_field = QComboBox()
            input_field.addItems(default_value)  # default_value should be a list of items for combobox
            input_field.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
            input_field.setFixedWidth(DEFAULT_LINE_EDIT_WIDTH)
        else:
            input_field = QLineEdit()
            input_field.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
            input_field.setFixedWidth(DEFAULT_LINE_EDIT_WIDTH)
            input_field.setText(default_value)

        layout = QHBoxLayout()
        layout.addWidget(input_field)

        units_combobox = None
        if units:
            units_combobox = QComboBox()
            units_combobox.addItems(units)
            units_combobox.setFixedWidth(DEFAULT_COMBOBOX_WIDTH)
            layout.addWidget(units_combobox, alignment=QtCore.Qt.AlignLeft)

        parent_layout.addRow(QLabel(label_text), layout)
        return input_field, units_combobox


    def setup_simulation_parameters_group(self):
        self.simulation_layout = QFormLayout()
        simulation_group_box = QGroupBox("Simulation Parameters")
        simulation_group_box.setLayout(self.simulation_layout)

        self.simulation_layout.addRow(QLabel(f"System: {get_os_info()} has {get_thread_count()} threads"))

        # Thread count
        self.thread_count_input, _, _ = self.create_simulation_field("Thread count:", QLineEdit)

        # Time Step with units
        self.time_step_input, self.time_step_units, self.time_step_converted = self.create_simulation_field("Time Step:", QLineEdit, ["ns", "μs", "ms", "s", "min"], "ms", "0.0")

        # Simulation time with units
        self.simulation_time_input, self.simulation_time_units, self.simulation_time_converted = self.create_simulation_field("Simulation Time:", QLineEdit, ["ns", "μs", "ms", "s", "min"], "s", "0.0")

        # Temperature with units
        self.temperature_input, self.temperature_units, self.temperature_converted = self.create_simulation_field("Temperature:", QLineEdit, ["K", "F", "C"], "K", "0.0 K")

        # Pressure with units
        self.pressure_input, self.pressure_units, self.pressure_converted = self.create_simulation_field("Pressure:", QLineEdit, ["mPa", "Pa", "kPa", "psi"], "Pa", "0.0")

        # Volume with units
        self.volume_input, self.volume_units, self.volume_converted = self.create_simulation_field("Volume:", QLineEdit, ["mm³", "cm³", "m³"], "m³", "0.0 m³")

        # Energy with units
        self.energy_input, self.energy_units, self.energy_converted = self.create_simulation_field("Energy:", QLineEdit, ["eV", "keV", "J", "kJ", "cal"], "eV", "0.0")

        simulation_group_box.setLayout(self.simulation_layout)
        
        # Create PIC and FEM group boxes
        picfem_group_box = QGroupBox("Particle In Cell (PIC) and Finite Element Method (FEM) Parameters")
        pic_layout = QFormLayout()
        fem_layout = QFormLayout()
        picfem_layout = QHBoxLayout()
        picfem_layout.addLayout(pic_layout)
        picfem_layout.addLayout(fem_layout)
        picfem_group_box.setLayout(picfem_layout)
        
        # Add PIC and FEM fields
        self.pic_input = QLineEdit()
        self.pic_input.setFixedWidth(DEFAULT_LINE_EDIT_WIDTH)
        self.pic_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.pic_input.setValidator(CustomDoubleValidator(0.1, 1000.0, 3))
        self.pic_input.setToolTip(
            "Cubic Grid Size: This parameter specifies the edge size of the cubic cells in the 3D grid. "
            "The grid is used to map tetrahedrons to their containing cells, facilitating the determination of which tetrahedron contains a given particle. "
            "This grid-based approach improves the efficiency of spatial queries in the mesh.\n\n"
            "Range: from 0.1 to 1'000\n"
            "Purpose: The cubic grid helps in tracking particles within the volume by determining which tetrahedron each particle is located in. "
            "This is achieved by checking the intersection of particles with the cells of the grid and identifying the corresponding tetrahedrons.\n\n"
            "Warning: \n"
            "- Setting the grid size too low (closer to 0.1) will result in a very fine grid, which may consume a significant amount of memory and can lead to performance issues.\n"
            "- Setting the grid size too high (closer to 1000) may result in an overly coarse grid, potentially causing incorrect determination of particle locations within the tetrahedrons."
        )
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(50, 0, 0, 0)
        h_layout.addWidget(self.pic_input)
        pic_layout.addRow(QLabel("Cubic grid size:"), h_layout)

        self.fem_input = QLineEdit()
        self.fem_input.setFixedWidth(DEFAULT_LINE_EDIT_WIDTH)
        self.fem_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.fem_input.setValidator(QIntValidator(1, 100))
        self.fem_input.setToolTip(
            "FEM Calculation Accuracy: This parameter determines the number of quadrature points used in the Finite Element Method (FEM) calculations, based on the desired accuracy. "
            "A higher accuracy typically requires more quadrature points, which increases both the computational cost and the memory usage of the program. "
            "However, it also improves the approximation of the integral.\n\n"
            "Purpose: The quadrature points are used to approximate integrals within the FEM. The more points used, the closer the numerical integration is to the actual value.\n\n"
            "Range: from 1 to 100\n"
            "Note: The specific number of quadrature points for a given accuracy is determined by an external library, Intrepid2.\n\n"
            "Warning: \n"
            "- Higher accuracy settings (closer to 100) will lead to increased computational costs and memory usage, but will provide better integral approximation.\n"
            "- Lower accuracy settings (closer to 1) will reduce computational costs and memory usage, but may result in less accurate integral approximations."
        )
        h1_layout = QHBoxLayout()
        h1_layout.setContentsMargins(25, 0, 0, 0)
        h1_layout.addWidget(self.fem_input)
        fem_layout.addRow(QLabel("FEM calculation accuracy:"), h1_layout)
        
        # Add Load Magnetic Induction button
        self.load_magnetic_induction_button = QPushButton("Load Magnetic Induction")
        self.load_magnetic_induction_button.setFixedWidth(DEFAULT_LINE_EDIT_WIDTH)
        self.load_magnetic_induction_button.clicked.connect(self.load_magnetic_induction)
        fem_layout.addRow(self.load_magnetic_induction_button)

        # Add Select Boundary Conditions button
        self.select_boundary_conditions_button = QPushButton("Select Boundary Conditions")
        self.select_boundary_conditions_button.setFixedWidth(DEFAULT_LINE_EDIT_WIDTH)
        self.select_boundary_conditions_button.clicked.connect(self.emit_select_boundary_conditions_signal)
        fem_layout.addRow(self.select_boundary_conditions_button)
        
        # Create additional fields group box
        solver_group_box = QGroupBox("Iterative Solver Parameters")
        additional_layout_left = QFormLayout()
        additional_layout_right = QFormLayout()
        additional_layout = QHBoxLayout()
        additional_layout.addLayout(additional_layout_left)
        additional_layout.addLayout(additional_layout_right)
        solver_group_box.setLayout(additional_layout)

        # Solver selection
        self.solver_selection = QComboBox()
        self.solver_selection.setFixedWidth(DEFAULT_LINE_EDIT_WIDTH)
        self.solver_selection.addItems([
            "CG", "Block CG", "GMRES", "Block GMRES", "Pseudo-block GMRES",
            "Block Flexible GMRES", "GCRO-DR", "Pseudo-block CG", "LSQR", "MINRES"
        ])
        self.solver_selection.setToolTip(
            "CG (Conjugate Gradient): Used for solving systems of linear equations with symmetric positive-definite matrices.\n"
            "Block CG: A variant of CG that handles multiple right-hand sides simultaneously.\n"
            "GMRES (Generalized Minimal Residual): Suitable for non-symmetric or indefinite matrices, minimizes the residual over a Krylov subspace.\n"
            "Block GMRES: A block version of GMRES for multiple right-hand sides.\n"
            "Pseudo-block GMRES: A variant of GMRES that improves performance for multiple right-hand sides.\n"
            "Block Flexible GMRES: Allows variable preconditioning within the GMRES algorithm, handling multiple right-hand sides.\n"
            "GCRO-DR (Generalized Conjugate Residual with Deflated Restarting): Combines GMRES with a deflation technique to accelerate convergence.\n"
            "Pseudo-block CG: Similar to CG but handles multiple right-hand sides more efficiently.\n"
            "LSQR: An iterative method for solving sparse linear equations and sparse least squares problems.\n"
            "MINRES (Minimal Residual): Solves symmetric linear systems, particularly effective for symmetric indefinite systems.\n"
            "For a more detailed description, see the corresponding Internet resources."
        )
        self.solver_selection.currentIndexChanged.connect(self.update_solver_parameters)
        additional_layout_left.addRow(QLabel("Solver:"), self.solver_selection)

        # Parameters for solvers
        self.solver_parameters = {}

        self.solver_parameters["maxIterations"] = self.create_solver_params_field(additional_layout_left, "Max Iterations:", "1000")
        self.solver_parameters["convergenceTolerance"] = self.create_solver_params_field(additional_layout_left, "Convergence Tolerance:", "1e-20")
        self.solver_parameters["outputFrequency"] = self.create_solver_params_field(additional_layout_left, "Output Frequency:", "1")
        self.solver_parameters["numBlocks"] = self.create_solver_params_field(additional_layout_left, "Num Blocks:", "30")
        self.solver_parameters["blockSize"] = self.create_solver_params_field(additional_layout_left, "Block Size:", "1")

        self.solver_parameters["maxRestarts"] = self.create_solver_params_field(additional_layout_right, "Max Restarts:", "20")
        self.solver_parameters["flexibleGMRES"] = self.create_solver_params_field(additional_layout_right, "Flexible GMRES:", ["false", "true"], is_combobox=True)
        self.solver_parameters["orthogonalization"] = self.create_solver_params_field(additional_layout_right, "Orthogonalization:", ["ICGS", "IMGS"], is_combobox=True)
        self.solver_parameters["adaptiveBlockSize"] = self.create_solver_params_field(additional_layout_right, "Adaptive Block Size:", ["false", "true"], is_combobox=True)
        self.solver_parameters["convergenceTestFrequency"] = self.create_solver_params_field(additional_layout_right, "Convergence Test Frequency:", "-1")
        self.solver_selection.setCurrentIndex(2) # By default using GMRES
        
        # Applying validators to different fields
        exp_regexp = QRegExp(r'1e-([1-9]|[1-4][0-9]|50)|1e-1')
        
        self.solver_parameters["maxIterations"][0].setValidator(QIntValidator(1, 1000000))
        self.solver_parameters["convergenceTolerance"][0].setValidator(QRegExpValidator(exp_regexp))
        self.solver_parameters["outputFrequency"][0].setValidator(QIntValidator(1, 1000))
        self.solver_parameters["numBlocks"][0].setValidator(QIntValidator(1, 1000))
        self.solver_parameters["blockSize"][0].setValidator(QIntValidator(1, 1000))
        self.solver_parameters["maxRestarts"][0].setValidator(QIntValidator(0, 1000))
        
        # Adding tooltips to different fields
        self.solver_parameters["maxIterations"][0].setToolTip("Max Iterations: The maximum number of iterations the solver will perform. Range: 1 to 1'000'000.")
        self.solver_parameters["convergenceTolerance"][0].setToolTip("Convergence Tolerance: The tolerance for the relative residual norm used to determine convergence. Range: 1e-50 to 1e-1.")
        self.solver_parameters["outputFrequency"][0].setToolTip("Output Frequency: Determines how often information is printed during the iterative process. Range: 1 to 1'000.")
        self.solver_parameters["numBlocks"][0].setToolTip("Num Blocks: Sets the number of blocks in the Krylov basis, related to the restart mechanism of GMRES. Range: 1 to 1'000.")
        self.solver_parameters["blockSize"][0].setToolTip("Block Size: Determines the block size for block methods. Range: 1 to 1'000.")
        self.solver_parameters["maxRestarts"][0].setToolTip("Max Restarts: Specifies the maximum number of restarts allowed. Range: 0 to 1'000.")
        self.solver_parameters["flexibleGMRES"][0].setToolTip("Flexible GMRES: Indicates whether to use the flexible version of GMRES. Options: true, false.")
        self.solver_parameters["orthogonalization"][0].setToolTip("Orthogonalization: Specifies the orthogonalization method to use. Options: ICGS, IMGS.")
        self.solver_parameters["adaptiveBlockSize"][0].setToolTip("Adaptive Block Size: Indicates whether to adapt the block size in block methods. Options: true, false.")
        self.solver_parameters["convergenceTestFrequency"][0].setToolTip("Convergence Test Frequency: Specifies how often convergence is tested (in iterations). Default setting is used if negative. Range: -1 or positive integers.")

        # Create main layout and add both group boxes
        main_layout = QHBoxLayout()
        main_layout.addWidget(simulation_group_box)
        main_rightside_layout = QVBoxLayout()
        main_rightside_layout.addWidget(picfem_group_box)
        main_rightside_layout.addWidget(solver_group_box)
        main_layout.addLayout(main_rightside_layout)

        # Create a QWidget to hold the main_layout
        main_widget = QWidget()
        main_widget.setLayout(main_layout)

        # Add the main_widget to the parent layout
        self.layout.addWidget(main_widget)

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

    def update_converted_values(self):
        self.time_step_converted.setText(
            f"{self.converter.to_seconds(self.time_step_input.text(), self.time_step_units.currentText())} s")
        self.simulation_time_converted.setText(
            f"{self.converter.to_seconds(self.simulation_time_input.text(), self.simulation_time_units.currentText())} s")
        self.temperature_converted.setText(
            f"{self.converter.to_kelvin(self.temperature_input.text(), self.temperature_units.currentText())} K")
        self.pressure_converted.setText(
            f"{self.converter.to_pascal(self.pressure_input.text(), self.pressure_units.currentText())} Pa")
        self.volume_converted.setText(
            f"{self.converter.to_cubic_meters(self.volume_input.text(), self.volume_units.currentText())} m³")
        self.energy_converted.setText(
            f"{self.converter.to_joules(self.energy_input.text(), self.energy_units.currentText())} J")

    def update_solver_parameters(self):
        solver = self.solver_selection.currentText()

        # Disable all fields initially and apply disabled style
        for param in self.solver_parameters.values():
            param[0].setEnabled(False)
            if isinstance(param[0], QLineEdit):
                param[0].setStyleSheet(DEFAULT_DISABLED_QLINEEDIT_STYLE)
            elif isinstance(param[0], QComboBox):
                param[0].setStyleSheet(DEFAULT_DISABLED_COMBOBOX_STYLE)

            if param[1] is not None:
                param[1].setEnabled(False)
                if isinstance(param[1], QLineEdit):
                    param[1].setStyleSheet(DEFAULT_DISABLED_QLINEEDIT_STYLE)
                elif isinstance(param[1], QComboBox):
                    param[1].setStyleSheet(DEFAULT_DISABLED_COMBOBOX_STYLE)

        # Define which fields should be visible for each solver
        visible_params = {
            "CG": ["maxIterations", "convergenceTolerance", "outputFrequency", "blockSize"],
            "Block CG": ["maxIterations", "convergenceTolerance", "outputFrequency", "blockSize", "adaptiveBlockSize"],
            "GMRES": ["maxIterations", "convergenceTolerance", "outputFrequency", "numBlocks", "maxRestarts", "orthogonalization", "flexibleGMRES"],
            "Block GMRES": ["maxIterations", "convergenceTolerance", "outputFrequency", "numBlocks", "maxRestarts", "orthogonalization", "adaptiveBlockSize", "convergenceTestFrequency"],
            "Pseudo-block GMRES": ["maxIterations", "convergenceTolerance", "outputFrequency", "numBlocks", "maxRestarts", "orthogonalization"],
            "Block Flexible GMRES": ["maxIterations", "convergenceTolerance", "outputFrequency", "numBlocks", "maxRestarts", "orthogonalization", "adaptiveBlockSize"],
            "GCRO-DR": ["maxIterations", "convergenceTolerance", "outputFrequency", "numBlocks", "maxRestarts", "orthogonalization", "adaptiveBlockSize", "convergenceTestFrequency"],
            "Pseudo-block CG": ["maxIterations", "convergenceTolerance", "outputFrequency", "blockSize"],
            "LSQR": ["maxIterations", "convergenceTolerance", "outputFrequency"],
            "MINRES": ["maxIterations", "convergenceTolerance", "outputFrequency"]
        }

        if solver in visible_params:
            for param in visible_params[solver]:
                self.solver_parameters[param][0].setEnabled(True)
                if isinstance(self.solver_parameters[param][0], QLineEdit):
                    self.solver_parameters[param][0].setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
                elif isinstance(self.solver_parameters[param][0], QComboBox):
                    self.solver_parameters[param][0].setStyleSheet(DEFAULT_COMBOBOX_STYLE)
                    
                if self.solver_parameters[param][1] is not None:
                    self.solver_parameters[param][1].setEnabled(True)
                    if isinstance(self.solver_parameters[param][1], QLineEdit):
                        self.solver_parameters[param][1].setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
                    elif isinstance(self.solver_parameters[param][1], QComboBox):
                        self.solver_parameters[param][1].setStyleSheet(DEFAULT_COMBOBOX_STYLE)


    def check_validity_of_params(self):
        if not self.thread_count or \
            int(self.thread_count) > get_thread_count() or \
            int(self.thread_count) < 1:
            QMessageBox.warning(self, "Invalid thread count",
                                f"Thread count can't be {self.thread_count} (less or equal 0). Your system has {get_thread_count()} threads.")
            return None
    
        if not str(self.particles_count) or int(self.particles_count) <= 0:
            QMessageBox.warning(self, "Invalid particle count", f"It doesn't make sense to run the simulation with {self.particles_count} particles.")
            return None
        
        if not (
            is_positive_real_number(self.time_step)
            and is_positive_real_number(self.simulation_time)
            and self.time_step >= MIN_TIME  # Time limitations
            and self.simulation_time >= MIN_TIME
        ):
            QMessageBox.warning(
                self,
                "Warning",
                f"Please enter valid numeric values for particles count, time step, and time interval.\n"
                f"Time can't be less than {MIN_TIME}.",
            )
            return None
        
        if not is_positive_real_number(self.pressure):
            QMessageBox.warning(self, "Warning", f"Pressure can't be less than 0. Your value is {self.pressure}.")
            return None
        if self.pressure > MAX_PRESSURE:
            QMessageBox.warning(self, "Warning", f"It might be overhead to start the simulation with pressure value > {MAX_PRESSURE} Pa. Your value is {self.pressure}")

        try:
            config = {
                "Mesh File": self.mesh_file,
                "Count": int(self.particles_count),
                "Threads": int(self.thread_count),
                "Time Step": float(self.time_step),
                "Simulation Time": float(self.simulation_time),
                "T": float(self.temperature),
                "P": float(self.pressure),
                "V": float(self.volume),
                "Particles": [
                    self.projective_input.currentText(),
                    self.gas_input.currentText()
                ],
                "Energy": float(self.energy),
                "Model": self.model_input.currentText(),
            }
        except ValueError as e:
            QMessageBox.critical(self, "Invalid Input", f"Error in input fields: Exception: {e}")
            return None
        return config
        

    def validate_input(self):     
        self.thread_count = self.thread_count_input.text()
        self.particles_count = self.particles_count_input.text()
        self.time_step = self.converter.to_seconds(
            self.time_step_input.text(), self.time_step_units.currentText()
        )
        self.simulation_time = self.converter.to_seconds(
            self.simulation_time_input.text(), self.simulation_time_units.currentText()
        )
        self.temperature = self.converter.to_kelvin(
            self.temperature_input.text(), self.temperature_units.currentText()
        )
        self.pressure = self.converter.to_pascal(
            self.pressure_input.text(), self.pressure_units.currentText()
        )
        self.volume = self.converter.to_cubic_meters(
            self.volume_input.text(), self.volume_units.currentText()
        )
        self.energy = self.converter.to_joules(
            self.energy_input.text(), self.energy_units.currentText()
        )

        if self.time_step > self.simulation_time:
            QMessageBox.warning(self, "Invalid Time",
                                f"Time step can't be greater than total simulation time: {self.time_step} > {self.simulation_time}")
            return None

        empty_fields = []
        if not self.particles_count or int(self.particles_count) <= 0:
            empty_fields.append("Particles Count")
        if not self.time_step:
            empty_fields.append("Time Step")
        if not self.simulation_time:
            empty_fields.append("Simulation Time")
        if not self.temperature:
            empty_fields.append("Temperature")
        if not self.pressure:
            empty_fields.append("Pressure")
        if not self.volume:
            empty_fields.append("Volume")
        if not self.energy:
            empty_fields.append("Energy")

        # If there are any empty fields, alert the user and abort the save
        if empty_fields:
            QMessageBox.warning(
                self,
                "Incomplete Configuration",
                "Please fill in the following fields before saving:\n"
                + "\n".join(empty_fields),
            )
            return None

        return self.check_validity_of_params()
    
    
    def validate_input_with_highlight(self):
        # Reset styles before validation
        self.reset_input_styles()

        all_valid = True
        self.invalid_fields = []

        # Validate thread count input
        thread_count = self.thread_count_input.text()
        if not thread_count.isdigit() or int(thread_count) < 1 or int(thread_count) > get_thread_count():
            self.highlight_invalid(self.thread_count_input)
            self.invalid_fields.append('Thread Count')
            all_valid = False

        # Validate particles count input
        particles_count = self.particles_count_input.text()
        if not particles_count.isdigit() or int(particles_count) <= 0:
            self.highlight_invalid(self.particles_count_input)
            self.invalid_fields.append('Particle Count')
            all_valid = False

        # Validate numeric inputs
        if not self.validate_and_convert_numbers():
            all_valid = False
            
        if self.invalid_fields:
            QMessageBox.warning(
                self,
                "Incomplete Configuration",
                "Please fill in the following fields before starting the simulation:\n"
                + "\n".join(self.invalid_fields),
            )
            return None
        else:
            if not self.mesh_file:
                QMessageBox.information(self,
                                        "Mesh File",
                                        "Firstly, You need to select the mesh file")
                self.upload_mesh_file()

            QMessageBox.information(self,
                                    "Value Checker",
                                    "All fields are valid. Staring the simulation...")
            self.requestToMoveToTheNextTab.emit()
            self.requestToStartSimulation.emit()

        return all_valid
            
            
    def highlight_invalid(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                border: 0.5px solid red;
                border-radius: 2px;
                background-color: light gray;
                color: black;
            }
        """)
    
            
    def reset_input_styles(self):
        self.thread_count_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.particles_count_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.time_step_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.simulation_time_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.temperature_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.pressure_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.volume_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.energy_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
    
    
    def validate_and_convert_numbers(self):        
        # Initialize validation status
        valid = True

        # Validate and convert time step
        time_step_value = self.converter.to_seconds(self.time_step_input.text(), self.time_step_units.currentText())
        if time_step_value is None or time_step_value < MIN_TIME or not self.time_step_input.text():
            self.highlight_invalid(self.time_step_input)
            self.invalid_fields.append('Time Step')
            valid = False

        # Validate and convert simulation time
        simulation_time_value = self.converter.to_seconds(self.simulation_time_input.text(), self.simulation_time_units.currentText())
        if simulation_time_value is None or simulation_time_value < MIN_TIME or not self.simulation_time_input.text():
            self.highlight_invalid(self.simulation_time_input)
            self.invalid_fields.append('Simulation Time')
            valid = False

        # Temperature validation
        temperature_value = self.converter.to_kelvin(self.temperature_input.text(), self.temperature_units.currentText())
        if temperature_value is None or not self.temperature_input.text():
            self.highlight_invalid(self.temperature_input)
            self.invalid_fields.append('Temperature')
            valid = False

        # Pressure validation
        pressure_value = self.converter.to_pascal(self.pressure_input.text(), self.pressure_units.currentText())
        if pressure_value is None or pressure_value < 0 or pressure_value > MAX_PRESSURE or not self.pressure_input.text():
            self.highlight_invalid(self.pressure_input)
            self.invalid_fields.append('Pressure')
            valid = False

        # Volume validation
        volume_value = self.converter.to_cubic_meters(self.volume_input.text(), self.volume_units.currentText())
        if volume_value is None or not self.volume_input.text():
            self.highlight_invalid(self.volume_input)
            self.invalid_fields.append('Volume')
            valid = False

        # Energy validation
        energy_value = self.converter.to_joules(self.energy_input.text(), self.energy_units.currentText())
        if energy_value is None or not self.energy_input.text():
            self.highlight_invalid(self.energy_input)
            self.invalid_fields.append('Energy')
            valid = False

        return valid
    
    
    def upload_config_with_filename(self, configFile: str):
        self.config_file_path = configFile
        if is_file_valid(self.config_file_path):  # If a file was selected
            if self.read_config_file(self.config_file_path) == 1:
                return
            
            if not is_path_accessable(self.mesh_file):
                QMessageBox.warning(self,
                                    "File Error",
                                    f"Your file {self.mesh_file} is unaccessable. Check the path or permissons to this path: {dirname(self.config_file_path)}")
                return
            
            self.meshFileSelected.emit(self.mesh_file)
            self.log_console.logSignal.emit(f'Selected configuration: {self.config_file_path}\n')
        else:
            QMessageBox.warning(
                self, "No Configuration File Selected", "No configuration file was uploaded.")
            return


    def upload_config(self):                
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.config_file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Configuration File", "",
            "JSON (*.json);;All Files (*)", options=options)

        if self.config_file_path:  # If a file was selected
            if self.read_config_file(self.config_file_path) == 1:
                return

            if not is_path_accessable(self.mesh_file):
                QMessageBox.warning(self,
                                    "File Error",
                                    f"Your file {self.mesh_file} is unaccessable. Check the path or permissons to this path: {dirname(self.config_file_path)}")
                return
            
            self.meshFileSelected.emit(self.mesh_file)
            self.log_console.logSignal.emit(f'Selected configuration: {self.config_file_path}\n')
        else:
            QMessageBox.warning(
                self, "No Configuration File Selected", "No configuration file was uploaded.")
            return

    def read_config_file(self, config_file_path):
        config = str()
        try:
            with open(config_file_path, 'r') as file:
                config = load(file)
        except FileNotFoundError:
            QMessageBox.warning(self, "Warning", f"File not found: {config_file_path}")
            return None
        except JSONDecodeError:
            QMessageBox.warning(self, "Warning", f"Failed to decode JSON from {config_file_path}")
            return None
        if not self.apply_config(config):
            return None
        else:
            return 1

    def apply_config(self, config):
        try:
            self.mesh_file = config.get('Mesh File', '')
            self.particles_count = int(config.get('Count', ''))
            self.thread_count = int(config.get('Threads', ''))
            self.time_step = float(config.get('Time Step', ''))
            self.simulation_time = float(config.get('Simulation Time', ''))
            self.temperature = float(config.get('T', ''))
            self.pressure = float(config.get('P', ''))
            self.volume = float(config.get('V', ''))
            self.energy = float(config.get('Energy', ''))
            
            config = self.check_validity_of_params()
            if not config:
                return None
            
            self.mesh_file_label.setText(f"Selected: {self.mesh_file}")
            self.particles_count_input.setText(str(config.get('Count', '')))
            self.thread_count_input.setText(str(config.get('Threads', '')))
            self.time_step_input.setText(str(config.get('Time Step', '')))
            self.simulation_time_input.setText(str(config.get('Simulation Time', '')))
            self.temperature_input.setText(str(config.get('T', '')))
            self.pressure_input.setText(str(config.get('P', '')))
            self.volume_input.setText(str(config.get('V', '')))
            self.energy_input.setText(str(config.get('Energy', '')))

            particles = config.get('Particles', [])
            if len(particles) == 2:                
                projective_text, gas_text = particles
                projective_index = self.projective_input.findText(
                    projective_text, QtCore.Qt.MatchFixedString)
                gas_index = self.gas_input.findText(
                    gas_text, QtCore.Qt.MatchFixedString)
                self.projective_input.setCurrentIndex(projective_index)
                self.gas_input.setCurrentIndex(gas_index)

            model_index = self.model_input.findText(
                config.get('Model', ''), QtCore.Qt.MatchFixedString)
            if model_index >= 0:
                self.model_input.setCurrentIndex(model_index)

            # Applying all measurement to SI (International System of Units)
            self.time_step_units.setCurrentIndex(3)
            self.simulation_time_units.setCurrentIndex(3)
            self.temperature_units.setCurrentIndex(0)
            self.pressure_units.setCurrentIndex(1)
            self.volume_units.setCurrentIndex(2)
            self.energy_units.setCurrentIndex(2)

        except Exception as e:
            QMessageBox.critical(self, "Error Applying Configuration",
                                 f"An error occurred while applying the configuration: Exception: {e}")
            return None


    def save_config_to_file_with_filename(self, configFile):
        if not is_file_valid(self.mesh_file) or not is_path_accessable(self.mesh_file):
            QMessageBox.warning(self, "File Error", f"Mesh file '{self.mesh_file}' can't be selected. Check path or existance of it")
            return
        
        config_content = self.validate_input()
        if not config_content:
            QMessageBox.critical(
                self, "Error", f"Failed to save configuration")
            return
    
        if configFile:
            try:
                with open(configFile, "w") as file:
                    dump(config_content, file, indent=4)  # Serialize dict to JSON
                self.log_console.logSignal.emit(f'Successfully saved data to new config: {configFile}\n')
            except Exception as e:
                self.log_console.logSignal.emit(f'Error: Failed to save configuration to {configFile}: Exception: {e}\n')


    def save_config_to_file(self):
        config_content = self.validate_input()
        if not config_content:
            QMessageBox.critical(
                self, "Error", f"Failed to save configuration")
            return

        # Ask the user where to save the file
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.config_file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            "",  # Start directory
            "JSON (*.json)",
            options=options,
        )
        
        # If string is empty - making name with temporary constant 
        if not self.config_file_path:
            self.config_file_path = DEFAULT_TEMP_CONFIG_FILE
        
        # Adding extension if needed
        if not self.config_file_path.endswith('.json'):
            self.config_file_path += '.json'
        
        if self.config_file_path:
            try:
                with open(self.config_file_path, "w") as file:
                    dump(config_content, file, indent=4)  # Serialize dict to JSON
                QMessageBox.information(self, "Success", f"Configuration saved to {self.config_file_path}")
                self.log_console.logSignal.emit(f'Successfully saved data to new config: {self.config_file_path}\n')
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save configuration: Exception: {e}")
                self.log_console.logSignal.emit(f'Error: Failed to save configuration to {self.config_file_path}: Exception: {e}\n')
                
    
    def upload_mesh_file_with_filename(self, meshfilename):
        if meshfilename:
            self.mesh_file = meshfilename
            self.mesh_file_label.setText(f"Selected: {meshfilename}")
            QMessageBox.information(
                self, "Mesh File Selected", f"File: {self.mesh_file}"
            )

        if meshfilename.endswith('.stp'):
            # Show dialog for user input
            dialog = MeshDialog(self)
            if dialog.exec() == QDialog.Accepted:
                mesh_size, mesh_dim = dialog.get_values()
                
                try:
                    mesh_size = float(mesh_size)
                    mesh_dim = int(mesh_dim)
                    if mesh_dim not in [2, 3]:
                        raise ValueError("Mesh dimensions must be 2 or 3.")
                    self.convert_stp_to_msh(meshfilename, mesh_size, mesh_dim)
                except ValueError as e:
                    QMessageBox.warning(self, "Invalid Input", str(e))
                    return None
            else:
                QMessageBox.critical(self, "Error", "Dialog was closed by user. Invalid mesh size or mesh dimensions")
                return
        else:
            self.mesh_file = meshfilename
        
        if self.config_file_path.endswith('.stp'):
            self.mesh_file.replace('.stp', '.msh')
        if self.config_file_path.endswith('.vtk'):
            self.mesh_file.replace('.vtk', '.msh')
        self.meshFileSelected.emit(self.mesh_file)
        self.log_console.logSignal.emit(f'Uploaded mesh: {self.mesh_file}\n')
                
    
    def upload_mesh_file(self):       
        # Open a file dialog when the button is clicked and filter for .msh files
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "Select Mesh File",
            "",
            "Mesh Files (*.msh);;Step Files(*.stp);;VTK (*.vtk);;All Files (*)",
            options=options,
            )
        if fileName:
            self.mesh_file = fileName
            self.mesh_file_label.setText(f"Selected: {fileName}")
            QMessageBox.information(
                self, "Mesh File Selected", f"File: {self.mesh_file}"
            )

        if fileName.endswith('.stp'):
            # Show dialog for user input
            dialog = MeshDialog(self)
            if dialog.exec() == QDialog.Accepted:
                mesh_size, mesh_dim = dialog.get_values()
                try:
                    mesh_size = float(mesh_size)
                    mesh_dim = int(mesh_dim)
                    if mesh_dim not in [2, 3]:
                        raise ValueError("Mesh dimensions must be 2 or 3.")
                    self.convert_stp_to_msh(fileName, mesh_size, mesh_dim)
                except ValueError as e:
                    QMessageBox.warning(self, "Invalid Input", str(e))
                    return None
            else:
                QMessageBox.critical(self, "Error", "Dialog was closed by user. Invalid mesh size or mesh dimensions")
                return None
        else:
            self.mesh_file = fileName
        
        if self.config_file_path.endswith('.stp'):
            self.mesh_file.replace('.stp', '.msh')
        if self.config_file_path.endswith('.vtk'):
            self.mesh_file.replace('.vtk', '.msh')
        self.meshFileSelected.emit(self.mesh_file)
        self.log_console.logSignal.emit(f'Uploaded mesh: {self.mesh_file}\n')
        
        return 1

    def ask_to_upload_mesh_file(self):
        if self.mesh_file:
            reply = QMessageBox.question(self, 'Mesh File', 
                                        f"Mesh file {self.mesh_file} is already chosen. Do you like to rechoose it?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.upload_mesh_file()
                self.log_console.logSignal.emit(f'Uploaded mesh: {self.mesh_file}\n')
            else:
                pass
        else:
            self.upload_mesh_file()
            self.log_console.logSignal.emit(f'Uploaded mesh: {self.mesh_file}\n')

    def convert_stp_to_msh(self, file_path, mesh_size, mesh_dim):
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
            self.mesh_file = output_file
            self.log_console.logSignal.emit(f'Successfully converted {file_path} to {output_file}. Mesh size is {mesh_size}. Mesh dimension: {mesh_dim}\n')

    def load_magnetic_induction(self):
        # TODO: Implement the functionality to load and parse the generated magnetic induction file from Ansys
        pass

    def emit_select_boundary_conditions_signal(self):
        self.selectBoundaryConditionsSignal.emit()
