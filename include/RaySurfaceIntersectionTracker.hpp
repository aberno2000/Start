#ifndef RAYSURFACEINTERSECTIONTRACKER_HPP
#define RAYSURFACEINTERSECTIONTRACKER_HPP

#include <CGAL/AABB_traits.h>
#include <CGAL/AABB_tree.h>
#include <CGAL/AABB_triangle_primitive.h>
#include <CGAL/Simple_cartesian.h>
#include <optional>
#include <vector>

using K = CGAL::Simple_cartesian<double>;
using Point3 = K::Point_3;
using Ray3 = K::Ray_3;
using Triangle3 = K::Triangle_3;

/// @brief Class for tracking ray-surface intersections using CGAL
class RaySurfaceIntersectionTracker
{
private:
    using Tree = CGAL::AABB_tree<CGAL::AABB_traits<K, CGAL::AABB_triangle_primitive<K, std::vector<Triangle3>::iterator>>>;

    Tree m_tree;

public:
    /**
     * @brief Constructor for RaySurfaceIntersectionTracker.
     * @details Initializes the tracker with a list of triangles representing the surface.
     * @param surface_triangles List of triangles representing the surface.
     */
    RaySurfaceIntersectionTracker(std::vector<Triangle3> &surface_triangles)
        : m_tree(surface_triangles.begin(), surface_triangles.end())
    {
        m_tree.accelerate_distance_queries();
    }

    /**
     * @brief Tracks the intersection of a ray with the surface.
     * @details Checks if the given ray intersects with the surface and returns the point of intersection.
     * @param ray Ray to be checked for intersection.
     * @return Optional point of intersection, empty if no intersection.
     */
    std::optional<Point3> trackIntersection(const Ray3 &ray) const
    {
        auto intersection{m_tree.first_intersection(ray)};
        if (intersection)
        {
            auto &variant{intersection->first};
            if (Point3 const *p{boost::get<Point3>(&variant)})
                return *p;
        }
        return std::nullopt;
    }
};

#endif // !RAYSURFACEINTERSECTIONTRACKER_HPP
