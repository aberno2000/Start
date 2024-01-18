#ifndef POINT_HPP
#define POINT_HPP

#include <cmath>
#include <iostream>
#include <concepts>

/**
 * @brief Template class representing a point in 3D space.
 * @tparam T Numeric type, must be a floating point type.
 */
template <typename T>
class Point
{
    static_assert(std::is_floating_point_v<T>, "Point class can only be used with floating point types");

public:
    T x; // X-coordinate of the point.
    T y; // Y-coordinate of the point.
    T z; // Z-coordinate of the point.

    Point();
    Point(T x, T y, T z);

    Point(Point const &other) = default;
    Point &operator=(Point const &other) = default;

    T distance(const Point &other) const;

    // Overloaded stream operators
    template <typename U>
    friend std::ostream &operator<<(std::ostream &os, Point<U> const &point);
    template <typename U>
    friend std::istream &operator>>(std::istream &is, Point &point);
};

#include "PointImpl.hpp"

#endif // !POINT_HPP
