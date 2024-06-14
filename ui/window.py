from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget,
    QVBoxLayout, QWidget,
    QMessageBox, QFileDialog,
    QProgressBar, QScrollArea, 
    QApplication, QColorDialog
)
import signal, os, psutil, json
from sys import exit
from time import time
from PyQt5.QtCore import Qt, QProcess, pyqtSlot
from PyQt5.QtGui import QColor, QTextCharFormat
from tabs.config_tab import ConfigTab
from tabs.results_tab import ResultsTab
from tabs.gedit_tab import GraphicalEditorTab
from logger.log_console import LogConsole
from util import ShortcutsInfoDialog, is_file_valid
from shutil import rmtree, copy
from util.styles import *
from util.converter import ansi_to_segments
from util.util import DEFAULT_COUNT_OF_PROJECT_FILES

class WindowApp(QMainWindow):    
    def __init__(self):
        super().__init__()
        self.process = QProcess(self)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.finished.connect(self.on_process_finished)
        
        self.setWindowTitle("Particle Collision Simulator")
        self.setupFontColor = DEFAULT_FONT_COLOR
        
        # Retrieve the size of the primary screen
        screen = QApplication.primaryScreen()
        rect = screen.availableGeometry()
        self.setGeometry(rect)

        self.log_console = LogConsole()

        # Create tab widget and tabs
        self.tab_widget = QTabWidget()
        self.config_tab = ConfigTab(self.log_console)
        self.config_tab.requestToMoveToTheNextTab.connect(self.switch_tab)
        self.config_tab.requestToStartSimulation.connect(self.start_simulation)
        self.config_tab.selectBoundaryConditionsSignal.connect(self.handle_select_boundary_conditions)
        self.mesh_tab = GraphicalEditorTab(self.config_tab, self.log_console)
        self.geditor = self.mesh_tab.geditor
        self.results_tab = ResultsTab(self.log_console)

        # Connecting signal to detect the selection of mesh file
        self.config_tab.meshFileSelected.connect(self.geditor.upload_mesh_file)
        
        # Connecting signal to tun the simulation from the CLI
        self.log_console.runSimulationSignal.connect(self.start_simulation_from_CLI)
        self.log_console.uploadMeshSignal.connect(self.config_tab.upload_mesh_file_with_filename)
        self.log_console.uploadConfigSignal.connect(self.config_tab.upload_config_with_filename)
        self.log_console.saveConfigSignal.connect(self.config_tab.save_config_to_file_with_filename)

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
        
        # Setting default app style and backgrounds of the graphical editors        
        self.change_style('dark')
        self.change_background_color('white')
        
        # Setting by default axes alignment by center
        self.geditor.align_view_by_axis('center')
        self.results_tab.align_view_by_axis('center')
        
    
    def read_stderr(self):
        try:
            errout = str(self.process.readAllStandardError().data().decode())
        except UnicodeDecodeError:
            errout = str(self.process.readAllStandardError().data())
        segments = ansi_to_segments(errout)
        for segment, color in segments:
            self.insert_colored_text('', segment, color)


    def read_stdout(self):
        try:
            out = str(self.process.readAllStandardOutput().data().decode())
        except UnicodeDecodeError:
            out = str(self.process.readAllStandardOutput().data())
        segments = ansi_to_segments(out)
        for segment, color in segments:
            self.insert_colored_text('', segment, color)



    def insert_colored_text(self, prefix: str, message: str, color: str):
        """
        Inserts colored text followed by default-colored text into a QPlainTextEdit widget.

        Parameters:
        - prefix: str, the prefix text to insert in color.
        - message: str, the message text to insert in default color.
        - color: str, the name of the color to use for the prefix.
        """
        cursor = self.log_console.log_console.textCursor()
        
        # Insert colored prefix
        prefix_format = QTextCharFormat()
        prefix_format.setForeground(QColor(color))
        cursor.mergeCharFormat(prefix_format)
        cursor.insertText(prefix, prefix_format)

        # Insert the message in specified color
        message_format = QTextCharFormat()
        message_format.setForeground(QColor(color))
        cursor.setCharFormat(message_format)
        cursor.insertText(message)

        # Ensure the cursor is moved to the end and reset the format
        cursor.movePosition(cursor.End)
        self.log_console.log_console.setTextCursor(cursor)
        self.log_console.log_console.setCurrentCharFormat(QTextCharFormat())

    
    def on_process_finished(self, exitCode, exitStatus):
        self.progress_bar.setHidden(True)
        exec_time = time() - self.start_time
        self.progress_bar.setValue(100)
        
        if exitStatus == QProcess.NormalExit and exitCode == 0:
            if not is_file_valid(self.hdf5_filename):
                QMessageBox.warning(self, 
                                    "Invalid HDF5 File", 
                                    "Something wrong with HDF5 file. Can't update results. Check the name of the file, try to rename it. Going back...")
                self.stop_simulation()
                return
                
            self.results_tab.update_plot(self.hdf5_filename)
            self.log_console.printSuccess(f'The simulation has completed in {exec_time:.3f}s')
            
            # Moving to the results tab after finishing
            self.tab_widget.setCurrentIndex(2)
            QMessageBox.information(self,
                                    "Process Finished",
                                    f"The simulation has completed in {exec_time:.3f}s\n\nScalar bar:\nLeft side - particles count.\nRight side - normalized value.\n\n*Normalized Value = (Scalar Value - Range Min) / (Range Max - Range Min)")
            
        elif exitStatus == QProcess.CrashExit and exitCode == 11:
            self.results_tab.clear_plot()
            
            QMessageBox.information(self,
                                    "Error",
                                    f"Something went wrong at the start of the simulation. Program stops the simulation. See log console to have details")
        else:
            self.results_tab.clear_plot()
            
            try:
                signal_name = signal.Signals(exitCode).name
            except ValueError:
                QMessageBox.warning(self,
                                    "Simulation Stopped",
                                    f"Got signal {exitCode} which is undefined!")
                signal_name = "Undefined"
            
            self.log_console.printError(f'The simulation has been forcibly stopped with a code {exitCode} <{signal_name}>')
            QMessageBox.information(self, 
                                    "Simulation Stopped", 
                                    f"The simulation has been forcibly stopped with a code {exitCode} <{signal_name}>")
    
    
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
        style_menu.addAction('Custom', lambda: self.change_style('custom'))
        
        bg_color_menu = edit_menu.addMenu('Background Color')
        bg_color_menu.addAction('Default', lambda: self.change_background_color('default'))
        bg_color_menu.addAction('White', lambda: self.change_background_color('white'))
        bg_color_menu.addAction('Light Gray', lambda: self.change_background_color('light gray'))
        bg_color_menu.addAction('Gray', lambda: self.change_background_color('gray'))
        bg_color_menu.addAction(self.setupFontColor, lambda: self.change_background_color(self.setupFontColor))
        bg_color_menu.addAction('Black', lambda: self.change_background_color('black'))
        bg_color_menu.addAction('Custom', lambda: self.change_background_color('custom'))
        
        edit_menu.addAction('Show Shortcuts', self.show_shortcuts)
        edit_menu.addAction('Change FPS (for animation)', self.results_tab.edit_fps)

        # Configurations Menu
        configurations_menu = menu_bar.addMenu('&Configurations')
        configurations_menu.addAction('Upload Configuration', 
                                    self.config_tab.upload_config, 
                                    shortcut='Ctrl+Shift+U')   #  Upload config
        configurations_menu.addAction('Save Configuration',
                                    self.config_tab.save_config_to_file,
                                    shortcut='Ctrl+Shift+S')   #  Save config
        configurations_menu.addSeparator()
        configurations_menu.addAction('Upload Mesh',
                                      self.upload_mesh_file,
                                      shortcut='Ctrl+Shift+M') #  Upload mesh file

        # Solution Menu
        solution_menu = menu_bar.addMenu('&Simulation')
        solution_menu.addAction('Run', self.start_simulation, shortcut='Ctrl+R') #  Run
        solution_menu.addAction('Stop', self.stop_simulation, shortcut='Ctrl+T') #  Terminate
        
        # Help Menu: *No need help on this stage
        # help_menu = menu_bar.addMenu('&Help')
        # help_menu.addAction('About', self.show_help, shortcut='F1')


    def upload_mesh_file(self):
        self.mesh_tab.clear_scene_and_tree_view()
        self.config_tab.upload_mesh_file()
            

    def change_style(self, style):
        if style == 'dark':
            self.setupFontColor = 'white'
            self.setStyleSheet(APPSTYLE_DARK)
            self.log_console.setDefaultTextColor(QColor('white'))
        elif style == 'light':
            self.setupFontColor = 'black'
            self.setStyleSheet(APPSTYLE_LIGHT)
            self.log_console.setDefaultTextColor(QColor('black'))
        elif style == 'night':
            self.setupFontColor = 'green'
            self.setStyleSheet(APPSTYLE_NIGHT)
            self.log_console.setDefaultTextColor(QColor('white'))
        elif style == 'classic':
            self.setupFontColor = 'black'
            self.setStyleSheet(APPSTYLE_CLASSIC)
            self.log_console.setDefaultTextColor(QColor('black'))
        elif style == 'bright':
            self.setupFontColor = 'white'
            self.setStyleSheet(APPSTYLE_BRIGHT)
            self.log_console.setDefaultTextColor(QColor('black'))
        elif style == 'default':
            self.setStyleSheet(APPSTYLE_DEFAULT)
            self.log_console.setDefaultTextColor(QColor(self.setupFontColor))
        elif style == 'custom':
            QMessageBox.information(self, 'Application Color', 'Choose application color')
            appColor = QColorDialog.getColor()
            
            QMessageBox.information(self, 'Application Fonr Color', 'Choose font color of the application')
            appFontColor = QColorDialog.getColor()
            if appColor.isValid() and appFontColor.isValid():
                appColorHex = appColor.name()
                appFontColorHex = appFontColor.name()
                self.setStyleSheet(f'QWidget {{ background-color: {appColorHex}; color: {appFontColorHex}; }}')
            else:
                return

            QMessageBox.information(self, 'Logger Font Color', 'Choose font color in the logger')
            logFontColor = QColorDialog.getColor()
            if appColor.isValid():
                self.log_console.setDefaultTextColor(logFontColor)
            else:
                return
        else:
            self.setStyleSheet('')
            self.log_console.setDefaultTextColor(QColor(self.setupFontColor))

    
    def change_background_color(self, color):
        if color == 'default':
            bgColor = [0.1, 0.2, 0.2]
        elif color == 'black':
            bgColor = [0, 0, 0]
        elif color == 'gray':
            bgColor = [0.5, 0.5, 0.5]
        elif color == 'white':
            bgColor = [1, 1, 1]
        elif color == 'light gray':
            bgColor = [0.75, 0.75, 0.75]
        elif color == self.setupFontColor:
            bgColor = [0.25, 0.25, 0.25]
        elif color == 'custom':
            # Open a color dialog to let the user choose a color
            qColor = QColorDialog.getColor()
            if qColor.isValid():
                # Convert QColor to a list of normalized RGB values
                bgColor = [qColor.red() / 255.0, qColor.green() / 255.0, qColor.blue() / 255.0]
            else:
                return

        # Set the background color and refresh the render window
        self.geditor.renderer.SetBackground(*bgColor)
        self.results_tab.renderer.SetBackground(*bgColor)
        self.geditor.vtkWidget.GetRenderWindow().Render()
        self.results_tab.vtkWidget.GetRenderWindow().Render()


    def create_project(self):
        options = QFileDialog.Options()
        project_dir = QFileDialog.getExistingDirectory(self, 'Choose Project Directory', options=options)
        
        if not project_dir:
            return
    
        if os.path.exists(project_dir):
            rmtree(project_dir)
        os.makedirs(project_dir, exist_ok=True)
        
        self.log_console.printSuccess(f'Created new project directory: {project_dir}')


    def open_project(self):
        options = QFileDialog.Options()
        project_dir = QFileDialog.getExistingDirectory(self, 'Choose Project Directory', options=options)
        
        if not project_dir:
            return

        files = os.listdir(project_dir)
        paths = [os.path.join(project_dir, file) for file in files]
        
        if len(paths) != DEFAULT_COUNT_OF_PROJECT_FILES or \
            not paths[0].endswith('.json') or not paths[1].endswith('scene_camera_meshTab.json') or \
            not paths[2].endswith('scene_actors_meshTab.vtk'):
                self.log_console.printError(f'Can\'t open the project, check contegrity of all the files in directory {project_dir}. There must be {DEFAULT_COUNT_OF_PROJECT_FILES} files')
                QMessageBox.critical(self, 'Open Project', f'Can\'t open the project, check contegrity of all the files in directory {project_dir}. There must be {DEFAULT_COUNT_OF_PROJECT_FILES} files')
                return
        
        self.geditor.load_scene(self.log_console, self.setupFontColor, paths[2], paths[1])
        self.config_tab.upload_config_with_filename(paths[0])
    
    
    def save_project(self):
        QMessageBox.warning(self, "Saving project", "WARNING: Preferably you need to choose empty directory without any files (especially if there are your personal files or any other important ones there).")
        
        options = QFileDialog.Options()
        project_dir = QFileDialog.getExistingDirectory(self, 'Choose Project Directory', options=options)
        
        if not project_dir:
            return
        
        # Generating all project files
        self.geditor.save_scene(self.log_console, self.setupFontColor)
        
        if not self.config_tab.config_file_path:
            self.config_tab.save_config_to_file()

        # Check if the directory exists. If yes, remove it and create a fresh one
        if os.path.exists(project_dir):
            choose = QMessageBox.warning(self, "Remove Directory", f"Are you sure that you want to remove all existing files in the directory {project_dir}? It needed for updating project configuration files.", QMessageBox.Yes | QMessageBox.No)
            if choose == QMessageBox.Yes:
                rmtree(project_dir)
            else:
                return
        os.makedirs(project_dir, exist_ok=True)

        try:
            original_files = ['scene_actors_meshTab.vtk', 'scene_camera_meshTab.json']
            original_files.append(os.path.basename(self.config_tab.config_file_path))

            # Move the generated files to the chosen project directory
            for filename in original_files:
                src = filename  # Assuming these files are in the current working directory
                dst = os.path.join(project_dir, filename)
                copy(src, dst)
            
            # Deleting unnecessary .vtks and .jsons
            original_files = original_files[:4]
            for filename in original_files:
                os.remove(filename)
            
        except Exception as e:
            self.log_console.printError(f'Message: {e}: Nothing to save or any file error occured')
            return
        self.log_console.printSuccess(f'Project had been saved into {project_dir} directory')


    def setup_tabs(self):
        self.tab_widget.addTab(self.mesh_tab, 'Mesh')
        self.tab_widget.addTab(self.config_tab, 'Configurations')
        self.tab_widget.addTab(self.results_tab, 'Results')


    def start_simulation_from_CLI(self, configFile):
        self.config_tab.upload_config_with_filename(configFile)
        if self.config_tab.mesh_file.endswith('.msh'):
            self.hdf5_filename = self.config_tab.mesh_file.replace('.msh', '.hdf5')
        elif self.config_tab.mesh_file.endswith('.vtk'):
            self.hdf5_filename = self.config_tab.mesh_file.replace('.vtk', '.hdf5')
        args = f'{self.config_tab.config_file_path}'
        self.run_cpp(args)
        self.progress_bar.setRange(0, 100)
    

    def start_simulation(self):        
        if not is_file_valid(self.config_tab.config_file_path):
            QMessageBox.warning(self,
                                "Save Configurataion",
                                "You need to save the configuration before start the simulation. Checking your input in config tab...")
            self.config_tab.save_config_to_file()
            return
        else:
            self.config_tab.save_config_to_file_with_filename(self.config_tab.config_file_path)
        
        if self.config_tab.mesh_file.endswith('.msh'):
            self.hdf5_filename = self.config_tab.mesh_file.replace('.msh', '.hdf5')
        elif self.config_tab.mesh_file.endswith('.vtk'):
            self.hdf5_filename = self.config_tab.mesh_file.replace('.vtk', '.hdf5')
        args = f"{self.config_tab.config_file_path}"

        # Measure execution time
        self.run_cpp(args)
        self.progress_bar.setRange(0, 100)
    
        
    def stop_simulation(self):
        if self.process.state() == QProcess.Running:
            self.process.terminate()
            
            if not self.process.waitForFinished(2000):
                self.process.kill()
                self.kill_application()
                
    
    def kill_application(self):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].startswith('nia_start'):
                    proc.kill()
                    self.log_console.printInfo(f"Process {proc.info['name']} with PID {proc.info['pid']} killed")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                self.log_console.printError(f"An error occurred while attempting to kill the process: {e}")
        
        
    def switch_tab(self):
        # Iterating by tabs
        currentTabIndex = self.tab_widget.currentIndex()
        totalTabs = self.tab_widget.count()
        nextTabIndex = (currentTabIndex + 1) % totalTabs
        self.tab_widget.setCurrentIndex(nextTabIndex)
    
        
    def keyPressEvent(self, event):
        # Main bindings
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
            self.switch_tab()
        elif event.key() == Qt.Key_F1:
            self.show_help()
            
        # Aligning by axes
        elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier and event.key() == Qt.Key_X:
            self.geditor.align_view_by_axis('x')
            self.results_tab.align_view_by_axis('x')
        elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier and event.key() == Qt.Key_Y:
            self.geditor.align_view_by_axis('y')
            self.results_tab.align_view_by_axis('y')
        elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier and event.key() == Qt.Key_Z:
            self.geditor.align_view_by_axis('z')
            self.results_tab.align_view_by_axis('z')
        elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier and event.key() == Qt.Key_C:
            self.geditor.align_view_by_axis('center')
            self.results_tab.align_view_by_axis('center')
            
        # History bindings
        elif event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Z:
            self.geditor.global_undo()
        elif event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Y:
            self.geditor.global_redo()
        else:
            super().keyPressEvent(event)
            
        # Delegate the event to the log console first
        if event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            self.log_console.keyPressEvent(event)
            return
        
    
    def run_cpp(self, args: str) -> None:
        self.progress_bar.setHidden(False)
        self.start_time = time()
        
        # Checking OS
        if os.name == 'nt':
            executable_path = 'Release/nia_start.exe'
        else:
            executable_path = './nia_start'
        self.process.start(executable_path, args.split())
    
    
    @pyqtSlot()
    def handle_select_boundary_conditions(self):
        self.tab_widget.setCurrentIndex(0)
        self.geditor.activate_selection_boundary_conditions_mode_slot()

    
    def show_shortcuts(self):
        shortcuts = [
            ("New Project", "Ctrl+N", "Creates a new project."),
            ("Open Project", "Ctrl+O", "Opens an existing project."),
            ("Save Project", "Ctrl+S", "Saves the current project."),
            ("Exit", "Ctrl+Q", "Exits the application."),
            ("Run Simulation", "Ctrl+R", "Starts the simulation."),
            ("Stop Simulation", "Ctrl+T", "Stops the currently running simulation."),
            ("Tab Switch", "Ctrl+Tab", "Switches current tab to the next one."),
            ("Hide/Show Log Console", "Ctrl+L", "Toggles visibility of the log console"),
            ("Upload Config", "Ctrl+Shift+U", "Uploads a configuration file."),
            ("Save Config", "Ctrl+Shift+S", "Saves the current configuration to a file."),
            ("Upload Mesh", "Ctrl+Shift+M", "Uploads a mesh file."),
            ("Reset View Size", "R", "Resets the size of the view in the render window. Works only within the editor."),
            ("Remove Fill", "W", "Removes the fill from the all shapes. Shows the mesh structure. Works only within the editor."),
            ("Restore Fill", "S", "Retores the fill from the all shapes. Works only within the editor."),
            ("About", "F1", "Shows information about the application."),
            ("Undo", "Ctrl+Z", "Reverses the most recent action, allowing you to step back through your changes one at a time."),
            ("Redo", "Ctrl+Y", "Reapplies actions that were previously undone using the Undo function, letting you move forward after reversing changes."),
            ("Search", "Ctrl+F", "Toggles on search mode within the log console."),
            ("Align by X axis", "Ctrl+Shift+X", "Make an alignment by X axis."),
            ("Align by Y axis", "Ctrl+Shift+Y", "Make an alignment by Y axis."),
            ("Align by Z axis", "Ctrl+Shift+Z", "Make an alignment by Z axis."),
            ("Align by center", "Ctrl+Shift+C", "Make an alignment by center."),
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
