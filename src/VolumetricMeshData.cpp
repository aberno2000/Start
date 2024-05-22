#include <gmsh.h>
#include <memory>
#include <mutex>

#include "../include/DataHandling/VolumetricMeshData.hpp"

std::unique_ptr<VolumetricMeshData> VolumetricMeshData::instance;
std::mutex VolumetricMeshData::instanceMutex;

Point VolumetricMeshData::TetrahedronData::getTetrahedronCenter() const
{
    try
    {
        double x{}, y{}, z{};
        for (auto const &node : nodes)
        {
            x += node.nodeCoords.x();
            y += node.nodeCoords.y();
            z += node.nodeCoords.z();
        }
        return Point{x / 4.0, y / 4.0, z / 4.0};
    }
    catch (std::exception const &e)
    {
        throw std::runtime_error(util::stringify("Error computing tetrahedron center: ", e.what()));
    }
}

VolumetricMeshData::VolumetricMeshData(std::string_view mesh_filename)
{
    try
    {
        gmsh::open(mesh_filename.data());

        std::vector<std::size_t> nodeTags;
        std::vector<double> coord, parametricCoord;
        gmsh::model::mesh::getNodes(nodeTags, coord, parametricCoord, -1, -1, false, false);

        std::map<size_t, std::array<double, 3>> nodeCoordinatesMap;
        for (size_t i{}; i < nodeTags.size(); ++i)
        {
            size_t nodeID{nodeTags[i]};
            std::array<double, 3> coords = {coord[i * 3 + 0], coord[i * 3 + 1], coord[i * 3 + 2]};
            nodeCoordinatesMap[nodeID] = coords;
        }

        std::vector<size_t> elTags, nodeTagsByEl;
        gmsh::model::mesh::getElementsByType(4, elTags, nodeTagsByEl, -1);

        for (size_t i{}; i < elTags.size(); ++i)
        {
            size_t tetrahedronID{elTags[i]};
            std::array<size_t, 4> nodes = {
                nodeTagsByEl[i * 4 + 0],
                nodeTagsByEl[i * 4 + 1],
                nodeTagsByEl[i * 4 + 2],
                nodeTagsByEl[i * 4 + 3]};

            std::array<Point, 4> vertices;
            for (size_t j{}; j < 4; ++j)
            {
                auto coords{nodeCoordinatesMap.at(nodes[j])};
                vertices[j] = Point(coords[0], coords[1], coords[2]);
            }

            Tetrahedron tetrahedron(vertices[0], vertices[1], vertices[2], vertices[3]);
            TetrahedronData data{tetrahedronID, tetrahedron, {}, std::nullopt};

            for (size_t j{}; j < nodes.size(); ++j)
                data.nodes[j] = {nodes[j], vertices[j], std::nullopt, std::nullopt};

            m_meshComponents.emplace_back(data);
        }
    }
    catch (std::exception const &e)
    {
        throw std::runtime_error(util::stringify("Error initializing VolumetricMeshData: ", e.what()));
    }
}

VolumetricMeshData &VolumetricMeshData::getInstance(std::string_view mesh_filename)
{
    std::lock_guard<std::mutex> lock(instanceMutex);
    if (instance == nullptr)
        instance = std::unique_ptr<VolumetricMeshData>(new VolumetricMeshData(mesh_filename));
    return *instance;
}

