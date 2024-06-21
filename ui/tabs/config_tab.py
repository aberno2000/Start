from os.path import dirname
from json import load, dump, JSONDecodeError
from util import *
from field_validators import CustomIntValidator, CustomDoubleValidator
from styles import *
from .configurations import *
from dialogs import MeshDialog
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QComboBox,
    QMessageBox, QLabel, QLineEdit, QFormLayout,
    QGroupBox, QFileDialog, QPushButton, QSizePolicy,
    QSpacerItem, QDialog
)
from PyQt5.QtCore import QSize, pyqtSignal, QRegExp
from PyQt5.QtGui import QRegExpValidator


class ConfigTab(QWidget):
    # Signal to check if mesh file was selected by user
    meshFileSelected = pyqtSignal(str)
    requestToMoveToTheNextTab = pyqtSignal()
    requestToStartSimulation = pyqtSignal()
    selectBoundaryConditionsSignal = pyqtSignal()

    def __init__(self, log_console, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.converter = PhysicalMeasurementUnitsConverter()
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
        nextButton.setToolTip(
            'Check this tab and move to the next with starting the simulation')
        nextButton.clicked.connect(self.next_button_on_clicked)

        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                             QSizePolicy.Minimum)
        button_layout.addSpacerItem(spacer)

        button_layout.addWidget(nextButton)
        self.layout.addLayout(button_layout)

    def next_button_on_clicked(self):
        self.save_config_to_file()

    def setup_mesh_group(self):
        self.mesh_file_label = QLabel("No file selected")
        self.mesh_file_label.setWordWrap(True)

        button_layout = QVBoxLayout()
        self.upload_mesh_button = QPushButton("Upload Mesh File")
        self.upload_mesh_button.setToolTip(HINT_CONFIG_MESH_FILE)
        self.upload_mesh_button.clicked.connect(self.ask_to_upload_mesh_file)
        button_layout.addWidget(self.upload_mesh_button)
        button_layout.addWidget(self.mesh_file_label)
        self.layout.addLayout(button_layout)

    def setup_particles_group(self):
        particles_group_box = QGroupBox("Particles")
        particles_layout = QFormLayout()

        self.projective_input = QComboBox()
        self.gas_input = QComboBox()
        self.gas_input.setToolTip(HINT_CONFIG_GAS_SELECTION)
        gas_particles = ["O2", "Ar", "Ne", "He"]
        self.gas_input.addItems(gas_particles)
        particles_layout.addRow(QLabel("Gas:"), self.gas_input)

        particles_group_box.setLayout(particles_layout)
        self.layout.addWidget(particles_group_box)

    def setup_scattering_model_group(self):
        scattering_group_box = QGroupBox("Scattering Model")
        scattering_layout = QVBoxLayout()

        self.model_input = QComboBox()
        self.model_input.setToolTip(HINT_CONFIG_SCATTERING_MODEL)
        self.model_input.addItems(["HS", "VHS", "VSS"])
        scattering_layout.addWidget(self.model_input)

        scattering_group_box.setLayout(scattering_layout)
        self.layout.addWidget(scattering_group_box)

    def create_simulation_field(self,
                                label_text,
                                input_type,
                                units=None,
                                default_unit=None,
                                default_value="0.0"):
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
            layout.addWidget(units_combobox, alignment=Qt.AlignLeft)

        converted_label = QLabel(
            f"{default_value} {units[0] if units else ''}")
        layout.addWidget(converted_label, alignment=Qt.AlignRight)

        self.simulation_layout.addRow(QLabel(label_text), layout)

        return input_field, units_combobox if units else None, converted_label

    def create_solver_params_field(self,
                                   parent_layout,
                                   label_text,
                                   default_value,
                                   units=None,
                                   is_combobox=False):
        DEFAULT_LINE_EDIT_WIDTH = 175
        DEFAULT_COMBOBOX_WIDTH = 85

        if is_combobox:
            input_field = QComboBox()
            # default_value should be a list of items for combobox
            input_field.addItems(default_value)
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
            layout.addWidget(units_combobox, alignment=Qt.AlignLeft)

        parent_layout.addRow(QLabel(label_text), layout)
        return input_field, units_combobox

    def setup_simulation_parameters_group(self):
        self.simulation_layout = QFormLayout()
        simulation_group_box = QGroupBox("Simulation Parameters")
        simulation_group_box.setLayout(self.simulation_layout)

        self.simulation_layout.addRow(
            QLabel(
                f"System: {get_os_info()} has {get_thread_count()} threads"))

        # Thread count
        self.thread_count_input, _, _ = self.create_simulation_field(
            "Thread count:", QLineEdit)
        self.thread_count_input.setToolTip(HINT_CONFIG_THREAD_COUNT)
        self.thread_count_input.setValidator(
            CustomIntValidator(LIMIT_CONFIG_MIN_THREAD_COUNT,
                               LIMIT_CONFIG_MAX_THREAD_COUNT))

        # Time Step with units
        self.time_step_input, self.time_step_units, self.time_step_converted = self.create_simulation_field(
            "Time Step:", QLineEdit, ["ns", "μs", "ms", "s", "min"], "ms",
            str(DEFAULT_TIME_STEP))
        self.time_step_input.setToolTip(HINT_CONFIG_TIME_STEP)
        self.time_step_input.setValidator(
            CustomDoubleValidator(LIMIT_CONFIG_MIN_TIME_STEP,
                                  LIMIT_CONFIG_MAX_TIME_STEP,
                                  SIM_PARAMS_PRECISION_TIME_STEP))

        # Simulation time with units
        self.simulation_time_input, self.simulation_time_units, self.simulation_time_converted = self.create_simulation_field(
            "Simulation Time:", QLineEdit, ["ns", "μs", "ms", "s", "min"], "s",
            str(DEFAULT_SIMULATION_TIME))
        self.simulation_time_input.setToolTip(HINT_CONFIG_SIMULATION_TIME)
        self.simulation_time_input.setValidator(
            CustomDoubleValidator(LIMIT_CONFIG_MIN_SIMULATION_TIME,
                                  LIMIT_CONFIG_MAX_SIMULATION_TIME,
                                  SIM_PARAMS_PRECISION_SIMULATION_TIME))

        # Temperature with units
        self.temperature_input, self.temperature_units, self.temperature_converted = self.create_simulation_field(
            "Temperature:", QLineEdit, ["K", "F", "C"], "K",
            str(DEFAULT_TEMPERATURE))
        self.temperature_input.setToolTip(HINT_CONFIG_TEMPERATURE)
        self.temperature_input.setValidator(
            CustomDoubleValidator(LIMIT_CONFIG_MIN_TEMPERATURE,
                                  LIMIT_CONFIG_MAX_TEMPERATURE,
                                  SIM_PARAMS_PRECISION_TEMPERATURE))

        # Pressure with units
        self.pressure_input, self.pressure_units, self.pressure_converted = self.create_simulation_field(
            "Pressure:", QLineEdit, ["mPa", "Pa", "kPa", "psi"], "Pa",
            str(DEFAULT_PRESSURE))
        self.pressure_input.setToolTip(HINT_CONFIG_PRESSURE)
        self.pressure_input.setValidator(
            CustomDoubleValidator(LIMIT_CONFIG_MIN_PRESSURE,
                                  LIMIT_CONFIG_MAX_PRESSURE,
                                  SIM_PARAMS_PRECISION_PRESSURE))

        simulation_group_box.setLayout(self.simulation_layout)

        # Create PIC and FEM group boxes
        picfem_group_box = QGroupBox(
            "Particle In Cell (PIC) and Finite Element Method (FEM) Parameters"
        )
        pic_layout = QFormLayout()
        fem_layout = QFormLayout()
        picfem_layout = QHBoxLayout()
        picfem_layout.addLayout(pic_layout)
        picfem_layout.addLayout(fem_layout)
        picfem_group_box.setLayout(picfem_layout)

        # Add PIC and FEM fields
        self.pic_input = QLineEdit()
        self.pic_input.setText(f"{DEFAULT_CUBIC_GRID_SIZE}")
        self.pic_input.setFixedWidth(DEFAULT_LINE_EDIT_WIDTH)
        self.pic_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.pic_input.setValidator(
            CustomDoubleValidator(LIMIT_CONFIG_MIN_CUBIC_GRID_SIZE,
                                  LIMIT_CONFIG_MAX_CUBIC_GRID_SIZE, 3))
        self.pic_input.setToolTip(HINT_CONFIG_CUBIC_GRID_SIZE)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(50, 0, 0, 0)
        h_layout.addWidget(self.pic_input)
        pic_layout.addRow(QLabel("Cubic grid size:"), h_layout)

        self.fem_input = QLineEdit()
        self.fem_input.setText(f"{DEFAULT_FEM_ACCURACY}")
        self.fem_input.setFixedWidth(DEFAULT_LINE_EDIT_WIDTH)
        self.fem_input.setStyleSheet(DEFAULT_QLINEEDIT_STYLE)
        self.fem_input.setValidator(
            CustomIntValidator(LIMIT_CONFIG_MIN_FEM_ACCURACY,
                               LIMIT_CONFIG_MAX_FEM_ACCURACY))
        self.fem_input.setToolTip(HINT_CONFIG_FEM_ACCURACY)
        h1_layout = QHBoxLayout()
        h1_layout.setContentsMargins(25, 0, 0, 0)
        h1_layout.addWidget(self.fem_input)
        fem_layout.addRow(QLabel("FEM calculation accuracy:"), h1_layout)

        # Add Load Magnetic Induction button
        self.load_magnetic_induction_button = QPushButton("Load Magnetic Induction")
        self.load_magnetic_induction_button.setToolTip(HINT_CONFIG_LOAD_MAGNETIC_INDUCTION)
        self.load_magnetic_induction_button.setFixedWidth(DEFAULT_LINE_EDIT_WIDTH)
        self.load_magnetic_induction_button.clicked.connect(self.load_magnetic_induction)
        fem_layout.addRow(self.load_magnetic_induction_button)

        # Add Select Boundary Conditions button
        self.select_boundary_conditions_button = QPushButton("Select Boundary Conditions")
        self.select_boundary_conditions_button.setToolTip(HINT_CONFIG_SELECT_BOUNDARY_CONDITIONS)
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
        self.solvername_input = QComboBox()
        self.solvername_input.setFixedWidth(DEFAULT_LINE_EDIT_WIDTH)
        self.solvername_input.addItems(ITERATIVE_SOLVER_NAMES)
        self.solvername_input.setToolTip(HINT_CONFIG_SOLVERNAME)
        self.solvername_input.currentIndexChanged.connect(
            self.update_solver_parameters)
        additional_layout_left.addRow(QLabel("Solver:"), self.solvername_input)

        # Parameters for solvers
        self.solver_parameters = {}

        self.solver_parameters[
            ITERATIVE_SOLVER_MAX_ITERATION_FIELD_NAME] = self.create_solver_params_field(
                additional_layout_left, "Max Iterations:",
                f"{DEFAULT_MAX_ITERATIONS}")
        self.solver_parameters[
            ITERATIVE_SOLVER_CONVERGENCE_TOLERANCE_FIELD_NAME] = self.create_solver_params_field(
                additional_layout_left, "Convergence Tolerance:",
                f"{DEFAULT_CONVERGENCE_TOLERANCE}")
        self.solver_parameters[
            ITERATIVE_SOLVER_OUTPUT_FREQUENCY_FIELD_NAME] = self.create_solver_params_field(
                additional_layout_left, "Output Frequency:",
                f"{DEFAULT_OUTPUT_FREQUENCY}")
        self.solver_parameters[
            ITERATIVE_SOLVER_NUM_BLOCKS_FIELD_NAME] = self.create_solver_params_field(
                additional_layout_left, "Num Blocks:", f"{DEFAULT_NUM_BLOCKS}")
        self.solver_parameters[
            ITERATIVE_SOLVER_BLOCK_SIZE_FIELD_NAME] = self.create_solver_params_field(
                additional_layout_left, "Block Size:", f"{DEFAULT_BLOCK_SIZE}")

        self.solver_parameters[
            ITERATIVE_SOLVER_MAX_RESTARTS_FIELD_NAME] = self.create_solver_params_field(
                additional_layout_right, "Max Restarts:",
                f"{DEFAULT_MAX_RESTARTS}")
        self.solver_parameters[
            ITERATIVE_SOLVER_FLEXIBLE_GMRES_FIELD_NAME] = self.create_solver_params_field(
                additional_layout_right,
                "Flexible GMRES:", ["false", "true"],
                is_combobox=True)
        self.solver_parameters[
            ITERATIVE_SOLVER_ORTHOGONALIZATION_FIELD_NAME] = self.create_solver_params_field(
                additional_layout_right,
                "Orthogonalization:", ["ICGS", "IMGS"],
                is_combobox=True)
        self.solver_parameters[
            ITERATIVE_SOLVER_ADAPTIVE_BLOCK_SIZE_FIELD_NAME] = self.create_solver_params_field(
                additional_layout_right,
                "Adaptive Block Size:", ["false", "true"],
                is_combobox=True)
        self.solver_parameters[
            ITERATIVE_SOLVER_CONVERGENCE_TEST_FREQUENCY_FIELD_NAME] = self.create_solver_params_field(
                additional_layout_right, "Convergence Test Frequency:", "-1")
        self.solvername_input.setCurrentIndex(2)  # By default using GMRES

        # Applying validators to different fields
        exp_regexp = QRegExp(r'1e-([1-9]|[1-4][0-9]|50)|1e-1')

        self.solver_parameters[ITERATIVE_SOLVER_MAX_ITERATION_FIELD_NAME][
            0].setValidator(
                CustomIntValidator(LIMIT_CONFIG_MIN_ITERATIONS,
                                   LIMIT_CONFIG_MAX_ITERATIONS))
        self.solver_parameters[
            ITERATIVE_SOLVER_CONVERGENCE_TOLERANCE_FIELD_NAME][0].setValidator(
                QRegExpValidator(exp_regexp))
        self.solver_parameters[ITERATIVE_SOLVER_OUTPUT_FREQUENCY_FIELD_NAME][
            0].setValidator(
                CustomIntValidator(LIMIT_CONFIG_MIN_OUTPUT_FREQUENCY,
                                   LIMIT_CONFIG_MAX_OUTPUT_FREQUENCY))
        self.solver_parameters[ITERATIVE_SOLVER_NUM_BLOCKS_FIELD_NAME][
            0].setValidator(
                CustomIntValidator(LIMIT_CONFIG_MIN_NUM_BLOCKS,
                                   LIMIT_CONFIG_MAX_NUM_BLOCKS))
        self.solver_parameters[ITERATIVE_SOLVER_BLOCK_SIZE_FIELD_NAME][
            0].setValidator(
                CustomIntValidator(LIMIT_CONFIG_MIN_BLOCK_SIZE,
                                   LIMIT_CONFIG_MAX_BLOCK_SIZE))
        self.solver_parameters[ITERATIVE_SOLVER_MAX_RESTARTS_FIELD_NAME][
            0].setValidator(
                CustomIntValidator(LIMIT_CONFIG_MIN_MAX_RESTARTS,
                                   LIMIT_CONFIG_MAX_MAX_RESTARTS))

        # Adding tooltips to different fields
        self.solver_parameters[ITERATIVE_SOLVER_MAX_ITERATION_FIELD_NAME][
            0].setToolTip(HINT_CONFIG_MAX_ITERATIONS)
        self.solver_parameters[
            ITERATIVE_SOLVER_CONVERGENCE_TOLERANCE_FIELD_NAME][0].setToolTip(
                HINT_CONFIG_CONVERGENCE_TOLERANCE)
        self.solver_parameters[ITERATIVE_SOLVER_OUTPUT_FREQUENCY_FIELD_NAME][
            0].setToolTip(HINT_CONFIG_OUTPUT_FREQUENCY)
        self.solver_parameters[ITERATIVE_SOLVER_NUM_BLOCKS_FIELD_NAME][
            0].setToolTip(HINT_CONFIG_NUM_BLOCKS)
        self.solver_parameters[ITERATIVE_SOLVER_BLOCK_SIZE_FIELD_NAME][
            0].setToolTip(HINT_CONFIG_BLOCK_SIZE)
        self.solver_parameters[ITERATIVE_SOLVER_MAX_RESTARTS_FIELD_NAME][
            0].setToolTip(HINT_CONFIG_MAX_RESTARTS)
        self.solver_parameters[ITERATIVE_SOLVER_FLEXIBLE_GMRES_FIELD_NAME][
            0].setToolTip(HINT_CONFIG_FLEXIBLE_GMRES)
        self.solver_parameters[ITERATIVE_SOLVER_ORTHOGONALIZATION_FIELD_NAME][
            0].setToolTip(HINT_CONFIG_ORTHOGONALIZATION)
        self.solver_parameters[
            ITERATIVE_SOLVER_ADAPTIVE_BLOCK_SIZE_FIELD_NAME][0].setToolTip(
                HINT_CONFIG_ADAPTIVE_BLOCK_SIZE)
        self.solver_parameters[
            ITERATIVE_SOLVER_CONVERGENCE_TEST_FREQUENCY_FIELD_NAME][
                0].setToolTip(HINT_CONFIG_CONVERGENCE_TEST_FREQUENCY)

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

    def update_converted_values(self):
        self.time_step_converted.setText(
            f"{self.converter.to_seconds(self.time_step_input.text(), self.time_step_units.currentText())} s"
        )
        self.simulation_time_converted.setText(
            f"{self.converter.to_seconds(self.simulation_time_input.text(), self.simulation_time_units.currentText())} s"
        )
        self.temperature_converted.setText(
            f"{self.converter.to_kelvin(self.temperature_input.text(), self.temperature_units.currentText())} K"
        )
        self.pressure_converted.setText(
            f"{self.converter.to_pascal(self.pressure_input.text(), self.pressure_units.currentText())} Pa"
        )

    def update_solver_parameters(self):
        solver = self.solvername_input.currentText()

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

        if solver in ITERATIVE_SOLVER_VISIBLE_PARAMETERS:
            for param in ITERATIVE_SOLVER_VISIBLE_PARAMETERS[solver]:
                self.solver_parameters[param][0].setEnabled(True)
                if isinstance(self.solver_parameters[param][0], QLineEdit):
                    self.solver_parameters[param][0].setStyleSheet(
                        DEFAULT_QLINEEDIT_STYLE)
                elif isinstance(self.solver_parameters[param][0], QComboBox):
                    self.solver_parameters[param][0].setStyleSheet(
                        DEFAULT_COMBOBOX_STYLE)

                if self.solver_parameters[param][1] is not None:
                    self.solver_parameters[param][1].setEnabled(True)
                    if isinstance(self.solver_parameters[param][1], QLineEdit):
                        self.solver_parameters[param][1].setStyleSheet(
                            DEFAULT_QLINEEDIT_STYLE)
                    elif isinstance(self.solver_parameters[param][1],
                                    QComboBox):
                        self.solver_parameters[param][1].setStyleSheet(
                            DEFAULT_COMBOBOX_STYLE)

    def upload_config(self, config_file: str = None):
        if config_file:
            self.config_file_path = config_file
        else:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            self.config_file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Configuration File",
                "",
                "JSON (*.json);;All Files (*)",
                options=options)

        if self.config_file_path:
            if not is_file_valid(self.config_file_path):
                QMessageBox.warning(
                    self, "Invalid File",
                    "The selected file is invalid or cannot be accessed.")
                return

            if self.read_config_file(self.config_file_path) == 1:
                return

            if not is_path_accessable(self.mesh_file):
                QMessageBox.warning(
                    self, "File Error",
                    f"Your file {self.mesh_file} is unaccessible. Check the path or permissions to this path: {dirname(self.config_file_path)}"
                )
                return

            self.meshFileSelected.emit(self.mesh_file)
            self.log_console.logSignal.emit(
                f'Selected configuration: {self.config_file_path}\n')
        else:
            QMessageBox.warning(self, "No Configuration File Selected",
                                "No configuration file was uploaded.")
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
            self.mesh_file_label.setText(f"Selected: {self.mesh_file}")

            self.thread_count_input.setText(str(config.get('Threads', '')))
            self.time_step_input.setText(str(config.get('Time Step', '')))
            self.simulation_time_input.setText(
                str(config.get('Simulation Time', '')))
            self.temperature_input.setText(str(config.get('T', '')))
            self.pressure_input.setText(str(config.get('P', '')))

            solvername_text = config.get("solverName")
            solvername_index = self.solvername_input.findText(
                solvername_text, Qt.MatchFixedString)
            if solvername_index >= 0:
                self.solvername_input.setCurrentIndex(solvername_index)

            gas_text = config.get("Gas")
            gas_index = self.gas_input.findText(gas_text, Qt.MatchFixedString)
            if gas_index >= 0:
                self.gas_input.setCurrentIndex(gas_index)

            model_index = self.model_input.findText(config.get('Model', ''),
                                                    Qt.MatchFixedString)
            if model_index >= 0:
                self.model_input.setCurrentIndex(model_index)

            self.pic_input.setText(config.get('EdgeSize', ''))
            self.fem_input.setText(config.get('DesiredAccuracy', ''))

            for key, (input_field,
                      units_combobox) in self.solver_parameters.items():
                if key in config:
                    if isinstance(input_field, QLineEdit):
                        input_field.setText(config[key])
                    elif isinstance(input_field, QComboBox):
                        index = input_field.findText(config[key],
                                                     Qt.MatchFixedString)
                        if index >= 0:
                            input_field.setCurrentIndex(index)

            # Applying all measurement to SI (International System of Units)
            self.time_step_units.setCurrentIndex(3)
            self.simulation_time_units.setCurrentIndex(3)
            self.temperature_units.setCurrentIndex(0)
            self.pressure_units.setCurrentIndex(1)

        except Exception as e:
            QMessageBox.critical(self, "Error Applying Configuration", f"An error occurred while applying the configuration: Exception: {e}")
            return None

    def save_solver_params_to_dict(self):
        solver_params = {}
        for key, (input_field,
                  units_combobox) in self.solver_parameters.items():
            if isinstance(input_field, QLineEdit):
                solver_params[key] = input_field.text()
            elif isinstance(input_field, QComboBox):
                solver_params[key] = input_field.currentText()
        solver_params["solverName"] = self.solvername_input.currentText()
        return solver_params

    def save_picfem_params_to_dict(self):
        picfem_params = {}

        picfem_params["EdgeSize"] = self.pic_input.text()
        picfem_params["DesiredAccuracy"] = self.fem_input.text()
        return picfem_params

    def save_boundary_conditions_to_dict(self, config_file_path: str):
        boundary_conditions = {}
        try:
            with open(config_file_path, 'r') as file:
                data = load(file)
                if "Boundary Conditions" in data:
                    boundary_conditions = data["Boundary Conditions"]
        except FileNotFoundError:
            pass
        except JSONDecodeError as e:
            QMessageBox.critical(
                self, "Error",
                f"Error parsing JSON file '{config_file_path}': {e}")
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"An error occurred while reading the configuration file '{config_file_path}': {e}"
            )

        return boundary_conditions

    def check_particle_sources(self, config_file_path):
        sources = {}
        try:
            with open(config_file_path, 'r') as file:
                data = load(file)

                if "ParticleSourcePoint" in data:
                    sources["ParticleSourcePoint"] = data[
                        "ParticleSourcePoint"]
                if "ParticleSourceSurface" in data:
                    sources["ParticleSourceSurface"] = data[
                        "ParticleSourceSurface"]

                if not sources:
                    QMessageBox.warning(
                        self, "Particle Sources",
                        f'Warning: No particle source defined in the configuration file: {config_file_path}\n'
                    )
                    self.log_console.printWarning(
                        f'Warning: No particle source defined in the configuration file: {config_file_path}\n'
                    )
                    return

                return 1

        except FileNotFoundError:
            QMessageBox.warning(
                self, "Warning",
                f"Configuration file not found: {config_file_path}")
            return
        except JSONDecodeError as e:
            QMessageBox.critical(
                self, "Error",
                f"Error parsing JSON file '{config_file_path}': {e}")
            return
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"An error occurred while reading the configuration file '{config_file_path}': {e}"
            )
            return

    def save_config_to_file(self):
        config_content = self.read_ui_values()
        if not config_content:
            return

        if not self.config_file_path:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            self.config_file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Configuration",
                "",
                "JSON (*.json)",
                options=options,
            )

            if not self.config_file_path:
                return

            if not self.config_file_path.endswith('.json'):
                self.config_file_path += '.json'

        if not is_file_valid(self.mesh_file) or not is_path_accessable(
                self.mesh_file):
            QMessageBox.warning(
                self, "File Error",
                f"Mesh file '{self.mesh_file}' can't be selected. Check path or existence of it"
            )
            return

        try:
            with open(self.config_file_path, "w") as file:
                dump(config_content, file, indent=4)
            self.check_particle_sources(self.config_file_path)

            QMessageBox.information(
                self, "Success",
                f"Configuration saved to {self.config_file_path}")
            self.log_console.logSignal.emit(
                f'Successfully saved data to new config: {self.config_file_path}\n'
            )

            self.upload_mesh_file(False)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save configuration: Exception: {e}")
            self.log_console.logSignal.emit(
                f'Error: Failed to save configuration to {self.config_file_path}: Exception: {e}\n'
            )

    def upload_mesh_file(self, need_to_create_actor: bool = True):
        self.mesh_file = None

        if not self.mesh_file:
            # Open a file dialog when the button is clicked and filter for .msh files
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            self.mesh_file, _ = QFileDialog.getOpenFileName(
                self,
                "Select Mesh File",
                "",
                "Mesh Files (*.msh);;Step Files(*.stp);;VTK (*.vtk);;All Files (*)",
                options=options,
            )

        if not self.mesh_file:
            QMessageBox.warning(self, "No Mesh File Selected",
                                "No mesh file was uploaded.")
            return

        self.mesh_file_label.setText(f"Selected: {self.mesh_file}")
        QMessageBox.information(self, "Mesh File Selected",
                                f"File: {self.mesh_file}")

        if self.mesh_file.endswith('.stp'):
            # Show dialog for user input
            dialog = MeshDialog(self)
            if dialog.exec() == QDialog.Accepted:
                mesh_size, mesh_dim = dialog.get_values()
                try:
                    mesh_size = float(mesh_size)
                    mesh_dim = int(mesh_dim)
                    if mesh_dim not in [2, 3]:
                        raise ValueError("Mesh dimensions must be 2 or 3.")
                    self.convert_stp_to_msh(self.mesh_file, mesh_size,
                                            mesh_dim)
                except ValueError as e:
                    QMessageBox.warning(self, "Invalid Input", str(e))
                    return None
            else:
                QMessageBox.critical(
                    self, "Error",
                    "Dialog was closed by user. Invalid mesh size or mesh dimensions"
                )
                return None

        if self.mesh_file.endswith('.stp'):
            self.mesh_file = self.mesh_file.replace('.stp', '.msh')
        if self.mesh_file.endswith('.vtk'):
            self.mesh_file = self.mesh_file.replace('.vtk', '.msh')

        if need_to_create_actor:
            self.meshFileSelected.emit(self.mesh_file)
        self.log_console.logSignal.emit(f'Uploaded mesh: {self.mesh_file}\n')

    def ask_to_upload_mesh_file(self):
        if self.mesh_file:
            reply = QMessageBox.question(
                self, 'Mesh File',
                f"Mesh file {self.mesh_file} is already chosen. Do you like to rechoose it?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.upload_mesh_file()
            else:
                pass
        else:
            self.upload_mesh_file()

    def convert_stp_to_msh(self, file_path, mesh_size, mesh_dim):
        from gmsh import initialize, finalize, isInitialized, write, model, option
        
        try:
            if not isInitialized():
                initialize()
            
            model.add("model")
            model.occ.importShapes(file_path)
            model.occ.synchronize()
            option.setNumber("Mesh.MeshSizeMin", mesh_size)
            option.setNumber("Mesh.MeshSizeMax", mesh_size)

            if mesh_dim == 2:
                model.mesh.generate(2)
            elif mesh_dim == 3:
                model.mesh.generate(3)

            output_file = file_path.replace(".stp", ".msh")
            write(output_file)
        
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"An error occurred during conversion: {str(e)}")
            return None
        finally:
            if isInitialized():
                finalize()
            
            self.mesh_file = output_file
            self.log_console.logSignal.emit(f'Successfully converted {file_path} to {output_file}. Mesh size is {mesh_size}. Mesh dimension: {mesh_dim}\n')

    def load_magnetic_induction(self):
        # TODO: Implement the functionality to load and parse the generated magnetic induction file from Ansys
        pass
    
    def emit_select_boundary_conditions_signal(self):
        self.selectBoundaryConditionsSignal.emit()

    def sync_config_with_ui(self):
        if self.check_particle_sources(self.config_file_path) != 1:
            return

        try:
            with open(self.config_file_path, 'r') as file:
                config_data = load(file)
        except FileNotFoundError:
            QMessageBox.warning(
                self, "Warning",
                f"Configuration file not found: {self.config_file_path}")
            return
        except JSONDecodeError as e:
            QMessageBox.critical(
                self, "Error",
                f"Error parsing JSON file '{self.config_file_path}': {e}")
            return
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"An error occurred while reading the configuration file '{self.config_file_path}': {e}"
            )
            return

        updated = False

        # Helper function to update config and mark as updated
        def update_config(key, value):
            nonlocal updated
            if config_data.get(key) != value:
                config_data[key] = value
                updated = True

        # Compare and update config values
        update_config("Mesh File", self.mesh_file)
        update_config("Threads", int(self.thread_count_input.text()))
        update_config(
            "Time Step",
            self.converter.to_seconds(self.time_step_input.text(),
                                      self.time_step_units.currentText()))
        update_config(
            "Simulation Time",
            self.converter.to_seconds(
                self.simulation_time_input.text(),
                self.simulation_time_units.currentText()))
        update_config(
            "T",
            self.converter.to_kelvin(self.temperature_input.text(),
                                     self.temperature_units.currentText()))
        update_config(
            "P",
            self.converter.to_pascal(self.pressure_input.text(),
                                     self.pressure_units.currentText()))
        update_config("Gas", self.gas_input.currentText())
        update_config("Model", self.model_input.currentText())
        update_config("EdgeSize", self.pic_input.text())
        update_config("DesiredAccuracy", self.fem_input.text())
        update_config("solverName", self.solvername_input.currentText())

        # Update solver parameters
        for key, (input_field,
                  units_combobox) in self.solver_parameters.items():
            if isinstance(input_field, QLineEdit):
                update_config(key, input_field.text())
            elif isinstance(input_field, QComboBox):
                update_config(key, input_field.currentText())

        # Save updated config if there were any changes
        if updated:
            try:
                with open(self.config_file_path, 'w') as file:
                    dump(config_data, file, indent=4)
            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"An error occurred while writing to the configuration file '{self.config_file_path}': {e}"
                )

        return 1

    def read_ui_values(self):
        try:
            config_content = {
                "Mesh File":
                self.mesh_file,
                "Threads":
                int(self.thread_count_input.text()),
                "Time Step":
                self.converter.to_seconds(self.time_step_input.text(),
                                          self.time_step_units.currentText()),
                "Simulation Time":
                self.converter.to_seconds(
                    self.simulation_time_input.text(),
                    self.simulation_time_units.currentText()),
                "T":
                self.converter.to_kelvin(self.temperature_input.text(),
                                         self.temperature_units.currentText()),
                "P":
                self.converter.to_pascal(self.pressure_input.text(),
                                         self.pressure_units.currentText()),
                "Gas":
                self.gas_input.currentText(),
                "Model":
                self.model_input.currentText(),
                "EdgeSize":
                self.pic_input.text(),
                "DesiredAccuracy":
                self.fem_input.text(),
                "solverName":
                self.solvername_input.currentText()
            }

            for key, (input_field,
                      units_combobox) in self.solver_parameters.items():
                if isinstance(input_field, QLineEdit):
                    config_content[key] = input_field.text()
                elif isinstance(input_field, QComboBox):
                    config_content[key] = input_field.currentText()

            return config_content
        except ValueError as e:
            QMessageBox.critical(self, "Invalid Input",
                                 f"Error in input fields: Exception: {e}")
            return None
