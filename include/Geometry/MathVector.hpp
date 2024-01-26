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

    /**
     * @brief Helper func. Rotates the vector around the y-axis.
     * @details The rotation is performed by multiplying the current vector
     *          with the rotation matrix for the y-axis.
     * @param beta The angle of rotation in radians.
     */
    void rotate_y(double beta);

    /**
     * @brief Helper func. Rotates the vector around the z-axis.
     * @details The rotation is performed by multiplying the current vector
     *          with the rotation matrix for the z-axis.
     * @param gamma The angle of rotation in radians.
     */
    void rotate_z(double gamma);

public:
    MathVector();
    MathVector(double, double, double);

    /**
     * @brief Assignment operator with custom double.
     * Sets all components of vector to custom value.
     */
    MathVector &operator=(double);

    /**
     * @brief Fills `MathVector` object with specified values.
     * @param x_ X-coordinate of the point.
     * @param y_ Y-coordinate of the point.
     * @param z_ Z-coordinate of the point.
     * @return Filled structure of the Cartesian coordinates.
     */
    static MathVector createCoordinates(double x_, double y_, double z_);

    /**
     * @brief Creates a random MathVector within the specified range for each coordinate.
     * @param from The lower bound of the range for random values.
     * @param to The upper bound of the range for random values.
     * @return A randomly generated MathVector.
     */
    static MathVector createRandomVector(double from, double to);

    /* === Getters for each component. === */
    constexpr double getX() const { return x; }
    constexpr double getY() const { return y; }
    constexpr double getZ() const { return z; }

    /* === Setters for each component. === */
    constexpr void setX(double x_) { x = x_; }
    constexpr void setY(double y_) { y = y_; }
    constexpr void setZ(double z_) { z = z_; }
    void setXYZ(double, double, double);

    /// @brief Calculates the module of the vector.
    double module() const;

    /// @brief Calculates the distance between two vectors.
    double distance(MathVector const &other) const;
    double distance(MathVector &&other) const;

    /// @brief Clears the vector (Sets all components to null).
    void clear() & _GLIBCXX_NOEXCEPT { *this = 0; }

    /**
     * @brief Checker for empty vector (are all values null).
     * @return `true` if vector is null, otherwise `false`.
     */
    _GLIBCXX_NODISCARD
    constexpr bool
    isNull() const { return (x == 0 && y == 0 && z == 0); }

    /**
     * @brief Checks if vectors are parallel.
     * `a` is parallel to `b` if `a = k⋅b` or `b=k⋅a` for some scalar `k`.
     * @return `true` if vectors are parallel, otherwise `false`.
     */
    bool isParallel(MathVector const &other) const;
    bool isParallel(MathVector &&other) const;

    /**
     * @brief Checks if vectors are orthogonal.
     * `a` is orthogonal to `b` if their dot (scalar) product is equals to 0.
     * @return `true` if vectors are orthogonal, otherwise `false`.
     */
    bool isOrthogonal(MathVector const &other) const;
    bool isOrthogonal(MathVector &&other) const;

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
                                        MathVector const &C);
    static double calculateTriangleArea(MathVector &&A,
                                        MathVector &&B,
                                        MathVector &&C);

    /// @brief Overload of unary minus. Negates all components of vector.
    MathVector operator-();

    /* +++ Subtract and sum of two vectors correspondingly. +++ */
    MathVector operator-(MathVector const &other) const;
    MathVector operator+(MathVector const &other) const;

    /* +++ Subtract and sum of value to vector. +++ */
    MathVector operator-(double value) const;
    MathVector operator+(double value) const;
    friend MathVector operator+(double value, MathVector const &other) { return MathVector(other.x + value, other.y + value, other.z + value); }

    /* *** Scalar and vector multiplication correspondingly. *** */
    MathVector operator*(double value) const;
    friend MathVector operator*(double value, MathVector const &other) { return MathVector(other.x * value, other.y * value, other.z * value); }
    double operator*(MathVector const &other) const;
    double operator*(MathVector &&other) const;
    double dotProduct(MathVector const &other) const;
    double dotProduct(MathVector &&other) const;
    MathVector crossProduct(MathVector const &other) const;
    MathVector crossProduct(MathVector &&other) const;

    /* /// Division operator. Vector / value. \\\ */
    MathVector operator/(double value) const;

    /* <=> Comparison operators. <=> */
    constexpr auto operator<=>(MathVector const &other) const
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

    /// @brief Calculates rotation angles.
    std::pair<double, double> calcBetaGamma() const;

    /**
     * @brief Linear transformation to return to the original system.
     * @param beta The angle of rotation around the Y-axis [rad].
     * @param gamma The angle of rotation around the Z-axis [rad].
     */
    void rotation(double beta, double gamma);
    void rotation(std::pair<double, double> const &p);
    void rotation(std::pair<double, double> &&p) _GLIBCXX_NOEXCEPT;

    /**
     * @brief Returns a MathVector where each component is the sign of the corresponding component.
     * @details The sign function returns -1 if x < 0, 0 if x==0, 1 if x > 0.
     *          For each component of the vector, this method computes the sign and returns
     *          a new vector with these sign values.
     * @return MathVector with each component being -1, 0, or 1.
     */
    MathVector sign() const _GLIBCXX_NOEXCEPT;
};

/* --> Aliases for human readability. <-- */
using PositionVector = MathVector;
using VelocityVector = MathVector;

#endif // !MATHVECTOR_HPP
