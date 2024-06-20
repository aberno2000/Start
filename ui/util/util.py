import gmsh
import tempfile
import meshio
import numpy as np
from math import pi
from re import split
from datetime import datetime
from os import remove
from vtk import (vtkRenderer, vtkPolyData, vtkPolyDataWriter,
                 vtkAppendPolyData, vtkPolyDataReader, vtkPolyDataMapper,
                 vtkActor, vtkPolyDataWriter, vtkUnstructuredGrid,
                 vtkGeometryFilter, vtkTransform, vtkCellArray, vtkTriangle,
                 vtkPoints, vtkDelaunay2D, vtkPolyLine, vtkVertexGlyphFilter,
                 vtkUnstructuredGridWriter, VTK_TRIANGLE)
from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtGui import QDoubleValidator, QStandardItemModel, QStandardItem
from multiprocessing import cpu_count
from platform import platform
from os.path import exists, isfile
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from json import dump, load
from styles import *
from constants import *


def get_thread_count():
    return cpu_count()


def get_os_info():
    return platform()


def is_mesh_dims(value: str):
    try:
        num = int(value)
        return num > 0 and num < 4
    except ValueError:
        return False


def convert_msh_to_vtk(msh_filename: str):
    if not msh_filename.endswith('.msh'):
        return None

    try:
        gmsh.initialize()
        vtk_filename = msh_filename.replace('.msh', '.vtk')
        gmsh.open(msh_filename)
        gmsh.write(vtk_filename)
        gmsh.finalize()
        return vtk_filename
    except Exception as e:
        print(f"Error converting VTK to Msh: {e}")
        return None


def convert_vtk_to_msh(vtk_filename: str):
    """
    Converts a VTK file to a Gmsh (.msh) file.

    Args:
        vtk_filename (str): The filename of the VTK file to convert.

    Returns:
        str: The filename of the converted Gmsh file if successful, None otherwise.
    """
    if not vtk_filename.endswith('.vtk'):
        return None

    msh_filename = vtk_filename.replace('.vtk', '.msh')
    msh_filename = msh_filename.replace('.msh.msh', '.msh')
    try:
        mesh = meshio.read(vtk_filename)
        
        for cell_block in mesh.cells:
            cell_block.data = cell_block.data
            mesh.cell_data.setdefault("gmsh:physical", []).append([1] * len(cell_block.data))
            mesh.cell_data.setdefault("gmsh:geometrical", []).append([1] * len(cell_block.data))
        
        meshio.write(msh_filename, mesh, file_format="gmsh22")
        return msh_filename
    except Exception as e:
        print(f"Error converting VTK to Msh: {e}")
        return None


def ansi_to_segments(text: str):
    segments = []
    current_color = 'light gray'  # Default color
    buffer = ""

    def append_segment(text, color):
        if text:  # Only append non-empty segments
            segments.append((text, color))

    # Split the text by ANSI escape codes
    parts = split(r'(\033\[\d+(?:;\d+)*m)', text)
    for part in parts:
        if not part:  # Skip empty strings
            continue
        if part.startswith('\033['):
            # Remove leading '\033[' and trailing 'm', then split
            codes = part[2:-1].split(';')
            for code in codes:
                if code in ANSI_TO_QCOLOR:
                    current_color = ANSI_TO_QCOLOR[code]
                    # Append the current buffer with the current color
                    append_segment(buffer, current_color)
                    buffer = ""  # Reset buffer
                    break  # Only apply the first matching color
        else:
            buffer += part  # Add text to the buffer
    append_segment(buffer, current_color)  # Append any remaining text
    return segments


