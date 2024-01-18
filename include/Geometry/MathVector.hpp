#ifndef MATHVECTOR_HPP
#define MATHVECTOR_HPP

#include <compare>
#include <format>
#include <random>
#include <stdexcept>

#include "Point.hpp"

/**
 * Description of the mathematical vector. In the simplest case, a
 * mathematical object characterized by magnitude and direction.
 *               ->  | x |
 * @brief Vector P = | y |
 *                   | z |
 */
template <typename T>
class MathVector
{
private:
    Point<T> m_p;

public:
    MathVector() : m_p(T(), T(), T()) {}
    MathVector(T x_, T y_, T z_) : m_p(x_, y_, z_) {}

    /**
     * @brief Assignment operator with custom double.
     * Sets all components of vector to custom value.
     */
    MathVector &operator=(T value)
    {
        m_p.x = value;
        m_p.y = value;
        m_p.z = value;
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

        cords.m_p.x = x_;
        cords.m_p.y = y_;
        cords.m_p.z = z_;

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
    constexpr T getX() const { return m_p.x; }
    constexpr T getY() const { return m_p.y; }
    constexpr T getZ() const { return m_p.z; }

    /* === Setters for each component. === */
    constexpr void setX(T x_) { m_p.x = x_; }
    constexpr void setY(T y_) { m_p.y = y_; }
    constexpr void setZ(T z_) { m_p.z = z_; }
    void setXYZ(T x_, T y_, T z_)
    {
        m_p.x = x_;
        m_p.y = y_;
        m_p.z = z_;
    }

    /// @brief Calculates the module of the vector.
    constexpr T module() const { return std::sqrt(m_p.x * m_p.x + m_p.y * m_p.y + m_p.z * m_p.z); }

    /// @brief Calculates the distance between two vectors.
    constexpr T distance(MathVector const &other) const { return m_p.distance(other.m_p); }

    /// @brief Clears the vector (Sets all components to null).
    void clear() noexcept { *this = 0; }

    /**
     * @brief Checker for empty vector (are all values null).
     * @return `true` if vector is null, otherwise `false`.
     */
    constexpr bool isNull() const { return (m_p.x == 0 && m_p.y == 0 && m_p.z == 0); }

    /**
     * @brief Checks if vectors are parallel.
     * `a` is parallel to `b` if `a = k⋅b` or `b=k⋅a` for some scalar `k`.
     * @return `true` if vectors are parallel, otherwise `false`.
     */
    bool isParallel(MathVector const &other) const
    {
        double koef{m_p.x / other.m_p.x};
        return (m_p.y == koef * other.m_p.y) && (m_p.z == koef * other.m_p.z);
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
    MathVector operator-() { return MathVector(-m_p.x, -m_p.y, -m_p.z); }

    /* +++ Subtract and sum of two vectors correspondingly. +++ */
    MathVector operator-(MathVector const &other) const { return MathVector(m_p.x - other.m_p.x, m_p.y - other.m_p.y, m_p.z - other.m_p.z); }
    MathVector operator+(MathVector const &other) const { return MathVector(m_p.x + other.m_p.x, m_p.y + other.m_p.y, m_p.z + other.m_p.z); }

    /* +++ Subtract and sum of value to vector. +++ */
    MathVector operator-(T value) const { return MathVector(m_p.x - value, m_p.y - value, m_p.z - value); }
    MathVector operator+(T value) const { return MathVector(m_p.x + value, m_p.y + value, m_p.z + value); }
    friend MathVector operator+(T value, MathVector const &other) { return MathVector(other.m_p.x + value, other.m_p.y + value, other.m_p.z + value); }

    /* *** Scalar and vector multiplication correspondingly. *** */
    MathVector operator*(T value) const { return MathVector(m_p.x * value, m_p.y * value, m_p.z * value); }
    friend MathVector operator*(T value, MathVector const &other) { return MathVector(other.m_p.x * value, other.m_p.y * value, other.m_p.z * value); }
    T operator*(MathVector const &other) const { return (m_p.x * other.m_p.x + m_p.y * other.m_p.y + m_p.z * other.m_p.z); }
    T dotProduct(MathVector const &other) const { return (*this) * other; }
    MathVector crossProduct(MathVector const &other) const { return MathVector(m_p.y * other.m_p.z - m_p.z * other.m_p.y, m_p.z * other.m_p.x - m_p.x * other.m_p.z, m_p.x * other.m_p.y - m_p.y * other.m_p.x); }

    /* /// Division operator. Vector / value. \\\ */
    MathVector operator/(T value) const
    {
        if (value == 0)
            throw std::overflow_error("Division by null: Elements of vector can't be divided by 0");
        return MathVector(m_p.x / value, m_p.y / value, m_p.z / value);
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
        if (auto cmp{m_p.x <=> other.m_p.x}; cmp != std::strong_ordering::equal)
            return cmp;
        if (auto cmp{m_p.y <=> other.m_p.y}; cmp != std::strong_ordering::equal)
            return cmp;
        return m_p.z <=> other.m_p.z;
    }
    constexpr bool operator==(MathVector const &other) const { return m_p.x == other.m_p.x && m_p.y == other.m_p.y && m_p.z == other.m_p.z; }
    constexpr bool operator!=(MathVector const &other) const { return !(*this == other); }

    /* << Output stream operator. << */
    friend std::ostream &operator<<(std::ostream &os, MathVector const &vector)
    {
        os << std::format("{} {} {}", vector.m_p.x, vector.m_p.y, vector.m_p.z);
        return os;
    }

    /* >> Input stream operator. >> */
    friend std::istream &operator>>(std::istream &is, MathVector &vector)
    {
        is >> vector.m_p.x >> vector.m_p.y >> vector.m_p.z;
        return is;
    }
};

/* --> Aliases for human readability. <-- */
using PositionVector = MathVector<double>;
using VelocityVector = MathVector<double>;

/**
 * @brief Custom type trait to determine if a type is MathVector.
 *
 * Inherits from std::false_type by default, indicating that the default
 * behavior for any type is not to be a MathVector.
 *
 * @tparam T The type to be checked.
 */
template <typename T>
struct is_mathvector : std::false_type
{
};

/**
 * @brief Specialization of the is_mathvector for the MathVector type.
 *
 * This specialization changes the inheritance to std::true_type,
 * specifically for the MathVector type. It effectively states that
 * MathVector is indeed a 'mathvector' type, distinguishing it
 * from other types.
 */
template <std::floating_point T>
struct is_mathvector<MathVector<T>> : std::true_type
{
};

/**
 * @brief Variable template for checking if a type is MathVector.
 *
 * Provides a convenient shorthand for accessing the value member
 * of the is_mathvector type trait. It simplifies the syntax needed
 * to check if a type is MathVector.
 *
 * @tparam T The type to be checked.
 */
template <typename T>
inline constexpr bool is_mathvector_v = is_mathvector<T>::value;

template <typename T>
MathVector(T, T, T) -> MathVector<T>;

#endif // !MATHVECTOR_HPP
