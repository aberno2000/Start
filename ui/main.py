import sys
from util.inst_deps import check_and_install_packages

# Installing dependencies
check_and_install_packages(["numpy", "h5py", "gmsh", "matplotlib", "PyQt5", "vtk"])

from PyQt5.QtWidgets import QApplication
from window import WindowApp

dark_stylesheet = """
QWidget {
    color: #b1b1b1;
    background-color: #313131;
}
"""


def main():    
    app = QApplication(sys.argv)
    app.setStyleSheet(dark_stylesheet)
    main_window = WindowApp()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