def align_view_by_axis(axis: str, renderer: vtkRenderer,
                       vtkWidget: QVTKRenderWindowInteractor):
    axis = axis.strip().lower()

    if axis not in ['x', 'y', 'z', 'center']:
        return

    camera = renderer.GetActiveCamera()
    if axis == 'x':
        camera.SetPosition(1, 0, 0)
        camera.SetViewUp(0, 0, 1)
    elif axis == 'y':
        camera.SetPosition(0, 1, 0)
        camera.SetViewUp(0, 0, 1)
    elif axis == 'z':
        camera.SetPosition(0, 0, 1)
        camera.SetViewUp(0, 1, 0)
    elif axis == 'center':
        camera.SetPosition(1, 1, 1)
        camera.SetViewUp(0, 0, 1)

    camera.SetFocalPoint(0, 0, 0)

    renderer.ResetCamera()
    vtkWidget.GetRenderWindow().Render()


def save_scene(renderer: vtkRenderer,
               logConsole,
               fontColor,
               actors_file='scene_actors.vtk',
               camera_file='scene_camera.json'):
    if save_actors(renderer, logConsole, fontColor, actors_file) is not None and \
            save_camera_settings(renderer, logConsole, fontColor, camera_file) is not None:

        logConsole.insert_colored_text('Successfully: ', 'green')
        logConsole.insert_colored_text(
            f'Saved scene from to the files: {actors_file} and {camera_file}\n',
            fontColor)


def save_actors(renderer: vtkRenderer,
                logConsole,
                fontColor,
                actors_file='scene_actors.vtk'):
    try:
        append_filter = vtkAppendPolyData()
        actors_collection = renderer.GetActors()
        actors_collection.InitTraversal()

        for i in range(actors_collection.GetNumberOfItems()):
            actor = actors_collection.GetNextActor()
            if actor.GetMapper() and actor.GetMapper().GetInput():
                poly_data = actor.GetMapper().GetInput()
                if isinstance(poly_data, vtkPolyData):
                    append_filter.AddInputData(poly_data)

        append_filter.Update()

        writer = vtkPolyDataWriter()
        writer.SetFileName(actors_file)
        writer.SetInputData(append_filter.GetOutput())
        writer.Write()

        logConsole.insert_colored_text('Info: ', 'blue')
        logConsole.insert_colored_text(f'Saved all actors to {actors_file}\n',
                                       fontColor)
        return 1
    except Exception as e:
        logConsole.insert_colored_text('Error: ', 'red')
        logConsole.insert_colored_text(f'Failed to save actors: {e}\n',
                                       fontColor)
        return None


def save_camera_settings(renderer: vtkRenderer,
                         logConsole,
                         fontColor,
                         camera_file='scene_camera.json'):
    try:
        camera = renderer.GetActiveCamera()
        camera_settings = {
            'position': camera.GetPosition(),
            'focal_point': camera.GetFocalPoint(),
            'view_up': camera.GetViewUp(),
            'clip_range': camera.GetClippingRange(),
        }
        with open(camera_file, 'w') as f:
            dump(camera_settings, f)

        return 1
    except Exception as e:
        logConsole.insert_colored_text('Error: ', 'red')
        logConsole.insert_colored_text(
            f'Failed to save camera settings: {e}\n', fontColor)
        return None


def load_scene(vtkWidget: QVTKRenderWindowInteractor,
               renderer: vtkRenderer,
               logConsole,
               fontColor,
               actors_file='scene_actors.vtk',
               camera_file='scene_camera.json'):
    if load_actors(renderer, logConsole, fontColor, actors_file) is not None and \
            load_camera_settings(renderer, logConsole, fontColor, camera_file) is not None:

        vtkWidget.GetRenderWindow().Render()
        logConsole.insert_colored_text('Successfully: ', 'green')
        logConsole.insert_colored_text(
            f'Loaded scene from the files: {actors_file} and {camera_file}\n',
            fontColor)


def load_actors(renderer: vtkRenderer,
                logConsole,
                fontColor,
                actors_file='scene_actors.vtk'):
    try:
        reader = vtkPolyDataReader()
        reader.SetFileName(actors_file)
        reader.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(reader.GetOutput())

        actor = vtkActor()
        actor.SetMapper(mapper)
        renderer.AddActor(actor)
        renderer.ResetCamera()

        logConsole.insert_colored_text('Info: ', 'blue')
        logConsole.insert_colored_text(f'Loaded actors from {actors_file}\n',
                                       fontColor)
        return 1
    except Exception as e:
        logConsole.insert_colored_text('Error: ', 'red')
        logConsole.insert_colored_text(f'Failed to load actors: {e}\n',
                                       fontColor)
        return None


