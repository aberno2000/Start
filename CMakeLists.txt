# 3.14 CMake version supports 6.28 version of ROOT CERN, that supports C++20 standard
cmake_minimum_required(VERSION 3.14 FATAL_ERROR)

# TODO: Add concise description
project(Start
        VERSION 1.0
        LANGUAGES CXX)

# execute_process(
#     COMMAND root-config --cflags --glibs
#     OUTPUT_VARIABLE ROOT_FLAGS
#     OUTPUT_STRIP_TRAILING_WHITESPACE
# )

set(CMAKE_CXX_FLAGS "-Wall -Wpedantic -Wextra -laabb -DLOG ${ROOT_FLAGS}")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(INCLUDES "~/Documents/Work/AABB/aabbcc")
# set(ROOT_DIR "/usr/share/root")

file(GLOB sources "src/*.cpp")

include_directories(${CMAKE_SOURCE_DIR}/include 
                    ${ROOT_INCLUDE_DIR}
                    ${ROOT_DIR}
                    ${INCLUDES})
add_executable(main ${sources})

set_target_properties(main PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}")
target_link_libraries(main PRIVATE aabb)
