import gmsh
from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QSplitter, QTreeView, QFileSystemModel, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from config_tab import ConfigTab


class MeshTab(QWidget):
    def __init__(self, config_tab: ConfigTab, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.config_tab = config_tab

        self.setup_ui()

    def setup_ui(self):
        # Initialize an empty QTreeView
        self.treeView = QTreeView()
        self.model = QStandardItemModel()
        self.treeView.setModel(self.model)

        # Initialize a placeholder for the graphical editor
        self.graphicalEditor = QFrame()
        self.graphicalEditor.setFrameShape(QFrame.StyledPanel)

        # Create a QSplitter and add both widgets
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.treeView)
        self.splitter.addWidget(self.graphicalEditor)

        # Initial sizes of the splitter
        self.splitter.setSizes([1, 150])

        # Add the QSplitter to the main layout
        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)

    def create_tree_model(self):
        # Load the .msh file using gmsh
        gmsh.initialize()
        gmsh.open(self.config_tab.mesh_file)

        # Create a model to hold the entities
        model = QStandardItemModel()
        rootItem = model.invisibleRootItem()

        # Iterate through the entities and add them to the model
        entities = gmsh.model.getEntities()
        for dim, tag in entities:
            entity_name = f"Dimension {dim} - Tag {tag}"
            item = QStandardItem(entity_name)
            rootItem.appendRow(item)

        gmsh.finalize()
        return model

    def set_mesh_file(self, file_path):
        self.mesh_file = file_path
        self.model = self.create_tree_model()
        self.treeView.setModel(self.model)