def load_camera_settings(renderer: vtkRenderer,
                         logConsole,
                         fontColor,
                         camera_file='scene_camera.json'):
    try:
        with open(camera_file, 'r') as f:
            camera_settings = load(f)

        camera = renderer.GetActiveCamera()
        camera.SetPosition(*camera_settings['position'])
        camera.SetFocalPoint(*camera_settings['focal_point'])
        camera.SetViewUp(*camera_settings['view_up'])
        camera.SetClippingRange(*camera_settings['clip_range'])

        renderer.ResetCamera()
        return 1
    except Exception as e:
        logConsole.insert_colored_text('Error: ', 'red')
        logConsole.insert_colored_text(
            f'Failed to load camera settings: {e}\n', fontColor)
        return None


def get_polydata_from_actor(actor: vtkActor):
    mapper = actor.GetMapper()
    if hasattr(mapper, "GetInput"):
        return mapper.GetInput()
    else:
        return None


def write_vtk_polydata_to_file(polyData):
    writer = vtkPolyDataWriter()
    writer.SetInputData(polyData)

    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.vtk')
    temp_file_name = temp_file.name
    temp_file.close()

    # Set the filename in the writer and write
    writer.SetFileName(temp_file_name)
    writer.Write()

    # Return the path to the temporary file
    return temp_file_name


def is_conversion_success(polyData):
    # Check if the polyData is not None
    if polyData is None:
        return False

    # Check if there are any points and cells in the polyData
    numberOfPoints = polyData.GetNumberOfPoints()
    numberOfCells = polyData.GetNumberOfCells()

    if numberOfPoints > 0 and numberOfCells > 0:
        return True  # Conversion was successful and resulted in a non-empty polyData
    else:
        return False  # Conversion failed to produce meaningful polyData


def convert_vtkUnstructuredGrid_to_vtkPolyData_helper(
        ugrid: vtkUnstructuredGrid):
    geometryFilter = vtkGeometryFilter()
    geometryFilter.SetInputData(ugrid)

    geometryFilter.Update()

    polyData = geometryFilter.GetOutput()
    if not is_conversion_success(polyData):
        return None

    return polyData


def convert_vtkUnstructuredGrid_to_vtkPolyData(data):
    if data.IsA("vtkUnstructuredGrid"):
        return convert_vtkUnstructuredGrid_to_vtkPolyData_helper(data)
    elif data.IsA("vtkPolyData"):
        return data
    else:
        return None


def convert_unstructured_grid_to_polydata(data):
    converted_part_1 = get_polydata_from_actor(data)
    converted_part_2 = convert_vtkUnstructuredGrid_to_vtkPolyData(
        converted_part_1)
    return converted_part_2


def convert_vtkPolyData_to_vtkUnstructuredGrid(polydata):
    """
    Converts vtkPolyData to vtkUnstructuredGrid.

    Args:
        polydata (vtkPolyData): The polydata to convert.

    Returns:
        vtkUnstructuredGrid: The converted unstructured grid.
    """
    if not polydata.IsA("vtkPolyData"):
        return None

    ugrid = vtkUnstructuredGrid()
    points = vtkPoints()
    points.SetDataTypeToDouble()
    cells = vtkCellArray()

    for i in range(polydata.GetNumberOfPoints()):
        points.InsertNextPoint(polydata.GetPoint(i))

    for i in range(polydata.GetNumberOfCells()):
        cell = polydata.GetCell(i)
        cell_type = cell.GetCellType()
        ids = cell.GetPointIds()

        if cell_type == VTK_TRIANGLE:
            triangle = vtkTriangle()
            triangle.GetPointIds().SetId(0, ids.GetId(0))
            triangle.GetPointIds().SetId(1, ids.GetId(1))
            triangle.GetPointIds().SetId(2, ids.GetId(2))
            cells.InsertNextCell(triangle)

    ugrid.SetPoints(points)
    ugrid.SetCells(VTK_TRIANGLE, cells)

    return ugrid


