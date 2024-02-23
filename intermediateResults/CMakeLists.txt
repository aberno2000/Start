# 3.14 CMake version supports 6.28 version of ROOT CERN, that supports C++20 standard
cmake_minimum_required(VERSION 3.14 FATAL_ERROR)

project(IntermediateResults
        VERSION 1.0
        DESCRIPTION "Only to compile intermediate results"
        LANGUAGES CXX)

find_package(Boost REQUIRED)
find_package(HDF5 REQUIRED COMPONENTS CXX)

# Adding support of TBB library if some OS requires it
find_package(TBB QUIET)
if (TBB_FOUND)
    set(TBB_NAMESPACE TBB::tbb)
endif()

execute_process(
    COMMAND root-config --cflags --glibs
    OUTPUT_VARIABLE ROOT_FLAGS
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

set(CMAKE_CXX_FLAGS "-Wall -Wpedantic -Wextra -lpthread -O3 ${ROOT_FLAGS}")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(SOURCES
    ${INTERMEDIATE_FILE}
    ../src/MathVector.cpp
    ../src/Particle.cpp
    ../src/RayTriangleIntersection.cpp
    ../src/RealNumberGenerator.cpp
    ../src/Utilities.cpp
    ../src/ConfigParser.cpp
)

include_directories(${CMAKE_SOURCE_DIR}/../include
                    ${Boost_INCLUDE_DIRS}
                    ${HDF5_INCLUDE_DIRS}
                    ${TBB_INCLUDE_DIRS})
add_executable(a.out ${SOURCES})

set_target_properties(a.out PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}")
target_link_libraries(a.out PRIVATE 
    aabb gmp mpfr ${Boost_LIBRARIES} ${TBB_LIBRARIES} ${TBB_NAMESPACE}
)
