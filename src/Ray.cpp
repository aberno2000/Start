#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/intersections.h>
#include <limits>

using Kernel = CGAL::Exact_predicates_exact_constructions_kernel;
using Ray3 = Kernel::Ray_3;
using Triangle3 = Kernel::Triangle_3;
using Point3 = Kernel::Point_3;

#include "../include/Ray.hpp"

Ray::Ray(PositionVector const &A, PositionVector const &B)
    : m_A(A), m_B(B) {}

Ray::Ray(PositionVector &&A, PositionVector &&B) noexcept
    : m_A(std::move(A)), m_B(std::move(B)) {}

PositionVector const &Ray::getA() const { return m_A; }

PositionVector const &Ray::getB() const { return m_B; }

bool Ray::isIntersectsTriangle(PositionVector const &vertexA,
                               PositionVector const &vertexB,
                               PositionVector const &vertexC) const
{
    return CGAL::do_intersect(Ray3(Point3(m_A.getX(),
                                          m_A.getY(),
                                          m_A.getZ()),
                                   Point3(m_B.getX(),
                                          m_B.getY(),
                                          m_B.getZ())),
                              Triangle3(Point3(vertexA.getX(), vertexA.getY(), vertexA.getZ()),
                                        Point3(vertexB.getX(), vertexB.getY(), vertexB.getZ()),
                                        Point3(vertexC.getX(), vertexC.getY(), vertexC.getZ())));
}
