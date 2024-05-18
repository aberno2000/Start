import tempfile
from PyQt5.QtWidgets import (
    QVBoxLayout, QPlainTextEdit,
    QWidget, QDockWidget,
    QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCharFormat, QTextCursor, QColor
from util import is_file_valid
from logger.cli_history import CommandLineHistory
from vtk import vtkLogger
from os import remove

class LogConsole(QWidget):
    logSignal = pyqtSignal(str)
    runSimulationSignal = pyqtSignal(str)
    uploadMeshSignal = pyqtSignal(str)
    uploadConfigSignal = pyqtSignal(str)
    saveConfigSignal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setup_ui()
        self.setup_vtk_logger()
        
        # Flag to check initial adding of extra new line
        self.isAddedExtraNewLine = False
    
    def __del__(self):
        try:
            self.cleanup()
        except Exception as e:
            print(f'Error closing up LogConsole resources: {e}')

    def setup_ui(self):        
        self.log_console = QPlainTextEdit()
        self.log_console.setReadOnly(True)  # Make the console read-only
        
        self.command_input = CommandLineHistory()
        self.command_input.setPlaceholderText('Enter command...')
        self.command_input.returnPressed.connect(self.handle_command)
        
        self.layout.addWidget(self.log_console)
        self.layout.addWidget(self.command_input)
        
        container = QWidget()
        container.setLayout(self.layout)
        
        self.setDefaultTextColor(QColor('dark gray'))
        self.log_dock_widget = QDockWidget("Console", self)
        self.log_dock_widget.setWidget(container)
        self.log_dock_widget.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.log_dock_widget.setVisible(True)
        
    
    def setup_vtk_logger(self):
        self.log_file_path = tempfile.mktemp()  # Create a temporary file
        vtkLogger.LogToFile(self.log_file_path, vtkLogger.APPEND, vtkLogger.VERBOSITY_INFO)
        self.start_monitoring_log_file()
    
    def start_monitoring_log_file(self):
        # Use QTimer for periodic checks in a GUI-friendly way
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.read_log_file)
        self.timer.start(1000)  # Check every second
    
    def read_log_file(self):
        # Read the log file line by line and append its contents to the log console with appropriate color
        with open(self.log_file_path, 'r') as file:
            for line in file:
                if 'WARN|' in line:
                    self.printWarning(line)
                elif 'ERR|' in line:
                    self.printError(line)
                else:
                    self.appendLog(line.strip())
        open(self.log_file_path, 'w').close()
        
        # Adding '\n' to the end of the first output
        if not self.isAddedExtraNewLine:
            logs = self.getAllLogs()
            if logs.endswith('verbosity: 0'):
                self.appendLog('\n')
            self.isAddedExtraNewLine = True
    
    def cleanup(self):
        self.timer.stop()
        remove(self.log_file_path)     
    
    def setDefaultTextColor(self, color):
        textFormat = QTextCharFormat()
        textFormat.setForeground(color)

        cursor = self.log_console.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.mergeCharFormat(textFormat)
        cursor.clearSelection()
        self.log_console.setTextCursor(cursor)


    def insert_colored_text(self, prefix: str, message: str, color: str):
        """
        Inserts colored text followed by default-colored text into a QPlainTextEdit widget.

        Parameters:
        - prefix: str, the prefix text to insert in color.
        - message: str, the message text to insert in default color.
        - color: str, the name of the color to use for the prefix.
        """
        cursor = self.log_console.textCursor()
        
        # Insert colored prefix
        prefix_format = QTextCharFormat()
        prefix_format.setForeground(QColor(color))
        cursor.mergeCharFormat(prefix_format)
        cursor.insertText(prefix, prefix_format)

        # Insert the message in default color
        message_format = QTextCharFormat()
        cursor.setCharFormat(message_format)
        cursor.insertText(message + '\n')

        # Ensure the cursor is moved to the end and reset the format
        cursor.movePosition(cursor.End)
        self.log_console.setTextCursor(cursor)
        self.log_console.setCurrentCharFormat(QTextCharFormat())

        
    def appendLog(self, message):
        self.log_console.appendPlainText(str(message))
    
    def printSuccess(self, message):
        self.insert_colored_text("Successfully: ", message, "green")
        
    def printError(self, message):
        self.insert_colored_text("Error: ", message, "red")

    def printInternalError(self, message):
        self.insert_colored_text("Internal error: ", message, "purple")

    def printWarning(self, message):
        self.insert_colored_text("Warning: ", message, "yellow")
    
    def printInfo(self, message):
        self.appendLog("Info: " + str(message))
        
    def getAllLogs(self) -> str:
        return self.log_console.toPlainText()        
        
    def handle_command(self):
        """
        Handles commands entered in the command input field.
        """
        command = self.command_input.text().strip().lower()
        self.appendLog(f'>> {command}')
        
        if command:
            self.command_input.history.append(command)
            self.command_input.history_idx = len(self.command_input.history)
        
        if command == 'clear' or command == 'clean' or command == 'cls':
            self.log_console.clear()
        elif command == 'exit' or command == 'quit':
            QApplication.quit()
        elif command.startswith('run ') or command.startswith('start '):
            splitted_command = command.split()
            
            if len(splitted_command) != 2:
                self.appendLog(f"Usage: {splitted_command[0]} <config_name.json>")
                self.command_input.clear()
                return

            configFile = splitted_command[1]
            if not is_file_valid(configFile):
                self.appendLog(f"Invalid or missing file: {configFile}")
                self.command_input.clear()
                return
            
            self.runSimulationSignal.emit(configFile)
            
        elif command.startswith('upload mesh '):
            splitted_command = command.split()
            
            if len(splitted_command) != 3:
                self.appendLog(f"Usage: {splitted_command[0]} {splitted_command[1]} <meshfile.[msh|stp|vtk]>. Make sure that you specify mesh file correctly. Check name of the files and path")
                self.command_input.clear()
                return

            meshFile = splitted_command[2]
            if not is_file_valid(meshFile):
                self.appendLog(f"Invalid or missing file: {meshFile}")
                self.command_input.clear()
                return
                
            self.uploadMeshSignal.emit(meshFile)
            
        elif command.startswith('upload config '):
            splitted_command = command.split()
            
            if len(splitted_command) != 3:
                self.appendLog(f"Usage: {splitted_command[0]} {splitted_command[1]} <config_name.json>")
                self.command_input.clear()
                return

            configFile = splitted_command[2]
            if not is_file_valid(configFile):
                self.appendLog(f"Invalid or missing file: {configFile}")
                self.command_input.clear()
                return
                
            self.uploadConfigSignal.emit(configFile)
            
        elif command.startswith('save config '):
            splitted_command = command.split()
            
            if len(splitted_command) != 3:
                self.appendLog(f"Usage: {splitted_command[0]} {splitted_command[1]} <config_name.json>")
                self.command_input.clear()
                return

            configFile = splitted_command[2]                
            self.saveConfigSignal.emit(configFile)
            
        elif command.strip() == '':
            return
        else:
            self.appendLog(f"Unknown command: {command}")
        self.command_input.clear()
