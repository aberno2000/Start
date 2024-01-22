#ifndef RAYTRIANGLEINTERSECTION_HPP
#define RAYTRIANGLEINTERSECTION_HPP

#include "../Utilities/Settings.hpp"

class RayTriangleIntersection
{
public:
    /**
     * @brief Checker for ray-triangle intersection.
     * @param ray Ray object.
     * @param triangle Triangle object.
     * @return `true` if ray intersects the triangle, otherwise `false`.
     */
    [[nodiscard("Ignoring the intersection test result can lead to \
    incorrect geometric or physical computations.")]] static bool
    isIntersectTriangle(Ray3 const &ray, Triangle3 const &triangle);

    /**
     * @brief Computes the intersection point of the ray with a given triangle.
     * @param ray Ray object.
     * @param triangle Triangle object.
     * @return A `std::optional<Point>` containing the intersection point if it exists;
     * otherwise, `std::nullopt`.
     */
    [[nodiscard("Ignoring the intersection point may lead to incorrect \
    behavior in applications relying on accurate geometric calculations.")]] static std::optional<Point3>
    getIntersectionPoint(Ray3 const &ray, Triangle3 const &triangle);
};

#endif // !RAYTRIANGLEINTERSECTION_HPP
