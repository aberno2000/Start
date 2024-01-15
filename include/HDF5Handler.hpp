#ifndef HDF5HANDLER_HPP
#define HDF5HANDLER_HPP

#include <hdf5.h>
#include <string_view>
#include <unordered_map>

#include "Mesh.hpp"

/**
 * @brief Handles operations related to HDF5 files for storing and managing mesh data.
 * @details This class provides functionalities to create, read, and update data in
 *          an HDF5 file. It is specifically designed to handle mesh data, including
 *          the coordinates, areas, and particle counters of each triangle in the mesh.
 */
class HDF5Handler final
{
private:
    hid_t m_file_id;    // File id
    size_t m_firstID{}, // ID of the first triangle in mesh
        m_lastID{-1ul}; // ID of the last triangle in mesh

    /**
     * @brief Creates a new group in the HDF5 file.
     * @details This function creates a new group in the HDF5 file with the specified name.
     *          It uses H5Gcreate2 for group creation and checks if the operation is successful.
     *          If the group creation fails, it throws an exception.
     * @param groupName The name of the group to be created.
     *                  It is a std::string_view to avoid unnecessary string copies.
     *
     * @throws `std::runtime_error` If the group creation fails.
     */
    void createGroup(std::string_view groupName);

    /**
     * @brief Writes data to a dataset in a specified group within the HDF5 file.
     * @details This function opens the specified group, creates a dataspace and a dataset,
     *          and then writes the provided data to the dataset. If any of these operations fail,
     *          it throws an exception. It uses H5Dwrite to write data and closes the handles
     *          for the dataset and dataspace after the operation.
     *
     * @param groupName The name of the group containing the dataset.
     * @param datasetName The name of the dataset to which data will be written.
     * @param type The HDF5 data type of the dataset.
     * @param data A pointer to the data to be written.
     * @param dims The dimension size of the dataset.
     *
     * @throws `std::runtime_error` If creating the dataspace or dataset fails.
     */
    void writeDataset(std::string_view groupName, std::string_view datasetName,
                      hid_t type, void const *data, hsize_t dims);

    /**
     * @brief Reads data from a dataset within a specified group in the HDF5 file.
     * @details This function opens the specified group and dataset, and then reads
     *          the data into the provided buffer. It uses H5Dread for reading the data.
     *          If opening the group or the dataset fails, an exception is thrown.
     *          After the operation, it closes the handles for the dataset and the group.
     *
     * @param groupName The name of the group containing the dataset.
     * @param datasetName The name of the dataset from which data will be read.
     * @param type The HDF5 data type of the dataset.
     * @param data A pointer where the read data will be stored.
     *
     * @throws `std::runtime_error` If the dataset opening fails.
     */
    void readDataset(std::string_view groupName, std::string_view datasetName,
                     hid_t type, void *data);

public:
    /**
     * @brief Constructs an HDF5Handler object and opens or creates an HDF5 file.
     * @param filename The name of the HDF5 file to be opened or created.
     * @details The constructor opens an HDF5 file if it exists, or creates a new one if it does not.
     *          The file is opened with write access, and the file handle is stored for future operations.
     */
    explicit HDF5Handler(std::string_view filename);
    ~HDF5Handler();

    /**
     * @brief Saves mesh data to the HDF5 file.
     * @param mesh A vector of tuples representing the mesh's triangles, with each tuple containing
     *                  the triangle's ID, vertices (as PositionVector objects), and area.
     * @details This method iterates through the given vector of triangles, creating a group for each
     *          triangle in the HDF5 file. Within each group, it stores datasets for the triangle's
     *          coordinates, area, and initializes the particle counter to zero.
     * @throws `std::runtime_error` if it fails to create a group or dataset within the HDF5 file,
     *         or if writing to the dataset fails.
     */
    void saveMeshToHDF5(TriangleMeshParamVector const &mesh);

    /**
     * @brief Reads mesh data from the HDF5 file starting from a specified object ID.
     * @return A vector of tuples representing the mesh's triangles, with each tuple containing
     *         the triangle's ID, vertices, area, and particle counter.
     * @details This method reads the HDF5 file and constructs a vector of tuples, each representing a
     *          triangle's data. It retrieves the triangle's ID, coordinates, area, and particle counter
     *          from the HDF5 file, starting from the triangle with ID `firstObjectID`.
     * @throws `std::runtime_error` if it fails to open a group or dataset within the HDF5 file.
     */
    TriangleMeshParamVector readMeshFromHDF5();
};

#endif // !HDF5HANDLER_HPP
