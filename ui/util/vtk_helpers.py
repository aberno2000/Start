from gmsh import initialize, finalize, isInitialized, write
from tempfile import NamedTemporaryFile
from meshio import read
from vtk import (
    vtkUnstructuredGrid, vtkPolyData, vtkPolyDataWriter, vtkActor,
    vtkGeometryFilter, vtkPoints, vtkCellArray, vtkTriangle, vtkTransform,
    vtkAppendPolyData, vtkPolyDataMapper, vtkFeatureEdges, vtkPolyDataConnectivityFilter,
    VTK_TRIANGLE
)
from styles import DEFAULT_ACTOR_COLOR


def convert_msh_to_vtk(msh_filename: str):
    from gmsh import open
    
    if not msh_filename.endswith('.msh'):
        return None

    try:
        if not isInitialized():
            initialize()
        initialize()
        
        vtk_filename = msh_filename.replace('.msh', '.vtk')
        open(msh_filename)
        write(vtk_filename)
        
        return vtk_filename
    except Exception as e:
        print(f"Error converting VTK to Msh: {e}")
        return None
    finally:
        if isInitialized():
            finalize()


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
        mesh = read(vtk_filename)
        
        for cell_block in mesh.cells:
            cell_block.data = cell_block.data
            mesh.cell_data.setdefault("gmsh:physical", []).append([1] * len(cell_block.data))
            mesh.cell_data.setdefault("gmsh:geometrical", []).append([1] * len(cell_block.data))
        
        write(msh_filename, mesh, file_format="gmsh")
        return msh_filename
    except Exception as e:
        print(f"Error converting VTK to Msh: {e}")
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
    temp_file = NamedTemporaryFile(delete=False, suffix='.vtk')
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


def convert_vtkUnstructuredGrid_to_vtkPolyData_helper(ugrid: vtkUnstructuredGrid):
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
    """Convert vtkPolyData to vtkUnstructuredGrid with boundaries and surfaces."""
    boundaries = extract_boundaries(polydata)
    surfaces = extract_surfaces(polydata)

    ugrid = vtkUnstructuredGrid()
    points = vtkPoints()
    points.SetDataTypeToDouble()
    cells = vtkCellArray()

    # Copy points
    points.DeepCopy(polydata.GetPoints())

    # Copy cells
    for i in range(polydata.GetNumberOfCells()):
        cell = polydata.GetCell(i)
        cell_type = cell.GetCellType()
        ids = cell.GetPointIds()

        if cell_type == VTK_TRIANGLE:
            triangle = vtkTriangle()
            for j in range(3):
                triangle.GetPointIds().SetId(j, ids.GetId(j))
            cells.InsertNextCell(triangle)

    ugrid.SetPoints(points)
    ugrid.SetCells(VTK_TRIANGLE, cells)

    return ugrid, boundaries, surfaces


def extract_geometry_data(actor: vtkActor):
    """Extract points and cells from a vtkActor."""
    from vtkmodules.util.numpy_support import vtk_to_numpy
    
    mapper = actor.GetMapper()
    polydata = mapper.GetInput()

    ug, boundaries, surfaces = convert_vtkPolyData_to_vtkUnstructuredGrid(polydata)
    if ug is None:
        raise ValueError("Failed to convert PolyData to UnstructuredGrid")

    points = vtk_to_numpy(ug.GetPoints().GetData()).astype('float64')
    if points is None or len(points) == 0:
        raise ValueError("No points found in the UnstructuredGrid")

    cells = vtk_to_numpy(ug.GetCells().GetData())
    if cells is None or len(cells) == 0:
        raise ValueError("No cells found in the UnstructuredGrid")

    cell_offsets = vtk_to_numpy(ug.GetCellLocationsArray())
    cell_types = vtk_to_numpy(ug.GetCellTypesArray())
    cells = extract_cells(cells, cell_offsets, cell_types)
    if not cells:
        raise ValueError("Failed to extract cells")

    return points, cells, boundaries, surfaces

def extract_boundaries(polydata):
    """Extract boundaries from vtkPolyData using vtkFeatureEdges."""
    feature_edges = vtkFeatureEdges()
    feature_edges.SetInputData(polydata)
    feature_edges.BoundaryEdgesOn()
    feature_edges.FeatureEdgesOff()
    feature_edges.ManifoldEdgesOff()
    feature_edges.NonManifoldEdgesOff()
    feature_edges.Update()

    return feature_edges.GetOutput()

def extract_surfaces(polydata):
    """Extract surfaces from vtkPolyData using vtkPolyDataConnectivityFilter."""
    connectivity_filter = vtkPolyDataConnectivityFilter()
    connectivity_filter.SetInputData(polydata)
    connectivity_filter.SetExtractionModeToAllRegions()
    connectivity_filter.ColorRegionsOn()
    connectivity_filter.Update()

    return connectivity_filter.GetOutput()

def extract_cells(cells, cell_offsets, cell_types):
        """
        Helper function to extract cells in the format meshio expects.
        """
        from numpy import array
        from vtk import VTK_TRIANGLE, VTK_TETRA

        cell_dict = {}
        for offset, ctype in zip(cell_offsets, cell_types):
            if ctype in cell_dict:
                cell_dict[ctype].append(cells[offset + 1:offset + 4])
            else:
                cell_dict[ctype] = [cells[offset + 1:offset + 4]]

        meshio_cells = []
        for ctype, cell_list in cell_dict.items():
            cell_list = array(cell_list)
            if ctype == VTK_TRIANGLE:
                meshio_cells.append(("triangle", cell_list[:, :3]))
            elif ctype == VTK_TETRA:
                meshio_cells.append(("tetra", cell_list[:, :4]))

        return meshio_cells


def extract_transform_from_actor(actor: vtkActor):
    matrix = actor.GetMatrix()

    transform = vtkTransform()
    transform.SetMatrix(matrix)

    return transform

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
        transformed_point = transform.TransformPoint(point[0], point[1], point[2])
        transformed_points.append(transformed_point)
    return transformed_points


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
