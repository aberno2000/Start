from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget,
    QVBoxLayout, QWidget,
    QMessageBox, QFileDialog,
)
from sys import exit
from time import time
from json import dump
from PyQt5.QtCore import Qt
from subprocess import run
from config_tab import ConfigTab
from results_tab import ResultsTab
from gedit_tab import GraphicalEditorTab


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
        self.results_tab = ResultsTab()
        self.config_tab = ConfigTab()
        self.mesh_tab = GraphicalEditorTab(self.config_tab)

        # Connecting signal to detect the selection of mesh file
        self.config_tab.meshFileSelected.connect(self.mesh_tab.set_mesh_file)

        # Setup Tabs
        self.setup_tabs()
        
        # Setup menu bar
        self.setup_menu_bar()

        # Set the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.layout.addWidget(self.tab_widget)
    
    def setup_menu_bar(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu('&File')
        # file_menu.addAction('Open', self.open_file)
        # file_menu.addAction('Save', self.save_file)
        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)

        # Edit Menu
        edit_menu = menu_bar.addMenu('&Edit')
        # TODO: Add actions for Edit menu...

        # Configurations Menu
        configurations_menu = menu_bar.addMenu('&Configurations')
        configurations_menu.addAction('Upload config', self.config_tab.upload_config)
        configurations_menu.addAction('Save config', self.config_tab.save_config_to_file)
        configurations_menu.addSeparator()
        configurations_menu.addAction('Upload mesh', self.config_tab.ask_to_upload_mesh_file)

        # Solution Menu
        solution_menu = menu_bar.addMenu('&Simulation')
        solution_menu.addAction('Start', self.run_simulation)
        solution_menu.addAction('Stop', self.stop_simulation)

        # Help Menu
        help_menu = menu_bar.addMenu('&Help')
        help_menu.addAction('About', self.show_help)

    def setup_tabs(self):
        self.tab_widget.addTab(self.mesh_tab, "Mesh")
        self.tab_widget.addTab(self.results_tab, "Results")
        self.tab_widget.addTab(self.config_tab, "Config")

    def run_simulation(self):
        config_content = self.config_tab.validate_input()
        if config_content is None:
            return
        if not config_content:
            # Prompt the user to select a configuration file
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            self.config_tab.config_file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Configuration File", "", "JSON Files (*.json);;All Files (*)", options=options)

            # If user cancels or selects no file
            if not self.config_tab.config_file_path:
                QMessageBox.warning(self, "No Configuration File Selected",
                                    "Simulation aborted because no configuration file was selected.")
                return

        # Disable UI components
        self.set_ui_enabled(False)

        # Rewrite configs if they have been changed
        try:
            with open(self.config_tab.config_file_path, "w") as file:
                dump(config_content, file, indent=4)  # Serialize dict to JSON
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
            return
        hdf5_filename = self.config_tab.mesh_file.replace(".msh", ".hdf5")

        args = f"{self.config_tab.config_file_path}"
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
        
    def stop_simulation(self):
        pass
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_W and event.modifiers() == Qt.ControlModifier:
            self.close()
        elif event.key() == Qt.Key_Q and event.modifiers() == Qt.ControlModifier:
            self.close()
        else:
            super().keyPressEvent(event)

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
        exit(0)
