#ifndef POINTIMPL_HPP
#define POINTIMPL_HPP

template <typename T>
Point<T>::Point() : x(0), y(0), z(0) {}

template <typename T>
Point<T>::Point(T x, T y, T z) : x(x), y(y), z(z) {}

template <typename T>
T Point<T>::distance(const Point &other) const
{
    return std::sqrt((x - other.x) * (x - other.x) +
                     (y - other.y) * (y - other.y) +
                     (z - other.z) * (z - other.z));
}

template <typename T>
std::ostream &operator<<(std::ostream &os, const Point<T> &point)
{
    os << "(" << point.x << ", " << point.y << ", " << point.z << ")";
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
