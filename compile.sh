#!/bin/bash

usage() {
    echo "Usage: $0 [-r|--rebuild]"
    echo "  -r, --rebuild   Clean and rebuild the project from scratch."
    exit 1
}

# Default behavior does not clean build
REBUILD=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
    -r | --rebuild)
        REBUILD=true
        shift # Remove argument name from processing
        ;;
    *) # Unknown option
        usage
        ;;
    esac
done

# Clean build directory if requested
if [ "$REBUILD" = true ]; then
    echo "Rebuilding from the scratch..."
    rm -rfv build
fi

mkdir -pv build && cd build
cmake .. && make -j$(nproc)
