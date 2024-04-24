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
    find_library(GMSH_LIBRARIES
                NAMES gmsh
                PATHS "C:/Program Files/gmsh-4.12.2-Windows64-sdk/lib"
                NO_DEFAULT_PATH)
    find_package(CGAL REQUIRED)
    if(CGAL_FOUND)
        set(CGAL_NAMESPACE CGAL::CGAL)
        message(STATUS "CGAL library found: ${CGAL_LIBRARIES}")
    endif()
else()
    find_library(GMSH_LIBRARIES
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
    find_package(GMP REQUIRED)
    if(GMP_FOUND)
        message(STATUS "GMP found\nGMP libraries: ${GMP_LIBRARIES}")
    endif()
else()
    set(GMP_LIBRARIES gmp)
endif()
include_directories(${GMP_INCLUDE_DIR})

find_package(Boost REQUIRED)
include_directories(${Boost_INCLUDE_DIRS})

find_package(HDF5 REQUIRED COMPONENTS CXX)
include_directories(${HDF5_INCLUDE_DIRS})

find_package(MPI REQUIRED)
if(MPI_FOUND)
    message(STATUS "MPI found\nMPI libraries: ${MPI_LIBRARIES}")
endif()
include_directories(${MPI_INCLUDE_PATH})

if(NOT "$ENV{TRILINOS_DIR}" STREQUAL "")
  	set(TRILINOS_DIR "$ENV{TRILINOS_DIR}")
 	find_package(Trilinos REQUIRED PATHS "${TRILINOS_DIR}")
  	message(STATUS "Trilinos directory set to custom enviroment variable")
else()
  	find_package(Trilinos REQUIRED PATHS "/usr/local/lib/cmake/Trilinos")
  	message(STATUS "Trilinos directory set to default location")
endif()

if (Trilinos_FOUND)
    message(STATUS "Trilinos libraries: ${Trilinos_LIBRARIES}\nTrilinos include dirs: ${Trilinos_INCLUDE_DIRS}")
else()
    message(FATAL_ERROR "Trilinos not found")
endif()
include_directories(${Trilinos_INCLUDE_DIRS})
link_directories(${Trilinos_LIBRARY_DIRS})

# Adding support of TBB library if some OS requires it
find_package(TBB QUIET)
if (TBB_FOUND)
    set(TBB_NAMESPACE TBB::tbb)
    message(STATUS "TBB library found")
endif()
include_directories(${TBB_INCLUDE_DIRS})

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

if(CMAKE_CXX_COMPILER_ID STREQUAL "Intel")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fp-model strict")
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -frounding-math")
else()
  message(WARNING "Unsupported compiler. You may need to manually set the appropriate flags for strict floating-point rounding.")
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(SOURCES
    src/tracking_particles_in_volume.cpp # Uncomment this line if want to compile this file and comment src/main.cpp 
    # src/main.cpp
    src/CollisionTracker.cpp
    src/ConfigParser.cpp
    src/Grid3D.cpp
    src/GSMatrixAssemblier.cpp
    src/HDF5Handler.cpp
    src/MathVector.cpp
    src/MatrixEquationSolver.cpp
    src/Mesh.cpp
    src/Particle.cpp
    src/ParticleTracker.cpp
    src/RayTriangleIntersection.cpp
    src/RealNumberGenerator.cpp
    src/SolutionVector.cpp
    src/Utilities.cpp
    src/VolumeCreator.cpp
)
include_directories(${CMAKE_SOURCE_DIR}/include)
add_executable(nia_start ${SOURCES})

set_target_properties(nia_start PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}")
target_link_libraries(nia_start PRIVATE 
    ${CGAL_NAMESPACE}
    ${CGAL_LIBRARIES}
    ${GMSH_LIBRARIES} 
    ${Boost_LIBRARIES} 
    ${GMP_LIBRARIES}
    ${HDF5_LIBRARIES}
    ${TBB_NAMESPACE}
    ${TBB_LIBRARIES}
    ${MPI_LIBRARIES}
    ${Trilinos_LIBRARIES}
)
