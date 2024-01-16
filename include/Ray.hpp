#ifndef RAY_HPP
#define RAY_HPP

#include "MathVector.hpp"

/**
 * @brief Class representing a Ray in 3D space.
 * @details The Ray is defined by an origin point and a direction vector.
 */
class Ray
{
private:
    PositionVector m_A; // The 1st point of the ray.
    PositionVector m_B; // The 2nd point of the ray.

public:
    /**
     * @brief Constructs a Ray with an origin and a direction.
     * @param A The 1st point of the ray.
     * @param B The 2nd point of the ray.
     */
    Ray(PositionVector const &A, PositionVector const &B);
    Ray(PositionVector &&A, PositionVector &&B) noexcept;

    // Getters for the ray's origin and direction
    [[nodiscard("The origin point is essential for defining the ray's position.")]] PositionVector const &getA() const;

    [[nodiscard("The direction vector is vital for understanding the ray's trajectory.")]] PositionVector const &getB() const;

    /**
     * @brief Checker for ray-triangle intersection.
     * @param vertexA 1st vertex of the triangle.
     * @param vertexB 2nd vertex of the triangle.
     * @param vertexC 3rd vertex of the triangle.
     * @return `true` if ray intersects the triangle, otherwise `false`.
     */
    [[nodiscard("Ignoring the intersection test result can lead to incorrect geometric or physical computations.")]] bool isIntersectsTriangle(PositionVector const &vertexA,
                                                                                                                                               PositionVector const &vertexB,
                                                                                                                                               PositionVector const &vertexC) const;
};

#endif // !RAY_HPP
