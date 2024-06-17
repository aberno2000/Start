from gmsh import initialize, finalize, model, isInitialized
from vtk import vtkCylinderSource, vtkPolyDataMapper, vtkActor
from logger import LogConsole
from util import get_cur_datetime
from .simple_geometry_constants import DEFAULT_CYLINDER_RESOLUTION


class Cylinder:
    """
    A class to represent a cylinder geometry.

    Attributes
    ----------
    log_console : LogConsole
        The logging console for outputting messages.
    x : float
        The x-coordinate of the cylinder's primary point.
    y : float
        The y-coordinate of the cylinder's primary point.
    z : float
        The z-coordinate of the cylinder's primary point.
    radius : float
        The radius of the cylinder.
    dx : float
        The length of the cylinder along the x-axis.
    dy : float
        The length of the cylinder along the y-axis.
    dz : float
        The length of the cylinder along the z-axis.

    Methods
    -------
    create_cylinder_with_vtk():
        Creates the cylinder using VTK and returns the actor.
    create_cylinder_with_gmsh():
        Creates the cylinder using 
    __repr__():
        Returns a string representation of the cylinder.
    """

    def __init__(self,
                 log_console: LogConsole,
                 x: float,
                 y: float,
                 z: float,
                 radius: float,
                 dx: float,
                 dy: float,
                 dz: float,
                 resolution: int = DEFAULT_CYLINDER_RESOLUTION):
        """
        Constructs all the necessary attributes for the cylinder object.

        Parameters
        ----------
            log_console : LogConsole
                The logging console for outputting messages.
            x : float
                The x-coordinate of the cylinder's primary point.
            y : float
                The y-coordinate of the cylinder's primary point.
            z : float
                The z-coordinate of the cylinder's primary point.
            radius : float
                The radius of the cylinder.
            dx : float
                The length of the cylinder along the x-axis.
            dy : float
                The length of the cylinder along the y-axis.
            dz : float
                The length of the cylinder along the z-axis.
        """
        self.log_console = log_console
        self.x = x
        self.y = y
        self.z = z
        self.radius = radius
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.resolution = resolution

    def create_cylinder_with_vtk(self) -> vtkActor:
        """
        Creates the cylinder using VTK and returns the actor.

        Returns
        -------
        vtkActor
            The actor representing the cylinder.
        """
        try:
            cylinder_source = vtkCylinderSource()
            cylinder_source.SetRadius(self.radius)
            cylinder_source.SetHeight(self.dz)
            cylinder_source.SetCenter(self.x, self.y, self.z + self.dz / 2)
            cylinder_source.SetResolution(self.resolution)
            cylinder_source.Update()

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(cylinder_source.GetOutputPort())

            actor = vtkActor()
            actor.SetMapper(mapper)

            return actor
        except Exception as e:
            self.log_console.printError(
                f"An error occurred while creating the cylinder with VTK: {e}")

    def create_cylinder_with_gmsh(self):
        """
        Creates the cylinder using Gmsh.
        """
        try:
            if not isInitialized():
                initialize()

            model.add(f"cylinder_{get_cur_datetime()}")
            model.occ.addCylinder(self.x, self.y, self.z, self.dx, self.dy,
                                  self.dz, self.radius)
            model.occ.synchronize()

            finalize()
        except Exception as e:
            self.log_console.printError(
                f"An error occurred while creating the cylinder with Gmsh: {e}"
            )
        finally:
            if isInitialized():
                finalize()

    def __repr__(self):
        """
        Returns a string representation of the cylinder.

        Returns
        -------
        str
            A string representation of the cylinder.
        """
        cylinder_data_str = []
        cylinder_data_str.append(
            f'Primary Point: ({self.x}, {self.y}, {self.z})')
        cylinder_data_str.append(f'Radius: {self.radius}')
        cylinder_data_str.append(f'Length: {self.dx}')
        cylinder_data_str.append(f'Width: {self.dy}')
        cylinder_data_str.append(f'Height: {self.dz}')
        return '\n'.join(cylinder_data_str)
