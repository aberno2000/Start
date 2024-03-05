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

if (WIN32)
    find_library(GMSH_LIB
                NAMES gmsh
                PATHS "C:/Program Files/gmsh-4.12.2-Windows64-sdk/lib"
                NO_DEFAULT_PATH)
    find_package(CGAL REQUIRED)
else()
    find_library(GMSH_LIB
                NAMES gmsh
                PATHS /usr/lib 
                      /usr/local/lib
                      /usr/lib/x86_64-linux-gnu
                      /usr/lib64 
                      /usr/lib64/mpich/lib 
                      /usr/lib64/openmpi/lib
                NO_DEFAULT_PATH)
endif()

if(MSVC)
    set(GMP_DIR "C:/Program Files/CGAL-5.6.1/auxiliary/gmp")
    find_path(GMP_INCLUDE_DIR NAMES gmp.h HINTS ${GMP_DIR}/include)
    find_library(GMP_LIBRARIES NAMES gmp libgmp HINTS ${GMP_DIR}/lib)
endif()

find_package(Boost REQUIRED)
find_package(HDF5 REQUIRED COMPONENTS CXX)

if(CGAL_FOUND)
    set(CGAL_NAMESPACE CGAL::CGAL)
    message(STATUS "CGAL library found: ${CGAL_LIB}")
endif()

# Adding support of TBB library if some OS requires it
find_package(TBB QUIET)
if (TBB_FOUND)
    set(TBB_NAMESPACE TBB::tbb)
    message(STATUS "TBB library found: ${TBB_LIB}")
endif()

if (MSVC)
    # Using Visual C++ compiler (MSVC)
    add_compile_options(/W4)  # Equivalent to -Wall in GCC/Clang

    # Separate the optimization flags for Release build
    string(REPLACE "/RTC1" "" CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG}")
    string(REPLACE "/O2" "" CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG}")
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /O2")
else()
    # Assuming GCC/Clang compiler
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wpedantic -Wextra -pthread -O3")
endif()

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
add_executable(argos_nia_start ${SOURCES})

set_target_properties(argos_nia_start PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}")
target_link_libraries(argos_nia_start PRIVATE 
    gmp mpfr ${CGAL_NAMESPACE}
    ${GMSH_LIB} ${Boost_LIBRARIES} ${GMP_LIBRARIES}
    ${HDF5_LIBRARIES} ${TBB_LIBRARIES} ${TBB_NAMESPACE}
)
