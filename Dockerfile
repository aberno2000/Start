FROM ubuntu:latest
WORKDIR /app

# Installing dependencies including
RUN apt-get update && apt-get install -y software-properties-common \
    && add-apt-repository ppa:ubuntu-toolchain-r/test \
    && apt-get install -y build-essential cmake g++-13 libboost-all-dev libgmp-dev libmpfr-dev python3 python3-pip python3-dev libx11-6 gmsh libgmsh-dev git libhdf5-dev libcgal-dev python2.7-dev swig doxygen graphviz
RUN pip3 install numpy h5py gmsh matplotlib PyQt5

# Installing AABB from the git repo
RUN git clone https://github.com/lohedges/aabbcc
RUN cd aabbcc && make build && make install

# Copying all contents from the current directory to the Docker directory /app
COPY . .

ENV CXX=g++-13
RUN cmake . && make
CMD [ "python3", "main.py" ]
