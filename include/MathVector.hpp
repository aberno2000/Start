#ifndef MATHVECTOR_HPP
#define MATHVECTOR_HPP

#include <cmath>

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
    double x{},
        y{},
        z{};

public:
    MathVector() {}
    MathVector(double x_, double y_, double z_) : x(x_), y(y_), z(z_) {}

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

    /* === Getters for each coordinate. === */
    constexpr void setX(double x_) { x = x_; }
    constexpr void setY(double y_) { y = y_; }
    constexpr void setZ(double z_) { z = z_; }

    /// @brief Calculates the module of the coordinate vector.
    constexpr double module() const { return std::sqrt(x * x + y * y + z * z); }

    /// @brief Calculates the distance between two vectors.
    constexpr double distance(MathVector const &other) const { return std::sqrt((x - other.x) * (x - other.x) +
                                                                                (y - other.y) * (y - other.y) +
                                                                                (z - other.z) * (z - other.z)); }

    /* +++ Subtract and sum of two vectors correspondingly. +++ */
    MathVector operator-(MathVector const &other) const { return MathVector(x - other.x, y - other.y, z - other.z); }
    MathVector operator+(MathVector const &other) const { return MathVector(x + other.x, y + other.y, z + other.z); }
    MathVector operator-(double value) const { return MathVector(x - value, y - value, z - value); }
    MathVector operator+(double value) const { return MathVector(x + value, y + value, z + value); }

    /* *** Scalar and vector multiplication correspondingly. *** */
    MathVector operator*(double scalar) const { return MathVector(x * scalar, y * scalar, z * scalar); }
    double operator*(MathVector const &other) const { return (x * other.x + y * other.y + z * other.z); }
};

/* --> Aliases for human readability. <--*/
using PositionVector = MathVector;
using VelocityVector = MathVector;

#endif // !MATHVECTOR_HPP
