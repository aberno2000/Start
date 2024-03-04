FROM ubuntu:latest
WORKDIR /app

# Set DEBIAN_FRONTEND to noninteractive to skip interactive prompts
ENV DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC

# Installing dependencies
RUN apt-get update && apt-get install -y software-properties-common wget bzip2 \
    ca-certificates libglib2.0-0 libxext6 libsm6 libxrender1 mercurial subversion \
    && add-apt-repository ppa:ubuntu-toolchain-r/test \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get install -y build-essential cmake g++-13 libboost-all-dev libgmp-dev \
    libmpfr-dev python3.7* python3 python3-pip python3-dev libx11-6 gmsh libgmsh-dev git \
    libhdf5-dev libcgal-dev python2.7-dev swig doxygen graphviz libqt5widgets5 \
    libqt5gui5 libqt5core5a libqt5dbus5 qt5-gtk-platformtheme libx11-xcb1 libxcb-icccm4 \
    libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0 libqt5xcb* libxcb* \
    libxkbcommon-x11-0 nlohmann-json3-dev libjpeg-dev libpng-dev libtiff-dev zlib1g-dev vtk9 python3-vtk9 \
    mesa-utils libgl1-mesa-dri libgl1-mesa-glx

# Adding g++-13 and reset DEBIAN_FRONTEND variable
ENV CXX=g++-13 DEBIAN_FRONTEND=

# Installing AABB from the git repo and installing miniconda
RUN git clone https://github.com/lohedges/aabbcc && \
    cd aabbcc && make build && make install

# Installing dependencies on python
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1 && \
    pip install numpy h5py gmsh matplotlib PyQt5 vtk

# Building source code of the gmsh
COPY ./gmsh-4.12.2-source.tgz /app
RUN mkdir -pv gmsh/gmsh_build && tar -xzvf gmsh-4.12.2-source.tgz && mv gmsh-4.12.2-source/ gmsh/ \
    && rm -rf *.tgz && cd gmsh/gmsh_build && cmake -DENABLE_BUILD_DYNAMIC=1 -DENABLE_FLTK=0 ../gmsh-4.12.2-source/ \
    && cmake --build . --config Release && cmake --install . && rm -rfv gmsh/

# Copying all contents from the current directory to the Docker directory /app
COPY . /app/start/
WORKDIR /app/start
RUN rm -rf gmsh-4.12.2-source && ./compile.sh -r
