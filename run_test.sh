#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 tests/<src_file.cpp>"
    exit 1
fi

g++ $1 -std=c++20 -Wall -Wpedantic -Wextra -Werror
if [ $? -eq 0 ]; then
    echo -e "\e[32;1mFile '$1' successfully compiled\e[0m"
else
    echo -e "\e[31;1mError: Compilation failed\e[0m"
    exit 1
fi
./a.out
rm a.out
