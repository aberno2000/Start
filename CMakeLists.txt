# 3.14 CMake version supports 6.28 version of ROOT CERN, that supports C++20 standard
cmake_minimum_required(VERSION 3.14 FATAL_ERROR)

project(Start
        VERSION 1.0
        DESCRIPTION "" # TODO: Add concise description
        LANGUAGES CXX)

set(CMAKE_CXX_FLAGS "-Wall -Wpedantic -Wextra -laabb -O2 -DLOG")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(SOURCES
    src/main.cpp
    src/Particle.cpp
    src/RealNumberGenerator.cpp
    src/Settings.cpp
)

include_directories(${CMAKE_SOURCE_DIR}/include)
add_executable(main ${SOURCES})

set_target_properties(main PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}")
target_link_libraries(main PRIVATE aabb)
