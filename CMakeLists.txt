# 3.14 CMake version supports 6.28 version of ROOT CERN, that supports C++20 standard
cmake_minimum_required(VERSION 3.14 FATAL_ERROR)

project(Start
        VERSION 1.0
        DESCRIPTION "" # TODO: Add concise description
        LANGUAGES CXX)

execute_process(
    COMMAND root-config --cflags --glibs
    OUTPUT_VARIABLE ROOT_FLAGS
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

set(CMAKE_CXX_FLAGS "-Wall -Wpedantic -Wextra -laabb -O2 ${ROOT_FLAGS}")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(ROOT_DIR "/usr/share/root")
set(HDF5_DIR "/usr/share/hdf5/1.14.3")
set(GMSH_DIR "/usr/share/gmsh")

set(SOURCES
    src/main.cpp
    src/Particle.cpp
    src/RealNumberGenerator.cpp
    src/Settings.cpp
    src/HDF5Handler.cpp
)

include_directories(${CMAKE_SOURCE_DIR}/include
                    ${ROOT_DIR}
                    ${HDF5_DIR}
                    ${GMSH_DIR})
add_executable(main ${SOURCES})

set_target_properties(main PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}")
target_link_libraries(main PRIVATE aabb hdf5 gmsh)
