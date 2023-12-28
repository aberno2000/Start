#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 intermediateResults/<src_file.cpp>"
    exit 1
fi

g++ $1 $(ls src/*.cpp | grep -v 'main.cpp') $(root-config --cflags --glibs) -std=c++20 -laabb -Wall -Wpedantic -Wextra
./a.out

if [ $? -eq 0 ]; then
    echo -e "\e[32;1mFile '$1' successfully compiled and ran\e[0m"
else
    echo -e "\e[31;1mError: Compilation or execution failed\e[0m"
    exit 1
fi

rm a.out
echo -e "To view results of a running file \e[1m$1\e[0m, you need to run the following commands:"
echo -e "\e[1;32mroot\e[0m"
echo -e "\e[1;34mnew TBrowser\e[0m"
echo -e "Then, select \e[1mfile.root\e[0m in TBrowser"