def remove_temp_files_helper(filename: str):
    try:
        if exists(filename):
            remove(filename)
    except Exception as ex:
        print(f"Some error occurs: Can't remove file {filename}. Error: {ex}")
        return


def remove_temp_files():
    # High probability that user don't want to delete temporary config file

    # Removing all temporary files excluding temporary config file
    remove_temp_files_helper(DEFAULT_TEMP_MESH_FILE)
    remove_temp_files_helper(DEFAULT_TEMP_VTK_FILE)
    remove_temp_files_helper(DEFAULT_TEMP_HDF5_FILE)


def extract_transform_from_actor(actor: vtkActor):
    matrix = actor.GetMatrix()

    transform = vtkTransform()
    transform.SetMatrix(matrix)

    return transform


def calculate_direction(base, tip):
    from numpy import array, linalg

    base = array(base)
    tip = array(tip)

    direction = tip - base

    norm = linalg.norm(direction)
    if norm == 0:
        raise ValueError("The direction vector cannot be zero.")
    direction /= norm

    return direction


def calculate_thetaPhi(base, tip):
    from numpy import arctan2, arccos

    direction = calculate_direction(base, tip)
    x, y, z = direction[0], direction[1], direction[2]

    theta = arccos(z)
    phi = arctan2(y, x)

    return theta, phi


def calculate_thetaPhi_with_angles(x, y, z, angle_x, angle_y, angle_z):
    direction_vector = np.array([
        np.cos(np.radians(angle_y)) * np.cos(np.radians(angle_z)),
        np.sin(np.radians(angle_x)) * np.sin(np.radians(angle_z)),
        np.cos(np.radians(angle_x)) * np.cos(np.radians(angle_y))
    ])
    norm = np.linalg.norm(direction_vector)
    theta = np.arccos(direction_vector[2] / norm)
    phi = np.arctan2(direction_vector[1], direction_vector[0])
    return theta, phi


def rad_to_degree(angle: float):
    return angle * 180. / pi


def degree_to_rad(angle: float):
    return angle * pi / 180.


def extract_transformed_points(polydata: vtkPolyData):
    points = polydata.GetPoints()
    return [points.GetPoint(i) for i in range(points.GetNumberOfPoints())]


def get_transformation_matrix(actor: vtkActor):
    return actor.GetMatrix()


def transform_coordinates(points, matrix):
    transform = vtkTransform()
    transform.SetMatrix(matrix)
    transformed_points = []
    for point in points:
        transformed_point = transform.TransformPoint(point[0], point[1],
                                                     point[2])
        transformed_points.append(transformed_point)
    return transformed_points


def getTreeDict(mesh_filename: str = None, obj_type: str = 'volume') -> dict:
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


def createActorsFromTreeDict(treedict: dict, objType: str) -> list:
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


