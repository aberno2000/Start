import meshio
import numpy as np
from gmsh import initialize, finalize, model, isInitialized
from vtk import vtkCubeSource, vtkPolyDataMapper, vtkActor, vtkTriangleFilter, vtkLinearSubdivisionFilter, vtkIdList, vtkFeatureEdges
from logger import LogConsole
from util import get_cur_datetime


class Box:
    """
    A class to represent a box geometry.

    Attributes
    ----------
    x : float
        The x-coordinate of the box's primary point.
    y : float
        The y-coordinate of the box's primary point.
    z : float
        The z-coordinate of the box's primary point.
    length : float
        The length of the box.
    width : float
        The width of the box.
    height : float
        The height of the box.

    Methods
    -------
    create_box_with_vtk():
        Creates the box using VTK and returns the actor.
    create_box_with_gmsh():
        Creates the box using Gmsh.
    __repr__():
        Returns a string representation of the box.
    """

    def __init__(self, log_console: LogConsole, x: float, y: float, z: float,
                 length: float, width: float, height: float):
        """
        Constructs all the necessary attributes for the box object.

        Parameters
        ----------
            x : float
                The x-coordinate of the box's primary point.
            y : float
                The y-coordinate of the box's primary point.
            z : float
                The z-coordinate of the box's primary point.
            length : float
                The length of the box.
            width : float
                The width of the box.
            height : float
                The height of the box.
        """
        self.log_console = log_console
        self.x = x
        self.y = y
        self.z = z
        self.length = length
        self.width = width
        self.height = height

    def create_box_with_vtk(self) -> vtkActor:
        """
        Creates the box using VTK and returns the actor.

        Returns
        -------
        vtkActor
            The actor representing the box.
        """
        try:
            cube_source = vtkCubeSource()
            cube_source.SetXLength(self.length)
            cube_source.SetYLength(self.width)
            cube_source.SetZLength(self.height)
            cube_source.SetCenter(self.length / 2, self.width / 2, self.height / 2)
            cube_source.Update()

            triangle_filter = vtkTriangleFilter()
            triangle_filter.SetInputConnection(cube_source.GetOutputPort())
            triangle_filter.Update()

            subdivision_filter = vtkLinearSubdivisionFilter()
            subdivision_filter.SetInputConnection(triangle_filter.GetOutputPort())
            subdivision_filter.SetNumberOfSubdivisions(3)
            subdivision_filter.Update()

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(subdivision_filter.GetOutputPort())

            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.SetPosition(self.x, self.y, self.z) 

            print("CREATING")
            print(f"Created <{hex(id(actor))}> cube. Entered coords: ({self.x}, {self.y}, {self.z})")
            print(f"Position: {actor.GetPosition()}")
            print(f"Center: {actor.GetCenter()}")
            print(f"Origin: {actor.GetOrigin()}")

            return actor

        except Exception as e:
            self.log_console.printError(
                f"An error occurred while creating the box with VTK: {e}")

    def create_box_with_gmsh(self):
        """
        Creates the box using Gmsh.
        """
        try:
            if not isInitialized():
                initialize()

            model.add(f"box_{get_cur_datetime()}")
            model.occ.add_box(self.x, self.y, self.z, self.length, self.width,
                              self.height)
            model.occ.synchronize()

            finalize()
        except Exception as e:
            self.log_console.printError(
                f"An error occurred while creating the box with Gmsh: {e}")
        finally:
            if isInitialized():
                finalize()

    def __repr__(self):
        """
        Returns a string representation of the box.

        Returns
        -------
        str
            A string representation of the box.
        """
        box_data_str = []
        box_data_str.append(f'Primary Point: ({self.x}, {self.y}, {self.z})')
        box_data_str.append(f'Length: {self.length}')
        box_data_str.append(f'Width: {self.width}')
        box_data_str.append(f'Height: {self.height}')
        return '\n'.join(box_data_str)
