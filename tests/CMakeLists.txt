cmake_minimum_required(VERSION 3.14)
project(Tests)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Werror -Wno-maybe-uninitialized")

find_package(Threads REQUIRED)

include(FetchContent)
FetchContent_Declare(
    googletest
    URL https://github.com/google/googletest/archive/release-1.10.0.tar.gz
)
FetchContent_MakeAvailable(googletest)

include_directories("../include/")

add_executable(
    all_tests
    main.cpp
    ../src/MathVector.cpp
    ../src/Particle.cpp
    ../src/RealNumberGenerator.cpp
    ../src/Utilities.cpp
    ../src/ConfigParser.cpp
    ParticleTests.cpp
)

target_link_libraries(
    all_tests
    gtest_main
    Threads::Threads
)

include(CTest)
enable_testing()

# Adding tests
add_test(
    NAME all_tests
    COMMAND all_tests
)
