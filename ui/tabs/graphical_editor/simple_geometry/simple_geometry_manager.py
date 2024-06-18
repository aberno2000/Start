from gmsh import initialize, finalize, isInitialized, model, option, write
from . import *
from vtk import vtkActor
from logger import LogConsole
from styles import DEFAULT_ACTOR_COLOR
from util import get_cur_datetime

POINT_OBJ_STR = 'point'
LINE_OBJ_STR = 'line'
SURFACE_OBJ_STR = 'surface'
SPHERE_OBJ_STR = 'sphere'
BOX_OBJ_STR = 'box'
CYLINDER_OBJ_STR = 'cylinder'


class SimpleGeometryManager:
    """
    A class to manage the creation of simple geometrical objects.

    Attributes
    ----------
    simple_geometry_objects : list
        A list to track created geometry objects.

    Methods
    -------
    create_point(log_console, x, y, z):
        Creates a point and returns the corresponding VTK actor.
    create_line(log_console, points):
        Creates a line and returns the corresponding VTK actor.
    create_surface(log_console, points):
        Creates a surface and returns the corresponding VTK actor.
    create_sphere(log_console, x, y, z, radius):
        Creates a sphere and returns the corresponding VTK actor.
    create_box(log_console, x, y, z, length, width, height):
        Creates a box and returns the corresponding VTK actor.
    create_cylinder(log_console, x, y, z, radius, dx, dy, dz):
        Creates a cylinder and returns the corresponding VTK actor.
    colorize_actor(actor, color):
        Sets the color of the actor.
    colorize_actor_with_rgb(actor, r, g, b):
        Sets the color of the actor using RGB values.
    """
    simple_geometry_objects = []

    @staticmethod
    def get_created_objects():
        """
        Returns a copy of the list of created geometry objects.

        Returns
        -------
        list
            A copy of the list of created geometry objects.
            For point:     'point', (x, y, z)
            For line:      'line', points
            For surface:   'surface', points
            For sphere:    'sphere', (x, y, z, radius, phi_resolution, theta_resolution)
            For box:       'box', (x, y, z, length, width, height
            For cylinder:  'cylinder', (x, y, z, radius, dx, dy, dz)
        """
        return SimpleGeometryManager.simple_geometry_objects.copy()

    @staticmethod
    def create_point(log_console: LogConsole,
                     x: float,
                     y: float,
                     z: float,
                     color=DEFAULT_ACTOR_COLOR) -> vtkActor:
        try:
            point = Point(log_console, x, y, z)
            point_data_str = repr(point)

            point.create_point_with_gmsh()
            point_actor = point.create_point_with_vtk()

            SimpleGeometryManager.simple_geometry_objects.append(
                (POINT_OBJ_STR, (x, y, z)))
            log_console.printInfo(
                f'Successfully created point: {point_data_str}')

            SimpleGeometryManager.colorize_actor(point_actor, color)

            return point_actor
        except ValueError as e:
            return None

    @staticmethod
    def create_line(log_console: LogConsole,
                    points: list,
                    color=DEFAULT_ACTOR_COLOR) -> vtkActor:
        try:
            line = Line(log_console, points)

            line_data_str = repr(line)
            line.create_line_with_gmsh()

            line_actor = line.create_line_with_vtk()
            SimpleGeometryManager.simple_geometry_objects.append(
                (LINE_OBJ_STR, points))
            log_console.printInfo(
                f'Successfully created line:\n{line_data_str}')

            SimpleGeometryManager.colorize_actor(line_actor, color)

            return line_actor
        except ValueError as e:
            return None

    @staticmethod
    def create_surface(log_console: LogConsole,
                       points: list,
                       color=DEFAULT_ACTOR_COLOR) -> vtkActor:
        try:
            surface = Surface(log_console, points)

            surface_data_str = repr(surface)
            surface.create_surface_with_gmsh()

            surface_actor = surface.create_surface_with_vtk()
            SimpleGeometryManager.simple_geometry_objects.append(
                (SURFACE_OBJ_STR, points))
            log_console.printInfo(
                f'Successfully created surface:\n{surface_data_str}')

            SimpleGeometryManager.colorize_actor(surface_actor, color)

            return surface_actor
        except ValueError as e:
            return None

    @staticmethod
    def create_sphere(log_console: LogConsole,
                      x: float,
                      y: float,
                      z: float,
                      radius: float,
                      phi_resolution: int = DEFAULT_SPHERE_PHI_RESOLUTION,
                      theta_resolution: int = DEFAULT_SPHERE_THETA_RESOLUTION,
                      color=DEFAULT_ACTOR_COLOR) -> vtkActor:
        try:
            sphere = Sphere(log_console, x, y, z, radius, phi_resolution,
                            theta_resolution)

            sphere_data_str = repr(sphere)
            sphere.create_sphere_with_gmsh()

            sphere_actor = sphere.create_sphere_with_vtk()
            SimpleGeometryManager.simple_geometry_objects.append(
                (SPHERE_OBJ_STR, (x, y, z, radius, phi_resolution,
                                  theta_resolution)))
            log_console.printInfo(
                f'Successfully created sphere:\n{sphere_data_str}')

            SimpleGeometryManager.colorize_actor(sphere_actor, color)

            return sphere_actor
        except ValueError as e:
            return None

    @staticmethod
    def create_box(log_console: LogConsole,
                   x: float,
                   y: float,
                   z: float,
                   length: float,
                   width: float,
                   height: float,
                   color=DEFAULT_ACTOR_COLOR) -> vtkActor:
        try:
            box = Box(log_console, x, y, z, length, width, height)

            box_data_str = repr(box)
            box.create_box_with_gmsh()
            box_actor = box.create_box_with_vtk()
            SimpleGeometryManager.simple_geometry_objects.append(
                (BOX_OBJ_STR, (x, y, z, length, width, height)))
            log_console.printInfo(f'Successfully created box:\n{box_data_str}')

            SimpleGeometryManager.colorize_actor(box_actor, color)

            return box_actor
        except ValueError as e:
            return None

    @staticmethod
    def create_cylinder(log_console: LogConsole,
                        x: float,
                        y: float,
                        z: float,
                        radius: float,
                        dx: float,
                        dy: float,
                        dz: float,
                        resolution: int = DEFAULT_CYLINDER_RESOLUTION,
                        color=DEFAULT_ACTOR_COLOR) -> vtkActor:
        try:
            cylinder = Cylinder(log_console, x, y, z, radius, dx, dy, dz,
                                resolution)

            cylinder_data_str = repr(cylinder)
            cylinder.create_cylinder_with_gmsh()

            cylinder_actor = cylinder.create_cylinder_with_vtk()
            SimpleGeometryManager.simple_geometry_objects.append(
                (CYLINDER_OBJ_STR, (x, y, z, radius, dx, dy, dz)))
            log_console.printInfo(
                f'Successfully created cylinder:\n{cylinder_data_str}')

            SimpleGeometryManager.colorize_actor(cylinder_actor, color)

            return cylinder_actor
        except ValueError as e:
            return None

    @staticmethod
    def colorize_actor(actor: vtkActor, color=DEFAULT_ACTOR_COLOR):
        """
        Sets the color of the actor. If color is not provided, DEFAULT_ACTOR_COLOR is used.

        Parameters
        ----------
        actor : vtkActor
            The actor to colorize.
        color : tuple or list, optional
            The RGB color values to set. If None, DEFAULT_ACTOR_COLOR is used.
        """
        if color is None:
            color = DEFAULT_ACTOR_COLOR
        actor.GetProperty().SetColor(color)

    @staticmethod
    def colorize_actor_with_rgb(actor: vtkActor, r: float, g: float, b: float):
        """
        Sets the color of the actor using RGB values.

        Parameters
        ----------
        actor : vtkActor
            The actor to colorize.
        r : float
            Red component (0-1).
        g : float
            Green component (0-1).
        b : float
            Blue component (0-1).
        """
        actor.GetProperty().SetColor(r, g, b)

    @staticmethod
    def save_and_mesh_objects(log_console: LogConsole, mesh_filename: str,
                              mesh_size: float, mesh_dim: int):
        try:
            if not isInitialized():
                initialize()

            model.add(f"merged_{'_'.join(obj_name for obj_name, obj_params in SimpleGeometryManager.simple_geometry_objects)}_{get_cur_datetime()}")

            for obj_name, params in SimpleGeometryManager.simple_geometry_objects:
                if obj_name == POINT_OBJ_STR:
                    model.occ.addPoint(*params, mesh_size)
                elif obj_name == LINE_OBJ_STR:
                    point_ids = []
                    for point in params:
                        point_id = model.occ.addPoint(*point, mesh_size)
                        point_ids.append(point_id)
                    for i in range(len(point_ids) - 1):
                        model.occ.addLine(point_ids[i], point_ids[i + 1])
                elif obj_name == SURFACE_OBJ_STR:
                    point_ids = []
                    for point in params:
                        point_id = model.occ.addPoint(*point, mesh_size)
                        point_ids.append(point_id)
                    line_loop = model.occ.addWire(point_ids)
                    model.occ.addPlaneSurface([line_loop])
                elif obj_name == SPHERE_OBJ_STR:
                    x, y, z, radius, phi_resolution, theta_resolution = params
                    model.occ.addSphere(x, y, z, radius)
                elif obj_name == BOX_OBJ_STR:
                    x, y, z, length, width, height = params
                    model.occ.addBox(x, y, z, length, width, height)
                elif obj_name == CYLINDER_OBJ_STR:
                    x, y, z, radius, dx, dy, dz = params
                    model.occ.addCylinder(x, y, z, radius, dx, dy, dz)

            option.setNumber("Mesh.MeshSizeMin", mesh_size)
            option.setNumber("Mesh.MeshSizeMax", mesh_size)

            model.occ.synchronize()
            model.mesh.generate(mesh_dim)
            
            write(mesh_filename)

            obj_names = '; '.join(
                obj_name for obj_name, obj_params in
                SimpleGeometryManager.simple_geometry_objects)
            log_console.printInfo(f"Successfully saved and meshed created objects: {obj_names} to the file '{mesh_filename}'")
            return True

        except Exception as e:
            log_console.printError(f"Can't save and mesh created objects: {e}")
            return False

        finally:
            if isInitialized():
                finalize()
                
    @staticmethod
    def clear_geometry_objects():
        """
        Clears the list of created geometry objects.
        """
        SimpleGeometryManager.simple_geometry_objects.clear()
