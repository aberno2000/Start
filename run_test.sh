#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 tests/<src_file.cpp>"
    exit 1
fi

if grep -q "#include <gmsh.h>" $1; then
    g++ $1 src/VolumeCreator.cpp src/RealNumberGenerator.cpp -std=c++20 -lgmsh -Wall -Wpedantic -Wextra -Werror
else
    g++ $1 -std=c++20 -Wall -Wpedantic -Wextra -Werror
fi

if [ $? -eq 0 ]; then
    echo -e "\e[32;1mFile '$1' successfully compiled\e[0m"
else
    echo -e "\e[31;1mError: Compilation failed\e[0m"
    exit 1
fi
./a.out
rm a.out
