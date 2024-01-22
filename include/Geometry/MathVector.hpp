#ifndef MATHVECTOR_HPP
#define MATHVECTOR_HPP

#include <compare>
#include <format>
#include <random>
#include <stdexcept>

#include "../Utilities/Settings.hpp"

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
    double x{};
    double y{};
    double z{};

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

    /**
     * @brief Creates a random MathVector within the specified range for each coordinate.
     * @param from The lower bound of the range for random values.
     * @param to The upper bound of the range for random values.
     * @return A randomly generated MathVector.
     */
    static MathVector createRandomVector(double from, double to)
    {
        std::random_device rd;
        std::mt19937 gen(rd.entropy() ? rd() : time(nullptr));
        std::uniform_real_distribution<double> dis(from, to);
        return MathVector(dis(gen), dis(gen), dis(gen));
    }

    /* === Getters for each component. === */
    constexpr double getX() const { return x; }
    constexpr double getY() const { return y; }
    constexpr double getZ() const { return z; }

    /* === Setters for each component. === */
    constexpr void setX(double x_) { x = x_; }
    constexpr void setY(double y_) { y = y_; }
    constexpr void setZ(double z_) { z = z_; }
    void setXYZ(double x_, double y_, double z_)
    {
        x = x_;
        y = y_;
        z = z_;
    }

    /// @brief Calculates the module of the vector.
    constexpr double module() const { return std::sqrt(x * x + y * y + z * z); }

    /// @brief Calculates the distance between two vectors.
    constexpr double distance(MathVector const &other) const { return std::sqrt(std::pow(other.x - x, 2) +
                                                                                std::pow(other.y - y, 2) +
                                                                                std::pow(other.z - z, 2)); }

    /// @brief Clears the vector (Sets all components to null).
    void clear() noexcept { *this = 0; }

    /**
     * @brief Checker for empty vector (are all values null).
     * @return `true` if vector is null, otherwise `false`.
     */
    constexpr bool isNull() const { return (x == 0 && y == 0 && z == 0); }

    /**
     * @brief Checks if vectors are parallel.
     * `a` is parallel to `b` if `a = k⋅b` or `b=k⋅a` for some scalar `k`.
     * @return `true` if vectors are parallel, otherwise `false`.
     */
    bool isParallel(MathVector const &other) const
    {
        double koef{x / other.x};
        return (y == koef * other.y) && (z == koef * other.z);
    }

    /**
     * @brief Checks if vectors are orthogonal.
     * `a` is orthogonal to `b` if their dot (scalar) product is equals to 0.
     * @return `true` if vectors are orthogonal, otherwise `false`.
     */
    bool isOrthogonal(MathVector const &other) const { return dotProduct(other) == 0; }

    /**
     * @brief Calculates the area of a triangle given its three vertices.
     * @details This function computes the area of a triangle in a 2D space using the vertices A, B, and C.
     *          The formula used is the absolute value of half the determinant of a 2x2 matrix formed by
     *          subtracting the coordinates of A from those of B and C. This method is efficient and
     *          works well for triangles defined in a Cartesian coordinate system.
     * @param A The first vertex of the triangle, represented as a MathVector.
     * @param B The second vertex of the triangle, represented as a MathVector.
     * @param C The third vertex of the triangle, represented as a MathVector.
     * @return The area of the triangle as a double value.
     */
    static double calculateTriangleArea(MathVector const &A,
                                        MathVector const &B,
                                        MathVector const &C)
    {
        return std::fabs((B.getX() - A.getX()) * (C.getY() - A.getY()) -
                         (B.getY() - A.getY()) * (C.getX() - A.getX())) /
               2.0;
    }

    /// @brief Overload of unary minus. Negates all components of vector.
    MathVector operator-() { return MathVector(-x, -y, -z); }

    /* +++ Subtract and sum of two vectors correspondingly. +++ */
    MathVector operator-(MathVector const &other) const { return MathVector(x - other.x, y - other.y, z - other.z); }
    MathVector operator+(MathVector const &other) const { return MathVector(x + other.x, y + other.y, z + other.z); }

    /* +++ Subtract and sum of value to vector. +++ */
    MathVector operator-(double value) const { return MathVector(x - value, y - value, z - value); }
    MathVector operator+(double value) const { return MathVector(x + value, y + value, z + value); }
    friend MathVector operator+(double value, MathVector const &other) { return MathVector(other.x + value, other.y + value, other.z + value); }

    /* *** Scalar and vector multiplication correspondingly. *** */
    MathVector operator*(double value) const { return MathVector(x * value, y * value, z * value); }
    friend MathVector operator*(double value, MathVector const &other) { return MathVector(other.x * value, other.y * value, other.z * value); }
    double operator*(MathVector const &other) const { return (x * other.x + y * other.y + z * other.z); }
    double dotProduct(MathVector const &other) const { return (*this) * other; }
    MathVector crossProduct(MathVector const &other) const { return MathVector(y * other.z - z * other.y, z * other.x - x * other.z, x * other.y - y * other.x); }

    /* /// Division operator. Vector / value. \\\ */
    MathVector operator/(double value) const
    {
        if (value == 0)
            throw std::overflow_error("Division by null: Elements of vector can't be divided by 0");
        return MathVector(x / value, y / value, z / value);
    }

    /* <=> Comparison operators. <=> */
    auto operator<=>(MathVector const &other) const
    {
        /**
         * Compares the components of two vectors (x, y, and z) in a
         * lexicographical order (first by x, then y, and finally z).
         * The `std::strong_ordering::equal` ensures that the comparison
         * result is specific and conforms to the ordering requirements.
         */
        if (auto cmp{x <=> other.x}; cmp != std::strong_ordering::equal)
            return cmp;
        if (auto cmp{y <=> other.y}; cmp != std::strong_ordering::equal)
            return cmp;
        return z <=> other.z;
    }
    constexpr bool operator==(MathVector const &other) const { return x == other.x && y == other.y && z == other.z; }
    constexpr bool operator!=(MathVector const &other) const { return !(*this == other); }

    /* << Output stream operator. << */
    friend std::ostream &operator<<(std::ostream &os, MathVector const &vector)
    {
        os << std::format("{} {} {}", vector.x, vector.y, vector.z);
        return os;
    }

    /* >> Input stream operator. >> */
    friend std::istream &operator>>(std::istream &is, MathVector &vector)
    {
        is >> vector.x >> vector.y >> vector.z;
        return is;
    }
};

/* --> Aliases for human readability. <-- */
using PositionVector = MathVector;
using VelocityVector = MathVector;

#endif // !MATHVECTOR_HPP
