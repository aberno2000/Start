FROM ubuntu:latest
WORKDIR /app

# Installing dependencies
RUN apt-get update && apt-get install -y software-properties-common wget bzip2 \
    ca-certificates libglib2.0-0 libxext6 libsm6 libxrender1 mercurial subversion \
    && add-apt-repository ppa:ubuntu-toolchain-r/test \
    && apt-get install -y build-essential cmake g++-13 libboost-all-dev libgmp-dev \
    libmpfr-dev python3 python3-pip python3-dev libx11-6 gmsh libgmsh-dev git \
    libhdf5-dev libcgal-dev python2.7-dev swig doxygen graphviz libqt5widgets5 \
    libqt5gui5 libqt5core5a libqt5dbus5 qt5-gtk-platformtheme libx11-xcb1 libxcb-icccm4 \
    libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0 libqt5xcb* \
    libxkbcommon-x11-0 nlohmann-json3-dev

# Installing AABB from the git repo and installing miniconda
RUN git clone https://github.com/lohedges/aabbcc && \
    cd aabbcc && make build && make install && \
    wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
        /bin/bash ~/miniconda.sh -b -p /opt/conda && \
        rm ~/miniconda.sh

# Adding necessary environment variables
ENV CXX=g++-13 PATH=/opt/conda/bin:$PATH

# Initializing miniconda, creating env, activate it and installing dependencies
RUN conda create -n startenv python=3.7 -y
SHELL [ "conda", "run", "-n", "startenv", "/bin/bash", "-c" ]
RUN pip install numpy h5py gmsh matplotlib PyQt5

# Copying all contents from the current directory to the Docker directory /app
WORKDIR /app/start
COPY . .
