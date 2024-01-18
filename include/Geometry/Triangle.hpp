#ifndef TRIANGLE_HPP
#define TRIANGLE_HPP

#include <CGAL/Exact_predicates_exact_constructions_kernel.h>

#include "Point.hpp"

using Kernel = CGAL::Exact_predicates_exact_constructions_kernel;
using Point3 = Kernel::Point_3;
using Triangle3 = Kernel::Triangle_3;

template <typename T>
class Triangle
{
private:
    Point<T> m_A;
    Point<T> m_B;
    Point<T> m_C;

    Triangle3 m_triangle; // CGAL triangle.

public:
    Triangle(Point<T> const &A, Point<T> const &B, Point<T> const &C);
    Triangle(Point<T> &&A, Point<T> &&B, Point<T> &&C) noexcept;

    /* --> Getters for points of triangle. <-- */
    constexpr Point<T> const &getA() const;
    constexpr Point<T> const &getB() const;
    constexpr Point<T> const &getC() const;

    /* ::: Getter for CGAL object of the triangle with {x,y,z}. ::: */
    constexpr Triangle3 const &getTriangleCGAL() const;
};

#include "TriangleImpl.hpp"

#endif // !TRIANGLE_HPP
