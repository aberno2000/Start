import gmsh
import sys
import random
import os


def read_particle_data(filename: str) -> list:
    with open(filename, "r") as file:
        particles = []
        for line in file:
            data = line.split()
            x, y, z, radius = map(float, data)
            particles.append((x, y, z, radius))
        return particles


def create_bounding_box(
    x: float = 0,
    y: float = 0,
    z: float = 0,
    dx: float = 100,
    dy: float = 100,
    dz: float = 100,
):
    gmsh.model.occ.addBox(x, y, z, dx, dy, dz)


def spawn_particles(particles):
    for x, y, z, radius in particles:
        gmsh.model.occ.addSphere(x, y, z, radius)


def update_positions(particles, time_step):
    for i in range(len(particles)):
        dx = random.uniform(-1, 1) * time_step
        dy = random.uniform(-1, 1) * time_step
        dz = random.uniform(-1, 1) * time_step

        particles[i] = (
            particles[i][0] + dx,
            particles[i][1] + dy,
            particles[i][2] + dz,
            particles[i][3],  # Radius unchanged
        )


def write_in_pos_file(particles: list, filename: str, time_point):
    with open(filename, "a") as file:
        file.write(f'View "Particles_{time_point}"{{')
        for particle in particles:
            x, y, z, _ = particle
            file.write(f"\nVP({x},{y},{z}){{0,0,0}};")
        file.write("};\n")


def animate(particles: list, time_step: float):
    gmsh.model.add("Particles_in_Bounded_Cubic_Volume_" + str(time_step))

    create_bounding_box()
    update_positions(particles, time_step)
    spawn_particles(particles)

    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(2)  # 2D mesh (only surfaces)

    return particles


def __main__():
    gmsh.initialize(sys.argv)

    time_interval = 10
    particles = read_particle_data("particles.txt")
    path = os.path.dirname(os.path.abspath(__file__))
    for time_step in range(time_interval):
        animate(particles, time_step)
        write_in_pos_file(particles, "view.pos", time_step)

    gmsh.merge(os.path.join(path, "view.pos"))
    if "-nopopup" not in sys.argv:
        gmsh.fltk.run()
    gmsh.finalize()


if __name__ == "__main__":
    __main__()
