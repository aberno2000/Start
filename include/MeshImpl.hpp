#ifndef MESHIMPL_HPP
#define MESHIMPL_HPP

#include <gmsh.h>
#include <iostream>

#include "RaySurfaceIntersectionTracker.hpp"

inline void Mesh::setMeshSize(double meshSizeFactor) { gmsh::option::setNumber("Mesh.MeshSizeFactor", meshSizeFactor); }

inline TriangleMeshParamVector Mesh::getMeshParams(std::string_view msh_filename)
{
    TriangleMeshParamVector result;
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

            result.emplace_back(std::make_tuple(triangleId, PositionVector(xyz1[0], xyz1[1], xyz1[2]),
                                                PositionVector(xyz2[0], xyz2[1], xyz2[2]),
                                                PositionVector(xyz3[0], xyz3[1], xyz3[2]), dS, 0));
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

inline size_t Mesh::intersectLineTriangle(PositionVector const &prevPointPosition,
                                          PositionVector const &nextPointPosition,
                                          TriangleMeshParam const &triangle)
{
    Point3 start{prevPointPosition.getX(), prevPointPosition.getY(), prevPointPosition.getZ()},
        end{nextPointPosition.getX(), nextPointPosition.getY(), nextPointPosition.getZ()};
    Ray3 ray{start, end - start};

    PositionVector const &A{std::get<1>(triangle)},
        &B{std::get<2>(triangle)},
        &C{std::get<3>(triangle)};
    Point3 vertexA{A.getX(), A.getY(), A.getZ()},
        vertexB{B.getX(), B.getY(), B.getZ()},
        vertexC{C.getX(), C.getY(), C.getZ()};

    Triangle3 cgal_triangle{vertexA, vertexB, vertexC};
    std::vector<Triangle3> cgal_triangles{{cgal_triangle}};
    RaySurfaceIntersectionTracker tracker(cgal_triangles);

    // Return the triangle ID if an intersection occurs
    auto intersection{tracker.trackIntersection(ray)};
    if (intersection)
        return std::get<0>(triangle);

    // Return max value of size_t if no intersection
    return std::numeric_limits<size_t>::max();
}

#endif // !MESHIMPL_HPP
