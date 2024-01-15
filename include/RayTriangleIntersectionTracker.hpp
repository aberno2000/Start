#ifndef RAYTRIANGLEINTERSECTIONTRACKER_HPP
#define RAYTRIANGLEINTERSECTIONTRACKER_HPP

#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/intersections.h>

using K = CGAL::Exact_predicates_exact_constructions_kernel;
using Ray3 = K::Ray_3;
using Triangle3 = K::Triangle_3;
using Point3 = K::Point_3;

/// @brief Class for tracking ray-surface intersections using CGAL
class RayTriangleIntersectionTracker
{
private:
    Triangle3 m_triangle;

public:
    /**
     * @brief Set a single triangle for intersection testing.
     * @details This method sets the triangle to be tested for intersection with a ray.
     *          The triangle is defined by three points in 3D space.
     * @param A First vertex of the triangle.
     * @param B Second vertex of the triangle.
     * @param C Third vertex of the triangle.
     */
    void setTriangle(Point3 const &A, Point3 const &B, Point3 const &C) { m_triangle = Triangle3(A, B, C); }

    /**
     * @brief Check if a ray intersects with the set triangle.
     * @details Determines whether the specified ray intersects with the currently set triangle.
     *          This function utilizes CGAL's intersection checking functionality.
     * @param ray The ray to be checked for intersection with the triangle.
     * @return True if the ray intersects the triangle, false otherwise.
     */
    bool isIntersect(const Ray3 &ray) const { return CGAL::do_intersect(ray, m_triangle); }
};

#endif // !RAYTRIANGLEINTERSECTIONTRACKER_HPP
