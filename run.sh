#!/bin/bash

g++ src/*.cpp -std=c++20 -Wall -Wpedantic -Wextra -laabb -DLOG -o main
./main

