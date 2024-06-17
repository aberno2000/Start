from gmsh import initialize, finalize, model, isInitialized
from vtk import vtkPoints, vtkVertexGlyphFilter, vtkPolyData, vtkPolyDataMapper, vtkActor, vtkCellArray
from logger import LogConsole
from util import get_cur_datetime


class Point:
    """
    A class to represent a point geometry.

    Attributes
    ----------
    log_console : LogConsole
        The logging console for outputting messages.
    x : float
        The x-coordinate of the point.
    y : float
        The y-coordinate of the point.
    z : float
        The z-coordinate of the point.

    Methods
    -------
    create_point_with_vtk():
        Creates the point using VTK and returns the actor.
    create_point_with_gmsh():
        Creates the point using Gmsh.
    __repr__():
        Returns a string representation of the point.
    """

    def __init__(self, log_console: LogConsole, x: float, y: float, z: float):
        """
        Constructs all the necessary attributes for the point object.

        Parameters
        ----------
            log_console : LogConsole
                The logging console for outputting messages.
            x : float
                The x-coordinate of the point.
            y : float
                The y-coordinate of the point.
            z : float
                The z-coordinate of the point.
        """
        self.log_console = log_console
        self.x = x
        self.y = y
        self.z = z

    def create_point_with_vtk(self) -> vtkActor:
        """
        Creates the point using VTK and returns the actor.

        Returns
        -------
        vtkActor
            The actor representing the point.
        """
        try:
            vtk_points = vtkPoints()
            vtk_points.InsertNextPoint(self.x, self.y, self.z)

            poly_data = vtkPolyData()
            poly_data.SetPoints(vtk_points)

            glyph_filter = vtkVertexGlyphFilter()
            glyph_filter.SetInputData(poly_data)
            glyph_filter.Update()

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(glyph_filter.GetOutputPort())

            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetPointSize(10)

            return actor
        except Exception as e:
            self.log_console.printError(
                f"An error occurred while creating the point with VTK: {e}")

    def create_point_with_gmsh(self):
        """
        Creates the point using Gmsh.
        """
        try:
            if not isInitialized():
                initialize()

            model.add(f"point_{get_cur_datetime()}")
            model.occ.addPoint(self.x, self.y, self.z)
            model.occ.synchronize()

            finalize()
        except Exception as e:
            self.log_console.printError(
                f"An error occurred while creating the point with Gmsh: {e}")
        finally:
            if isInitialized():
                finalize()

    def __repr__(self):
        """
        Returns a string representation of the point.

        Returns
        -------
        str
            A string representation of the point.
        """
        return f'Point: ({self.x}, {self.y}, {self.z})'
