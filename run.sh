#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <test file to compile>"
    exit 1
fi

g++ $1 $(ls src/*.cpp | grep -v 'main.cpp') $(root-config --cflags --glibs) -std=c++20 -laabb -Wall -Wpedantic -Wextra
./a.out

if [ $? -eq 0 ]; then
    echo -e "\e[32;1mFile $1 successfully compiled and ran\e[0m"
else
    echo -e "\e[31;1mError: Compilation or execution failed\e[0m"
fi
