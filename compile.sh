#!/bin/bash

usage() {
    echo "Usage: $0 [-r|--rebuild] [-j <num_ths>]"
    echo "  -r, --rebuild       Clean and rebuild the project from scratch."
    echo "  -j <num_ths>        Specify the number of threads to run simultaneously."
    echo "                      If not specified, use all available cores."
    exit 1
}

REBUILD=false     # Default behavior does not clean build
NUM_JOBS=$(nproc) # Default to all available processors

while [[ "$#" -gt 0 ]]; do
    case $1 in
    -r | --rebuild)
        REBUILD=true
        ;;
    -j)
        if [[ -n $2 && $2 =~ ^[0-9]+$ ]]; then
            NUM_JOBS=$2
            shift # Remove argument name from processing
        else
            echo "Error: -j requires a numeric argument."
            usage
        fi
        ;;
    *) # Unknown option
        usage
        ;;
    esac
    shift # Move to next argument or value
done

# Clean build directory if requested
if [ "$REBUILD" = true ]; then
    echo "Rebuilding from the scratch..."
    rm -rfv build
fi

mkdir -pv build && cd build
cmake .. && make -j$(nproc)
