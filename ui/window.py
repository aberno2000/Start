from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget,
    QVBoxLayout, QWidget,
    QMessageBox, QFileDialog,
    QProgressBar, QScrollArea, 
    QApplication, QColorDialog,
    QLabel
)
import signal
from sys import exit
from time import time
from json import dump
from PyQt5.QtCore import Qt, QProcess
from config_tab import ConfigTab
from results_tab import ResultsTab
from gedit_tab import GraphicalEditorTab
from log_console import LogConsole
from util import ShortcutsInfoDialog


class WindowApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.process = QProcess(self)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.finished.connect(self.on_process_finished)
        
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
        self.log_console = LogConsole()

        # Connecting signal to detect the selection of mesh file
        self.config_tab.meshFileSelected.connect(self.mesh_tab.set_mesh_file)

        # Setup Tabs
        self.setup_tabs()
        
        # Setup menu bar
        self.setup_menu_bar()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setHidden(True)
        
        # Set the scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Set the central widget
        central_widget = QWidget()
        self.layout = QVBoxLayout(central_widget)        
        self.layout.addWidget(self.tab_widget)
        self.layout.addWidget(self.progress_bar)
        
        # Adding central widget to the scroll area
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        
        # Add the dock widget to the main window
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_console.log_dock_widget)
        
        # Setting default background colors of both vtk renderers
        self.mesh_tab.geditor.renderer.SetBackground(0.1, 0.2, 0.2)
        self.results_tab.renderer.SetBackground(0.1, 0.2, 0.2)

    
    def read_stderr(self):
        errout = self.process.readAllStandardError().data().decode('utf-8').strip()
        self.log_console.log_console.appendPlainText(errout)


    def read_stdout(self):
        out = self.process.readAllStandardOutput().data().decode('utf-8').strip()
        self.log_console.log_console.appendPlainText(out)
        
    
    def on_process_finished(self, exitCode, exitStatus):
        self.progress_bar.setHidden(True)
        exec_time = time() - self.start_time
        self.progress_bar.setValue(100)
        
        if exitStatus == QProcess.NormalExit and exitCode == 0:
            self.results_tab.update_plot(self.hdf5_filename)
            self.log_console.insert_colored_text('\nSuccessfully: ', 'green')
            self.log_console.insert_colored_text(f'The simulation has completed in {exec_time:.3f}s', 'dark gray')
            QMessageBox.information(self,
                                    "Process Finished",
                                    f"The simulation has completed in {exec_time:.3f}s")
        else:
            self.results_tab.clear_plot()
            signal_name = signal.Signals(exitCode).name
            
            self.log_console.insert_colored_text('\nWarning: ', 'yellow')
            self.log_console.insert_colored_text(f'The simulation has been forcibly stopped with a code {exitCode} <{signal_name}>.', 'dark gray')
            QMessageBox.information(self, 
                                    "Simulation Stopped", 
                                    f"The simulation has been forcibly stopped with a code {exitCode} <{signal_name}>.")
    
    
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
        style_menu = edit_menu.addMenu('Application Style')
        style_menu.addAction('Default', lambda: self.change_style('default'))
        style_menu.addAction('Dark', lambda: self.change_style('dark'))
        style_menu.addAction('Light', lambda: self.change_style('light'))
        style_menu.addAction('Night', lambda: self.change_style('night'))
        style_menu.addAction('Classic', lambda: self.change_style('classic'))
        style_menu.addAction('Bright', lambda: self.change_style('bright'))
        
        bg_color_menu = edit_menu.addMenu('Background Color')
        bg_color_menu.addAction('Default', lambda: self.change_background_color('default'))
        bg_color_menu.addAction('White', lambda: self.change_background_color('white'))
        bg_color_menu.addAction('Light Gray', lambda: self.change_background_color('light gray'))
        bg_color_menu.addAction('Gray', lambda: self.change_background_color('gray'))
        bg_color_menu.addAction('Dark Gray', lambda: self.change_background_color('dark gray'))
        bg_color_menu.addAction('Black', lambda: self.change_background_color('black'))
        bg_color_menu.addAction('Custom', lambda: self.change_background_color('custom'))
        
        edit_menu.addAction('Show Shortcuts', self.show_shortcuts)

        # Configurations Menu
        configurations_menu = menu_bar.addMenu('&Configurations')
        configurations_menu.addAction('Upload Config', 
                                    self.config_tab.upload_config, 
                                    shortcut='Ctrl+Shift+U')   #  Upload config
        configurations_menu.addAction('Save Config', 
                                    self.config_tab.save_config_to_file,
                                    shortcut='Ctrl+Shift+S')   #  Save config
        configurations_menu.addSeparator()
        configurations_menu.addAction('Upload Mesh',
                                      self.config_tab.upload_mesh_file,
                                      shortcut='Ctrl+Shift+M') #  Upload mesh file

        # Solution Menu
        solution_menu = menu_bar.addMenu('&Simulation')
        solution_menu.addAction('Run', self.start_simulation, shortcut='Ctrl+R') #  Run
        solution_menu.addAction('Stop', self.stop_simulation, shortcut='Ctrl+T') #  Terminate
        
        # Help Menu
        help_menu = menu_bar.addMenu('&Help')
        help_menu.addAction('About', self.show_help, shortcut='F1')


    def change_style(self, style):
        if style == 'dark':
            self.setStyleSheet("QWidget { background-color: #333; color: white; }")
        elif style == 'light':
            self.setStyleSheet("QWidget { background-color: #eee; color: black; }")
        elif style == 'night':
            self.setStyleSheet("QWidget { background-color: #000; color: #0f0; }")
        elif style == 'classic':
            self.setStyleSheet("QWidget { background-color: #f0f0f0; color: black; }")
        elif style == 'bright':
            self.setStyleSheet("QWidget { background-color: white; color: #666; }")
        elif style == 'default':
            self.setStyleSheet("")
        else:
            self.setStyleSheet("")

    
    def change_background_color(self, color):
        if color == "default":
            bgColor = [0.1, 0.2, 0.2]
        elif color == "black":
            bgColor = [0, 0, 0]
        elif color == "gray":
            bgColor = [0.5, 0.5, 0.5]
        elif color == "white":
            bgColor = [1, 1, 1]
        elif color == 'light gray':
            bgColor = [0.75, 0.75, 0.75]
        elif color == 'dark gray':
            bgColor = [0.25, 0.25, 0.25]
        elif color == "custom":
            # Open a color dialog to let the user choose a color
            qColor = QColorDialog.getColor()
            if qColor.isValid():
                # Convert QColor to a list of normalized RGB values
                bgColor = [qColor.red() / 255.0, qColor.green() / 255.0, qColor.blue() / 255.0]
            else:
                return

        # Set the background color and refresh the render window
        self.mesh_tab.geditor.renderer.SetBackground(*bgColor)
        self.results_tab.renderer.SetBackground(*bgColor)
        self.mesh_tab.geditor.vtkWidget.GetRenderWindow().Render()
        self.results_tab.vtkWidget.GetRenderWindow().Render()


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
        self.tab_widget.addTab(self.config_tab, "Configurations")
        self.tab_widget.addTab(self.results_tab, "Results")


    def start_simulation(self):
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
        
        # Rewrite configs if they have been changed
        try:
            with open(self.config_tab.config_file_path, "w") as file:
                dump(config_content, file, indent=4)  # Serialize dict to JSON
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
            return
        self.hdf5_filename = self.config_tab.mesh_file.replace(".msh", ".hdf5")
        args = f"{self.config_tab.config_file_path}"

        # Measure execution time
        self.run_cpp(args)
        self.progress_bar.setRange(0, 100)
        
        
    def stop_simulation(self):
        if self.process.state() == QProcess.Running:
            self.process.terminate()
            
            if not self.process.waitForFinished(2000):
                self.process.kill()
        
        
    def keyPressEvent(self, event):
        if (event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Q) or \
            event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_W:
            self.close()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_R:
            self.start_simulation()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_T:
            self.stop_simulation()
        elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier and event.key() == Qt.Key_U:
            self.config_tab.upload_config()
        elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier and event.key() == Qt.Key_S:
            self.config_tab.save_config_to_file()
        elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier and event.key() == Qt.Key_M:
            self.config_tab.upload_mesh_file()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_L:
            self.log_console.log_dock_widget.setVisible(not self.log_console.log_dock_widget.isVisible())
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
        
    
    def run_cpp(self, args: str) -> None:
        self.progress_bar.setHidden(False)
        self.start_time = time()
        self.process.start('./argos_nia_start', args.split())

    
    def show_shortcuts(self):
        shortcuts = [
            ("New Project", "Ctrl+N", "Creates a new project."),
            ("Open Project", "Ctrl+O", "Opens an existing project."),
            ("Save Project", "Ctrl+S", "Saves the current project."),
            ("Exit", "Ctrl+Q", "Exits the application."),
            ("Run Simulation", "Ctrl+R", "Starts the simulation."),
            ("Stop Simulation", "Ctrl+T", "Stops the currently running simulation."),
            ("Upload Config", "Ctrl+Shift+U", "Uploads a configuration file."),
            ("Save Config", "Ctrl+Shift+S", "Saves the current configuration to a file."),
            ("Upload Mesh", "Ctrl+Shift+M", "Uploads a mesh file."),
            ("Reset View Size", "R", "Resets the size of the view in the render window. Works only within the editor."),
            ("Remove Fill", "W", "Removes the fill from the all shapes. Shows the mesh structure. Works only within the editor."),
            ("Restore Fill", "S", "Retores the fill from the all shapes. Works only within the editor."),
            ("About", "F1", "Shows information about the application."),
        ]
        dialog = ShortcutsInfoDialog(shortcuts, self)
        dialog.exec_()


    def show_help(self):
        QMessageBox.information(
            self,
            "Help",
            "This is help message. Don't forget to write a desc to ur app here pls!!!",
        )
        

    def exit(self):
        exit(0)
