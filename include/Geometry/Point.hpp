#ifndef POINT_HPP
#define POINT_HPP

#include <cmath>
#include <concepts>
#include <iostream>

/**
 * @brief Template class representing a point in 3D space.
 * @tparam T Numeric type, must be a floating point type or an integral type.
 * @warning All non-floating types implicitly will converted to `double` by default.
 */
template <typename T>
class Point
{
    static_assert(std::is_floating_point_v<T>,
                  "Point class template requires a floating-point type (float, double, long double)");

public:
    T x; // X-coordinate of the point.
    T y; // Y-coordinate of the point.
    T z; // Z-coordinate of the point.

    Point();
    Point(T, T, T);

    Point(Point const &other) = default;
    Point &operator=(Point const &other) = default;

    T distance(Point const &other) const;
    
    template <typename U>
    friend std::ostream &operator<<(std::ostream &os, Point<U> const &point);
    template <typename U>
    friend std::istream &operator>>(std::istream &is, Point &point);
};

#include "PointImpl.hpp"

#endif // !POINT_HPP
