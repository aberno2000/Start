#include <algorithm>
#include <boost/dynamic_bitset.hpp>
#include <ranges>
#include <utility>
#include <vector>

#include "../include/ParticleInCell/Grid3D.hpp"

Grid3D::Grid3D(VolumetricMeshData const &meshData, double edgeSize)
    : m_cubeEdgeSize(edgeSize), m_meshData(meshData)
{
    if (m_meshData.empty())
        return;

    // 1. Defining one common boundary box by merging all bboxes of tetrahedrons
    m_commonBbox = m_meshData.getMeshComponents().front().tetrahedron.bbox();
    for (const auto &tetrahedronData : m_meshData.getMeshComponents())
        m_commonBbox += tetrahedronData.tetrahedron.bbox();

    // 2. Calculating divisions for each axis
    m_divisionsX = static_cast<short>(std::ceil((m_commonBbox.xmax() - m_commonBbox.xmin()) / m_cubeEdgeSize));
    m_divisionsY = static_cast<short>(std::ceil((m_commonBbox.ymax() - m_commonBbox.ymin()) / m_cubeEdgeSize));
    m_divisionsZ = static_cast<short>(std::ceil((m_commonBbox.zmax() - m_commonBbox.zmin()) / m_cubeEdgeSize));

    // 3. Limitation on grid cells
    if (m_divisionsX * m_divisionsY * m_divisionsZ > MAX_GRID_SIZE)
        throw std::runtime_error("The grid is too small, you risk to overflow your memory with it");

    // 4. Mapping each tetrahedron with cells
    for (const auto &tetrahedronData : m_meshData.getMeshComponents())
    {
        for (short x = 0; x < m_divisionsX; ++x)
            for (short y = 0; y < m_divisionsY; ++y)
                for (short z = 0; z < m_divisionsZ; ++z)
                {
                    CGAL::Bbox_3 cellBox(
                        m_commonBbox.xmin() + x * edgeSize,
                        m_commonBbox.ymin() + y * edgeSize,
                        m_commonBbox.zmin() + z * edgeSize,
                        m_commonBbox.xmin() + (x + 1) * edgeSize,
                        m_commonBbox.ymin() + (y + 1) * edgeSize,
                        m_commonBbox.zmin() + (z + 1) * edgeSize);

                    if (CGAL::do_overlap(cellBox, tetrahedronData.tetrahedron.bbox()))
                        m_tetrahedronCells[tetrahedronData.globalTetraId].emplace_back(x, y, z);
                }
    }
}

GridIndex Grid3D::getGridIndexByPosition(double x, double y, double z) const
{
    return {
        std::clamp(short((x - m_commonBbox.xmin()) / m_cubeEdgeSize), short(0), static_cast<short>(m_divisionsX - 1)),
        std::clamp(short((y - m_commonBbox.ymin()) / m_cubeEdgeSize), short(0), static_cast<short>(m_divisionsY - 1)),
        std::clamp(short((z - m_commonBbox.zmin()) / m_cubeEdgeSize), short(0), static_cast<short>(m_divisionsZ - 1))};
}

GridIndex Grid3D::getGridIndexByPosition(Point const &point) const
{
    double x{CGAL_TO_DOUBLE(point.x())},
        y{CGAL_TO_DOUBLE(point.y())},
        z{CGAL_TO_DOUBLE(point.z())};
    return {
        std::clamp(short((x - m_commonBbox.xmin()) / m_cubeEdgeSize), short(0), static_cast<short>(m_divisionsX - 1)),
        std::clamp(short((y - m_commonBbox.ymin()) / m_cubeEdgeSize), short(0), static_cast<short>(m_divisionsY - 1)),
        std::clamp(short((z - m_commonBbox.zmin()) / m_cubeEdgeSize), short(0), static_cast<short>(m_divisionsZ - 1))};
}

bool Grid3D::isInsideTetrahedronMesh(Point const &point) const
{
    auto gridIndex{getGridIndexByPosition(point)};
    auto tetrahedrons{getTetrahedronsByGridIndex(gridIndex)};

    // One cube grid component can return multiple tetrahedra, so we need to fill the vector of checkings with results of checkings.
    boost::dynamic_bitset<> checks(tetrahedrons.size());
    size_t i{};
    for (auto const &tetrahedron : tetrahedrons)
        checks[i++] = Mesh::isPointInsideTetrahedron(point, tetrahedron.tetrahedron);

    // If bitset contains at least one `true` - it means that point is inside the tetrahedron mesh.
    return checks.any();
}

std::vector<VolumetricMeshData::TetrahedronData> Grid3D::getTetrahedronsByGridIndex(GridIndex const &index) const
{
    std::vector<VolumetricMeshData::TetrahedronData> meshParams;
    for (auto const &[tetrId, cells] : m_tetrahedronCells)
        if (std::ranges::find(cells.begin(), cells.end(), index) != cells.end())
            meshParams.push_back(m_meshData.getMeshDataByTetrahedronId(tetrId).value());
    return meshParams;
}

void Grid3D::printGrid() const
{
    for (auto const &[id, cells] : m_tetrahedronCells)
    {
        std::cout << std::format("Tetrahedron[{}] is in cells: ", id);
        for (auto const &[x, y, z] : cells)
            std::cout << std::format("[{}][{}][{}] ", x, y, z);
        std::cout << std::endl;
    }
}