def populateTreeView(treedict: dict, object_idx: int,
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


def can_create_surface(point_data):
    """
    Check if a surface can be created from the given set of points using VTK.

    Parameters:
    point_data (list of tuples): List of (x, y, z) coordinates of the points.

    Returns:
    bool: True if the surface can be created, False otherwise.
    """
    # Create a vtkPoints object and add the points
    points = vtkPoints()
    for x, y, z in point_data:
        points.InsertNextPoint(x, y, z)

    # Create a polydata object and set the points
    poly_data = vtkPolyData()
    poly_data.SetPoints(points)

    # Create a Delaunay2D object and set the input
    delaunay = vtkDelaunay2D()
    delaunay.SetInputData(poly_data)

    # Try to create the surface
    delaunay.Update()

    # Check if the surface was created
    output = delaunay.GetOutput()
    if output.GetNumberOfCells() > 0:
        return True
    else:
        return False


def can_create_line(point_data):
    """
    Check if a line can be created from the given set of points using VTK.

    Parameters:
    point_data (list of tuples): List of (x, y, z) coordinates of the points.

    Returns:
    bool: True if the line can be created, False otherwise.
    """
    # Check if all points are the same
    if all(point == point_data[0] for point in point_data):
        return False

    # Create a vtkPoints object and add the points
    points = vtkPoints()
    for x, y, z in point_data:
        points.InsertNextPoint(x, y, z)

    # Create a polyline object
    line = vtkPolyLine()
    line.GetPointIds().SetNumberOfIds(len(point_data))

    for i in range(len(point_data)):
        line.GetPointIds().SetId(i, i)

    # Create a vtkCellArray and add the line to it
    lines = vtkCellArray()
    lines.InsertNextCell(line)

    # Create a polydata object and set the points and lines
    poly_data = vtkPolyData()
    poly_data.SetPoints(points)
    poly_data.SetLines(lines)

    # Check if the line was created
    if poly_data.GetNumberOfLines() > 0:
        return True
    else:
        return False


def print_tree_structure(self, tree_view: QTreeView):
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


def formActorNodesDictionary(treedict: dict, actor_rows: dict, objType: str):
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


def get_cur_datetime() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def compare_matrices(mat1, mat2):
    """
    Compare two vtkMatrix4x4 matrices for equality.

    Args:
        mat1 (vtkMatrix4x4): The first matrix.
        mat2 (vtkMatrix4x4): The second matrix.

    Returns:
        bool: True if the matrices are equal, False otherwise.
    """
    for i in range(4):
        for j in range(4):
            if mat1.GetElement(i, j) != mat2.GetElement(i, j):
                return False
    return True


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
        copy_children(source_item.child(row), child)


def merge_actors(actors):
    """
    Merge the provided list of actors into a single actor.

    Args:
        actors (list): List of vtkActor objects to be merged.

    Returns:
        vtkActor: A new actor that is the result of merging the provided actors.
    """
    # Merging actors
    append_filter = vtkAppendPolyData()
    for actor in actors:
        poly_data = actor.GetMapper().GetInput()
        append_filter.AddInputData(poly_data)
    append_filter.Update()

    # Creating a new merged actor
    merged_mapper = vtkPolyDataMapper()
    merged_mapper.SetInputData(append_filter.GetOutput())

    merged_actor = vtkActor()
    merged_actor.SetMapper(merged_mapper)
    merged_actor.GetProperty().SetColor(DEFAULT_ACTOR_COLOR)

    return merged_actor


def compute_distance_between_points(coord1, coord2):
    """
    Compute the Euclidean distance between two points in 3D space.
    """
    try:
        result = np.sqrt((coord1[0] - coord2[0])**2 +
                         (coord1[1] - coord2[1])**2 +
                         (coord1[2] - coord2[2])**2)
    except Exception as e:
        print_warning_none_result()
        return None
    return result


def pretty_function_details() -> str:
    """
    Prints the details of the calling function in the format:
    <file name>: line[<line number>]: <func name>(<args>)
    """
    from inspect import currentframe, getargvalues

    current_frame = currentframe()
    caller_frame = current_frame.f_back
    function_name = caller_frame.f_code.co_name
    args, _, _, values = getargvalues(caller_frame)
    function_file = caller_frame.f_code.co_filename
    formatted_args = ', '.join([f"{arg}={values[arg]}" for arg in args])
    return f"{function_file}: {function_name}({formatted_args})"


def get_warning_none_result():
    return f"Warning, {pretty_function_details()} returned {None} result"


def print_warning_none_result():
    print(get_warning_none_result())


def get_warning_none_result_with_exception_msg(exmsg: str):
    return f"Warning, {pretty_function_details()} returned {None} result. Exception: {exmsg}"
    

def print_warning_none_result_with_exception_msg(exmsg: str):
    print(get_warning_none_result_with_exception_msg(exmsg))
