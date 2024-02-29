import gmsh
from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QSplitter, QTreeView, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from .config_tab import ConfigTab
from util.graphical_editor import GraphicalEditor
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
        
        self.geditor.updateTreeSignal.connect(self.updateTreeModel)
        self.object_idx = 0
        self.undo_stack = []
        self.redo_stack = []

    def setup_ui(self):        
        # Initialize an empty QTreeView
        self.treeView = QTreeView()
        self.model = QStandardItemModel()
        self.treeView.setModel(self.model)

        # Initialize a placeholder for the graphical editor
        self.geditor = GraphicalEditor()

        # Create a QSplitter and add both widgets
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.treeView)
        self.splitter.addWidget(self.geditor)

        # Initial sizes of the splitter
        self.splitter.setSizes([100, 500])

        # Add the QSplitter to the main layout
        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)
        
    
    def undo_action_tree_view(self):
        if self.undo_stack:
            action = self.undo_stack.pop()
            if action['action'] == 'add':
                row = action['row']
                self.model.removeRow(row)
                self.object_idx -= 1

                # Prepare an action for the redo stack with descriptive data.
                redo_action = {
                    'action': 'add',
                    'row': row,
                    'figure_type': action['figure_type'],
                    'data': action['data']
                }
                self.redo_stack.append(redo_action)


    def redo_action_tree_view(self):
        if self.redo_stack:
            action = self.redo_stack.pop()

            if action['action'] == 'add':
                figure_type = action.get('figure_type')
                data = action.get('data')
                row = action.get('row')

                if figure_type and data is not None:                    
                    items = QStandardItem(f'Created objects[{self.object_idx}]: ' + figure_type + 's')
                    item = QStandardItem(data)

                    self.model.appendRow(items)
                    items.appendRow(item)
                    self.treeView.setModel(self.model)

                    # Update undo stack accordingly without resetting the model.
                    self.undo_stack.append({
                        'action': 'add',
                        'row': row,
                        'figure_type': figure_type,
                        'data': data
                    })

                    self.object_idx += 1


    def set_mesh_file(self, file_path):        
        if exists(file_path) and isfile(file_path):
            self.mesh_file = file_path
            self.vtk_file = self.mesh_file.replace('.msh', '.vtk')
            self.initialize_tree()
            self.geditor.display_mesh(self.mesh_file)
        else:
            QMessageBox.warning(self, "Warning", f"Unable to open file {file_path}")
            return None


    def initialize_tree(self):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([basename(self.mesh_file)])
        self.rootItem = self.model.invisibleRootItem()

        gmsh.initialize()
        gmsh.open(self.mesh_file)
        
        # Converting from .msh to .vtk
        gmsh.write(self.vtk_file)
        self.geditor.parse_vtk_polydata_and_populate_tree(self.vtk_file, self.model)
        
        gmsh.finalize()
        self.treeView.setModel(self.model)
        
        
    def updateTreeModel(self, figure_type: str, data: str):
        items = QStandardItem(f'Created objects[{self.object_idx}]: ' + figure_type + 's')
        self.model.appendRow(items)
        item = QStandardItem(data)
        items.appendRow(item)
        self.treeView.setModel(self.model)
        
        # Record the action in undo stack
        action = {
            'action': 'add',
            'row': self.object_idx,
            'figure_type': figure_type,
            'data': data,
            'parent': self.model.invisibleRootItem()  # Storing parent for context, might need refactoring
        }
        self.undo_stack.append(action)
        self.object_idx += 1
