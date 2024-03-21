import sys
from util.inst_deps import check_and_install_packages

# Installing dependencies
check_and_install_packages(["numpy", "h5py", "gmsh", "matplotlib", "PyQt5", "vtk", "nlohmann-json", "meshio"])

from PyQt5.QtWidgets import QApplication
from window import WindowApp


def main():    
    app = QApplication(sys.argv)
    main_window = WindowApp()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
