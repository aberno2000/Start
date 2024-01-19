from inst_deps import check_and_install_packages

# Installing dependencies
check_and_install_packages(["numpy", "h5py", "gmsh", "matplotlib"])
from hdf5handler import HDF5Handler
from mesh_renderer import MeshRenderer


def show_mesh(hdf5_filename: str) -> None:
    handler = HDF5Handler(hdf5_filename)
    mesh = handler.read_mesh_from_hdf5()
    renderer = MeshRenderer(mesh)
    renderer.show()


def __main__():
    show_mesh("results/box_mesh.hdf5")
    show_mesh("results/sphere_mesh.hdf5")
    show_mesh("results/cylinder_mesh.hdf5")
    show_mesh("results/cone_mesh.hdf5")


if __name__ == "__main__":
    __main__()
