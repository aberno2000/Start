from inst_deps import check_and_install_packages

# Installing dependencies
check_and_install_packages(["gmsh", "numpy", "h5py"])

from sys import argv
from simulate_motion import *
from work_with_mesh import *
from work_with_hdf5 import *


def __main__():
    gmsh.initialize(argv)

    particles = read_particle_data("../results/particles.txt")
    create_bounding_box()
    set_mesh_size_constraint(0.75)
    gmsh.model.occ.synchronize()  # Synchronizing changes
    gmsh.model.mesh.generate(2)  # Generating 2D mesh only for bounded volume

    create_particles(particles)
    gmsh.model.occ.synchronize()

    gmsh.write("../results/mesh.msh")  # Filling .msh file with points

    triangles = get_mesh_params("../results/mesh.msh")
    save_to_hdf5(triangles, "../results/mesh.hdf5")

    # Format is: id x1 y1 z1 x2 y2 z2 x3 y3 z3 dS (square of triangle)
    settled = simulate_movement_of_particles(particles, triangles, 0.1, 0.3)
    save_settled_to_hdf5(settled, "../results/settled.hdf5")
    settled = read_settled_hdf5("../results/settled.hdf5")
    for x in settled:
        print(" ".join(str(val) for val in x) + "\n")

    if "-nopopup" not in argv:
        gmsh.fltk.run()
    gmsh.finalize()


if __name__ == "__main__":
    __main__()
