from inst_deps import check_and_install_packages

# Installing dependencies
check_and_install_packages(["gmsh", "numpy"])
import gmsh
import numpy
from sys import argv


def read_file_content(filename: str) -> list:
    """
    Reads data from a file.

    Args:
    - filename (str): Name of the file containing any data.

    Returns:
    - list: List containing lines of content.
    """
    try:
        with open(filename, "r") as file:
            content = []
            for line in file:
                content.append(line)
            return content
    except FileNotFoundError:
        return f"File '{filename}' not found"


def read_particle_data(filename: str) -> [()]:
    """
    Gets particle data from a file.

    Args:
    - filename (str): Name of the file containing particle data.

    Returns:
    - list: List containing particle data as tuples.
    """
    particles = []
    for line in read_file_content(filename):
        data = line.split()
        x, y, z, Vx, Vy, Vz, radius = map(float, data)
        particles.append((x, y, z, Vx, Vy, Vz, radius))
    return particles


def create_particles(particles: [()]) -> [()]:
    """
    Create particles based on input data.

    Args:
    - particles (list of tuples): List containing particle data as tuples.

    Returns:
    - list of tuples: List of tuples representing particle positions and properties.
    """
    dimTags = [()]
    for particle in particles:
        dimTags.append(
            (
                3,
                gmsh.model.occ.addSphere(
                    particle[0], particle[1], particle[2], particle[6]
                ),
            ),
        )
    # Erasing empty tuples from list
    return list(filter(lambda x: x != (), dimTags))


def create_bounding_box(
    x: float = 0,
    y: float = 0,
    z: float = 0,
    dx: float = 100,
    dy: float = 100,
    dz: float = 100,
) -> [()]:
    """
    Create a bounding box.

    Args:
    - x (float): X-coordinate of the bounding box (default: 0).
    - y (float): Y-coordinate of the bounding box (default: 0).
    - z (float): Z-coordinate of the bounding box (default: 0).
    - dx (float): X-length of the bounding box (default: 100).
    - dy (float): Y-length of the bounding box (default: 100).
    - dz (float): Z-length of the bounding box (default: 100).

    Returns:
    - list of tuples: List containing dimension and tag of the bounding box.
    """
    return [(3, gmsh.model.occ.addBox(x, y, z, dx, dy, dz))]


def update_positions(particles: [()], time_step: float) -> None:
    """
    Update particle positions based on their velocities over a time step.

    Args:
    - particles ([()]): List of particles, each represented as a tuple of coordinates and velocities.
    - time_step (float): Time step for updating particle positions.

    Returns:
    - None
    """
    i = 0
    for particle in particles:
        _, _, _, Vx, Vy, Vz, _ = particle
        particles[i] = (
            particles[i][0] + Vx * time_step,
            particles[i][1] + Vy * time_step,
            particles[i][2] + Vz * time_step,
            particles[i][3],
            particles[i][4],
            particles[i][5],
            particles[i][6],
        )
        i += 1


def simulate_movement_of_particles(
    particles: [()], triangles: [()], time_step: float, time_interval: float
) -> None:
    """
    Simulate movement of particles over a specified time interval.

    Args:
    - particles (list): List of particles, each containing position and velocity information.
    - time_step (float): Time step used to update particle positions based on velocities.
    - time_interval (float): Total time interval for the simulation.

    Returns:
    - None
    """
    time = 0.0
    while time <= time_interval:
        has_settled(particles, triangles)
        update_positions(particles, time_step)
        time += time_step


def get_mesh_params(msh_filename: str) -> [()]:
    """
    Parse mesh data from a Gmsh .msh file and write information to 'mesh.hdf5'.

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
            a = numpy.sqrt(numpy.dot(xyz1 - xyz2, xyz1 - xyz2))
            b = numpy.sqrt(numpy.dot(xyz1 - xyz3, xyz1 - xyz3))
            c = numpy.sqrt(numpy.dot(xyz2 - xyz3, xyz2 - xyz3))

            s = (a + b + c) / 2
            # Heron's formula for triangle's area
            dS = numpy.sqrt(s * (s - a) * (s - b) * (s - c))

            with open("mesh.hdf5", "a") as out:
                out.write(
                    f"{triangle_id} \
                    {xyz1[0]} {xyz1[1]} {xyz1[2]} \
                    {xyz2[0]} {xyz2[1]} {xyz2[2]} \
                    {xyz3[0]} {xyz3[1]} {xyz3[2]} \
                    {a} {b} {c} {dS}\n"
                )
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


def is_point_belongs_to_the_triangle(point: list, triangleVertices: [()]) -> bool:
    """
    Check if a point lies inside a triangle defined by its vertices A, B, and C.

    Args:
    - point (tuple): Coordinates of the point (x, y).
    - triangleVertices (list): List containing the coordinates of the triangle's
    vertices as tuples (xA, yA), (xB, yB), (xC, yC).

    Returns:
    - bool: True if the point is inside the triangle, False otherwise.
    """

    def sign(point: list, triangleVertices1: list, triangleVertices2: list):
        return (point[0] - triangleVertices2[0]) * (
            triangleVertices1[1] - triangleVertices2[1]
        ) - (triangleVertices1[0] - triangleVertices2[0]) * (
            point[1] - triangleVertices2[1]
        )

    d1 = sign(point, triangleVertices[0:3], triangleVertices[3:6])
    d2 = sign(point, triangleVertices[3:6], triangleVertices[6:9])
    d3 = sign(point, triangleVertices[6:9], triangleVertices[0:3])

    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

    return not (has_neg and has_pos)

    # rA = numpy.array(triangleVertices[0:3])
    # rB = numpy.array(triangleVertices[3:6])
    # rC = numpy.array(triangleVertices[6:9])

    # u = rB - rA
    # v = rC - rA
    # w = numpy.cross(u, v)

    # x = numpy.array(point) - rA
    # y = numpy.array(point) - rB

    # w1 = numpy.cross(x, u)
    # w2 = numpy.cross(v, y)

    # signs_w1 = numpy.sign(w1)
    # signs_w2 = numpy.sign(w1)

    # if (
    #     signs_w1[0] == signs_w2[0]
    #     and signs_w1[1] == signs_w2[1]
    #     and signs_w1[2] == signs_w2[2]
    # ):
    #     return True
    # else:
    #     return False


def has_settled(particles: [()], triangles: [()]):
    """
    Check if a particle has settled or collided with a triangle mesh.

    Args:
    - particle (list): Particle containing position and velocity information.
    - triangles (list): List of triangles, each represented by vertices.

    Returns:
    - bool: True if the particle has settled or collided, False otherwise.
    """
    for triangle in triangles:
        for particle in particles:
            if is_point_belongs_to_the_triangle(particle[:3], triangle[1:10]):
                print(
                    f"Particle {particle[:3]} has settled on the triangle with id: {triangle[0]}"
                )
                particles.remove(particle)
                break


def __main__():
    gmsh.initialize(argv)

    particles = read_particle_data("particles.txt")
    create_bounding_box()
    gmsh.model.occ.synchronize()  # Synchronizing changes
    gmsh.model.mesh.generate(2)  # Generating 2D mesh only for bounded volume

    create_particles(particles)
    gmsh.model.occ.synchronize()

    gmsh.write("mesh.msh")  # Filling .msh file with points

    triangles = get_mesh_params("mesh.msh")
    simulate_movement_of_particles(particles, triangles, 0.1, 1)

    if "-nopopup" not in argv:
        gmsh.fltk.run()
    gmsh.finalize()


if __name__ == "__main__":
    __main__()
