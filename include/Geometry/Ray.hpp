#ifndef RAY_HPP
#define RAY_HPP

#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/intersections.h>
#include <optional>

#include "Point.hpp"

using Kernel = CGAL::Exact_predicates_exact_constructions_kernel;
using Point3 = Kernel::Point_3;
using Ray3 = Kernel::Ray_3;
using Triangle3 = Kernel::Triangle_3;

/**
 * @brief Class representing a Ray in 3D space.
 * @details The Ray is defined by an origin point and a direction vector.
 */
template <typename T>
class Ray
{
private:
    Point<T> m_A; // The 1st point of the ray.
    Point<T> m_B; // The 2nd point of the ray.
    Ray3 m_ray;   // CGAL ray.

public:
    Ray(Point<T> const &A, Point<T> const &B);
    Ray(Point<T> &&A, Point<T> &&B) noexcept;

    /* --> Getters for points of ray. <-- */
    constexpr Point<T> const &getA() const;
    constexpr Point<T> const &getB() const;

    /* ::: Getter for CGAL object of the ray with {x,y,z}. ::: */
    constexpr Ray3 const &getRayCGAL() const;
};

#include "RayImpl.hpp"

#endif // !RAY_HPP
