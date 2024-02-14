import gmsh
from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QSplitter, QTreeView, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from config_tab import ConfigTab
from os.path import isfile, exists, basename

elemTypeToNodeCount = {
    1: 2,    # 2-node line
    2: 3,    # 3-node triangle
    3: 4,    # 4-node quadrangle
    4: 4,    # 4-node tetrahedron
    5: 8,    # 8-node hexahedron
    6: 6,    # 6-node prism
    7: 5,    # 5-node pyramid
}


class GraphicalEditorTab(QWidget):
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
    
    def set_mesh_file(self, file_path):        
        if exists(file_path) and isfile(file_path):
            self.mesh_file = file_path
            self.initialize_tree()
        else:
            QMessageBox.warning(self, "Warning", f"Unable to open file {file_path}")
            return None

    def initialize_tree(self):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([basename(self.mesh_file)])
        self.rootItem = self.model.invisibleRootItem()

        gmsh.initialize()
        gmsh.open(self.mesh_file)

        self.add_maingeo_to_treeview()
        self.add_mesh_to_treeview()
        
        gmsh.finalize()
        self.treeView.setModel(self.model)
        self.treeView.expandAll()
        
    def add_maingeo_to_treeview(self):
        mainItem = QStandardItem('Main Geometry Elements')
        self.model.appendRow(mainItem)
        
        # Getting all nodes
        nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes()
        nodeCoords = nodeCoords.reshape(-1, 3)
        
        # Map node tags to their coordinates for easy lookup
        nodeMap = {tag: coords for tag, coords in zip(nodeTags, nodeCoords)}
        
        _, pointTags, pointElemNodeTags = gmsh.model.mesh.getElements(dim=0)
        for pointTag, nodeTags in zip(pointTags[0], pointElemNodeTags[0].reshape(-1, 2)):
            pointItem = QStandardItem(f'Point[{pointTag}]: ' + ', '.join(str(nt) for nt in nodeTags))
            mainItem.appendRow(pointItem)

            # For each node tag associated with the point, add its coordinates as a child item
            for nodeTag in nodeTags:
                if nodeTag in nodeMap:  # Check if the node tag exists in the map
                    coords = nodeMap[nodeTag]
                    nodeItem = QStandardItem(f'Point node[{nodeTag}]: {coords[0]:.3f} {coords[1]:.3f} {coords[2]:.3f}')
                    pointItem.appendRow(nodeItem)
        
        _, lineTags, lineElemNodeTags = gmsh.model.mesh.getElements(dim=1)
        for lineTag, nodeTags in zip(lineTags[0], lineElemNodeTags[0].reshape(-1, 2)):
            lineItem = QStandardItem(f'Line[{lineTag}]: ' + ', '.join(str(nt) for nt in nodeTags))
            mainItem.appendRow(lineItem)

            # For each node tag associated with the line, add its coordinates as a child item
            for nodeTag in nodeTags:
                if nodeTag in nodeMap:  # Check if the node tag exists in the map
                    coords = nodeMap[nodeTag]
                    nodeItem = QStandardItem(f'Line node[{nodeTag}]: {coords[0]:.3f} {coords[1]:.3f} {coords[2]:.3f}')
                    lineItem.appendRow(nodeItem)

    def add_mesh_to_treeview(self):
        # Get all triangle elements (type 2 for 3-node triangles in GMSH)
        _, elTags, nodeTagsPerEl = gmsh.model.mesh.getElements(2)
        
        nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes()
        nodeCoords = nodeCoords.reshape(-1, 3)

        meshItem = QStandardItem('Mesh')
        self.model.appendRow(meshItem)
        
        # Mapping node tags to their coordinates for easy lookup
        nodeMap = {tag: coords for tag, coords in zip(nodeTags, nodeCoords)}
        for elTag, nodes in zip(elTags[0], nodeTagsPerEl[0].reshape(-1, 3)):
            triangleItem = QStandardItem(f'Triangle[{elTag}]: {nodes[0]}, {nodes[1]}, {nodes[2]}')
            meshItem.appendRow(triangleItem)
    
            for nodeTag in nodes:
                coords = nodeMap[nodeTag]
                vertexItem = QStandardItem(f'Vertex[{nodeTag}]: {coords[0]:.3f} {coords[1]:.3f} {coords[2]:.3f}')
                triangleItem.appendRow(vertexItem)

