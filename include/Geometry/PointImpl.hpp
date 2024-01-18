#ifndef POINTIMPL_HPP
#define POINTIMPL_HPP

template <typename T>
Point<T>::Point() : x(T()), y(T()), z(T()) {}

template <typename T>
Point<T>::Point(T x_, T y_, T z_)
    : x(static_cast<T>(x_)), y(static_cast<T>(y_)), z(static_cast<T>(z_)) {}

template <typename T>
T Point<T>::distance(Point<T> const &other) const
{
    return std::sqrt((x - other.x) * (x - other.x) +
                     (y - other.y) * (y - other.y) +
                     (z - other.z) * (z - other.z));
}

template <typename T>
std::ostream &operator<<(std::ostream &os, Point<T> const &point)
{
    os << point.x << ' ' << point.y << ' ' << point.z << '\n';
    return os;
}

template <typename T>
std::istream &operator>>(std::istream &is, Point<T> &point)
{
    is >> point.x >> point.y >> point.z;
    return is;
}

using PointF = Point<float>;
using PointD = Point<double>;

#endif // !POINTIMPL_HPP
