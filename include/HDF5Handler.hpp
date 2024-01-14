#ifndef HDF5HANDLER_HPP
#define HDF5HANDLER_HPP

#include <hdf5.h>
#include <string_view>
#include <unordered_map>

#include "Mesh.hpp"

/**
 * @brief RAII wrapper class for managing HDF5 resources.
 *
 * HDF5Resource is a utility class that encapsulates an HDF5 resource handle (such as a dataset or group handle),
 * ensuring that the resource is properly released when the HDF5Resource object goes out of scope.
 * This class follows the RAII (Resource Acquisition Is Initialization) pattern, which is crucial for
 * resource management in C++.
 */
class HDF5Resource
{
private:
    hid_t m_resource; // Handle to an HDF5 resource (e.g., dataset or group).

public:
    /**
     * @brief Constructor that takes an HDF5 resource handle.
     * @param resource The HDF5 resource handle to be managed.
     */
    HDF5Resource(hid_t resource);

    /**
     * @brief Destructor that releases the HDF5 resource.
     * @details This destructor ensures that the HDF5 resource is properly closed
     *          when the HDF5Resource object is destroyed.
     */
    ~HDF5Resource();

    // Deleted copy constructor and assignment operator to prevent copying.
    HDF5Resource(const HDF5Resource &) = delete;
    HDF5Resource &operator=(const HDF5Resource &) = delete;

    // Move constructor and move assignment operator for transfer of ownership.
    HDF5Resource(HDF5Resource &&other) noexcept;

    HDF5Resource &operator=(HDF5Resource &&other) noexcept;

    /**
     * @brief Returns the managed HDF5 resource handle.
     * @return The HDF5 resource handle.
     */
    hid_t get() const;

    /**
     * @brief Closes the managed HDF5 resource if it is valid.
     *
     * This method can be called to explicitly close the HDF5 resource
     * before the HDF5Resource object is destroyed.
     */
    void close();
};

/**
 * @brief Handles operations related to HDF5 files for storing and managing mesh data.
 * @details This class provides functionalities to create, read, and update data in
 *          an HDF5 file. It is specifically designed to handle mesh data, including
 *          the coordinates, areas, and particle counters of each triangle in the mesh.
 */
class HDF5Handler final
{
private:
    hid_t m_file_id;
    size_t m_IDofFirstTriangle{};

    /* +++ Helper methods that throws exceptions if smth goes wrong. +++ */
    hid_t openGroup(std::string_view groupName) const;
    hid_t createDataSet(hid_t grp_id, std::string_view dataSetName, hid_t dataType, hsize_t *dims, int rank) const;
    void writeDataSet(hid_t dataset, hid_t dataType, void const *data, std::string_view dataSetName) const;
    void readDataSet(hid_t dataset, hid_t dataType, void *data, std::string_view dataSetName) const;
    void closeHDF5Resource(hid_t resource) const;

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
     * @brief Updates the particle counters for each triangle in the HDF5 file.
     * @details This method takes a map of triangle IDs and their corresponding
     *          updated particle counts. It then iterates through each triangle
     *          in the HDF5 file and updates the 'Counter' dataset with the new values.
     * @param triangleCounters A map with triangle IDs as keys and updated particle
     *                         counts as values.
     * @throws `std::runtime_error` if it fails to open a group or dataset within the HDF5 file,
     *         or if writing to the dataset fails.
     */
    void updateParticleCounters(std::unordered_map<size_t, int> const &triangleCounters);

    /**
     * @brief Saves mesh data to the HDF5 file.
     * @param triangles A vector of tuples representing the mesh's triangles, with each tuple containing
     *                  the triangle's ID, vertices (as PositionVector objects), and area.
     * @details This method iterates through the given vector of triangles, creating a group for each
     *          triangle in the HDF5 file. Within each group, it stores datasets for the triangle's
     *          coordinates, area, and initializes the particle counter to zero.
     * @throws `std::runtime_error` if it fails to create a group or dataset within the HDF5 file,
     *         or if writing to the dataset fails.
     */
    void saveMeshToHDF5(TriangleMeshParamVector const &triangles);

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
