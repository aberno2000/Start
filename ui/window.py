from PyQt5.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMessageBox,
    QFileDialog,
)
import sys
import gmsh
from time import time
from subprocess import run, Popen
from config_tab import ConfigTab
from results_tab import ResultsTab


def compile_cpp():
    run(["./compile.sh"], check=True)


def run_cpp(args: str) -> None:
    cmd = ["./main"] + args.split()
    run(cmd, check=True)


class WindowApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Particle Collision Simulator")
        self.setGeometry(100, 100, 1200, 600)

        # Create tab widget and tabs
        self.tab_widget = QTabWidget()
        self.mesh_tab = QWidget()
        self.results_tab = ResultsTab()
        self.config_tab = ConfigTab()

        # Setup Tabs
        self.setup_tabs()

        # Set the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.layout.addWidget(self.tab_widget)
        self.setup_buttons()

    def setup_tabs(self):
        self.tab_widget.addTab(self.mesh_tab, "Mesh")
        self.tab_widget.addTab(self.results_tab, "Results")
        self.tab_widget.addTab(self.config_tab, "Config")

        self.setup_mesh_tab()

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

    def setup_buttons(self):
        buttons_layout = QHBoxLayout()

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_simulation)
        buttons_layout.addWidget(self.run_button)

        self.help_button = QPushButton("Help")
        self.help_button.clicked.connect(self.show_help)
        buttons_layout.addWidget(self.help_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.exit)
        buttons_layout.addWidget(self.exit_button)

        self.layout.addLayout(buttons_layout)

    def run_simulation(self):
        config_content = self.config_tab.validate_input()
        if config_content is None:
            return
        if not config_content:
            # Prompt the user to select a configuration file
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            self.config_tab.config_file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Configuration File", "", "Configuration Files (*.txt);;All Files (*)", options=options)

            # If user cancels or selects no file
            if not self.config_tab.config_file_path:
                QMessageBox.warning(self, "No Configuration File Selected",
                                    "Simulation aborted because no configuration file was selected.")
                return

        # Disable UI components
        self.set_ui_enabled(False)

        # Rewrite configs
        with open(self.config_tab.config_file_path, "w") as file:
            file.write(config_content)
        hdf5_filename = self.config_tab.file_path.replace(".msh", ".hdf5")
        args = f"{self.config_tab.config_file_path} \
        {self.config_tab.file_path}"
        self.config_tab.progress_bar.setRange(0, 0)

        # Measure execution time
        self.start_time = time()
        run_cpp(args)
        end_time = time()
        execution_time = end_time - self.start_time
        self.config_tab.progress_bar.setRange(0, 1)
        self.config_tab.progress_bar.setValue(1)
        QMessageBox.information(self,
                                "Process Finished",
                                f"The simulation has completed in {execution_time:.6f}s")
        self.results_tab.update_plot(hdf5_filename)

        # Re-enable UI components
        self.set_ui_enabled(True)

    def set_ui_enabled(self, enabled):
        """Enable or disable UI components."""
        self.setEnabled(enabled)

    def show_help(self):
        QMessageBox.information(
            self,
            "Help",
            "This is help message. Don't forget to write a desc to ur app here pls!!!",
        )

    def exit(self):
        sys.exit(0)
