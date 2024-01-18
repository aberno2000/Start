#ifndef MESHIMPL_HPP
#define MESHIMPL_HPP

#include <gmsh.h>

inline void Mesh::setMeshSize(double meshSizeFactor) { gmsh::option::setNumber("Mesh.MeshSizeFactor", meshSizeFactor); }

inline MeshParamVector Mesh::getMeshParams(std::string_view msh_filename)
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

            double a{std::sqrt(std::pow(xyz1[0] - xyz2[0], 2) + std::pow(xyz1[1] - xyz2[1], 2) + std::pow(xyz1[2] - xyz2[2], 2))},
                b{std::sqrt(std::pow(xyz1[0] - xyz3[0], 2) + std::pow(xyz1[1] - xyz3[1], 2) + std::pow(xyz1[2] - xyz3[2], 2))},
                c{std::sqrt(std::pow(xyz2[0] - xyz3[0], 2) + std::pow(xyz2[1] - xyz3[1], 2) + std::pow(xyz2[2] - xyz3[2], 2))};

            double s{(a + b + c) / 2},
                dS{std::sqrt(s * (s - a) * (s - b) * (s - c))};

            result.emplace_back(std::make_tuple(triangleId,
                                                Triangle(Point(xyz1[0], xyz1[1], xyz1[2]),
                                                         Point(xyz2[0], xyz2[1], xyz2[2]),
                                                         Point(xyz3[0], xyz3[1], xyz3[2])),
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

inline size_t Mesh::isRayIntersectTriangle(RayD const &ray, MeshParam const &triangle)
{
    return (RayTriangleIntersection<double>::isIntersectTriangle(ray, std::get<1>(triangle)))
               ? std::get<0>(triangle)
               : -1ul;
}

inline std::optional<std::tuple<size_t, PointD>>
Mesh::getIntersectionPoint(RayD const &ray, MeshParam const &triangle)
{
    auto ip(RayTriangleIntersection<double>::getIntersectionPoint(ray, std::get<1>(triangle)));
    if (!ip)
        return std::nullopt;
    return std::make_tuple(std::get<0>(triangle), *ip);
}

#endif // !MESHIMPL_HPP
