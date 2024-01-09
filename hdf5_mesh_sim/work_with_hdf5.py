import h5py
import numpy as np
from collections import defaultdict


def save_to_hdf5(triangles, filename):
    """
    Save triangle data to an HDF5 file.

    Args:
    - triangles: List of tuples containing triangle data.
    - filename: Path to the output HDF5 file.

    Returns:
    - None
    """
    with h5py.File(filename, "w") as hf:
        for idx, triangle in enumerate(triangles):
            # Create a group for each triangle using the triangle ID as the group name
            grp = hf.create_group(f"Triangle_{triangle[0]}")

            # Store data related to the triangle in the group
            grp.create_dataset("Coordinates", data=np.array(triangle[1:10]))
            grp.create_dataset("Area", data=triangle[10])


def save_settled_to_hdf5(triangles, filename):
    """
    Save triangle data to an HDF5 file.

    Args:
    - triangles: List of tuples containing triangle data.
    - filename: Path to the output HDF5 file.

    Returns:
    - None
    """
    # Create a dictionary to store counts for each triangle ID
    triangle_counts = defaultdict(int)

    with h5py.File(filename, "w") as hf:
        for idx, triangle in enumerate(triangles):
            triangle_id = triangle[0]

            # Check if triangle ID exists in the dictionary
            if triangle_id in triangle_counts:
                # If the ID exists, increment the counter
                triangle_counts[triangle_id] += 1
            else:
                # If it's a new ID, set the counter to 1
                triangle_counts[triangle_id] = 1

            # Create a group for each triangle using the triangle ID as the group name
            grp = hf.create_group(
                f"Triangle_{triangle_id}_{triangle_counts[triangle_id]}"
            )

            # Store data related to the triangle in the group
            grp.create_dataset("Coordinates", data=np.array(triangle[1:10]))
            grp.create_dataset("Area", data=triangle[10])
            grp.create_dataset("Counter", data=triangle_counts[triangle_id])


def read_hdf5(filename):
    """
    Read triangle data from an HDF5 file.

    Args:
    - filename: Path to the input HDF5 file.

    Returns:
    - List of tuples containing triangle data.
    """
    triangles = []

    with h5py.File(filename, "r") as hf:
        for key in hf.keys():
            grp = hf[key]
            coordinates = grp["Coordinates"][:]
            area = grp["Area"][()]

            triangle_data = (int(key.split("_")[1]), *coordinates, area)
            triangles.append(triangle_data)

    return triangles


def read_settled_hdf5(filename):
    """
    Read triangle data from an HDF5 file.

    Args:
    - filename: Path to the input HDF5 file.

    Returns:
    - List of tuples containing triangle data.
    """
    triangles = []

    with h5py.File(filename, "r") as hf:
        for key in hf.keys():
            grp = hf[key]
            coordinates = grp["Coordinates"][:]
            area = grp["Area"][()]
            counter = grp["Counter"][()]

            triangle_data = (int(key.split("_")[1]), *coordinates, area, counter)
            triangles.append(triangle_data)

    return triangles
