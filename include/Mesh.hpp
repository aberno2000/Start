#ifndef MESH_HPP
#define MESH_HPP

#include <concepts>
#include <string_view>
#include <tuple>
#include <vector>

/**
 * @brief Represents triangle mesh parameters (for surfaces):
 * int, double, double, double, double, double, double, double, double, double, double, int.
 * id,  x1,     y1,     z1,     x2,     y2,     z2,     x3,     y3,     z3,     dS,     counter.
 * `counter` is counter of settled objects on specific triangle (defines by its `id` field).
 */
using TriangleMeshParams = std::vector<std::tuple<int, double, double, double,
                                                  double, double, double,
                                                  double, double, double,
                                                  double, int>>;

/// @brief Represents GMSH mesh.
class Mesh
{
public:
    /**
     * @brief Sets the mesh size factor (globally -> for all objects).
     * This method sets the mesh size factor for generating the mesh.
     * The mesh size factor controls the size of mesh elements in the mesh.
     * @param meshSizeFactor The factor to set for mesh size.
     */
    void setMeshSize(double meshSizeFactor);

    /**
     * @brief Retrieves parameters from a Gmsh mesh file.
     * This function reads information about triangles from a Gmsh .msh file.
     * It calculates triangle properties such as coordinates, side lengths, area, etc.
     * @param msh_filename The filename of the Gmsh .msh file to parse.
     * @return TriangleMeshParams A vector containing information about each triangle in the mesh.
     */
    TriangleMeshParams getMeshParams(std::string_view msh_filename);
};

#endif // !MESH_HPP
