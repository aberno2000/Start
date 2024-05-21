#ifndef VOLUMETRICMESHDATA_HPP
#define VOLUMETRICMESHDATA_HPP

#include <array>
#include <optional>

#include "../Geometry/CGALTypes.hpp"
#include "../Utilities/Utilities.hpp"

/**
 * @brief Class representing volumetric mesh data for a tetrahedron.
 *        All the global indexes refers to GMSH indexing.
 *        Uses Singleton pattern.
 */
class VolumetricMeshData final
{
private:
    static std::unique_ptr<VolumetricMeshData> instance; ///< Singleton instance of VolumetricMeshData.
    static std::mutex instanceMutex;                     ///< Mutex for thread-safe access to the singleton instance.

    struct TetrahedronData
    {
        struct NodeData
        {
            size_t globalNodeId{};           ///< Global Id of the node.
            Point nodeCoords;                ///< Coordinates of this node.
            std::optional<Point> nablaPhi;   ///< Optional field for the gradient of basis function.
            std::optional<double> potential; ///< Optional field for the potential in node.
        };

        size_t globalTetraId{};             ///< Global ID of the tetrahedron according to GMSH indexing.
        Tetrahedron tetrahedron;            ///< CGAL::Tetrahedron_3 object from the mesh.
        std::array<NodeData, 4ul> nodes;    ///< Tetrahedron verteces and their coordinates.
        std::optional<Point> electricField; ///< Optional field for the electric field of the tetrahedron.

        /**
         * @brief Get the center point of the tetrahedron.
         * @return Point representing the center of the tetrahedron.
         */
        [[nodiscard("The center of the tetrahedron is important for further geometric calculations and shouldn't be discarded.")]]
        Point getTetrahedronCenter() const;
    };
    std::vector<TetrahedronData> m_meshComponents; ///< Array of all the tetrahedrons from the mesh.

    /**
     * @brief Constructor. Fills storage for the volumetric mesh.
     * @details This constructor reads the mesh file once, extracts the node coordinates and tetrahedron
     *          connections, and initializes the internal storage for the volumetric mesh data.
     * @param mesh_filename The filename of the mesh file to read.
     * @throw std::runtime_error if there is an error reading the mesh file or extracting the data.
     */
    VolumetricMeshData(std::string_view mesh_filename);

public:
    using NodeData = VolumetricMeshData::TetrahedronData::NodeData;
    using TetrahedronData = VolumetricMeshData::TetrahedronData;

    // Preventing copy of this object.
    VolumetricMeshData(VolumetricMeshData const &) = delete;
    VolumetricMeshData(VolumetricMeshData &&) = delete;
    VolumetricMeshData &operator=(VolumetricMeshData const &) = delete;
    VolumetricMeshData &operator=(VolumetricMeshData &&) = delete;

    /**
     * @brief Retrieves the singleton instance of the VolumetricMeshData class.
     *
     * This static method ensures that only one instance of the VolumetricMeshData
     * class is created. It initializes the instance if it hasn't been initialized yet
     * using the provided mesh filename. Subsequent calls will return the same instance.
     *
     * @param mesh_filename The filename of the mesh file to read during the initialization.
     *                      This parameter is used only the first time the instance is initialized.
     * @return VolumetricMeshData& A reference to the singleton instance of the VolumetricMeshData class.
     * @throw std::runtime_error if there is an error reading the mesh file or extracting the data.
     */
    static VolumetricMeshData &getInstance(std::string_view mesh_filename);

    /// @brief Getter for all the tetrahedra mesh components from the mesh.
    auto &getMeshComponents() { return m_meshComponents; }
    constexpr auto const &getMeshComponents() const { return m_meshComponents; }

    /// @brief Prints all the mesh components to the stdout.
    void print() const noexcept;

    /// @brief Returns count of the tetrahedra in the mesh.
    constexpr size_t size() const { return m_meshComponents.size(); }

    /// @brief Checks and returns result of the checking if there is no tetrahedra in the mesh.
    constexpr bool empty() const { return m_meshComponents.empty(); }

    /**
     * @brief Retrieves the mesh data for a specific tetrahedron by its global ID.
     *
     * This function searches through the mesh components and returns the data
     * for the tetrahedron with the specified global ID. If no such tetrahedron
     * is found, it returns `std::nullopt`.
     *
     * @param globalTetrahedronId The global ID of the tetrahedron to retrieve.
     * @return std::optional<TetrahedronData> An optional containing the TetrahedronData if found, or std::nullopt if not found.
     */
    std::optional<TetrahedronData> getMeshDataByTetrahedronId(size_t globalTetrahedronId) const;

    /**
     * @brief Assigns the gradient of the basis function to the corresponding node.
     * @param tetrahedronId The global ID of the tetrahedron.
     * @param nodeId The global ID of the node.
     * @param gradient The gradient of the basis function.
     */
    void assignNablaPhi(size_t tetrahedronId, size_t nodeId, Point const &gradient);

    /**
     * @brief Assigns the potential to the corresponding node.
     * @param nodeId The global ID of the node.
     * @param potential The potential value.
     */
    void assignPotential(size_t nodeId, double potential);

    /**
     * @brief Assigns the electric field to the corresponding tetrahedron.
     * @param tetrahedronId The global ID of the tetrahedron.
     * @param electricField The electric field vector.
     */
    void assignElectricField(size_t tetrahedronId, Point const &electricField);
};

#endif // !VOLUMETRICMESHDATA_HPP
