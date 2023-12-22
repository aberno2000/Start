#ifndef MATHVECTOR_HPP
#define MATHVECTOR_HPP

#include <cmath>
#include <compare>
#include <format>
#include <iostream>

/**
 * Description of the mathematical vector. In the simplest case, a
 * mathematical object characterized by magnitude and direction.
 *               ->  | x |
 * @brief Vector P = | y |
 *                   | z |
 */
class MathVector
{
private:
    double x{}, // X-axis component of the math vector.
        y{},    // Y-axis component of the math vector.
        z{};    // Z-axis component of the math vector.

public:
    MathVector() {}
    MathVector(double x_, double y_, double z_) : x(x_), y(y_), z(z_) {}

    /**
     * @brief Assignment operator with custom double.
     * Sets all components of vector to custom value.
     */
    MathVector &operator=(double value)
    {
        x = value;
        y = value;
        z = value;
        return *this;
    }

    /**
     * @brief Fills `MathVector` object with specified values.
     * @param x_ X-coordinate of the point.
     * @param y_ Y-coordinate of the point.
     * @param z_ Z-coordinate of the point.
     * @return Filled structure of the Cartesian coordinates.
     */
    static MathVector createCoordinates(double x_, double y_, double z_)
    {
        MathVector cords;

        cords.x = x_;
        cords.y = y_;
        cords.z = z_;

        return cords;
    }

    /* === Getters for each coordinate. === */
    constexpr double getX() const { return x; }
    constexpr double getY() const { return y; }
    constexpr double getZ() const { return z; }

    /* === Setters for each coordinate. === */
    constexpr void setX(double x_) { x = x_; }
    constexpr void setY(double y_) { y = y_; }
    constexpr void setZ(double z_) { z = z_; }

    /// @brief Calculates the module of the vector.
    constexpr double module() const { return std::sqrt(x * x + y * y + z * z); }

    /// @brief Calculates the distance between two vectors.
    constexpr double distance(MathVector const &other) const { return std::sqrt((x - other.x) * (x - other.x) +
                                                                                (y - other.y) * (y - other.y) +
                                                                                (z - other.z) * (z - other.z)); }

    /// @brief Clears the vector (Sets all components to null).
    void clear() noexcept { *this = 0; }

    /**
     * @brief Checker for empty vector (are all values null).
     * @return `true` if vector is null, otherwise `false`
     */
    constexpr bool empty() const { return (x == 0 && y == 0 && z == 0); }

    /* +++ Subtract and sum of two vectors correspondingly. +++ */
    MathVector operator-(MathVector const &other) const { return MathVector(x - other.x, y - other.y, z - other.z); }
    MathVector operator+(MathVector const &other) const { return MathVector(x + other.x, y + other.y, z + other.z); }

    /* +++ Subtract and sum of value to vector +++ */
    MathVector operator-(double value) const { return MathVector(x - value, y - value, z - value); }
    MathVector operator+(double value) const { return MathVector(x + value, y + value, z + value); }

    /* *** Scalar and vector multiplication correspondingly. *** */
    MathVector operator*(double scalar) const { return MathVector(x * scalar, y * scalar, z * scalar); }
    double operator*(MathVector const &other) const { return (x * other.x + y * other.y + z * other.z); }

    /* <=> Comparison operators <=> */
    auto operator<=>(MathVector const &other) const
    {
        if (auto cmp{x <=> other.x}; cmp != std::strong_ordering::equal)
            return cmp;
        if (auto cmp{y <=> other.y}; cmp != std::strong_ordering::equal)
            return cmp;
        return z <=> other.z;
    }
    constexpr bool operator==(MathVector const &other) const { return x == other.x && y == other.y && z == other.z; }
    constexpr bool operator!=(MathVector const &other) const { return !(*this == other); }

    /* << Output stream operator << */
    friend std::ostream &operator<<(std::ostream &os, MathVector const &vector)
    {
        os << std::format("{} {} {}", vector.x, vector.y, vector.z);
        return os;
    }

    /* >> Input stream operator >> */
    friend std::istream &operator>>(std::istream &is, MathVector &vector)
    {
        is >> vector.x >> vector.y >> vector.z;
        return is;
    }
};

/* --> Aliases for human readability. <--*/
using PositionVector = MathVector;
using VelocityVector = MathVector;

#endif // !MATHVECTOR_HPP