void VolumetricMeshData::print() const noexcept
{
    for (auto const &meshComponent : m_meshComponents)
    {
        std::cout << std::format("Tetrahedron[{}]\n", meshComponent.globalTetraId);
        for (short i{}; i < 4; ++i)
        {
            std::cout << std::format("Vertex[{}]: ({}, {}, {})\n", meshComponent.nodes.at(i).globalNodeId,
                                     meshComponent.nodes.at(i).nodeCoords.x(),
                                     meshComponent.nodes.at(i).nodeCoords.y(),
                                     meshComponent.nodes.at(i).nodeCoords.z());
            if (meshComponent.nodes.at(i).nablaPhi)
            {
                std::cout << std::format("  ∇φ: ({}, {}, {})\n",
                                         meshComponent.nodes.at(i).nablaPhi->x(),
                                         meshComponent.nodes.at(i).nablaPhi->y(),
                                         meshComponent.nodes.at(i).nablaPhi->z());
            }
            else
                std::cout << "  ∇φ: empty\n";

            if (meshComponent.nodes.at(i).potential)
                std::cout << std::format(" Potential φ: {}\n", meshComponent.nodes.at(i).potential.value());
            else
                std::cout << "  Potential φ: empty\n";
        }
        if (meshComponent.electricField)
        {
            std::cout << std::format("ElectricField: ({}, {}, {})\n",
                                     meshComponent.electricField->x(),
                                     meshComponent.electricField->y(),
                                     meshComponent.electricField->z());
        }
        else
            std::cout << "ElectricField: empty\n";
    }
    std::endl(std::cout);
}

std::optional<VolumetricMeshData::TetrahedronData> VolumetricMeshData::getMeshDataByTetrahedronId(size_t globalTetrahedronId) const
{
    auto it{std::ranges::find_if(m_meshComponents, [globalTetrahedronId](const TetrahedronData &data)
                                 { return data.globalTetraId == globalTetrahedronId; })};
    if (it != m_meshComponents.cend())
        return *it;
    return std::nullopt;
}

void VolumetricMeshData::assignNablaPhi(size_t tetrahedronId, size_t nodeId, Point const &gradient)
{
    auto it{std::ranges::find_if(m_meshComponents, [tetrahedronId](const TetrahedronData &data)
                                 { return data.globalTetraId == tetrahedronId; })};
    if (it != m_meshComponents.cend())
    {
        for (auto &node : it->nodes)
        {
            if (node.globalNodeId == nodeId)
            {
                node.nablaPhi = gradient;
                return;
            }
        }
    }
}

void VolumetricMeshData::assignPotential(size_t nodeId, double potential)
{
    for (auto &tetrahedron : m_meshComponents)
        for (auto &node : tetrahedron.nodes)
            if (node.globalNodeId == nodeId)
                node.potential = potential;
}

void VolumetricMeshData::assignElectricField(size_t tetrahedronId, Point const &electricField)
{
    auto it{std::ranges::find_if(m_meshComponents, [tetrahedronId](const TetrahedronData &data)
                                 { return data.globalTetraId == tetrahedronId; })};
    if (it != m_meshComponents.end())
    {
        it->electricField = electricField;
    }
}

std::map<size_t, std::vector<size_t>> VolumetricMeshData::getTetrahedronNodesMap()
{
    std::map<size_t, std::vector<size_t>> tetrahedronNodesMap;

    for (auto const &meshData : m_meshComponents)
        for (short i{}; i < 4; ++i)
            tetrahedronNodesMap[meshData.globalTetraId].emplace_back(meshData.nodes.at(i).globalNodeId);

    if (tetrahedronNodesMap.empty())
        WARNINGMSG("Tetrahedron - nodes map is empty");
    return tetrahedronNodesMap;
}

std::map<size_t, std::vector<size_t>> VolumetricMeshData::getNodeTetrahedronsMap()
{
    std::map<size_t, std::vector<size_t>> nodeTetrahedronsMap;

    for (auto const &meshData : m_meshComponents)
        for (short i{}; i < 4; ++i)
            nodeTetrahedronsMap[meshData.nodes.at(i).globalNodeId].emplace_back(meshData.globalTetraId);

    if (nodeTetrahedronsMap.empty())
        WARNINGMSG("Node - tetrahedrons map is empty");
    return nodeTetrahedronsMap;
}

std::map<size_t, Point> VolumetricMeshData::getTetrahedronCenters()
{
    std::map<size_t, Point> tetraCentres;

    for (auto const &meshData : m_meshComponents)
        tetraCentres[meshData.globalTetraId] = meshData.getTetrahedronCenter();

    if (tetraCentres.empty())
        WARNINGMSG("Tetrahedron centres map is empty");
    return tetraCentres;
}
