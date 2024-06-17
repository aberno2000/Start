from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QSplitter
)
from PyQt5.QtCore import Qt
from .config_tab import ConfigTab
from .graphical_editor import GraphicalEditor
from logger import LogConsole


class GraphicalEditorTab(QWidget):
    def __init__(self, config_tab: ConfigTab, log_console: LogConsole, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.config_tab = config_tab
        self.log_console = log_console
        self.setup_ui()

    def setup_ui(self):
        # Initialize a placeholder for the graphical editor
        self.geditor = GraphicalEditor(self.log_console, self.config_tab)

        # Initialize an empty QTreeView
        self.treeView = self.geditor.treeView
        self.model = self.geditor.model
        self.treeView.setModel(self.model)

        # Create a QSplitter and add both widgets
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.treeView)
        self.splitter.addWidget(self.geditor)

        # Initial sizes of the splitter
        self.splitter.setSizes([100, 500])

        # Add the QSplitter to the main layout
        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)

    def clear_scene_and_tree_view(self):
        self.geditor.clear_scene_and_tree_view()
