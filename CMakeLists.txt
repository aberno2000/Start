# 3.14 CMake version supports 6.28 version of ROOT CERN, that supports C++20 standard
cmake_minimum_required(VERSION 3.14 FATAL_ERROR)

project(Start
        VERSION 1.0
        DESCRIPTION "The Start project is dedicated to the development and testing of \
        a software prototype for optimizing the technological process in vacuum-plasma installations. \
        This software aims to address the current limitations in accurately obtaining process \
        parameters in vacuum-plasma installations with non-rectangular geometries, due to the \
        lack of algorithms for calculating non-standard grids of the electrostatic field generated \
        by plasma particles."
        LANGUAGES CXX)

set(GMSH_LIB /usr/local/lib/libgmsh.so.4.12)
set(HDF5_DIR "/usr/local/HDF5-1.14.3-Linux/HDF_Group/HDF5/1.14.3/cmake")
find_package(Boost REQUIRED)
find_package(HDF5 REQUIRED COMPONENTS CXX)

# Adding support of TBB library if some OS requires it
find_package(TBB QUIET)

execute_process(
    COMMAND root-config --cflags --glibs
    OUTPUT_VARIABLE ROOT_FLAGS
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

set(CMAKE_CXX_FLAGS "-Wall -Wpedantic -Wextra -lpthread -O3 ${ROOT_FLAGS}")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(SOURCES
    src/CollisionTracker.cpp
    src/ConfigParser.cpp
    src/HDF5Handler.cpp
    src/main.cpp
    src/MathVector.cpp
    src/Mesh.cpp
    src/Particle.cpp
    src/RayTriangleIntersection.cpp
    src/RealNumberGenerator.cpp
    src/Utilities.cpp
    src/VolumeCreator.cpp
)

include_directories(${CMAKE_SOURCE_DIR}/include
                    ${Boost_INCLUDE_DIRS}
                    ${HDF5_INCLUDE_DIRS}
                    ${TBB_INCLUDE_DIRS})
add_executable(main ${SOURCES})

set_target_properties(main PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}")
target_link_libraries(main PRIVATE 
    aabb gmp mpfr 
    ${GMSH_LIB} ${Boost_LIBRARIES} 
    ${HDF5_LIBRARIES} ${TBB_LIBRARIES}
)
