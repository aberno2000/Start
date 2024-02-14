from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget,
    QVBoxLayout, QWidget,
    QMessageBox, QFileDialog,
    QProgressBar, QPlainTextEdit, 
    QDockWidget, QScrollArea,
    QApplication
)
from sys import exit
from time import time
from json import dump
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QTextCharFormat, QColor, QScreen
from subprocess import run, check_output, CalledProcessError, Popen, PIPE
from config_tab import ConfigTab
from results_tab import ResultsTab
from gedit_tab import GraphicalEditorTab


def insert_colored_text(widget, text, color):
    """
    Inserts colored text into a QPlainTextEdit widget.

    Parameters:
    - widget: QPlainTextEdit, the widget where the text will be inserted.
    - text: str, the text to insert.
    - color: str, the name of the color to use for the text.
    """
    if not isinstance(widget, QPlainTextEdit):
        raise ValueError("widget must be a QPlainTextEdit instance")
    cursor = widget.textCursor()
    text_format = QTextCharFormat()
    text_format.setForeground(QColor(color))
    cursor.mergeCharFormat(text_format)
    cursor.insertText(text, text_format)
    cursor.movePosition(cursor.End)
    widget.setTextCursor(cursor)
    default_format = QTextCharFormat()
    cursor.mergeCharFormat(default_format)


def kill_processes_by_pattern(pattern):
    try:
        # Find processes by the given pattern
        pids = check_output(["pgrep", "-f", pattern]).decode('utf-8').strip().split('\n')
        for pid in pids:
            if pid:  # Ensure the pid is not an empty string
                # Kill each process found by its PID
                run(["kill", "-9", pid], check=True)
                print(f"Process with PID {pid} has been killed.")
    except CalledProcessError as e:
        print(f"No process found with pattern '{pattern}' or error occurred: {e}")


class WindowApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Particle Collision Simulator")
        
        # Retrieve the size of the primary screen
        screen = QApplication.primaryScreen()
        rect = screen.availableGeometry()
        self.setGeometry(rect)

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

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 0)
        self.progressBar.setHidden(True)
        
        # Set the scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Set the central widget
        central_widget = QWidget()
        self.layout = QVBoxLayout(central_widget)        
        self.layout.addWidget(self.tab_widget)
        self.layout.addWidget(self.progressBar)
        
        # Adding central widget to the scroll area
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        
        # Redirecting logs to the console
        self.setup_log_console()
    
    
    def setup_menu_bar(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction('New project', self.create_project, shortcut='Ctrl+N')
        file_menu.addAction('Open project', self.open_project, shortcut='Ctrl+O')
        file_menu.addAction('Save project', self.save_project, shortcut='Ctrl+S')
        file_menu.addSeparator()
        exit_action = file_menu.addAction('Exit', self.close)
        exit_action.setShortcuts(['Ctrl+Q', 'Ctrl+W'])
        

        # Edit Menu
        edit_menu = menu_bar.addMenu('&Edit')
        # TODO: Add actions for Edit menu...

        # Configurations Menu
        configurations_menu = menu_bar.addMenu('&Configurations')
        configurations_menu.addAction('Upload config', 
                                    self.config_tab.upload_config, 
                                    shortcut='Ctrl+Shift+U')   #  Upload config
        configurations_menu.addAction('Save config', 
                                    self.config_tab.save_config_to_file,
                                    shortcut='Ctrl+Shift+S')   #  Save config
        configurations_menu.addSeparator()
        configurations_menu.addAction('Upload mesh',
                                      self.config_tab.upload_mesh_file,
                                      shortcut='Ctrl+Shift+M') #  Upload mesh file

        # Solution Menu
        solution_menu = menu_bar.addMenu('&Simulation')
        solution_menu.addAction('Run', self.run_simulation, shortcut='Ctrl+R')   #  Run
        solution_menu.addAction('Stop', self.stop_simulation, shortcut='Ctrl+T') #  Terminate
        
        # Help Menu
        help_menu = menu_bar.addMenu('&Help')
        about_action = help_menu.addAction('About', self.show_help, shortcut='F1')
        about_action.setShortcut('F1')


    def create_project(self):
        # TODO: Implement
        pass


    def open_project(self):
        # TODO: Implement
        pass
    
    
    def save_project(self):
        # TODO: Implement
        pass


    def setup_tabs(self):
        self.tab_widget.addTab(self.mesh_tab, "Mesh")
        self.tab_widget.addTab(self.results_tab, "Results")
        self.tab_widget.addTab(self.config_tab, "Config")

    
    def setup_log_console(self):
        self.log_console = QPlainTextEdit()
        self.log_console.setReadOnly(True)  # Make the console read-only

        self.log_dock_widget = QDockWidget("Log Console", self)
        self.log_dock_widget.setWidget(self.log_console)
        self.log_dock_widget.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.log_dock_widget.setVisible(True)

        # Add the dock widget to the main window
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock_widget)


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
        self.set_ui_enabled(True)
        
        # Rewrite configs if they have been changed
        try:
            with open(self.config_tab.config_file_path, "w") as file:
                dump(config_content, file, indent=4)  # Serialize dict to JSON
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
            return
        hdf5_filename = self.config_tab.mesh_file.replace(".msh", ".hdf5")
        args = f"{self.config_tab.config_file_path}"

        # Measure execution time
        self.progressBar.setHidden(False)
        start_time = time()
        self.run_cpp(args)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(100)
        exec_time = time() - start_time
        QMessageBox.information(self,
                                "Process Finished",
                                f"The simulation has completed in {exec_time:.3f}s")
        insert_colored_text(self.log_console, '\nSuccessfully: ', 'green')
        insert_colored_text(self.log_console, f'The simulation has completed in {exec_time:.3f}s', 'dark gray')
        self.results_tab.update_plot(hdf5_filename)

        # Re-enable UI components
        self.set_ui_enabled(True)
        self.progressBar.setHidden(True)
        
        
    def stop_simulation(self):
        # TODO: Implement
        pass
        
        
    def keyPressEvent(self, event):
        if (event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Q) or \
            event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_W:
            self.close()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_E:
            kill_processes_by_pattern(r'\./main .*\.json')
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_R:
            self.run_simulation()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_T:
            self.stop_simulation()
        elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier and event.key() == Qt.Key_U:
            self.config_tab.upload_config()
        elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier and event.key() == Qt.Key_S:
            self.config_tab.save_config_to_file()
        elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier and event.key() == Qt.Key_M:
            self.config_tab.upload_mesh_file()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Tab:
            # Iterating by tabs
            currentTabIndex = self.tab_widget.currentIndex()
            totalTabs = self.tab_widget.count()
            nextTabIndex = (currentTabIndex + 1) % totalTabs
            self.tab_widget.setCurrentIndex(nextTabIndex)
        elif event.key() == Qt.Key_F1:
            self.show_help()
        else:
            super().keyPressEvent(event)


    def set_ui_enabled(self, enabled):
        """Enable or disable UI components."""
        self.setEnabled(enabled)
        
    
    def run_cpp(self, args: str) -> None:
        cmd = ["./main"] + args.split()
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        
        for line in process.stdout:
            self.log_console.appendPlainText(line.strip().decode('utf-8'))
            
        for line in process.stderr:
            self.log_console.appendPlainText(line.strip().decode('utf-8'))
        
        process.wait()


    def show_help(self):
        QMessageBox.information(
            self,
            "Help",
            "This is help message. Don't forget to write a desc to ur app here pls!!!",
        )

    def exit(self):
        exit(0)
