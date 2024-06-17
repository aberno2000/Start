from gmsh import initialize, finalize, model, isInitialized
from vtk import vtkSphereSource, vtkPolyDataMapper, vtkActor
from logger import LogConsole
from util import get_cur_datetime
from .simple_geometry_constants import *


class Sphere:
    """
    A class to represent a sphere geometry.

    Attributes
    ----------
    log_console : LogConsole
        The logging console for outputting messages.
    x : float
        The x-coordinate of the sphere's center.
    y : float
        The y-coordinate of the sphere's center.
    z : float
        The z-coordinate of the sphere's center.
    radius : float
        The radius of the sphere.

    Methods
    -------
    create_sphere_with_vtk():
        Creates the sphere using VTK and returns the actor.
    create_sphere_with_gmsh():
        Creates the sphere using 
    __repr__():
        Returns a string representation of the sphere.
    """

    def __init__(self,
                 log_console: LogConsole,
                 x: float,
                 y: float,
                 z: float,
                 radius: float,
                 phi_resolution: int = DEFAULT_SPHERE_PHI_RESOLUTION,
                 theta_resolution: int = DEFAULT_SPHERE_THETA_RESOLUTION):
        """
        Constructs all the necessary attributes for the sphere object.

        Parameters
        ----------
            log_console : LogConsole
                The logging console for outputting messages.
            x : float
                The x-coordinate of the sphere's center.
            y : float
                The y-coordinate of the sphere's center.
            z : float
                The z-coordinate of the sphere's center.
            radius : float
                The radius of the sphere.
            phi_resolution : int, optional
                The phi resolution of the sphere (default is DEFAULT_SPHERE_PHI_RESOLUTION).
            theta_resolution : int, optional
                The theta resolution of the sphere (default is DEFAULT_SPHERE_THETA_RESOLUTION).
        """
        self.log_console = log_console
        self.x = x
        self.y = y
        self.z = z
        self.radius = radius
        self.phi_resolution = phi_resolution
        self.theta_resolution = theta_resolution

    def create_sphere_with_vtk(self) -> vtkActor:
        """
        Creates the sphere using VTK and returns the actor.

        Returns
        -------
        vtkActor
            The actor representing the sphere.
        """
        try:
            sphere_source = vtkSphereSource()
            sphere_source.SetCenter(self.x, self.y, self.z)
            sphere_source.SetRadius(self.radius)
            sphere_source.Update()
            sphere_source.SetPhiResolution(self.phi_resolution)
            sphere_source.SetThetaResolution(self.theta_resolution)

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(sphere_source.GetOutputPort())

            actor = vtkActor()
            actor.SetMapper(mapper)

            return actor
        except Exception as e:
            self.log_console.printError(
                f"An error occurred while creating the sphere with VTK: {e}")

    def create_sphere_with_gmsh(self):
        """
        Creates the sphere using Gmsh.
        """
        try:
            if not isInitialized():
                initialize()

            model.add(f"sphere_{get_cur_datetime()}")
            model.occ.addSphere(self.x, self.y, self.z, self.radius)
            model.occ.synchronize()

            finalize()
        except Exception as e:
            self.log_console.printError(
                f"An error occurred while creating the sphere with Gmsh: {e}")
        finally:
            if isInitialized():
                finalize()

    def __repr__(self):
        """
        Returns a string representation of the sphere.

        Returns
        -------
        str
            A string representation of the sphere.
        """
        sphere_data_str = []
        sphere_data_str.append(f'Center: ({self.x}, {self.y}, {self.z})')
        sphere_data_str.append(f'Radius: {self.radius}')
        return '\n'.join(sphere_data_str)
