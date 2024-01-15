from inst_deps import check_and_install_packages

# Installing dependencies
check_and_install_packages(["numpy", "h5py", "PyQt5", "PyOpenGL"])
from hdf5handler import *
from mesh_renderer import *


def __main__():
    app = QApplication([])
    handler = HDF5Handler("results/box_mesh.hdf5")
    mesh = handler.read_mesh_from_hdf5()

    window = MeshRenderer(mesh)
    window.show()
    app.exec_()


if __name__ == "__main__":
    __main__()
