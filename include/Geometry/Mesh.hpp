#ifndef MESH_HPP
#define MESH_HPP

#include <optional>
#include <string_view>
#include <tuple>
#include <vector>

#include "RayTriangleIntersection.hpp"

/**
 * @brief Represents triangle mesh parameters (for surfaces):
 * int, double, double, double, double, double, double, double, double, double, double, int.
 * id,  x1,     y1,     z1,     x2,     y2,     z2,     x3,     y3,     z3,     dS,     counter.
 * `counter` is counter of settled objects on specific triangle (defines by its `id` field).
 */
using MeshParam = std::tuple<size_t, Triangle3, double, int>;
using MeshParamVector = std::vector<MeshParam>;

/// @brief Represents GMSH mesh.
class Mesh
{
private:
    static size_t isRayIntersectTriangleImpl(Ray3 const &ray, MeshParam const &triangle);
    static std::optional<std::tuple<size_t, Point3>>
    getIntersectionPointImpl(Ray3 const &ray, MeshParam const &triangle);

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
     * @return MeshParams A vector containing information about each triangle in the mesh.
     */
    static MeshParamVector getMeshParams(std::string_view msh_filename);

    /**
     * @brief Determines if a ray intersects with a given triangle in the mesh.
     *
     * @details This function utilizes the `isIntersectTriangle` method from the `RayTriangleIntersection`
     *          class or namespace to check for an intersection between a ray and a triangle. It is used
     *          to identify whether a given ray intersects with a specific triangle within the mesh, which
     *          can be useful in various applications like ray tracing, collision detection, or physics simulations.
     *
     * @param ray The ray to be tested for intersection. This should be an instance of `RayD`,
     *            which is a template specialization of `Ray` for `double` type. The ray contains
     *            the information about its origin and direction.
     * @param triangle A tuple representing the triangle with which the intersection test is to be performed.
     *                 The tuple contains the triangle's parameters, which likely include its vertices
     *                 and other relevant geometric data.
     *
     * @return Returns the index or ID of the triangle (as size_t) if the ray intersects with it.
     *         If there is no intersection, it returns a special value (usually -1 cast to size_t) to indicate this.
     */
    static size_t isRayIntersectTriangle(Ray3 const &ray, MeshParam const &triangle) { return isRayIntersectTriangleImpl(ray, triangle); }
    static size_t isRayIntersectTriangle(Ray3 &&ray, MeshParam const &triangle) { return isRayIntersectTriangleImpl(std::move(ray), triangle); }
    static size_t isRayIntersectTriangle(Ray3 const &ray, MeshParam &&triangle) { return isRayIntersectTriangleImpl(ray, std::move(triangle)); }
    static size_t isRayIntersectTriangle(Ray3 &&ray, MeshParam &&triangle) { return isRayIntersectTriangleImpl(std::move(ray), std::move(triangle)); }

    /**
     * @brief Gets intersection point of ray and triangle if ray intersects the triangle.
     * @param ray The ray to check for intersection with the triangle.
     * @param triangle MeshParam representing the triangle with which the line segment
     *                 is tested for intersection. It includes the necessary parameters to define
     *                 a triangle in 3D space.
     *
     * @return Returns the ID of the triangle where the particle has settled if an intersection occurs
     *         and intersection point.
     *         If the particle doesn't intersect with the specified triangle, it returns `std::nullopt`
     */
    static std::optional<std::tuple<size_t, Point3>>
    getIntersectionPoint(Ray3 const &ray, MeshParam const &triangle) { return getIntersectionPointImpl(ray, triangle); }
    static std::optional<std::tuple<size_t, Point3>>
    getIntersectionPoint(Ray3 &&ray, MeshParam const &triangle) { return getIntersectionPointImpl(std::move(ray), triangle); }
    static std::optional<std::tuple<size_t, Point3>>
    getIntersectionPoint(Ray3 const &ray, MeshParam &&triangle) { return getIntersectionPointImpl(ray, std::move(triangle)); }
    static std::optional<std::tuple<size_t, Point3>>
    getIntersectionPoint(Ray3 &&ray, MeshParam &&triangle) { return getIntersectionPointImpl(std::move(ray), std::move(triangle)); }
};

#endif // !MESH_HPP
