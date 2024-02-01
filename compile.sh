#!/bin/bash

usage() {
    echo "Usage: $0 [-r|--rebuild] [-j <NUM_THREADS>] [-h|--help]"
    echo "  -r, --rebuild       Clean and rebuild the project from scratch."
    echo "  -j <NUM_THREADS>    Specify the number of threads to run simultaneously."
    echo "                      If not specified, use all available cores."
    echo "  -h, --help          Display this help message and exit."
    exit 1
}

REBUILD=false      # Default behavior does not clean build
NUM_THREADS=$(nproc) # Default to all available cores

while [[ "$#" -gt 0 ]]; do
    case $1 in
    -r | --rebuild)
        REBUILD=true
        ;;
    -j)
        if [[ -n $2 && $2 =~ ^[0-9]+$ ]]; then
            NUM_THREADS=$2
            shift # Remove argument name from processing
        else
            echo "Error: -j requires a numeric argument."
            usage
        fi
        ;;
    -h | --help)
        usage
        ;;
    *) # Unknown option
        usage
        ;;
    esac
    shift # Move to next argument or value
done

# Clean build directory if requested
if [ "$REBUILD" = true ]; then
    echo "Rebuilding from scratch..."
    rm -rfv build
fi

mkdir -pv results
mkdir -pv build && cd build
echo "Making with $NUM_THREADS threads. Your PC provides $(nproc) threads."
cmake .. && make -j$NUM_THREADS
