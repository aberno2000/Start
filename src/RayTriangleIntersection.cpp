#include "../include/Geometry/RayTriangleIntersection.hpp"

bool RayTriangleIntersection::isIntersectTriangleImpl(Ray3 const &ray, Triangle3 const &triangle)
{
    return CGAL::do_intersect(ray, triangle);
}

std::optional<Point3> RayTriangleIntersection::getIntersectionPointImpl(Ray3 const &ray, Triangle3 const &triangle)
{
    auto result{CGAL::intersection(ray, triangle)};
    if (!result)
        return std::nullopt;

    // Intersection is a point
    if (Point3 const *p{boost::get<Point3>(boost::addressof(*result))})
        return Point3(p->x(), p->y(), p->z());
    else
        return std::nullopt;
}
