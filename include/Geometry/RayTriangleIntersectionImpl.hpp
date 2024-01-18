#ifndef RAYTRIANGLEINTERSECTIONIMPL_HPP
#define RAYTRIANGLEINTERSECTIONIMPL_HPP

template <typename T>
constexpr bool
RayTriangleIntersection<T>::isIntersectTriangle(Ray<T> const &ray, Triangle<T> const &triangle)
{
    return CGAL::do_intersect(ray.getRayCGAL(), triangle.getTriangleCGAL());
}

template <typename T>
constexpr std::optional<Point<T>>
RayTriangleIntersection<T>::getIntersectionPoint(Ray<T> const &ray, Triangle<T> const &triangle)
{
    auto result{CGAL::intersection(ray.getRayCGAL(), triangle.getTriangleCGAL())};
    if (!result)
        return std::nullopt;

    // Intersection is a point
    if (Point3 const *p{boost::get<Point3>(boost::addressof(*result))})
        return Point<T>(CGAL::to_double(p->x()),
                        CGAL::to_double(p->y()),
                        CGAL::to_double(p->z()));
    else
        return std::nullopt;
}

#endif // !RAYTRIANGLEINTERSECTIONIMPL_HPP
