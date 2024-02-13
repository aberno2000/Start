FROM ubuntu:latest
WORKDIR /app

# Installing dependencies including
RUN apt-get update && apt-get install -y software-properties-common \
    && add-apt-repository ppa:ubuntu-toolchain-r/test \
    && apt-get install -y build-essential cmake g++-13 libboost-all-dev libgmp-dev libmpfr-dev python3.7 python3.7-pip python3.7-dev libx11-6 gmsh libgmsh-dev git libhdf5-dev libcgal-dev python2.7-dev swig doxygen graphviz libqt5widgets5 libqt5gui5 libqt5core5a libqt5dbus5 qt5-gtk-platformtheme libx11-xcb1 libxcb* libxkbcommon-x11-0
RUN pip3 install numpy h5py gmsh matplotlib PyQt5

# Installing AABB from the git repo
RUN git clone https://github.com/lohedges/aabbcc
RUN cd aabbcc && make build && make install

# Copying all contents from the current directory to the Docker directory /app
COPY . .

ENV CXX=g++-13
RUN ./compile.sh -r
