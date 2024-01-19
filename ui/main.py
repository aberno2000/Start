from inst_deps import check_and_install_packages

# Installing dependencies
check_and_install_packages(["numpy", "h5py", "gmsh", "matplotlib"])
import sys
from subprocess import run
from hdf5handler import HDF5Handler
from mesh_renderer import MeshRenderer


def run_cpp(particles_count: int, mshfilename: str) -> None:
    run(["./compile.sh"], check=True)
    run(["./main", str(particles_count), mshfilename], check=True)


def show_mesh(hdf5_filename: str) -> None:
    handler = HDF5Handler(hdf5_filename)
    mesh = handler.read_mesh_from_hdf5()
    renderer = MeshRenderer(mesh)
    renderer.show()


def __main__():
    if len(sys.argv) != 3:
        print("Usage: python main.py <particles_count> <msh_filename>")
        sys.exit(1)
    particles_count = int(sys.argv[1])
    msh_filename = sys.argv[2]
    hdf5_filename = msh_filename.replace(".msh", ".hdf5")

    run_cpp(particles_count, msh_filename)
    show_mesh(hdf5_filename)


if __name__ == "__main__":
    __main__()
