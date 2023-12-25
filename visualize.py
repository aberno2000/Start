import gmsh
import sys


def create_bounding_box(size: float, mesh_factor: float = 10):
    mesh_size = size / mesh_factor

    p1 = gmsh.model.geo.addPoint(0, 0, 0, mesh_size)
    p2 = gmsh.model.geo.addPoint(size, 0, 0, mesh_size)
    p3 = gmsh.model.geo.addPoint(0, size, 0, mesh_size)
    p4 = gmsh.model.geo.addPoint(size, size, 0, mesh_size)
    p5 = gmsh.model.geo.addPoint(0, 0, size, mesh_size)
    p6 = gmsh.model.geo.addPoint(size, 0, size, mesh_size)
    p7 = gmsh.model.geo.addPoint(0, size, size, mesh_size)
    p8 = gmsh.model.geo.addPoint(size, size, size, mesh_size)

    l1 = gmsh.model.geo.addLine(p1, p2)
    l2 = gmsh.model.geo.addLine(p1, p3)
    l3 = gmsh.model.geo.addLine(p1, p5)
    l4 = gmsh.model.geo.addLine(p2, p4)
    l5 = gmsh.model.geo.addLine(p2, p6)
    l6 = gmsh.model.geo.addLine(p3, p4)
    l7 = gmsh.model.geo.addLine(p3, p7)
    l8 = gmsh.model.geo.addLine(p4, p8)
    l9 = gmsh.model.geo.addLine(p5, p6)
    l10 = gmsh.model.geo.addLine(p5, p7)
    l11 = gmsh.model.geo.addLine(p7, p8)
    l12 = gmsh.model.geo.addLine(p6, p8)

    cl1 = gmsh.model.geo.addCurveLoop([l1, l5, -l9, -l3])
    cl2 = gmsh.model.geo.addCurveLoop([l2, l7, -l10, -l3])
    cl3 = gmsh.model.geo.addCurveLoop([l6, l8, -l11, -l7])
    cl4 = gmsh.model.geo.addCurveLoop([l12, l5, -l4, -l8])
    cl5 = gmsh.model.geo.addCurveLoop([l1, l4, -l6, -l2])
    cl6 = gmsh.model.geo.addCurveLoop([l9, l12, -l11, -l10])

    surface1 = gmsh.model.geo.addPlaneSurface([cl1])
    surface2 = gmsh.model.geo.addPlaneSurface([cl2])
    surface3 = gmsh.model.geo.addPlaneSurface([cl3])
    surface4 = gmsh.model.geo.addPlaneSurface([cl4])
    surface5 = gmsh.model.geo.addPlaneSurface([cl5])
    surface6 = gmsh.model.geo.addPlaneSurface([cl6])

    # Generating tetrahedal volume
    # volume = gmsh.model.geo.addSurfaceLoop(
    #     [surface1, surface2, surface3, surface4, surface5, surface6]
    # )
    # gmsh.model.geo.addVolume([volume])

    return [surface1, surface2, surface3, surface4, surface5, surface6]


def read_particle_data(filename: str) -> list:
    with open(filename, "r") as file:
        particles = []
        for line in file:
            data = line.split()
            x, y, z, radius = map(float, data)
            particles.append((x, y, z, radius))
        return particles


def spawn_particles():
    particles = read_particle_data("particles.txt")
    spheres = []
    for particle in particles:
        x, y, z, radius = particle
        spheres.append(gmsh.model.occ.addSphere(x, y, z, radius))
    return spheres


def __main__():
    gmsh.initialize()
    gmsh.model.add("particles")

    # Create a bounding box of size 100x100x100
    bounding_box = create_bounding_box(100)
    particles = spawn_particles()

    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate(3)
    gmsh.write("particles.msh")

    if "-nopopup" not in sys.argv:
        gmsh.fltk.run()

    gmsh.finalize()


if __name__ == "__main__":
    __main__()
