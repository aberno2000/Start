#ifndef RAYTRIANGLEINTERSECTION_HPP
#define RAYTRIANGLEINTERSECTION_HPP

#include "CGALTypes.hpp"

class RayTriangleIntersection
{
private:
    [[nodiscard("Ignoring the intersection test result can lead to incorrect geometric or physical computations.")]] static bool
    isIntersectTriangleImpl(Ray const &ray, Triangle const &triangle);

    [[nodiscard("Ignoring the intersection point may lead to incorrect behavior in applications relying on accurate geometric calculations.")]] static std::optional<Point>
    getIntersectionPointImpl(Ray const &ray, Triangle const &triangle);

public:
    /**
     * @brief Checker for ray-triangle intersection.
     * @param ray Ray object.
     * @param triangle Triangle object.
     * @return `true` if ray intersects the triangle, otherwise `false`.
     */
    static bool isIntersectTriangle(Ray const &ray, Triangle const &triangle) { return isIntersectTriangleImpl(ray, triangle); }
    static bool isIntersectTriangle(Ray &&ray, Triangle const &triangle) { return isIntersectTriangleImpl(std::move(ray), triangle); }
    static bool isIntersectTriangle(Ray const &ray, Triangle &&triangle) { return isIntersectTriangleImpl(ray, std::move(triangle)); }
    static bool isIntersectTriangle(Ray &&ray, Triangle &&triangle) { return isIntersectTriangleImpl(std::move(ray), std::move(triangle)); }

    /**
     * @brief Computes the intersection point of the ray with a given triangle.
     * @param ray Ray object.
     * @param triangle Triangle object.
     * @return A `std::optional<Point>` containing the intersection point if it exists;
     * otherwise, `std::nullopt`.
     */
    static std::optional<Point> getIntersectionPoint(Ray const &ray, Triangle const &triangle) { return getIntersectionPointImpl(ray, triangle); }
    static std::optional<Point> getIntersectionPoint(Ray &&ray, Triangle const &triangle) { return getIntersectionPointImpl(std::move(ray), triangle); }
    static std::optional<Point> getIntersectionPoint(Ray const &ray, Triangle &&triangle) { return getIntersectionPointImpl(ray, std::move(triangle)); }
    static std::optional<Point> getIntersectionPoint(Ray &&ray, Triangle &&triangle) { return getIntersectionPointImpl(std::move(ray), std::move(triangle)); }
};

#endif // !RAYTRIANGLEINTERSECTION_HPP
