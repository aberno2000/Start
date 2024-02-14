import h5py
import numpy as np
from re import compile


class HDF5Handler:
    def __init__(self, filename, first_id=0):
        """
        Initialize the HDF5Handler object.

        Args:
            filename (str): Path to the HDF5 file.
            first_id (int, optional): Starting ID for reading groups. Defaults to 0.
        """
        # Check if the file exists and is not empty
        if not h5py.is_hdf5(filename):
            raise ValueError(
                f"The file {filename} doesn't exist or is empty.")

        self.filename = filename
        self.file = h5py.File(filename, "r")
        self.first_id = self.get_first_id_from_hdf5(self.filename) or first_id

    def get_first_id_from_hdf5(self, filename):
        """
        Extracts the first ID from the HDF5 file based on the naming convention of groups.

        Args:
            filename (str): Path to the HDF5 file.

        Returns:
            int or None: The smallest ID found in the group names, or None if no ID is found.
        """
        with h5py.File(filename, "r") as file:
            group_names = list(file.keys())

            # Extract IDs using a regular expression
            ids = []
            pattern = compile(r"Triangle_(\d+)")
            for name in group_names:
                match = pattern.match(name)
                if match:
                    ids.append(int(match.group(1)))

            # Returning the samllest ID of the triangle or None if no IDs found
            return min(ids) if ids else None

    def __del__(self):
        if hasattr(self, 'file'):  # Check if self.file exists before attempting to close it
            self.file.close()

    def read_dataset(self, group_name, dataset_name):
        """
        Reads a dataset from a specified group in the HDF5 file.

        Args:
            group_name (str): The name of the group containing the dataset.
            dataset_name (str): The name of the dataset to read.

        Returns:
            np.ndarray: The data contained in the specified dataset.

        Raises:
            RuntimeError: If the dataset cannot be opened.
        """
        try:
            group = self.file[group_name]
            return group[dataset_name][:]
        except Exception as e:
            raise RuntimeError(
                f"Failed to open dataset {dataset_name} in group: {group_name}"
            ) from e

    def read_mesh_from_hdf5(self):
        """
        Reads mesh data from the HDF5 file, based on the group names following the pattern "Triangle_{id}".

        Returns:
            list of tuples: Each tuple contains the mesh data for a triangle.
        """
        mesh = []
        num_objs = len(self.file.keys())
        last_id = self.first_id + num_objs

        for id in range(self.first_id, last_id):
            group_name = f"Triangle_{id}"

            coordinates = self.read_dataset(
                group_name, "Coordinates").reshape(3, 3)
            area = self.read_dataset(group_name, "Area")[0]
            counter = self.read_dataset(group_name, "Counter")[0]

            vertex1 = np.array(coordinates[0])
            vertex2 = np.array(coordinates[1])
            vertex3 = np.array(coordinates[2])

            mesh.append((id, vertex1, vertex2, vertex3, area, counter))

        return mesh
