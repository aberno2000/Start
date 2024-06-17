from gmsh import initialize, finalize, model, isInitialized
from vtk import vtkPoints, vtkPolyLine, vtkCellArray, vtkPolyData, vtkPolyDataMapper, vtkActor
from logger import LogConsole
from util import can_create_line, get_cur_datetime


class Line:
    """
    A class to represent a line geometry.

    Attributes
    ----------
    log_console : LogConsole
        The logging console for outputting messages.
    points : list of tuple
        The list of points defining the line.

    Methods
    -------
    create_line_with_vtk():
        Creates the line using VTK and returns the actor.
    create_line_with_gmsh():
        Creates the line using 
    can_create_line():
        Checks if the line can be created with the specified points.
    __repr__():
        Returns a string representation of the line.
    """

    def __init__(self, log_console: LogConsole, points: list):
        """
        Constructs all the necessary attributes for the line object.

        Parameters
        ----------
            log_console : LogConsole
                The logging console for outputting messages.
            points : list of tuple
                The list of points defining the line.
        """
        self.log_console = log_console
        self.points = points

        if not can_create_line(self.points):
            self.log_console.printWarning(
                f"Can't create line with specified points:\n{self.points}")
            raise ValueError("Invalid points for creating a line.")

    def create_line_with_vtk(self) -> vtkActor:
        """
        Creates the line using VTK and returns the actor.

        Returns
        -------
        vtkActor
            The actor representing the line.
        """
        try:
            vtk_points = vtkPoints()
            polyline = vtkPolyLine()
            polyline.GetPointIds().SetNumberOfIds(len(self.points))

            for i, (x, y, z) in enumerate(self.points):
                vtk_points.InsertNextPoint(x, y, z)
                polyline.GetPointIds().SetId(i, i)

            cells = vtkCellArray()
            cells.InsertNextCell(polyline)

            poly_data = vtkPolyData()
            poly_data.SetPoints(vtk_points)
            poly_data.SetLines(cells)

            mapper = vtkPolyDataMapper()
            mapper.SetInputData(poly_data)

            actor = vtkActor()
            actor.SetMapper(mapper)

            return actor
        except Exception as e:
            self.log_console.printError(
                f"An error occurred while creating the line with VTK: {e}")

    def create_line_with_gmsh(self):
        """
        Creates the line using Gmsh.
        """
        try:
            if not isInitialized():
                initialize()

            model.add(f"line_{get_cur_datetime()}")
            for idx, (x, y, z) in enumerate(self.points, start=1):
                model.occ.addPoint(x, y, z)
            for i in range(len(self.points) - 1):
                model.occ.addLine(i + 1, i + 2)
            model.occ.synchronize()

            finalize()
        except Exception as e:
            self.log_console.printError(
                f"An error occurred while creating the line with Gmsh: {e}")
        finally:
            if isInitialized():
                finalize()

    def __repr__(self):
        """
        Returns a string representation of the line.

        Returns
        -------
        str
            A string representation of the line.
        """
        points_str = [
            f'Point{i + 1}: ({x}, {y}, {z})'
            for i, (x, y, z) in enumerate(self.points)
        ]
        return '\n'.join(points_str)
