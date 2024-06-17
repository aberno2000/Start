from gmsh import initialize, finalize, model, isInitialized
from vtk import vtkPoints, vtkPolygon, vtkCellArray, vtkPolyData, vtkPolyDataMapper, vtkActor
from logger import LogConsole
from util import can_create_surface, get_cur_datetime


class Surface:
    """
    A class to represent a surface geometry.

    Attributes
    ----------
    log_console : LogConsole
        The logging console for outputting messages.
    points : list of tuple
        The list of points defining the surface.

    Methods
    -------
    create_surface_with_vtk():
        Creates the surface using VTK and returns the actor.
    create_surface_with_gmsh():
        Creates the surface using Gmsh.
    can_create_surface():
        Checks if the surface can be created with the specified points.
    __repr__():
        Returns a string representation of the surface.
    """

    def __init__(self, log_console: LogConsole, points: list):
        """
        Constructs all the necessary attributes for the surface object.

        Parameters
        ----------
            log_console : LogConsole
                The logging console for outputting messages.
            points : list of tuple
                The list of points defining the surface.
        """
        self.log_console = log_console
        self.points = points

        if not can_create_surface(self.points):
            self.log_console.printWarning(
                f"Can't create surface with specified points:\n{self.points}")
            raise ValueError("Invalid points for creating a surface.")

    def create_surface_with_vtk(self) -> vtkActor:
        """
        Creates the surface using VTK and returns the actor.

        Returns
        -------
        vtkActor
            The actor representing the surface.
        """
        try:
            vtk_points = vtkPoints()
            polygon = vtkPolygon()
            polygon.GetPointIds().SetNumberOfIds(len(self.points))

            for i, (x, y, z) in enumerate(self.points):
                vtk_points.InsertNextPoint(x, y, z)
                polygon.GetPointIds().SetId(i, i)

            cells = vtkCellArray()
            cells.InsertNextCell(polygon)

            poly_data = vtkPolyData()
            poly_data.SetPoints(vtk_points)
            poly_data.SetPolys(cells)

            mapper = vtkPolyDataMapper()
            mapper.SetInputData(poly_data)

            actor = vtkActor()
            actor.SetMapper(mapper)

            return actor
        except Exception as e:
            self.log_console.printError(
                f"An error occurred while creating the surface with VTK: {e}")

    def create_surface_with_gmsh(self):
        """
        Creates the surface using Gmsh.
        """
        try:
            if not isInitialized():
                initialize()

            model.add(f"surface_{get_cur_datetime()}")

            for idx, (x, y, z) in enumerate(self.points, start=1):
                model.geo.addPoint(x, y, z, tag=idx)
            for i in range(len(self.points)):
                model.geo.addLine(i + 1, ((i + 1) % len(self.points)) + 1)
            loop = model.geo.addCurveLoop(list(range(1, len(self.points) + 1)))
            model.geo.addPlaneSurface([loop])
            model.geo.synchronize()

            finalize()
        except Exception as e:
            self.log_console.printError(
                f"An error occurred while creating the surface with Gmsh: {e}")
        finally:
            if isInitialized():
                finalize()

    def __repr__(self):
        """
        Returns a string representation of the surface.

        Returns
        -------
        str
            A string representation of the surface.
        """
        points_str = [
            f'Point{i + 1}: ({x}, {y}, {z})'
            for i, (x, y, z) in enumerate(self.points)
        ]
        return '\n'.join(points_str)
