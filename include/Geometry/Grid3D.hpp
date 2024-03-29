#ifndef GRID3D_HPP
#define GRID3D_HPP

#include <CGAL/Bbox_3.h>
#include <map>

#include "Mesh.hpp"

#define MAX_GRID_SIZE 0x7A1200 ///< Maximum allowed grid size to prevent memory overflow (default: 8'000'000).

/// @brief Represents a 3D grid index with x, y, and z components.
struct GridIndex
{
    short m_x{}, m_y{}, m_z{};

    GridIndex() {}
    GridIndex(short x, short y, short z) : m_x(x), m_y(y), m_z(z) {}
    bool operator==(GridIndex const &other) const { return m_x == other.m_x && m_y == other.m_y && m_z == other.m_z; }
    bool operator<(GridIndex const &other) const { return std::tie(m_x, m_y, m_z) < std::tie(other.m_x, other.m_y, other.m_z); }
};

/// @brief Represents a 3D grid that maps tetrahedrons to their containing cells.
class Grid3D
{
private:
    std::map<size_t, std::vector<GridIndex>> m_tetrahedronCells; ///< Each tetrahedron contains list of cells. Key - ID of tetrahedron, Value - list of cells.
    double m_cubeEdgeSize{};                                     ///< Edge size of the cell.
    short m_divisionsX{}, m_divisionsY{}, m_divisionsZ{};        ///< Count of divisions by each axis.
    CGAL::Bbox_3 m_commonBbox;                                   ///< Common boundary box.
    MeshTetrahedronParamVector m_meshParams;                     ///< Saving mesh params from ctor.

public:
    /**
     * @brief Ctor with params.
     * @param tetrahedrons Tetrahedron mesh params.
     * @param edgeSize Size of the cube edge.
     */
    Grid3D(MeshTetrahedronParamVector const &meshParams, double edgeSize);

    /**
     * @brief Getter for grid index by spatial position of some object.
     * @param x Position by X-axis.
     * @param y Position by Y-axis.
     * @param z Position by Z-axis.
     * @return Grid index.
     */
    GridIndex getGridIndexByPosition(double x, double y, double z) const;

    /**
     * @brief Getter for grid index by spatial position of some object.
     * @param point `CGAL::Point_3` point.
     * @return Grid index.
     */
    GridIndex getGridIndexByPosition(Point const &point) const;

    /// @return The total number of cells.
    constexpr size_t size() const { return static_cast<size_t>(m_divisionsX * m_divisionsY * m_divisionsZ); }

    /// @return The edge size of the cells.
    constexpr double edgeSize() const { return m_cubeEdgeSize; }

    /// @brief Prints a list of which tetrahedrons intersect with which grid cells.
    void printGrid() const;

    /**
     * @brief Retrieves the mesh parameters for a tetrahedron given its ID.
     * @param tetrahedronId The ID of the tetrahedron.
     * @return The mesh parameters for the specified tetrahedron.
     */
    MeshTetrahedronParam getTetrahedronMeshParamById(size_t tetrahedronId) const;

    /**
     * @brief Retrieves the list of tetrahedrons that intersect a specific grid cell.
     * @param index The index of the grid cell.
     * @return A vector of tetrahedrons that intersect with the specified cell.
     */
    MeshTetrahedronParamVector getTetrahedronsByGridIndex(GridIndex const &index) const;
};

#endif // !GRID3D_HPP
