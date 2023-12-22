# 3.14 CMake version supports 6.28 version of ROOT CERN, that supports C++20 standard
cmake_minimum_required(VERSION 3.14 FATAL_ERROR)

# TODO: Add concise description
project(Start
        VERSION 1.0
        LANGUAGES CXX)

set(CMAKE_CXX_FLAGS "-Wall -Wpedantic -Wextra -laabb -lm -O2 -DLOG")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

file(GLOB sources "src/*.cpp")

include_directories(${CMAKE_SOURCE_DIR}/include)
add_executable(main ${sources})

set_target_properties(main PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}")
target_link_libraries(main PRIVATE aabb)
