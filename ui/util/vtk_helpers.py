from gmsh import initialize, finalize, isInitialized, write
from tempfile import NamedTemporaryFile
from meshio import read, write
from vtk import (
    vtkUnstructuredGrid, vtkPolyData, vtkPolyDataWriter, vtkActor,
    vtkGeometryFilter, vtkPoints, vtkCellArray, vtkTriangle, vtkTransform,
    vtkAppendPolyData, vtkPolyDataMapper,
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
        
        write(msh_filename, mesh, file_format="gmsh2")
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
