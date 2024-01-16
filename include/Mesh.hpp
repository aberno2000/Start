#ifndef MESH_HPP
#define MESH_HPP

#include <concepts>
#include <optional>
#include <string_view>
#include <tuple>
#include <vector>

#include "Ray.hpp"

/**
 * @brief Represents triangle mesh parameters (for surfaces):
 * int, double, double, double, double, double, double, double, double, double, double, int,     {double, double, double}.
 * id,  x1,     y1,     z1,     x2,     y2,     z2,     x3,     y3,     z3,     dS,     counter, triangle surface coefs.
 * `counter` is counter of settled objects on specific triangle (defines by its `id` field).
 */
using TriangleMeshParam = std::tuple<size_t, PositionVector,
                                     PositionVector,
                                     PositionVector,
                                     double, int>;
using TriangleMeshParamVector = std::vector<TriangleMeshParam>;

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
    static void setMeshSize(double meshSizeFactor);

    /**
     * @brief Retrieves parameters from a Gmsh mesh file.
     * This function reads information about triangles from a Gmsh .msh file.
     * It calculates triangle properties such as coordinates, side lengths, area, etc.
     * @param msh_filename The filename of the Gmsh .msh file to parse.
     * @return TriangleMeshParams A vector containing information about each triangle in the mesh.
     */
    static TriangleMeshParamVector getMeshParams(std::string_view msh_filename);

    /**
     * @brief Checks if a line segment intersects with a given triangle in 3D space.
     *
     * @details This function determines if a line segment, defined by two points (previous and next centers),
     *          intersects a specified triangle. The triangle is defined by its mesh parameters. This is commonly
     *          used in simulations, collision detection, or graphics rendering to understand interactions between
     *          moving objects (like particles) and static structures (like meshes).
     *
     * @param ray The ray to check for intersection with the triangle.
     * @param triangle TriangleMeshParam representing the triangle with which the line segment
     *                 is tested for intersection. It includes the necessary parameters to define
     *                 a triangle in 3D space.
     *
     * @return Returns the ID of the triangle where the particle has settled if an intersection occurs.
     *         If the particle doesn't intersect with the specified triangle, it returns the max value
     *         of `size_t`.
     */
    static size_t isRayIntersectsTriangle(Ray const &ray, TriangleMeshParam const &triangle);

    /**
     * @brief Gets intersection point of ray and triangle if ray intersects the triangle.
     * @param ray The ray to check for intersection with the triangle.
     * @param triangle TriangleMeshParam representing the triangle with which the line segment
     *                 is tested for intersection. It includes the necessary parameters to define
     *                 a triangle in 3D space.
     *
     * @return Returns the ID of the triangle where the particle has settled if an intersection occurs
     *         and intersection point.
     *         If the particle doesn't intersect with the specified triangle, it returns `std::nullopt`
     */
    static std::optional<std::tuple<size_t, PositionVector>>
    getRayIntersectsTriangle(Ray const &ray, TriangleMeshParam const &triangle);
};

#include "MeshImpl.hpp"

#endif // !MESH_HPP
