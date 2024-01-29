#include <gmsh.h>

#include "../include/Geometry/MathVector.hpp"
#include "../include/Geometry/Mesh.hpp"

size_t Mesh::isRayIntersectTriangleImpl(Ray3 const &ray, MeshParam const &triangle)
{
    return (RayTriangleIntersection::isIntersectTriangle(ray, std::get<1>(triangle)))
               ? std::get<0>(triangle)
               : -1ul;
}

std::optional<std::tuple<size_t, Point3>>
Mesh::getIntersectionPointImpl(Ray3 const &ray, MeshParam const &triangle)
{
    auto ip(RayTriangleIntersection::getIntersectionPoint(ray, std::get<1>(triangle)));
    if (!ip)
        return std::nullopt;
    return std::make_tuple(std::get<0>(triangle), *ip);
}

double Mesh::calcTetrahedronVolume(MathVector const &a, MathVector const &b, MathVector const &c, MathVector const &d) { return std::abs((c - a).crossProduct(d - a).dotProduct(b - a)) / 6.0; }

void Mesh::setMeshSize(double meshSizeFactor) { gmsh::option::setNumber("Mesh.MeshSizeFactor", meshSizeFactor); }

MeshParamVector Mesh::getMeshParams(std::string_view msh_filename)
{
    MeshParamVector result;
    try
    {
        gmsh::open(msh_filename.data());

        std::vector<size_t> nodeTags;
        std::vector<double> coords, parametricCoords;
        gmsh::model::mesh::getNodes(nodeTags, coords, parametricCoords, -1, -1);

        std::vector<double> xyz;
        for (size_t i{}; i < coords.size(); i += 3)
        {
            xyz.emplace_back(coords[i]);
            xyz.emplace_back(coords[i + 1]);
            xyz.emplace_back(coords[i + 2]);
        }

        std::vector<size_t> elTags, nodeTagsByEl;
        gmsh::model::mesh::getElementsByType(2, elTags, nodeTagsByEl, -1);

        std::vector<std::vector<size_t>> nodeTagsPerEl;
        for (size_t i{}; i < nodeTagsByEl.size(); i += 3)
            nodeTagsPerEl.push_back({nodeTagsByEl[i], nodeTagsByEl[i + 1], nodeTagsByEl[i + 2]});

        for (size_t i{}; i < elTags.size(); ++i)
        {
            size_t triangleId{elTags[i]};
            std::vector<size_t> nodes = nodeTagsPerEl[i];

            std::vector<double> xyz1{{xyz[(nodes[0] - 1) * 3], xyz[(nodes[0] - 1) * 3 + 1], xyz[(nodes[0] - 1) * 3 + 2]}},
                xyz2{{xyz[(nodes[1] - 1) * 3], xyz[(nodes[1] - 1) * 3 + 1], xyz[(nodes[1] - 1) * 3 + 2]}},
                xyz3{{xyz[(nodes[2] - 1) * 3], xyz[(nodes[2] - 1) * 3 + 1], xyz[(nodes[2] - 1) * 3 + 2]}};

            double dS{MathVector::calculateTriangleArea(MathVector(xyz1[0], xyz1[1], xyz1[2]),
                                                        MathVector(xyz2[0], xyz2[1], xyz2[2]),
                                                        MathVector(xyz3[0], xyz3[1], xyz3[2]))};

            result.emplace_back(std::make_tuple(triangleId,
                                                Triangle3(Point3(xyz1[0], xyz1[1], xyz1[2]),
                                                          Point3(xyz2[0], xyz2[1], xyz2[2]),
                                                          Point3(xyz3[0], xyz3[1], xyz3[2])),
                                                dS, 0));
        }
    }
    catch (std::exception const &e)
    {
        std::cerr << e.what() << '\n';
    }
    catch (...)
    {
        std::cerr << "Something went wrong\n";
    }
    return result;
}

double Mesh::getVolumeFromMesh(std::string_view msh_filename)
{
    double result{};
    try
    {
        gmsh::open(msh_filename.data());
        std::vector<size_t> nodeTags;
        std::vector<double> coords, parametricCoords;
        gmsh::model::mesh::getNodes(nodeTags, coords, parametricCoords, -1, -1);

        std::vector<double> xyz;
        for (size_t i{}; i < coords.size(); i += 3)
        {
            xyz.emplace_back(coords[i]);
            xyz.emplace_back(coords[i + 1]);
            xyz.emplace_back(coords[i + 2]);
        }

        std::vector<size_t> elTags, nodeTagsByEl;
        gmsh::model::mesh::getElementsByType(2, elTags, nodeTagsByEl, -1);

        std::vector<std::vector<size_t>> nodeTagsPerEl;
        for (size_t i{}; i < nodeTagsByEl.size(); i += 3)
            nodeTagsPerEl.push_back({nodeTagsByEl[i], nodeTagsByEl[i + 1], nodeTagsByEl[i + 2]});

        for (size_t i{}; i < elTags.size(); ++i)
        {
            std::vector<size_t> nodes = nodeTagsPerEl[i];
            std::vector<double> xyz1{{xyz[(nodes[0] - 1) * 3], xyz[(nodes[0] - 1) * 3 + 1], xyz[(nodes[0] - 1) * 3 + 2]}},
                xyz2{{xyz[(nodes[1] - 1) * 3], xyz[(nodes[1] - 1) * 3 + 1], xyz[(nodes[1] - 1) * 3 + 2]}},
                xyz3{{xyz[(nodes[2] - 1) * 3], xyz[(nodes[2] - 1) * 3 + 1], xyz[(nodes[2] - 1) * 3 + 2]}},
                xyz4{{xyz[(nodes[3] - 1) * 3], xyz[(nodes[3] - 1) * 3 + 1], xyz[(nodes[3] - 1) * 3 + 2]}};

            double dV{calcTetrahedronVolume(MathVector(xyz1[0], xyz1[1], xyz1[2]),
                                            MathVector(xyz2[0], xyz2[1], xyz2[2]),
                                            MathVector(xyz3[0], xyz3[1], xyz3[2]),
                                            MathVector(xyz4[0], xyz4[1], xyz4[2]))};

            result += dV;
        }
    }
    catch (std::exception const &e)
    {
        std::cerr << e.what() << '\n';
    }
    catch (...)
    {
        std::cerr << "Something went wrong\n";
    }
    return result;
}
