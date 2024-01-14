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
    hid_t m_file_id;

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
     * @param firstObjectID The ID of the first object in the HDF5 file to start reading from.
     * @return A vector of tuples representing the mesh's triangles, with each tuple containing
     *         the triangle's ID, vertices, area, and particle counter.
     * @details This method reads the HDF5 file and constructs a vector of tuples, each representing a
     *          triangle's data. It retrieves the triangle's ID, coordinates, area, and particle counter
     *          from the HDF5 file, starting from the triangle with ID `firstObjectID`.
     * @throws `std::runtime_error` if it fails to open a group or dataset within the HDF5 file.
     */
    TriangleMeshParamVector readMeshFromHDF5(size_t firstObjectID);
};

#endif // !HDF5HANDLER_HPP
