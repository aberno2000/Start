from create_entities import *


def update_positions(particles: [()], time_step: float) -> [()]:
    """
    Update particle positions based on their velocities over a time step.

    Args:
    - particles ([()]): List of particles, each represented as a tuple of coordinates and velocities.
    - time_step (float): Time step for updating particle positions.

    Returns:
    - [()]: List of updated particles, each represented as a tuple of coordinates and velocities.
    """
    for particle in particles:
        x, y, z, Vx, Vy, Vz, _ = particle
        particle = (
            x + Vx * time_step,
            y + Vy * time_step,
            z + Vz * time_step,
            Vx,
            Vy,
            Vz,
            _,
        )


def is_particle_overlaps_mesh(particle, triangleVertices):
    """
    Checks if a particle overlaps with a triangular mesh.

    Args:
    - particle (array-like): Represents the particle coordinates and radius.
    - triangleVertices (array-like): Contains coordinates of the vertices of the triangle.

    Returns:
    - bool: True if the particle overlaps with the mesh, False otherwise.
    """

    def get_triangle_equation_coeffs(triangleVertices):
        """
        Calculates the coefficients of the equation for the plane of the triangle.

        Args:
        - triangleVertices (array-like): Contains coordinates of the vertices of the triangle.

        Returns:
        - tuple: Coefficients A, B, C, and D of the plane equation.
        """
        vertices = np.array(
            [triangleVertices[:3], triangleVertices[3:6], triangleVertices[6:9]]
        )

        v = vertices[1] - vertices[0]
        u = vertices[2] - vertices[0]
        normal = np.cross(v, u)

        A, B, C = normal
        D = -np.dot(normal, vertices[0])
        return A, B, C, D

    def check_sphere_intersection(sphere_center, sphere_radius, A, B, C, D):
        """
        Checks if a sphere (particle) intersects with the triangle.

        Args:
        - sphere_center (array-like): Coordinates of the center of the sphere.
        - sphere_radius (float): Radius of the sphere (particle).
        - A, B, C, D (float): Coefficients of the plane equation for the triangle.

        Returns:
        - bool: True if the sphere intersects with the triangle, False otherwise.
        """
        x, y, z = sphere_center

        # Distance between center of particle and triangle surface
        distance = abs((A * x + B * y + C * z + D) / np.sqrt(A**2 + B**2 + C**2))
        return distance <= sphere_radius

    # Extract particle center and radius
    particle_center = particle[:3]
    particle_radius = particle[6]

    # Calculate coefficients of the plane equation for the triangle
    A, B, C, D = get_triangle_equation_coeffs(triangleVertices)

    # Check if the particle overlaps with the triangle
    return check_sphere_intersection(particle_center, particle_radius, A, B, C, D)


def get_settled_particles(particles: [()], triangles: [()]) -> None:
    """
    Check if a particle has settled or collided with a triangle mesh and write settled particles to a file.

    Args:
    - particles ([()]): List of particles containing position and velocity information.
    - triangles ([()]): List of triangles, each represented by vertices.

    Returns:
    - None
    """
    settled = []
    for particle in particles:
        for triangle in triangles:
            if is_particle_overlaps_mesh(particle, triangle[1:10]):
                settled.append(triangle)
                particles.remove(particle)
                break
    return settled


def simulate_movement_of_particles(
    particles: [()], triangles: [()], time_step: float, time_interval: float
) -> [()]:
    """
    Simulate movement of particles over a specified time interval and write settled particles to an HDF5 file.

    Args:
    - particles (list): List of particles, each containing position and velocity information.
    - time_step (float): Time step used to update particle positions based on velocities.
    - time_interval (float): Total time interval for the simulation.

    Returns:
    - list of tuples: List of unique settled particles.
    """
    time = 0.0
    settled_particles = []
    while time <= time_interval:
        settled_particles.extend(get_settled_particles(particles, triangles))
        update_positions(particles, time_step)
        time += time_step

    unique_settled_particles = list(set(tuple(p) for p in settled_particles))
    return unique_settled_particles
