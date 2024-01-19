from inst_deps import check_and_install_packages

# Installing dependencies
check_and_install_packages(["numpy", "h5py", "gmsh", "matplotlib", "argparse", "argcomplete"])
import argparse
import argcomplete
from subprocess import run
from hdf5handler import HDF5Handler
from mesh_renderer import MeshRenderer


def run_cpp(args: str) -> None:
    run(["./compile.sh"], check=True)
    cmd = ["./main"] + args.split()
    run(cmd, check=True)


def show_mesh(hdf5_filename: str) -> None:
    handler = HDF5Handler(hdf5_filename)
    mesh = handler.read_mesh_from_hdf5()
    renderer = MeshRenderer(mesh)
    renderer.show()


def __main__():
    parser = argparse.ArgumentParser(
        description="Run a particle collision simulation and render the results."
    )
    parser.add_argument(
        "particles_count", type=int, help="The number of particles to simulate."
    )
    parser.add_argument(
        "time_step", type=float, help="The time step for the simulation."
    )
    parser.add_argument(
        "time_interval", type=float, help="The total time interval for the simulation."
    )
    parser.add_argument(
        "msh_filename", help="The filename for the mesh file (with .msh extension)."
    )

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    hdf5_filename = args.msh_filename.replace(".msh", ".hdf5")
    args = f"{args.particles_count} {args.time_step} {args.time_interval} {args.msh_filename}"
    run_cpp(args)

    show_mesh(hdf5_filename)


if __name__ == "__main__":
    __main__()
