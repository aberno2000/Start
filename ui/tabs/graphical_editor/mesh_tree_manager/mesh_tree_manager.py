import gmsh
from vtk import (
    vtkPoints, vtkCellArray, vtkUnstructuredGrid, vtkUnstructuredGridWriter,
    vtkTriangle, vtkPolyData, vtkPolyDataMapper, vtkActor, vtkVertexGlyphFilter,
    vtkPolyLine,
    VTK_TRIANGLE
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtCore import QModelIndex
from styles import *


class MeshTreeManager:
    
    @staticmethod
    def get_tree_dict(mesh_filename: str = None, obj_type: str = 'volume') -> dict:
        """
        Extracts the data from Gmsh and returns it in a structured format.

        Parameters:
        mesh_filename (str): The filename of the Gmsh mesh file to read.
        obj_type (str): The type of object to extract ('point', 'line', 'surface', 'volume').

        Returns:
        dict: A dictionary representing the object map.

        Raises:
        ValueError: If the obj_type is invalid.
        RuntimeError: If there is an error opening the mesh file or processing the Gmsh data.
        """
        try:
            if mesh_filename:
                gmsh.open(mesh_filename)

            gmsh.model.occ.synchronize()

            # Getting all the nodes and their coordinates
            all_node_tags, all_node_coords, _ = gmsh.model.mesh.getNodes()
            node_coords_map = {
                tag: (all_node_coords[i * 3], all_node_coords[i * 3 + 1],
                    all_node_coords[i * 3 + 2])
                for i, tag in enumerate(all_node_tags)
            }

            if obj_type == 'point':
                point_map = {
                    f'Point[{tag}]': coords
                    for tag, coords in node_coords_map.items()
                }
                return point_map

            if obj_type == 'line':
                lines = gmsh.model.getEntities(dim=1)
                line_map = {}

                for line_dim, line_tag in lines:
                    element_types, element_tags, node_tags = gmsh.model.mesh.getElements(
                        line_dim, line_tag)

                    for elem_type, elem_tags, elem_node_tags in zip(
                            element_types, element_tags, node_tags):
                        if elem_type == 1:  # 1st type for lines
                            for i in range(len(elem_tags)):
                                node_indices = elem_node_tags[i * 2:(i + 1) * 2]
                                line = [(node_indices[0],
                                        node_coords_map[node_indices[0]]),
                                        (node_indices[1],
                                        node_coords_map[node_indices[1]])]
                                line_map[f'Line[{elem_tags[i]}]'] = line
                return line_map

            if obj_type == 'surface':
                surfaces = gmsh.model.getEntities(dim=2)
                surface_map = {}

                for surf_dim, surf_tag in surfaces:
                    element_types, element_tags, node_tags = gmsh.model.mesh.getElements(
                        surf_dim, surf_tag)

                    triangles = []
                    for elem_type, elem_tags, elem_node_tags in zip(
                            element_types, element_tags, node_tags):
                        if elem_type == 2:  # 2nd type for the triangles
                            for i in range(len(elem_tags)):
                                node_indices = elem_node_tags[i * 3:(i + 1) * 3]
                                triangle = [(node_indices[0],
                                            node_coords_map[node_indices[0]]),
                                            (node_indices[1],
                                            node_coords_map[node_indices[1]]),
                                            (node_indices[2],
                                            node_coords_map[node_indices[2]])]
                                triangles.append((elem_tags[i], triangle))
                    surface_map[surf_tag] = triangles
                return surface_map

            if obj_type == 'volume':
                volumes = gmsh.model.getEntities(dim=3)
                treedict = {}

                entities = volumes if volumes else gmsh.model.getEntities(dim=2)

                for dim, tag in entities:
                    surfaces = gmsh.model.getBoundary(
                        [(dim, tag)], oriented=False,
                        recursive=False) if volumes else [(dim, tag)]

                    surface_map = {}
                    for surf_dim, surf_tag in surfaces:
                        element_types, element_tags, node_tags = gmsh.model.mesh.getElements(
                            surf_dim, surf_tag)

                        triangles = []
                        for elem_type, elem_tags, elem_node_tags in zip(
                                element_types, element_tags, node_tags):
                            if elem_type == 2:  # 2nd type for the triangles
                                for i in range(len(elem_tags)):
                                    node_indices = elem_node_tags[i * 3:(i + 1) * 3]
                                    triangle = [(node_indices[0],
                                                node_coords_map[node_indices[0]]),
                                                (node_indices[1],
                                                node_coords_map[node_indices[1]]),
                                                (node_indices[2],
                                                node_coords_map[node_indices[2]])]
                                    triangles.append((elem_tags[i], triangle))
                        surface_map[surf_tag] = triangles
                    treedict[tag] = surface_map
                return treedict

            raise ValueError("Invalid obj_type. Must be one of 'point', 'line', 'surface', 'volume'.")

        except Exception as e:
            raise RuntimeError(f"An error occurred while processing the Gmsh data: {e}")

    @staticmethod
    def write_treedict_to_vtk(treedict: dict, filename: str) -> bool:
        """
        Writes the object map to a VTK file.

        Args:
            treedict (dict): The object map containing mesh data.
            filename (str): The filename to write the VTK file to.

        Returns:
            bool: True if the file was successfully written, False otherwise.
        """
        try:
            if not filename.endswith('.vtk'):
                filename += '.vtk'

            points = vtkPoints()
            points.SetDataTypeToDouble()
            triangles = vtkCellArray()
            ugrid = vtkUnstructuredGrid()

            point_index_map = {}
            current_index = 0

            for volume_id, surfaces in treedict.items():
                for surface_id, triangle_data in surfaces.items():
                    for triangle_id, triangle in triangle_data:
                        pts = []
                        for node_id, point in triangle:
                            if node_id not in point_index_map:
                                points.InsertNextPoint(point)
                                point_index_map[node_id] = current_index
                                current_index += 1
                            pts.append(point_index_map[node_id])
                        triangle_cell = vtkTriangle()
                        triangle_cell.GetPointIds().SetId(0, pts[0])
                        triangle_cell.GetPointIds().SetId(1, pts[1])
                        triangle_cell.GetPointIds().SetId(2, pts[2])
                        triangles.InsertNextCell(triangle_cell)

            ugrid.SetPoints(points)
            ugrid.SetCells(VTK_TRIANGLE, triangles)

            writer = vtkUnstructuredGridWriter()
            writer.SetFileName(filename)
            writer.SetInputData(ugrid)

            writer.Write()
            return True, filename

        except Exception as e:
            print(f"Error writing VTK file: {e}")
            return False, filename

    @staticmethod
    def create_actors_from_tree_dict(treedict: dict, objType: str) -> list:
        """
        Create VTK actors for each surface, volume, or line in the object map.

        Parameters:
        treedict (dict): The object map generated by the getTreeDict function, which contains volumes,
                        surfaces, triangles, and their nodes with coordinates.
        objType (str): The type of the object, which can be 'volume', 'surface', or 'line'.

        Returns:
        list: List of the VTK actors.
        """
        actors = []

        if objType == 'volume':
            for _, surfaces in treedict.items():
                for surface_tag, triangles in surfaces.items():
                    points = vtkPoints()
                    triangles_array = vtkCellArray()

                    # Dictionary to map node tags to point IDs in vtkPoints
                    point_id_map = {}

                    for triangle_tag, nodes in triangles:
                        point_ids = []
                        for node_tag, coords in nodes:
                            if node_tag not in point_id_map:
                                point_id = points.InsertNextPoint(coords)
                                point_id_map[node_tag] = point_id
                            else:
                                point_id = point_id_map[node_tag]
                            point_ids.append(point_id)

                        # Create a VTK triangle and add it to the vtkCellArray
                        triangle = vtkTriangle()
                        for i, point_id in enumerate(point_ids):
                            triangle.GetPointIds().SetId(i, point_id)
                        triangles_array.InsertNextCell(triangle)

                    poly_data = vtkPolyData()
                    poly_data.SetPoints(points)
                    poly_data.SetPolys(triangles_array)
                    mapper = vtkPolyDataMapper()
                    mapper.SetInputData(poly_data)

                    # Create a vtkActor to represent the surface in the scene
                    actor = vtkActor()
                    actor.SetMapper(mapper)
                    actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)

                    # Add the actor to the list
                    actors.append(actor)

        elif objType == 'surface':
            for surface_tag, triangles in treedict.items():
                points = vtkPoints()
                triangles_array = vtkCellArray()

                # Dictionary to map node tags to point IDs in vtkPoints
                point_id_map = {}

                for triangle_tag, nodes in triangles:
                    point_ids = []
                    for node_tag, coords in nodes:
                        if node_tag not in point_id_map:
                            point_id = points.InsertNextPoint(coords)
                            point_id_map[node_tag] = point_id
                        else:
                            point_id = point_id_map[node_tag]
                        point_ids.append(point_id)

                    # Create a VTK triangle and add it to the vtkCellArray
                    triangle = vtkTriangle()
                    for i, point_id in enumerate(point_ids):
                        triangle.GetPointIds().SetId(i, point_id)
                    triangles_array.InsertNextCell(triangle)

                poly_data = vtkPolyData()
                poly_data.SetPoints(points)
                poly_data.SetPolys(triangles_array)
                mapper = vtkPolyDataMapper()
                mapper.SetInputData(poly_data)

                # Create a vtkActor to represent the surface in the scene
                actor = vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)

                # Add the actor to the list
                actors.append(actor)

        elif objType == 'line':
            for line_tag, points in treedict.items():
                vtk_points = vtkPoints()
                poly_line = vtkPolyLine()
                poly_line.GetPointIds().SetNumberOfIds(len(points))

                # Dictionary to map node tags to point IDs in vtkPoints
                point_id_map = {}

                for i, (node_tag, coords) in enumerate(points):
                    if node_tag not in point_id_map:
                        point_id = vtk_points.InsertNextPoint(coords)
                        point_id_map[node_tag] = point_id
                    else:
                        point_id = point_id_map[node_tag]

                    poly_line.GetPointIds().SetId(i, point_id)

                lines_array = vtkCellArray()
                lines_array.InsertNextCell(poly_line)

                poly_data = vtkPolyData()
                poly_data.SetPoints(vtk_points)
                poly_data.SetLines(lines_array)
                mapper = vtkPolyDataMapper()
                mapper.SetInputData(poly_data)

                # Create a vtkActor to represent the line in the scene
                actor = vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)

                # Add the actor to the list
                actors.append(actor)

        elif objType == 'point':
            for point_tag, coords in treedict.items():
                vtk_points = vtkPoints()
                vtk_points.InsertNextPoint(coords)

                poly_data = vtkPolyData()
                poly_data.SetPoints(vtk_points)

                glyph_filter = vtkVertexGlyphFilter()
                glyph_filter.SetInputData(poly_data)
                glyph_filter.Update()

                mapper = vtkPolyDataMapper()
                mapper.SetInputConnection(glyph_filter.GetOutputPort())

                actor = vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetPointSize(5)
                actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)

                actors.append(actor)

        return actors

    @staticmethod
    def populate_tree_view(treedict: dict, object_idx: int,
                        tree_model: QStandardItemModel, tree_view: QTreeView,
                        type: str) -> int:
        """
        Populate the tree model with the hierarchical structure of the object map.

        Parameters:
        treedict (dict): The object map generated by the getTreeDict function, which contains volumes,
                        surfaces, triangles, and their nodes with coordinates.
        object_idx (int): Index of the object.
        tree_model (QStandardItemModel): The QStandardItemModel where the hierarchical data will be inserted.
        tree_view (QTreeView): The QTreeView where the tree model will be displayed.
        type (str): The type of the object, which can be 'volume', 'surface', or 'line'.

        Returns:
        int: The row index of the volume or surface item.
        """
        rows = []
        root_row_index = -1

        if type == 'volume':
            # Case when treedict contains volumes
            for _, surfaces in treedict.items():
                # Add the volume node to the tree model
                volume_item = QStandardItem(f'Volume[{object_idx}]')
                tree_model.appendRow(volume_item)

                # Get the index of the volume item
                volume_index = tree_model.indexFromItem(volume_item)
                root_row_index = volume_index.row()

                for surface_tag, triangles in surfaces.items():
                    # Add the surface node to the tree model under the volume node
                    surface_item = QStandardItem(f'Surface[{surface_tag}]')
                    volume_item.appendRow(surface_item)

                    for triangle_tag, nodes in triangles:
                        # Add the triangle node to the tree model under the surface node
                        triangle_item = QStandardItem(f'Triangle[{triangle_tag}]')
                        surface_item.appendRow(triangle_item)

                        # Generate lines for the triangle
                        lines = [(nodes[0], nodes[1]), (nodes[1], nodes[2]),
                                (nodes[2], nodes[0])]

                        for line_idx, (start, end) in enumerate(lines, start=1):
                            # Add the line node under the triangle node
                            line_item = QStandardItem(f'Line[{line_idx}]')
                            triangle_item.appendRow(line_item)

                            # Add the point data under the line node
                            start_str = f'Point[{start[0]}]: {start[1]}'
                            end_str = f'Point[{end[0]}]: {end[1]}'
                            start_item = QStandardItem(start_str)
                            end_item = QStandardItem(end_str)
                            line_item.appendRow(start_item)
                            line_item.appendRow(end_item)

        elif type == 'surface':
            # Case when treedict contains surfaces directly
            for surface_tag, triangles in treedict.items():
                # Add the surface node to the tree model
                surface_item = QStandardItem(f'Surface[{surface_tag}]')
                tree_model.appendRow(surface_item)

                # Get the index of the surface item
                surface_index = tree_model.indexFromItem(surface_item)
                root_row_index = surface_index.row()

                for triangle_tag, nodes in triangles:
                    # Add the triangle node to the tree model under the surface node
                    triangle_item = QStandardItem(f'Triangle[{triangle_tag}]')
                    surface_item.appendRow(triangle_item)

                    # Generate lines for the triangle
                    lines = [(nodes[0], nodes[1]), (nodes[1], nodes[2]),
                            (nodes[2], nodes[0])]

                    for line_idx, (start, end) in enumerate(lines, start=1):
                        # Add the line node under the triangle node
                        line_item = QStandardItem(f'Line[{line_idx}]')
                        triangle_item.appendRow(line_item)

                        # Add the point data under the line node
                        start_str = f'Point[{start[0]}]: {start[1]}'
                        end_str = f'Point[{end[0]}]: {end[1]}'
                        start_item = QStandardItem(start_str)
                        end_item = QStandardItem(end_str)
                        line_item.appendRow(start_item)
                        line_item.appendRow(end_item)

        elif type == 'line':
            # Case when treedict contains lines directly
            for line_tag, points in treedict.items():
                # Add the line node to the tree model
                line_item = QStandardItem(f'{line_tag}')
                tree_model.appendRow(line_item)

                # Get the index of the line item
                line_index = tree_model.indexFromItem(line_item)
                root_row_index = line_index.row()
                rows.append(root_row_index)

                for point_idx, (point_tag, coords) in enumerate(points, start=1):
                    # Add the point node to the tree model under the line node
                    point_str = f'Point[{point_tag}]: {coords}'
                    point_item = QStandardItem(point_str)
                    line_item.appendRow(point_item)

        elif type == 'point':
            for point_tag, coords in treedict.items():
                point_item = QStandardItem(f'{point_tag}: {coords}')
                tree_model.appendRow(point_item)
                point_index = tree_model.indexFromItem(point_item)
                root_row_index = point_index.row()

        tree_view.setModel(tree_model)
        if type != 'line':
            return root_row_index
        else:
            return rows
        
    @staticmethod
    def form_actor_nodes_dictionary(treedict: dict, actor_rows: dict, objType: str):
        actor_nodes_dict = {}

        for actor, (volume_index, surface_index) in actor_rows.items():
            if actor not in actor_nodes_dict:
                actor_nodes_dict[actor] = set()

            if objType == 'volume':
                for volume_tag, surfaces in treedict.items():
                    for surface_tag, triangles in surfaces.items():
                        if surface_tag - 1 == surface_index:
                            for triangle_tag, nodes in triangles:
                                for node in nodes:
                                    actor_nodes_dict[actor].add(node[0])
            elif objType == 'surface':
                for surface_tag, triangles in treedict.items():
                    if surface_tag - 1 == surface_index:
                        for triangle_tag, nodes in triangles:
                            for node in nodes:
                                actor_nodes_dict[actor].add(node[0])
            elif objType == 'line':
                for line_tag, line_nodes in treedict.items():
                    if surface_index == int(line_tag.split('[')[1][:-1]):
                        for node in line_nodes:
                            actor_nodes_dict[actor].add(node[0])
            elif objType == 'point':
                if f'Point[{surface_index}]' in treedict:
                    actor_nodes_dict[actor].add(surface_index)

        return actor_nodes_dict
    
    @staticmethod
    def copy_children(source_item, target_item):
        """
        Recursively copy children from source_item to target_item.

        Args:
            source_item (QStandardItem): The item from which to copy children.
            target_item (QStandardItem): The item to which the children will be copied.
        """
        # Iterate through all rows (children) of the source item
        for row in range(source_item.rowCount()):
            # Clone the child item at the current row
            child = source_item.child(row).clone()

            # Append the cloned child to the target item
            target_item.appendRow(child)

            # Recursively call copy_children to copy the children of the current child
            MeshTreeManager.copy_children(source_item.child(row), child)
    
    @staticmethod
    def rename_first_selected_row(model, volume_row, surface_indices):
        """
        Rename the first selected row in the tree view with the merged surface name.

        Args:
            model (QStandardItemModel): The model of the tree view.
            volume_row (int): The row index of the volume item in the tree view.
            surface_indices (list): The list of indices of the surface items to be merged.
        """
        # Creating the new merged item name
        merged_surface_name = f"Surface_merged_{'_'.join(map(str, sorted([i + 1 for i in surface_indices])))}"
        parent_index = model.index(volume_row, 0)

        # Replacing the name of the first selected row with the new name
        first_surface_index = surface_indices[0]
        first_child_index = model.index(first_surface_index, 0, parent_index)
        first_item = model.itemFromIndex(first_child_index)
        first_item.setText(merged_surface_name)
        
    @staticmethod
    def update_tree_view(model, volume_row, surface_indices):
        surface_indices = sorted(surface_indices)
        MeshTreeManager.rename_first_selected_row(model, volume_row, surface_indices)
        parent_index = model.index(volume_row, 0)

        # Copying the hierarchy from the rest of the selected rows to the first selected row
        for surface_index in surface_indices[1:]:
            child_index = model.index(surface_index, 0, parent_index)
            child_item = model.itemFromIndex(child_index)
            MeshTreeManager.copy_children(child_item, model.itemFromIndex(
                model.index(surface_indices[0], 0, parent_index)))

        # Deleting the rest of the selected rows from the tree view
        for surface_index in surface_indices[1:][::-1]:
            child_index = model.index(surface_index, 0, parent_index)
            model.removeRow(child_index.row(), parent_index)

    @staticmethod
    def print_tree_structure(tree_view: QTreeView):
        model = tree_view.model()

        def iterate(index, level):
            if not index.isValid():
                return

            print(' ' * level * 4 + str(index.row()))

            # Iterate over children
            for i in range(model.rowCount(index)):
                child_index = model.index(i, 0, index)
                iterate(child_index, level + 1)

        root_index = model.index(0, 0, QModelIndex())
        iterate(root_index, 0)
