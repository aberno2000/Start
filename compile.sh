#!/bin/bash

# Rebuild from null each time
rm -rf build
mkdir build && cd build
cmake .. && make
