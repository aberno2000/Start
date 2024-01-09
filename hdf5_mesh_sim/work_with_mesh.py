import gmsh
import numpy as np
from os.path import exists
from os import truncate


def set_mesh_size_constraint(mesh_size_factor: float):
    gmsh.option.setNumber("Mesh.MeshSizeFactor", mesh_size_factor)


def get_mesh_params(msh_filename: str) -> [()]:
    """
    Parse mesh data from a Gmsh .msh file and write information.

    Args:
    - msh_filename (str): Filename of the Gmsh .msh file to parse.

    Returns:
    - list of tuples: List of tuples containing information about each triangle in the mesh.
      Each tuple includes:
        - Triangle ID
        - Coordinates of vertex 1 (x1, y1, z1)
        - Coordinates of vertex 2 (x2, y2, z2)
        - Coordinates of vertex 3 (x3, y3, z3)
        - Length of side a
        - Length of side b
        - Length of side c
        - Area of the triangle
    - str: Message indicating file status or error.
    """
    try:
        gmsh.open(msh_filename)

        # -1 to get all dimensions
        # -1 to get all elements
        nodeTags, cords, parametricCord = gmsh.model.mesh.getNodes(-1, -1)

        cords = cords.reshape((-1, 3))
        xyz = cords.reshape(-1, 3)

        # 2 means "triangles"
        # -1 means "for all elements"
        # Defined by GMSH standard 2 is type of triangles:
        # https://gmsh.info/doc/texinfo/gmsh.html#MSH-file-format
        elTags, nodeTags = gmsh.model.mesh.getElementsByType(2, -1)
        nodeTags = nodeTags.reshape((-1, 3))

        total_surface_area = 0.0
        triangles = []
        for triangle_id, nodes in zip(elTags, nodeTags):
            # Getting all 3 xyz coordinates for each triangle
            xyz1 = xyz[int(nodes[0] - 1), :]
            xyz2 = xyz[int(nodes[1] - 1), :]
            xyz3 = xyz[int(nodes[2] - 1), :]

            # Getting all sides of triangle
            a = np.sqrt(np.dot(xyz1 - xyz2, xyz1 - xyz2))
            b = np.sqrt(np.dot(xyz1 - xyz3, xyz1 - xyz3))
            c = np.sqrt(np.dot(xyz2 - xyz3, xyz2 - xyz3))
            s = (a + b + c) / 2

            # Heron's formula for triangle's area
            dS = np.sqrt(s * (s - a) * (s - b) * (s - c))

            triangles.append(
                (
                    triangle_id,
                    xyz1[0],
                    xyz1[1],
                    xyz1[2],
                    xyz2[0],
                    xyz2[1],
                    xyz2[2],
                    xyz3[0],
                    xyz3[1],
                    xyz3[2],
                    a,
                    b,
                    c,
                    dS,
                )
            )
            total_surface_area += dS
        return triangles
    except FileNotFoundError:
        return f"File '{msh_filename}' not found"
