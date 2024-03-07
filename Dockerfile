FROM python:3.7
WORKDIR /app

# Installing OpenGL
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx libopengl0 gmsh libgmsh-dev && \
    pip install numpy matplotlib vtk h5py gmsh PyQt5 nlohmann-json

# Copy all the necessary files and directories
COPY ./dist/nia_start /app/
COPY ./icons /app/icons
COPY ./results /app/results
COPY ./*.json /app/

WORKDIR /app/
