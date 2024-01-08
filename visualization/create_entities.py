from inst_deps import check_and_install_packages

# Installing dependencies
check_and_install_packages(["gmsh", "numpy"])
import gmsh


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
    Creates a bounding box.

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
