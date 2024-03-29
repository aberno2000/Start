#include "../include/Geometry/RayTriangleIntersection.hpp"

bool RayTriangleIntersection::isIntersectTriangleImpl(Ray const &ray, Triangle const &triangle)
{
    return CGAL::do_intersect(ray, triangle);
}

std::optional<Point> RayTriangleIntersection::getIntersectionPointImpl(Ray const &ray, Triangle const &triangle)
{
    auto result{CGAL::intersection(ray, triangle)};
    if (!result)
        return std::nullopt;

    // Intersection is a point
    if (Point const *p{boost::get<Point>(boost::addressof(*result))})
        return Point(p->x(), p->y(), p->z());
    else
        return std::nullopt;
}
