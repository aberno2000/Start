#!/bin/bash

# Rebuild from null each time
# rm -rf build
mkdir -p build && cd build
cmake .. && make
