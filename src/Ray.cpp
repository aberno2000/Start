#include <limits>

#include "../include/Ray.hpp"

Ray::Ray(PositionVector const &A, PositionVector const &B)
    : m_A(A), m_B(B), m_ray(Ray3(Point3(m_A.getX(),
                                        m_A.getY(),
                                        m_A.getZ()),
                                 Point3(m_B.getX(),
                                        m_B.getY(),
                                        m_B.getZ()))) {}

Ray::Ray(PositionVector &&A, PositionVector &&B) noexcept
    : m_A(std::move(A)), m_B(std::move(B)), m_ray(Ray3(Point3(m_A.getX(),
                                                              m_A.getY(),
                                                              m_A.getZ()),
                                                       Point3(m_B.getX(),
                                                              m_B.getY(),
                                                              m_B.getZ()))) {}

PositionVector const &Ray::getA() const { return m_A; }

PositionVector const &Ray::getB() const { return m_B; }

bool Ray::isIntersectsTriangle(PositionVector const &vertexA,
                               PositionVector const &vertexB,
                               PositionVector const &vertexC) const
{
    Triangle3 cgal_triangle{Point3(vertexA.getX(), vertexA.getY(), vertexA.getZ()),
                            Point3(vertexB.getX(), vertexB.getY(), vertexB.getZ()),
                            Point3(vertexC.getX(), vertexC.getY(), vertexC.getZ())};
    return CGAL::do_intersect(m_ray, cgal_triangle);
}

std::optional<PositionVector> Ray::getIntersectionPoint(PositionVector const &vertexA,
                                                        PositionVector const &vertexB,
                                                        PositionVector const &vertexC) const
{
    Triangle3 cgal_triangle{Point3(vertexA.getX(), vertexA.getY(), vertexA.getZ()),
                            Point3(vertexB.getX(), vertexB.getY(), vertexB.getZ()),
                            Point3(vertexC.getX(), vertexC.getY(), vertexC.getZ())};
    auto result{CGAL::intersection(m_ray, cgal_triangle)};

    // Intersection is a point
    if (Point3 const *p{boost::get<Point3>(std::addressof(*result))})
        return PositionVector(CGAL::to_double(p->x()),
                              CGAL::to_double(p->y()),
                              CGAL::to_double(p->z()));
    else
        return std::nullopt;
}
