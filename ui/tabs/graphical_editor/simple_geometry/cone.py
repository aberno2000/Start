from gmsh import initialize, finalize, model, isInitialized
from vtk import vtkConeSource, vtkActor, vtkPolyDataMapper, vtkTriangleFilter, vtkLinearSubdivisionFilter
from logger import LogConsole
from util import get_cur_datetime

class Cone:
    """
    A class to represent a cone geometry.

    Attributes
    ----------
    x : float
        The x-coordinate of the cone's base center.
    y : float
        The y-coordinate of the cone's base center.
    z : float
        The z-coordinate of the cone's base center.
    dx : float
        The x-component of the cone's axis direction.
    dy : float
        The y-component of the cone's axis direction.
    dz : float
        The z-component of the cone's axis direction.
    r : float
        The radius of the cone's base.
    mesh_resolution : int
        The resolution of the cone's mesh.

    Methods
    -------
    create_cone_with_vtk():
        Creates the cone using VTK and returns the actor.
    create_cone_with_gmsh():
        Creates the cone using Gmsh.
    __repr__():
        Returns a string representation of the cone.
    """

    def __init__(self, log_console: LogConsole, x: float, y: float, z: float, dx: float, dy: float, dz: float, height: float, r: float, resolution: int, mesh_resolution: int):
        """
        Constructs all the necessary attributes for the cone object.

        Parameters
        ----------
            x : float
                The x-coordinate of the cone's base center.
            y : float
                The y-coordinate of the cone's base center.
            z : float
                The z-coordinate of the cone's base center.
            dx : float
                The x-component of the cone's axis direction.
            dy : float
                The y-component of the cone's axis direction.
            dz : float
                The z-component of the cone's axis direction.
            r : float
                The radius of the cone's base.
            mesh_resolution : int
                The resolution of the cone's mesh.
        """
        self.log_console = log_console
        self.x = x
        self.y = y
        self.z = z
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.height = height
        self.r = r
        self.resolution = resolution
        self.mesh_resolution = mesh_resolution

    def create_cone_with_vtk(self) -> vtkActor:
        """
        Creates the cone using VTK and returns the actor.

        Returns
        -------
        vtkActor
            The actor representing the cone.
        """
        try:
            cone_source = vtkConeSource()
            cone_source.SetCenter(self.x, self.y, self.z)
            cone_source.SetDirection(self.dx, self.dy, self.dz)
            cone_source.SetRadius(self.r)
            cone_source.SetHeight(self.height)
            cone_source.SetResolution(self.resolution)
            cone_source.Update()

            triangle_filter = vtkTriangleFilter()
            triangle_filter.SetInputConnection(cone_source.GetOutputPort())
            triangle_filter.Update()

            subdivision_filter = vtkLinearSubdivisionFilter()
            subdivision_filter.SetInputConnection(triangle_filter.GetOutputPort())
            subdivision_filter.SetNumberOfSubdivisions(self.mesh_resolution)
            subdivision_filter.Update()

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(subdivision_filter.GetOutputPort())

            actor = vtkActor()
            actor.SetMapper(mapper)

            return actor

        except Exception as e:
            self.log_console.printError(f"An error occurred while creating the cone with VTK: {e}")
            return None

    def create_cone_with_gmsh(self):
        """
        Creates the cone using Gmsh.
        """
        try:
            if not isInitialized():
                initialize()

            model.add(f"cone_{get_cur_datetime()}")
            model.occ.addCone(self.x, self.y, self.z, self.dx, self.dy, self.dz, self.r, 0)
            model.occ.synchronize()
        
        except Exception as e:
            self.log_console.printError(f"An error occurred while creating the cone with Gmsh: {e}")
        finally:
            if isInitialized():
                finalize()

    def __repr__(self):
        """
        Returns a string representation of the cone.

        Returns
        -------
        str
            A string representation of the cone.
        """
        cone_data_str = []
        cone_data_str.append(f'Base Center: ({self.x}, {self.y}, {self.z})')
        cone_data_str.append(f'Axis Direction: ({self.dx}, {self.dy}, {self.dz})')
        cone_data_str.append(f'Base Radius: {self.r}')
        cone_data_str.append(f'Height: {self.height}')
        return '\n'.join(cone_data_str)
